#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool

### These change from time to time. They should be stored in a config file
SOURCE_FILE = 'data/RH_combined.geojson'
SOURCE_FORMAT = 'geojson'
DATASET_OWNER = 'openplans'
DATASET_SLUG = 'devnyrrh'
DATASET_KEY = 'YjY4YzBjYTk1N2E2YWZjOWMzYmE5MWUy'
MAPPED_FIELDS = {
    'ASSET_CLAS': 'location_type'
}

# SOURCE_FILE = 'data/RH_combined.geojson'
# SOURCE_FORMAT = 'geojson'
# DATASET_OWNER = 'demo-user'
# DATASET_SLUG = 'mirrornyrrh'
# DATASET_KEY = 'YmJhNzRlMmRkYTdjOGUyNjBkMWJlOTZh'
# MAPPED_FIELDS = {
#     'ASSET_CLAS': 'location_type'
# }

SOURCE_FILE = 'data/RH_combined.geojson'
SOURCE_FORMAT = 'geojson'
DATASET_OWNER = 'demo-user'
DATASET_SLUG = 'mirrornyrrh'
DATASET_KEY = 'ZWJmMjE4NTUxOTkwZmU5YWM2MmEwZTU1'
MAPPED_FIELDS = {
    'ASSET_CLAS': 'location_type'
}

# SOURCE_FILE = 'data/RH_combined.geojson'
# SOURCE_FORMAT = 'geojson'
# DATASET_OWNER = 'nyrising'
# DATASET_SLUG = 'rh'
# DATASET_KEY = 'ZGQ5OTNkZWQ1NzI3NGRjYjA0ZWY2NTA0'
# MAPPED_FIELDS = {
#     'ASSET_CLAS': 'location_type'
# }

INCLUDE_FIELDS = set([
    'Address',
    'ASSET_CLAS',
    'ASSET',
    'OwnerName',
    'AssetID',
    'Zone',
    'Socially_V',
    'Name',
    'notes',
    'UID',
    'displaynam',
    'displayadd',
])

# SOURCE_FILE = 'data/CD39.csv'
# SOURCE_FORMAT = 'csv'
# DATASET_OWNER = 'pbnyc'
# DATASET_SLUG = 'd39'
# DATASET_KEY = 'ZGUxZjZiMWFmYzYwMGEzYjg4OGZmMjlm'
# MAPPED_FIELDS = {
#     'ASSET_CLAS': 'location_type'
# }
###

### These can change, but seldom need to, as these are reasonable defaults
DEFAULT_ID_FIELD_NAME = '_imported_id'
SHAREABOUTS_HOST = 'http://api.shareabouts.org'
# SHAREABOUTS_HOST = 'http://devsaapi-civicworks.dotcloud.com'
SHAREABOUTS_HOST = 'http://localhost:8000'
###

tool = ShareaboutsTool(SHAREABOUTS_HOST)
all_places = tool.get_places(DATASET_OWNER, DATASET_SLUG)
mapped_places = tool.get_source_place_map(all_places)

if SOURCE_FORMAT == 'geojson':
    loaded_places = tool.updated_from_geojson(mapped_places, SOURCE_FILE)
elif SOURCE_FORMAT == 'csv':
    loaded_places = tool.updated_from_csv(mapped_places, SOURCE_FILE)
else:
    raise ValueError('Unrecognized source format: %s' % (SOURCE_FORMAT,))

print('Saving the places...')

# Upload the places, with PUT if they have a URL, otherwise with POST
spinner_frames = '\|/―'
step = 0

def place_done_callback(place, place_response):
    global step

    if place_response.status_code not in (200, 201):
        print('Error saving place %s: %s (%s)' % (place, place_response.status_code, place_response.text))
        return
    elif place_response.status_code == 200:
        print('\r%s - Saved   %s  ' % (step, spinner_frames[step % 4]), end='')
    else:
        print('\r%s - Created %s  ' % (step, spinner_frames[step % 4]), end='')

    step += 1

tool.save_places(DATASET_OWNER, DATASET_SLUG, DATASET_KEY, loaded_places, place_done_callback)

print('')
print('Done!')