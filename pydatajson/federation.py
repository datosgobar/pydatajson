#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extensión de pydatajson para la federación de metadatos de datasets a través de la API de CKAN.
"""
from __future__ import print_function
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .ckan_utils import map_dataset_to_package
from .search import get_datasets


def push_dataset_to_ckan(catalog, catalog_id, owner_org, dataset_origin_identifier, portal_url, apikey):
    """Escribe la metadata de un dataset en el portal pasado por parámetro.

        Args:
            catalog (DataJson): El catálogo de origen que contiene el dataset.
            catalog_id (str): El prefijo con el que va a preceder el id del dataset en catálogo destino.
            owner_org (str): La organización a la cual pertence el dataset.
            dataset_origin_identifier (str): El id del dataset que se va a federar.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le permitan crear o actualizar el dataset.

        Returns:
            str: El id del dataset en el catálogo de destino.
    """
    dataset = catalog.get_dataset(dataset_origin_identifier)
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)

    package = map_dataset_to_package(dataset, catalog_id)
    package['owner_org'] = owner_org

    # Get license id
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

    # Move themes to keywords
    themes = dataset.get('theme')
    if themes:
        package['tags'] = package.get('tags') or []
        theme_taxonomy = catalog.themes
        for theme in themes:
            label = next(x['label'] for x in theme_taxonomy if x['id'] == theme)
            package['tags'].append({'name': label})

    try:
        pushed_package = ckan_portal.call_action(
            'package_update', data_dict=package)
    except NotFound:
        pushed_package = ckan_portal.call_action(
            'package_create', data_dict=package)

    ckan_portal.close()
    return pushed_package['id']


def remove_dataset_from_ckan(identifier, portal_url, apikey):
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)
    ckan_portal.call_action('dataset_purge', data_dict={'id': identifier})


def remove_datasets_from_ckan(portal_url, apikey, filter_in=None, filter_out=None,
                              only_time_series=False, organization=None):
    """Borra un dataset en el portal pasado por parámetro.

            Args:
                portal_url (str): La URL del portal CKAN de destino.
                apikey (str): La apikey de un usuario con los permisos que le permitan borrar el dataset.
                filter_in(dict): Diccionario de filtrado positivo, similar al de search.get_datasets.
                filter_out(dict): Diccionario de filtrado negativo, similar al de search.get_datasets.
                only_time_series(bool): Filtrar solo los datasets que tengan recursos con series de tiempo.
                organization(str): Filtrar solo los datasets que pertenezcan a cierta organizacion.
            Returns:
                None
    """
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)
    identifiers = []
    datajson_filters = filter_in or filter_out or only_time_series
    if datajson_filters:
        identifiers += get_datasets(portal_url + '/data.json', filter_in=filter_in, filter_out=filter_out,
                                    only_time_series=only_time_series, meta_field='identifier')
    if organization:
        query = 'organization:"' + organization + '"'
        search_result = ckan_portal.call_action('package_search', data_dict={
                                                'q': query, 'rows': 500, 'start': 0})
        org_identifiers = [dataset['id']
                           for dataset in search_result['results']]
        start = 500
        while search_result['count'] > start:
            search_result = ckan_portal.call_action('package_search',
                                                    data_dict={'q': query, 'rows': 500, 'start': start})
            org_identifiers += [dataset['id']
                                for dataset in search_result['results']]
            start += 500

        if datajson_filters:
            identifiers = set(identifiers).intersection(set(org_identifiers))
        else:
            identifiers = org_identifiers

    for identifier in identifiers:
        ckan_portal.call_action('dataset_purge', data_dict={'id': identifier})
