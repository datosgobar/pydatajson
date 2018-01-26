#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from dateutil import parser, tz


def append_attribute_to_extra(package, dataset, attribute, serialize=False):
    value = dataset.get(attribute)
    if value:
        if serialize:
            value = json.dumps(value)
        package['extras'].append({'key': attribute, 'value': value})


def map_dataset_to_package(dataset):
    package = dict()
    package['extras'] = []
#   Obligatorios
    package['name'] = re.sub(r'(\W+|-)', '', dataset['title']).lower()
    package['title'] = dataset['title']
    package['private'] = False
    package['notes'] = dataset['description']
    package['author'] = dataset['publisher']['name']

    append_attribute_to_extra(package, dataset, 'issued')
    append_attribute_to_extra(package, dataset, 'accrualPeriodicity')

    distributions = dataset['distribution']
    package['resources'] = map_distributions_to_resources(distributions)

    super_themes = dataset['superTheme']
    package['groups'] = [{'name': re.sub(r'(\W+|-)', '', super_theme).lower()} for super_theme in super_themes]
    package['extras'].append({'key': 'super_theme', 'value': json.dumps(super_themes)})

#   Recomendados y opcionales
    package['url'] = dataset.get('landingPage')
    package['author_email'] = dataset['publisher'].get('mbox')
    append_attribute_to_extra(package, dataset, 'modified')
    append_attribute_to_extra(package, dataset, 'temporal')
    append_attribute_to_extra(package, dataset, 'language')

    spatial = dataset.get('spatial')

    if spatial:
        serializable = type(spatial) is not unicode
        append_attribute_to_extra(package, dataset, 'spatial', serializable)

    contact_point = dataset.get('contactPoint')
    if contact_point:
        package['maintainer'] = contact_point.get('fn')
        package['maintainer_email'] = contact_point.get('hasEmail')

    package['tags'] = []
    keywords = dataset.get('keyword')
    if keywords:
        package['tags'] += [{'name': re.sub(r'(\W+|-)', '', keyword).lower()} for keyword in keywords]
    themes = dataset.get('theme')
    if themes:
        package['tags'] += [{'name': re.sub(r'(\W+|-)', '', theme).lower()} for theme in themes]

    return package


def convert_iso_string_to_utc(date_string):
    date_time = parser.parse(date_string)
    utc_date_time = date_time.astimezone(tz.tzutc())
    utc_date_time = utc_date_time.replace(tzinfo=None)
    return utc_date_time.isoformat()


def map_distributions_to_resources(distributions):
    resources = []
    for distribution in distributions:
        resource = dict()
#       Obligatorios
        resource['id'] = distribution['identifier']
        resource['name'] = distribution['title']
        resource['url'] = distribution['downloadURL']
        resource['created'] = convert_iso_string_to_utc(distribution['issued'])
#       Recomendados y opcionales
        resource['description'] = distribution.get('description')
        resource['format'] = distribution.get('format')
        last_modified = distribution.get('modified')
        if last_modified:
            resource['last_modified'] = convert_iso_string_to_utc(last_modified)
        resource['mimetype'] = distribution.get('mediaType')
        resource['size'] = distribution.get('byteSize')
        resources.append(resource)

    return resources
