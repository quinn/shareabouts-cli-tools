#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json

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

def main(config, silent=True, create=True, update=True):
    tool = ShareaboutsTool(config['host'])
    all_places = tool.get_places(config['owner'], config['dataset'])
    mapped_places = tool.get_source_place_map(all_places)

    if config['source_file'].endswith('geojson'):
        loaded_places = tool.updated_from_geojson(
            mapped_places, config['source_file'],
            include_fields=set(config.get('fields', [])),
            mapped_fields=config.get('mapped_fields', {}),
            source_id_field=config.get('imported_id_field', '_imported_id'))
    elif config['source_file'].endswith('csv'):
        loaded_places = tool.updated_from_csv(
            mapped_places, config['source_file'],
            include_fields=set(config.get('fields', [])),
            mapped_fields=config.get('mapped_fields', {}),
            source_id_field=config.get('imported_id_field', '_imported_id'))
    else:
        raise ValueError('Unrecognized extension for source file: %s' % (config['source_file'],))

    print('Saving the places...')

    tool.save_places(
        config['owner'], config['dataset'], config['key'],
        loaded_places, place_done_callback, silent=silent, create=create, update=update)

    print('\nDone!')

if __name__ == '__main__':
    parser = ArgumentParser(description='Print the number of places in a dataset.')
    parser.add_argument('configuration', type=str, help='The configuration file name')
    parser.add_argument('--no-create', dest='create', action='store_false', help='Create non-existant places?')
    parser.add_argument('--no-update', dest='update', action='store_false' ,help='Update pre-existing places?')
    parser.add_argument('--log-activity', dest='silent', action='store_false' ,help='Log save and update activity?')

    args = parser.parse_args()
    config = json.load(open(args.configuration))

    main(config, create=args.create, update=args.update, silent=args.silent)