#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json
import sys

spinner_frames = '\|/―'
step = 0

def place_done_callback(place, place_response):
    global step

    step += 1

    if place_response.status_code == 200:
        print('\r%s - Saved   %s  ' % (step, spinner_frames[step % 4]), end='')
    elif place_response.status_code == 201:
        print('\r%s - Created %s  ' % (step, spinner_frames[step % 4]), end='')
    elif place_response.status_code == 204:
        print('\r%s - Deleted %s  ' % (step, spinner_frames[step % 4]), end='')
    else:
        print('Error saving place %s: %s (%s)' % (place, place_response.status_code, place_response.text))
        return
    sys.stdout.flush()

def main(config, silent=True, create=True, update=True, delete=False):
    tool = ShareaboutsTool(config['host'])
    all_places = tool.get_places(config['owner'], config['dataset'])
    mapped_places = tool.get_source_place_map(all_places, mapped_id_field=config.get('mapped_id_field', '_imported_id'))

    if config['source_file'].endswith('geojson'):
        load_func = tool.updated_from_geojson
    elif config['source_file'].endswith('csv'):
        load_func = tool.updated_from_csv
    else:
        raise ValueError('Unrecognized extension for source file: %s' % (config['source_file'],))

    loaded_places = load_func(
        mapped_places, config['source_file'],
        include_fields=set(config.get('fields', [])),
        mapped_fields=config.get('mapped_fields', {}),
        source_id_field=config.get('source_id_field', None),
        mapped_id_field=config.get('mapped_id_field', '_imported_id'),
        default_values=config.get('default_values', {}))

    print('Saving the places...')

    tool.save_places(
        config['owner'], config['dataset'], config['key'],
        loaded_places, place_done_callback, silent=silent, create=create, update=update)

    source_id_field = config.get('source_id_field', None)
    loaded_ids = set([
        place['properties'].get(source_id_field or 'id')
        for place in loaded_places])
    gone_places = [place for (mapped_id, place) in mapped_places.items() if mapped_id not in loaded_ids]
    gone_place_ids = [str(place.get('id')) for place in gone_places]

    print('\n%s places are no longer present in the imported data: %s.' % (len(gone_places), ', '.join(gone_place_ids)), file=sys.stderr)
    print('Deleting the places...', file=sys.stderr)

    if delete:
        global step
        step = 1
        tool.delete_places(
            config['owner'], config['dataset'], config['key'],
            gone_places, place_done_callback)

    print('\nDone!')

if __name__ == '__main__':
    parser = ArgumentParser(description='Print the number of places in a dataset.')
    parser.add_argument('configuration', type=str, help='The configuration file name')
    parser.add_argument('--test', dest='test', action='store_true', help='Do a test run. Equivalent to --no-create --no-update --no-delete.')
    parser.add_argument('--no-create', dest='create', action='store_false', help='Create non-existant places?')
    parser.add_argument('--no-update', dest='update', action='store_false', help='Update pre-existing places?')
    parser.add_argument('--no-delete', dest='delete', action='store_false', help='Delete no longer existing places?')
    parser.add_argument('--log-activity', dest='silent', action='store_false' ,help='Log save and update activity?')

    args = parser.parse_args()
    config = json.load(open(args.configuration))

    if args.test:
        args.create = False
        args.update = False
        args.delete = False

    main(config, create=args.create, update=args.update, delete=args.delete, silent=args.silent)