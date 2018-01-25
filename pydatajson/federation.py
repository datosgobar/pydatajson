#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .ckan_utils import map_dataset_to_package
import re


def push_dataset_to_ckan(catalog, dataset_origin_identifier, portal_url, owner_org,
                         apikey, dataset_destination_identifier=None, remote_ckan_class=RemoteCKAN):
    if not catalog.is_valid_catalog():
        raise ValueError('The catalog is invalid')
    dataset = catalog.get_dataset(dataset_origin_identifier)
    ckan_portal = remote_ckan_class(portal_url, apikey=apikey)

#   Create missing groups
    existing_groups = ckan_portal.call_action('group_list')
    dataset_groups = [re.sub(r'(\W+|-)', '', group).lower() for group in dataset['superTheme']]
    new_groups = set(dataset_groups) - set(existing_groups)
    for new_group in new_groups:
        ckan_portal.call_action('group_create', {'name': new_group.lower()})

    package = map_dataset_to_package(dataset)
    package['owner_org'] = owner_org

#   Get license id
    if dataset.get('license'):
        license_list = ckan_portal.call_action('license_list')
        try:
            license = next(license for license in license_list if
                           license['title'] == dataset['license'] or license['url'] == dataset['license'])
            package['license_id'] = license['id']
        except StopIteration:
            package['license_id'] = 'notspecified'
    else:
        package['license_id'] = 'notspecified'

    if dataset_destination_identifier:
        package['id'] = dataset_destination_identifier
        try:
            pushed_package = ckan_portal.call_action('package_update', data_dict=package)
        except NotFound:
            pushed_package = ckan_portal.call_action('package_create', data_dict=package)
    else:
        pushed_package = ckan_portal.call_action('package_create', data_dict=package)

    return pushed_package['id']
