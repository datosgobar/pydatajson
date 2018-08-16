#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extensión de pydatajson para la federación de metadatos de datasets a través
de la API de CKAN.
"""

from __future__ import print_function, unicode_literals
import logging
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .ckan_utils import map_dataset_to_package, map_theme_to_group
from .search import get_datasets

logger = logging.getLogger('pydatajson.federation')


def push_dataset_to_ckan(catalog, owner_org, dataset_origin_identifier,
                         portal_url, apikey, catalog_id=None,
                         demote_superThemes=True, demote_themes=True):
    """Escribe la metadata de un dataset en el portal pasado por parámetro.

        Args:
            catalog (DataJson): El catálogo de origen que contiene el dataset.
            owner_org (str): La organización a la cual pertence el dataset.
            dataset_origin_identifier (str): El id del dataset que se va a
                federar.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
            catalog_id (str): El prefijo con el que va a preceder el id del
                dataset en catálogo destino.
            demote_superThemes(bool): Si está en true, los ids de los super
                themes del dataset, se propagan como grupo.
            demote_themes(bool): Si está en true, los labels de los themes
                del dataset, pasan a ser tags. Sino, se pasan como grupo.
        Returns:
            str: El id del dataset en el catálogo de destino.
    """
    dataset = catalog.get_dataset(dataset_origin_identifier)
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)

    package = map_dataset_to_package(catalog, dataset, owner_org, catalog_id,
                                     demote_superThemes, demote_themes)

    # Get license id
    if dataset.get('license'):
        license_list = ckan_portal.call_action('license_list')
        try:
            ckan_license = next(
                license_item for license_item in license_list if
                license_item['title'] == dataset['license'] or
                license_item['url'] == dataset['license']
            )
            package['license_id'] = ckan_license['id']
        except StopIteration:
            package['license_id'] = 'notspecified'
    else:
        package['license_id'] = 'notspecified'

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


def remove_harvested_ds_from_ckan(catalog, portal_url, apikey,
                                  catalog_id=None, original_ids=None):
    catalog_id = catalog_id or catalog.get("identifier")
    assert catalog_id, "Necesita un identificador de catálogo."

    if not original_ids:
        original_ids = catalog.get_datasets(meta_field="identifier")
    harvested_ids = ["_".join([catalog_id, original_id])
                     for original_id in original_ids]

    for harvested_id in harvested_ids:
        try:
            remove_dataset_from_ckan(harvested_id, portal_url, apikey)
            logger.info("{} eliminado de {}".format(harvested_id, catalog_id))
        except Exception:
            logger.exception(
                "{} de {} no existe.".format(
                    harvested_id, catalog_id))


def remove_datasets_from_ckan(portal_url, apikey, filter_in=None,
                              filter_out=None, only_time_series=False,
                              organization=None):
    """Borra un dataset en el portal pasado por parámetro.

            Args:
                portal_url (str): La URL del portal CKAN de destino.
                apikey (str): La apikey de un usuario con los permisos que le
                    permitan borrar el dataset.
                filter_in(dict): Diccionario de filtrado positivo, similar al
                    de search.get_datasets.
                filter_out(dict): Diccionario de filtrado negativo, similar al
                    de search.get_datasets.
                only_time_series(bool): Filtrar solo los datasets que tengan
                    recursos con series de tiempo.
                organization(str): Filtrar solo los datasets que pertenezcan a
                    cierta organizacion.
            Returns:
                None
    """
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)
    identifiers = []
    datajson_filters = filter_in or filter_out or only_time_series
    if datajson_filters:
        identifiers += get_datasets(
            portal_url + '/data.json',
            filter_in=filter_in, filter_out=filter_out,
            only_time_series=only_time_series, meta_field='identifier'
        )
    if organization:
        query = 'organization:"' + organization + '"'
        search_result = ckan_portal.call_action('package_search', data_dict={
            'q': query, 'rows': 500, 'start': 0})
        org_identifiers = [dataset['id']
                           for dataset in search_result['results']]
        start = 500
        while search_result['count'] > start:
            search_result = ckan_portal.call_action(
                'package_search', data_dict={
                    'q': query, 'rows': 500, 'start': start})
            org_identifiers += [dataset['id']
                                for dataset in search_result['results']]
            start += 500

        if datajson_filters:
            identifiers = set(identifiers).intersection(set(org_identifiers))
        else:
            identifiers = org_identifiers

    for identifier in identifiers:
        ckan_portal.call_action('dataset_purge', data_dict={'id': identifier})


def push_theme_to_ckan(catalog, portal_url, apikey,
                       identifier=None, label=None):
    """Escribe la metadata de un theme en el portal pasado por parámetro.

            Args:
                catalog (DataJson): El catálogo de origen que contiene el
                    theme.
                portal_url (str): La URL del portal CKAN de destino.
                apikey (str): La apikey de un usuario con los permisos que le
                    permitan crear o actualizar el dataset.
                identifier (str): El identificador para buscar el theme en la
                    taxonomia.
                label (str): El label para buscar el theme en la taxonomia.
            Returns:
                str: El name del theme en el catálogo de destino.
        """
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)
    theme = catalog.get_theme(identifier=identifier, label=label)
    group = map_theme_to_group(theme)
    pushed_group = ckan_portal.call_action('group_create', data_dict=group)
    return pushed_group['name']


def restore_dataset_to_ckan(catalog, owner_org, dataset_origin_identifier,
                            portal_url, apikey):
    """Restaura la metadata de un dataset en el portal pasado por parámetro.

        Args:
            catalog (DataJson): El catálogo de origen que contiene el dataset.
            owner_org (str): La organización a la cual pertence el dataset.
            dataset_origin_identifier (str): El id del dataset que se va a
                restaurar.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
        Returns:
            str: El id del dataset restaurado.
    """
    return push_dataset_to_ckan(catalog, owner_org, dataset_origin_identifier,
                                portal_url, apikey, None, False, False)


def harvest_dataset_to_ckan(catalog, owner_org, dataset_origin_identifier,
                            portal_url, apikey, catalog_id):
    """Federa la metadata de un dataset en el portal pasado por parámetro.

        Args:
            catalog (DataJson): El catálogo de origen que contiene el dataset.
            owner_org (str): La organización a la cual pertence el dataset.
            dataset_origin_identifier (str): El id del dataset que se va a
                restaurar.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
            catalog_id(str): El id que prep
        Returns:
            str: El id del dataset restaurado.
    """

    return push_dataset_to_ckan(catalog, owner_org, dataset_origin_identifier,
                                portal_url, apikey, catalog_id=catalog_id)


def restore_catalog_to_ckan(catalog, owner_org, portal_url, apikey,
                            dataset_list=None):
    """Restaura los datasets de un catálogo al portal pasado por parámetro.
        Si hay temas presentes en el DataJson que no están en el portal de
        CKAN, los genera.

        Args:
            catalog (DataJson): El catálogo de origen que se restaura.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
            dataset_list(list(str)): Los ids de los datasets a restaurar. Si no
                se pasa una lista, todos los datasests se restauran.
            owner_org (str): La organización a la cual pertencen los datasets.
                Si no se pasa, se utiliza el catalog_id.
        Returns:
            str: El id del dataset en el catálogo de destino.
    """
    push_new_themes(catalog, portal_url, apikey)
    dataset_list = dataset_list or [ds['identifier']
                                    for ds in catalog.datasets]
    restored = []
    for dataset_id in dataset_list:
        restored_id = restore_dataset_to_ckan(
            catalog, owner_org, dataset_id, portal_url, apikey)
        restored.append(restored_id)
    return restored


def harvest_catalog_to_ckan(catalog, portal_url, apikey, catalog_id,
                            dataset_list=None, owner_org=None):
    """Federa los datasets de un catálogo al portal pasado por parámetro.

        Args:
            catalog (DataJson): El catálogo de origen que se federa.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
            catalog_id (str): El prefijo con el que va a preceder el id del
                dataset en catálogo destino.
            dataset_list(list(str)): Los ids de los datasets a federar. Si no
                se pasa una lista, todos los datasests se federan.
            owner_org (str): La organización a la cual pertencen los datasets.
                Si no se pasa, se utiliza el catalog_id.
        Returns:
            str: El id del dataset en el catálogo de destino.
    """
    # Evitar entrar con valor falsy
    if dataset_list is None:
        dataset_list = [ds['identifier'] for ds in catalog.datasets]
    owner_org = owner_org or catalog_id
    harvested = []
    errors = {}
    for dataset_id in dataset_list:
        try:
            harvested_id = harvest_dataset_to_ckan(
                catalog, owner_org, dataset_id, portal_url, apikey, catalog_id)
            harvested.append(harvested_id)
        except Exception as e:
            msg = "Error federando catalogo: %s, dataset: %s al portal: %s\n"\
                  % (catalog_id, dataset_id, portal_url)
            msg += str(e)
            logger.error(msg)
            errors[dataset_id] = str(e)

    return harvested, errors


def push_new_themes(catalog, portal_url, apikey):
    """Toma un catálogo y escribe los temas de la taxonomía que no están
    presentes.

        Args:
            catalog (DataJson): El catálogo de origen que contiene la
                taxonomía.
            portal_url (str): La URL del portal CKAN de destino.
            apikey (str): La apikey de un usuario con los permisos que le
                permitan crear o actualizar el dataset.
        Returns:
            str: Los ids de los temas creados.
    """
    ckan_portal = RemoteCKAN(portal_url, apikey=apikey)
    existing_themes = ckan_portal.call_action('group_list')
    new_themes = [theme['id'] for theme in catalog[
        'themeTaxonomy'] if theme['id'] not in existing_themes]
    pushed_names = []
    for new_theme in new_themes:
        name = push_theme_to_ckan(
            catalog, portal_url, apikey, identifier=new_theme)
        pushed_names.append(name)
    return pushed_names
