#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json


def main(config):
    tool = ShareaboutsTool(config['host'])
    all_places = tool.get_places(config['owner'], config['dataset'])
    tool.get_source_place_map(all_places)

if __name__ == '__main__':
    parser = ArgumentParser(description='Print the number of places in a dataset.')
    parser.add_argument('configuration', type=str, help='The configuration file name')

    args = parser.parse_args()
    config = json.load(open(args.configuration))

    main(config)