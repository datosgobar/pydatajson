#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import time
from dateutil import parser, tz
from .helpers import title_to_name


def append_attribute_to_extra(package, dataset, attribute, overriding_name=None, serialize=False):
    value = dataset.get(attribute)
    key = overriding_name or attribute
    if value:
        if serialize:
            value = json.dumps(value)
        package['extras'].append({'key': key, 'value': value})


def map_dataset_to_package(dataset, catalog_id):
    package = dict()
    package['extras'] = []
#   Obligatorios
    package['id'] = catalog_id+'_'+dataset['identifier']
    package['name'] = title_to_name(dataset['title'], decode=False)
    package['title'] = dataset['title']
    package['private'] = False
    package['notes'] = dataset['description']
    package['author'] = dataset['publisher']['name']

    append_attribute_to_extra(package, dataset, 'issued')
    append_attribute_to_extra(package, dataset, 'accrualPeriodicity')

    distributions = dataset['distribution']
    package['resources'] = map_distributions_to_resources(distributions, catalog_id)

    super_themes = dataset['superTheme']
    package['groups'] = [{'name': title_to_name(super_theme, decode=False)} for super_theme in super_themes]
    append_attribute_to_extra(package, dataset, 'superTheme', overriding_name='super_theme', serialize=True)

#   Recomendados y opcionales
    package['url'] = dataset.get('landingPage')
    package['author_email'] = dataset['publisher'].get('mbox')
    append_attribute_to_extra(package, dataset, 'modified')
    append_attribute_to_extra(package, dataset, 'temporal')
    append_attribute_to_extra(package, dataset, 'source')
    append_attribute_to_extra(package, dataset, 'language', serialize=True)

    spatial = dataset.get('spatial')

    if spatial:
        serializable = type(spatial) is list
        append_attribute_to_extra(package, dataset, 'spatial', serializable)

    contact_point = dataset.get('contactPoint')
    if contact_point:
        package['maintainer'] = contact_point.get('fn')
        package['maintainer_email'] = contact_point.get('hasEmail')

    keywords = dataset.get('keyword')
    if keywords:
        package['tags'] = [{'name': keyword} for keyword in keywords]

    return package


def convert_iso_string_to_utc(date_string):
    date_time = parser.parse(date_string)
    if date_time.time() == time(0):
        return date_string

    if date_time.tzinfo is not None:
        utc_date_time = date_time.astimezone(tz.tzutc())
    else:
        utc_date_time = date_time
    utc_date_time = utc_date_time.replace(tzinfo=None)
    return utc_date_time.isoformat()


def map_distributions_to_resources(distributions, catalog_id):
    resources = []
    for distribution in distributions:
        resource = dict()
#       Obligatorios
        resource['id'] = catalog_id + '_' + distribution['identifier']
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
        resource['accessURL'] = distribution.get('accessURL')
        resource['fileName'] = distribution.get('fileName')
        dist_fields = distribution.get('field')
        if dist_fields:
            resource['attributesDescription'] = json.dumps(dist_fields)
        resources.append(resource)

    return resources
