#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division

from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json
import pybars
import requests
from pybars._compiler import Scope
from handlebars_utils import helpers


dataset = None

def _with_place(this, options):
    place_id = int(this['place'].rsplit('/', 1)[-1])
    context = dataset.places.get(place_id).serialize()

    scope = Scope(context, this)
    return options['fn'](scope)
helpers['with_place'] = _with_place


def main(config, report):
    template_filename = report.get('summary_template')
    assert template_filename, 'No template file specified'

    tool = ShareaboutsTool(config['host'])
    tool.get_places(config['owner'], config['dataset'])
    tool.get_submissions(config['owner'], config['dataset'])

    # Compile the template
    compiler = pybars.Compiler()
    with open(report['summary_template'], 'rb') as template_file:
        template_source = template_file.read().decode()
        template = compiler.compile(template_source)

    global dataset
    dataset = tool.api.account(config['owner']).dataset(config['dataset'])

    # Render the template
    rendered_template = template({
        'dataset': dataset.serialize(),
        'report': report
    }, helpers=helpers)

    # Print the template, and send it where it needs to go
    print(rendered_template)

    # Send an email
    # NOTE: Remember, you must register your sender email addresses with
    #       Postmark: https://postmarkapp.com/signatures
    # email_body = {
    #     "From" : config['email']['sender'],
    #     "To" : config['email']['recipient'],
    #     "Subject" : "Weekly summary",
    #     "HtmlBody" : rendered_template,
    #     # "TextBody" : rendered_template,
    #     "ReplyTo" : config['email']['sender'],
    #     # "Headers" : [{}]
    # }

    # email_headers = {
    #     'Content-type': 'application/json',
    #     'X-Postmark-Server-Token': config['postmarkapp_token']
    # }

    # response = requests.post('http://api.postmarkapp.com/email',
    #     data=json.dumps(email_body),
    #     headers=email_headers
    # )

    # if response.status_code != 200:
    #     print('Received a non-success response (%s): %s' % (response.status_code, response.content))

if __name__ == '__main__':
    parser = ArgumentParser(description='Print the number of places in a dataset.')
    parser.add_argument('configuration', help='The dataset configuration file name')
    parser.add_argument('report', help='The report configuration file name')
    # parser.add_argument('--template', help='The path to the template file.')
    # parser.add_argument('--begin', default='0001-01-01', help='The date from which you want results. Submissions on or after this date will be included.')
    # parser.add_argument('--end', default='9999-12-31', help='The date until which you want results. Submissions before this date will be included.')

    args = parser.parse_args()
    config = json.load(open(args.configuration))
    report = json.load(open(args.report))

    # main(config, args.template, args.begin, args.end)
    main(config, report)