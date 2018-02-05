#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .ckan_utils import map_dataset_to_package
import re


def push_dataset_to_ckan(catalog, catalog_id, owner_org, dataset_origin_identifier, portal_url, apikey):

    if not catalog.is_valid_catalog():
        raise ValueError('The catalog is invalid')
    dataset = catalog.get_dataset(dataset_origin_identifier)
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)

    package = map_dataset_to_package(dataset, catalog_id)
    package['owner_org'] = owner_org

#   Create missing groups
    existing_groups = ckan_portal.call_action('group_list')
    dataset_groups = [re.sub(r'[^a-z-_]+', '', group.lower()) for group in dataset['superTheme']]
    new_groups = set(dataset_groups) - set(existing_groups)
    for new_group in new_groups:
        ckan_portal.call_action('group_create', {'name': new_group.lower()})


#   Get license id
    if dataset.get('license'):
        license_list = ckan_portal.call_action('license_list')
        try:
            ckan_license = next(license_item for license_item in license_list if
                                license_item['title'] == dataset['license'] or
                                license_item['url'] == dataset['license'])
            package['license_id'] = ckan_license['id']
        except StopIteration:
            package['license_id'] = 'notspecified'
    else:
        package['license_id'] = 'notspecified'

    try:
        pushed_package = ckan_portal.call_action('package_update', data_dict=package)
    except NotFound:
        pushed_package = ckan_portal.call_action('package_create', data_dict=package)

    ckan_portal.close()
    return pushed_package['id']
