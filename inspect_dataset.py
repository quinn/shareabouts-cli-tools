#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json


def main(config):
    tool = ShareaboutsTool(config['host'])
    all_places = tool.get_places(config['owner'], config['dataset'])
    all_submissions = tool.get_submissions(config['owner'], config['dataset'])

    place_fields = set()
    for place in tool.api.account(config['owner']).dataset(config['dataset']).places:
        place_fields.update(place._data['properties'].keys())

    print('Place fields: ')
    for field in place_fields:
        print('  - %s' % (field,))

    for sset in tool.api.account(config['owner']).dataset(config['dataset']).submission_sets:
        submission_fields = set()

        for submission in sset:
            submission_fields.update(submission._data.keys())

        print('%s fields:' % (sset.name.title(),))
        for field in submission_fields:
            print('  - %s' % (field,))

if __name__ == '__main__':
    parser = ArgumentParser(description='Print the number of places in a dataset.')
    parser.add_argument('configuration', type=str, help='The configuration file name')

    args = parser.parse_args()
    config = json.load(open(args.configuration))

    main(config)