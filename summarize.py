#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division

from shareabouts_tool import ShareaboutsTool
from argparse import ArgumentParser
import json
import os
import pybars
import pytz
import sys
from handlebars_utils import helpers

try:
    # Python 2
    str_type = unicode
except NameError:
    # Python 3
    str_type = str


dataset = None

def _with_place(this, options, url):
    place_id = int(url.rsplit('/', 1)[-1])
    place_context = dataset.places.get(place_id).serialize()
    return options['fn'](place_context)
helpers['with_place'] = _with_place

def _created_between(this, options, begin, end, context=None):
    if context is None:
        context = this

    if not context:
        return options['inverse'](this)

    def get_created_date(d):
        try:
            return d['created_datetime']
        except KeyError:
            return d['properties']['created_datetime']

    filtered_context = list(filter((lambda d: begin <= get_created_date(d) < end), context))

    if len(filtered_context) == 0:
        return options['inverse'](this)

    return options['fn'](filtered_context)
helpers['created_between'] = _created_between


def main(config, report):
    template_filename = report.get('summary_template')
    assert template_filename, 'No template file specified'

    # Download the data
    tool = ShareaboutsTool(config['host'])
    places = tool.get_places(config['owner'], config['dataset'])
    submissions = tool.get_submissions(config['owner'], config['dataset'])

    global dataset
    dataset = tool.api.account(config['owner']).dataset(config['dataset'])

    # Compile the template
    print ('Compiling and rendering the template(s): %s' % (report['summary_template'],), file=sys.stderr)

    compiler = pybars.Compiler()
    with open(report['summary_template'], 'rb') as template_file:
        template_source = template_file.read().decode()
        template = compiler.compile(template_source)

    # Convert times to local timezone
    tzname = config.get('timezone') or report.get('timezone') or None
    try:
        localtz = pytz.timezone(tzname) if tzname else pytz.utc
    except pytz.exceptions.UnknownTimeZoneError:
        print ('I do not recognize the timezone "%s".' % tzname)
        print ('To see a list of common timezone names, run '
               '"common_timezones.py".')
        return 1

    tool.convert_times(places, localtz)
    tool.convert_times(submissions, localtz)
    tool.convert_times(dataset, localtz)

    helpers['config'] = lambda this, attr: config[attr]
    helpers['report'] = lambda this, attr: report[attr]

    # Render the template
    rendered_template = template({
        'dataset': dataset.serialize(),
        'report': report,
        'config': config
    }, helpers=helpers)

    # Print the template, and send it where it needs to go
    doc = str_type(rendered_template)
    with os.fdopen(sys.stdout.fileno(), 'wb') as stdout_b:
        stdout_b.write(doc.encode('utf-8'))

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

    return 0

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
    result = main(config, report) or 0
    sys.exit(result)