#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
from datetime import time
from dateutil import parser, tz
from .helpers import title_to_name


def append_attribute_to_extra(package, dataset, attribute, serialize=False):
    value = dataset.get(attribute)
    if value:
        if serialize:
            value = json.dumps(value)
        package['extras'].append({'key': attribute, 'value': value})


def map_dataset_to_package(catalog, dataset, owner_org, catalog_id=None,
                           demote_superThemes=True, demote_themes=True):
    package = dict()
    package['extras'] = []
#   Obligatorios
    package['id'] = catalog_id+'_'+dataset['identifier'] if catalog_id else dataset['identifier']
    package['name'] = title_to_name(catalog_id+'-'+dataset['title'] if catalog_id else dataset['title'])
    package['title'] = dataset['title']
    package['private'] = False
    package['notes'] = dataset['description']
    package['author'] = dataset['publisher']['name']
    package['owner_org'] = owner_org

    append_attribute_to_extra(package, dataset, 'issued')
    append_attribute_to_extra(package, dataset, 'accrualPeriodicity')

    distributions = dataset['distribution']
    package['resources'] = map_distributions_to_resources(distributions, catalog_id)

    super_themes = dataset['superTheme']
    append_attribute_to_extra(package, dataset, 'superTheme', serialize=True)
    if demote_superThemes:
        package['groups'] = [{'name': title_to_name(super_theme, decode=False)} for super_theme in super_themes]


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

    # Move themes to keywords
    themes = dataset.get('theme', [])
    if themes and demote_themes:
        package['tags'] = package.get('tags', [])
        for theme in themes:
            label = catalog.get_theme(identifier=theme)['label']
            label = re.sub(r'[^\wá-úÁ-ÚñÑ .-]+', '', label, flags=re.UNICODE)
            package['tags'].append({'name': label})
    else:
        package['groups'] = package.get('groups', []) + [{'name': title_to_name(theme, decode=False)}
                                                         for theme in themes]

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


def map_distributions_to_resources(distributions, catalog_id=None):
    resources = []
    for distribution in distributions:
        resource = dict()
#       Obligatorios
        resource['id'] = catalog_id + '_' + distribution['identifier'] if catalog_id else distribution['identifier']
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
        fileName = distribution.get('fileName')
        if fileName:
            resource['fileName'] = fileName
        dist_fields = distribution.get('field')
        if dist_fields:
            resource['attributesDescription'] = json.dumps(dist_fields)
        resources.append(resource)

    return resources


def map_theme_to_group(theme):

    return {
        "name": title_to_name(theme.get('id') or theme['label']),
        "title": theme.get('label'),
        "description": theme.get('description'),
    }
