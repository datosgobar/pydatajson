#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import re
import logging

from dateutil import parser, tz

from pydatajson.constants import DEFAULT_TIMEZONE
from .helpers import title_to_name
from . import custom_exceptions as ce

logger = logging.getLogger('pydatajson')


def append_attribute_to_extra(package, dataset, attribute, serialize=False):
    value = dataset.get(attribute)
    if value:
        if serialize:
            value = json.dumps(value)
        package['extras'].append({'key': attribute, 'value': value})


def map_dataset_to_package(catalog, dataset, owner_org, catalog_id=None,
                           demote_superThemes=True, demote_themes=True,
                           origin_tz=DEFAULT_TIMEZONE,
                           dst_tz=DEFAULT_TIMEZONE):
    package = dict()
    package['extras'] = []

    # Obligatorios
    package['id'] = catalog_id + '_' + dataset['identifier'] \
        if catalog_id else dataset['identifier']
    package['name'] = title_to_name(
        catalog_id + '-' +
        dataset['title'] if catalog_id else dataset['title'],
        max_len=100, use_complete_words=True
    )
    package['title'] = dataset['title']
    package['private'] = False
    package['notes'] = dataset['description']
    package['author'] = dataset['publisher']['name']
    package['owner_org'] = owner_org

    append_attribute_to_extra(package, dataset, 'issued')
    append_attribute_to_extra(package, dataset, 'accrualPeriodicity')

    distributions = dataset['distribution']
    package['resources'] = map_distributions_to_resources(
        distributions, catalog_id, origin_tz=origin_tz, dst_tz=dst_tz)

    super_themes = dataset['superTheme']
    append_attribute_to_extra(package, dataset, 'superTheme', serialize=True)
    if demote_superThemes:
        package['groups'] = [
            {'name': title_to_name(super_theme, decode=False)}
            for super_theme in super_themes
        ]

    # Recomendados y opcionales
    package['url'] = dataset.get('landingPage')
    package['author_email'] = dataset['publisher'].get('mbox')
    append_attribute_to_extra(package, dataset, 'modified')
    append_attribute_to_extra(package, dataset, 'temporal')
    append_attribute_to_extra(package, dataset, 'source')
    append_attribute_to_extra(package, dataset, 'language', serialize=True)

    spatial = dataset.get('spatial')
    if spatial:
        serializable = isinstance(spatial, list)
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
            # si falla continúa sin agregar ese theme a los tags del dataset
            try:
                label = _get_theme_label(catalog, theme)
                package['tags'].append({'name': label})
            except Exception:
                logger.exception('Theme no presente en catálogo.')
                continue
    else:
        package.setdefault('groups', [])
        for theme in themes:
            theme_dict = catalog.get_theme(identifier=theme) or \
                         catalog.get_theme(label=theme)
            if theme_dict:
                package['groups'].append(map_theme_to_group(theme_dict))
    return package


def _get_theme_label(catalog, theme):
    """Intenta conseguir el theme por id o por label."""
    try:
        label = catalog.get_theme(identifier=theme)['label']
    except BaseException:
        try:
            label = catalog.get_theme(label=theme)['label']
        except BaseException:
            raise ce.ThemeNonExistentError(theme)

    label = re.sub(r'[^\wá-úÁ-ÚñÑ .-]+', '',
                   label, flags=re.UNICODE)
    return label


def convert_iso_string_to_dst_timezone(date_string,
                                       origin_tz=DEFAULT_TIMEZONE,
                                       dst_tz=DEFAULT_TIMEZONE):
    date_time = parser.parse(date_string)

    dest_timezone = tz.gettz(dst_tz)
    if date_time.tzinfo is None:
        origin_timezone = tz.gettz(origin_tz)
        date_time = date_time.replace(tzinfo=origin_timezone)

    date_time = date_time.astimezone(dest_timezone)

    date_time = date_time.replace(tzinfo=None)
    return date_time.isoformat()


def map_distributions_to_resources(distributions, catalog_id=None,
                                   origin_tz=DEFAULT_TIMEZONE,
                                   dst_tz=DEFAULT_TIMEZONE):
    resources = []
    for distribution in distributions:
        resource = dict()
        #       Obligatorios
        resource['id'] = catalog_id + '_' + distribution['identifier'] \
            if catalog_id else distribution['identifier']
        resource['name'] = distribution['title']
        resource['url'] = distribution['downloadURL']
        resource['created'] = \
            convert_iso_string_to_dst_timezone(distribution['issued'],
                                               origin_tz=origin_tz,
                                               dst_tz=dst_tz)
        #       Recomendados y opcionales
        resource['description'] = distribution.get('description')
        resource['format'] = distribution.get('format')
        last_modified = distribution.get('modified')
        if last_modified:
            resource['last_modified'] = \
                convert_iso_string_to_dst_timezone(last_modified,
                                                   origin_tz=origin_tz,
                                                   dst_tz=dst_tz)
        resource['mimetype'] = distribution.get('mediaType')
        resource['size'] = distribution.get('byteSize')
        resource['accessURL'] = distribution.get('accessURL')
        resource['resource_type'] = distribution.get('type')
        file_name = distribution.get('fileName')
        if file_name:
            resource['fileName'] = file_name
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
