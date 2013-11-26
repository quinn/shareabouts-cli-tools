#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json

spinner_frames = '\|/―'
step = 0

def place_done_callback(place, place_response):
    import sys
    global step

    if place_response.status_code != 204:
        print('Error deleting place %s: %s (%s)' % (place, place_response.status_code, place_response.text))
        return
    else:
        print('\r%s - Deleted %s  ' % (step, spinner_frames[step % 4]), end='')
    sys.stdout.flush()

    step += 1

def main(config, delete=True):
    tool = ShareaboutsTool(config['host'])
    all_places = [
        place for place in
        tool.get_places(config['owner'], config['dataset'])
        #...put a condition here to filter the places, if desired...
        if 'Soc_V' in place
    ]

    print('Deleting the %s places...' % (len(all_places),))

    if delete:
        tool.delete_places(
            config['owner'], config['dataset'], config['key'],
            all_places, place_done_callback)

    print('\nDone!')

if __name__ == '__main__':
    parser = ArgumentParser(description='Remove all places from a dataset.')
    parser.add_argument('configuration', type=str, help='The configuration file name')
    parser.add_argument('--test', '--no-delete', dest='delete', action='store_false', help='Actually delete the places?')

    args = parser.parse_args()
    config = json.load(open(args.configuration))

    main(config, delete=args.delete)