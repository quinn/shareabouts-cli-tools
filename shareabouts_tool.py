from __future__ import print_function, unicode_literals, division

import csv
import json
import math
import requests
import threading


class ShareaboutsTool (object):
    def __init__(self, host):
        self.places_url_template = host + '/api/v2/%s/datasets/%s/places'

    def get_places(self, owner, dataset):
        places_url = self.places_url_template % (owner, dataset)

        # Load all of the dataset's places into memory, mapped by their ids
        print('Loading places from %s...' % places_url)

        all_places = {}
        places_page_url = places_url
        total_num_pages = None
        num_loaded_pages = 0

        while places_page_url:
            places_response = requests.get(places_page_url)

            assert places_response.status_code == 200

            places_page = json.loads(places_response.text)

            assert 'features' in places_page
            assert 'metadata' in places_page

            if total_num_pages is None:
                # Calculate the total number of pages if it hasn't been calculated
                # yet.
                if len(places_page['features']) > 0:
                    total_num_pages = int(math.ceil(places_page['metadata'].get('length') / len(places_page['features'])))
                else:
                    total_num_pages = 0
                    break

            for place in places_page['features']:
                all_places[place['id']] = place

            num_loaded_pages += 1
            print('\r...loaded page %s of %s  ' % (num_loaded_pages, total_num_pages), end='')
            places_page_url = places_page['metadata'].get('next')

        return list(all_places.values())
    
    def get_source_place_map(self, all_places, source_id_field='_imported_id'):
        mapped_places = {}

        for place in all_places:
            # If a place has an field that matches the id_field_name, assume
            # that it corresponds to the ID of the place from the imported
            # data.
            if source_id_field in place['properties']:
                source_id = place['properties'][source_id_field]
                mapped_places[source_id] = place

        print('\nSaw %s places, with %s having come from somewhere else.' % (len(all_places), len(mapped_places)))
        return mapped_places

    def updated_from_geojson(self, mapped_places, source_filename, source_id_field='_imported_id', include_fields=set(), mapped_fields={}):
        print('Loading places from %s...' % source_filename)

        # Load the new places from the file
        loaded_places = []

        with open(source_filename) as geojson_file:
            loaded_featureset = json.load(geojson_file)

            assert 'features' in loaded_featureset
            for feature in loaded_featureset['features']:
                # Take note of the source data's ID
                feature_id = feature['id']

                # Make a new "place" out of a copy of the source data
                place = feature.copy()

                # Keep only fields we want
                if include_fields:
                    for field in list(place['properties'].keys()):
                        if field not in include_fields:
                            del place['properties'][field]

                # Use the source ID to match any existing data, if it exists
                if feature_id in mapped_places:
                    old_place = mapped_places[feature_id]
                    if 'id' in old_place:
                        place['id'] = old_place['id']
                    elif 'id' in old_place['properties']:
                        place['id'] = old_place['properties']['id']
                    else:
                        del place['id']
                    place['properties']['url'] = old_place['properties']['url']
                else:
                    place.pop('id')

                # Apply field mappings
                for field_name in list(place['properties'].keys()):
                    if field_name in mapped_fields:
                        place['properties'][mapped_fields[field_name]] = place['properties'][field_name]
                place['properties'][source_id_field] = feature_id

                loaded_places.append(place)

        print('%s place(s) loaded, with %s having been seen before.' % (len(loaded_places), len([place for place in loaded_places if 'url' in place['properties']])))
        return loaded_places

    def updated_from_csv(self, mapped_places, source_filename, source_id_field='_imported_id', include_fields=set(), mapped_fields={}):
        print('Loading places from %s...' % source_filename)

        # Load the new places from the file
        loaded_places = []

        with open(source_filename) as csv_file:
            reader = csv.reader(csv_file)
            headers = None

            for row in reader:
                if headers is None:
                    headers = row
                    continue
                properties = dict(zip(headers, row))

                # Take note of the source ID
                feature_id = properties['id']

                # Make a new "place" from the source data
                place = {
                    'properties': properties,
                    'id': feature_id,
                    'type': 'Feature'
                }

                # Special case for lat/lng
                if 'lat' in properties and 'lon' in properties:
                    place['geometry'] = {
                        'type': 'Point',
                        'coordinates': [float(properties.pop('lon')), float(properties.pop('lat'))]
                    }

                # Keep only fields we want
                if include_fields:
                    for field in place['properties'].keys():
                        if field not in include_fields:
                            del place['properties'][field]
                
                # Use the source ID to match and existing data
                if feature_id in mapped_places:
                    old_place = mapped_places[feature_id]
                    place['id'] = old_place['id'] if 'id' in old_place else old_place['properties']['id']
                    place['properties']['url'] = old_place['properties']['url']
                else:
                    place.pop('id')

                # Apply field mappings
                for field_name in list(place['properties'].keys()):
                    if field_name in mapped_fields:
                        place['properties'][mapped_fields[field_name]] = place['properties'][field_name]
                place['properties'][source_id_field] = feature_id

                loaded_places.append(place)

        print('%s place(s) loaded, with %s having been seen before.' % (len(loaded_places), len([place for place in loaded_places if 'url' in place['properties']])))
        return loaded_places

    def save_places(self, owner, dataset, dataset_key, loaded_places, callback):
        # Upload the places, with PUT if they have a URL, otherwise with POST
        places_url = self.places_url_template % (owner, dataset)

        save_threads = []
        for place in loaded_places:
            thread = UploadPlaceThread(place, places_url, dataset_key, callback)
            thread.start()
            save_threads.append(thread)

        for thread in save_threads:
            thread.join()

    def delete_places(self, owner, dataset, dataset_key, loaded_places, callback):
        delete_threads = []
        for place in loaded_places:
            thread = DeletePlaceThread(place, dataset_key, callback)
            thread.start()
            delete_threads.append(thread)

        for thread in delete_threads:
            thread.join()


class UploadPlaceThread (threading.Thread):
    finite_threads = threading.BoundedSemaphore(value=4)

    def __init__(self, place, places_url, dataset_key, callback):
        self.place = place
        self.places_url = places_url
        self.dataset_key = dataset_key
        self.callback = callback
        super(UploadPlaceThread, self).__init__()

    def run(self):
        place = self.place
        with UploadPlaceThread.finite_threads:
            place_url = self.place['properties'].get('url')
            if place_url is not None:
                place_response = requests.put(
                    place_url,
                    data=json.dumps(place),
                    headers={
                        'content-type': 'application/json',
                        'x-shareabouts-silent': 'true',
                        'x-shareabouts-key': self.dataset_key,
                        'x-csrftoken': '123'
                    },
                    cookies={'csrftoken': '123'}
                )

            else:
                place_response = requests.post(
                    self.places_url,
                    data=json.dumps(place),
                    headers={
                        'content-type': 'application/json',
                        'x-shareabouts-silent': 'true',
                        'x-shareabouts-key': self.dataset_key,
                        'x-csrftoken': '123'
                    },
                    cookies={'csrftoken': '123'}
                )

            self.callback(place, place_response)


class DeletePlaceThread (threading.Thread):
    finite_threads = threading.BoundedSemaphore(value=4)

    def __init__(self, place, dataset_key, callback):
        self.place = place
        self.dataset_key = dataset_key
        self.callback = callback
        super(DeletePlaceThread, self).__init__()

    def run(self):
        place = self.place
        with DeletePlaceThread.finite_threads:
            place_url = place['properties'].get('url')
            assert place_url is not None
            place_response = requests.delete(
                place_url,
                headers={
                    'content-type': 'application/json',
                    'x-shareabouts-silent': 'true',
                    'x-shareabouts-key': self.dataset_key,
                    'x-csrftoken': '123'
                },
                cookies={'csrftoken': '123'}
            )

            self.callback(place, place_response)
