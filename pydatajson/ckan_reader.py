#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extensión de pydatajson para leer catálogos de metadatos a través de la API
de CKAN v3.
"""
from __future__ import unicode_literals, print_function,\
    with_statement, absolute_import
import os.path
import logging
import json
import time
from six.moves.urllib_parse import urljoin
from six import iteritems
from requests.exceptions import RequestException
from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError
from .helpers import clean_str, title_to_name
from .custom_exceptions import NonParseableCatalog

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('pydatajson')


ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ABSOLUTE_PROJECT_DIR, "schemas",
                       "accrualPeriodicity.json")) as frequencies:
    RAW_FREQUENCIES = json.load(frequencies)
    FREQUENCIES = {row["description"]: row["id"] for row in RAW_FREQUENCIES}

with open(os.path.join(ABSOLUTE_PROJECT_DIR, "schemas",
                       "superThemeTaxonomy.json")) as super_themes:
    RAW_SUPER_THEMES = json.load(super_themes)
    SUPER_THEMES = {row["label"]: row["id"] for row in RAW_SUPER_THEMES}


def read_ckan_catalog(portal_url):
    """Convierte los metadatos de un portal disponibilizados por la Action API
    v3 de CKAN al estándar data.json.

    Args:
        portal_url (str): URL de un portal de datos CKAN que soporte la API v3.

    Returns:
        dict: Representación interna de un catálogo para uso en las funciones
            de esta librería.
    """
    portal = RemoteCKAN(portal_url)
    try:
        status = portal.call_action(
            'status_show', requests_kwargs={"verify": False})
        packages_list = portal.call_action(
            'package_list', requests_kwargs={"verify": False})
        groups_list = portal.call_action(
            'group_list', requests_kwargs={"verify": False})

        # itera leyendo todos los datasets del portal
        packages = []
        num_packages = len(packages_list)
        for index, pkg in enumerate(packages_list):
            # progreso (necesario cuando son muchos)
            msg = "Leyendo dataset {} de {}".format(index + 1, num_packages)
            logger.info(msg)

            # agrega un nuevo dataset a la lista
            packages.append(portal.call_action(
                'package_show', {'id': pkg},
                requests_kwargs={"verify": False}
            ))

            # tiempo de espera padra evitar baneos
            time.sleep(0.2)

        # itera leyendo todos los temas del portal
        groups = [portal.call_action(
            'group_show', {'id': grp},
            requests_kwargs={"verify": False})
            for grp in groups_list]

        catalog = map_status_to_catalog(status)
        catalog["dataset"] = map_packages_to_datasets(
            packages, portal_url)
        catalog["themeTaxonomy"] = map_groups_to_themes(groups)

    except (CKANAPIError, RequestException) as e:
        logger.exception(
            'Error al procesar el portal %s', portal_url, exc_info=True)
        raise NonParseableCatalog(portal_url, e)

    return catalog


def map_status_to_catalog(status):
    """Convierte el resultado de action.status_show() en metadata a nivel de
    catálogo."""
    catalog = dict()

    catalog_mapping = {
        "site_title": "title",
        "site_description": "description"
    }

    for status_key, catalog_key in iteritems(catalog_mapping):
        try:
            catalog[catalog_key] = status[status_key]
        except BaseException:
            logger.exception("""
            La clave '%s' no está en el endpoint de status. No se puede
            completar catalog['%s'].""", status_key, catalog_key)

    publisher_mapping = {
        "site_title": "name",
        "error_emails_to": "mbox"
    }

    if any([k in status for k in publisher_mapping.keys()]):
        catalog["publisher"] = dict()
        for status_key, publisher_key in iteritems(publisher_mapping):
            try:
                catalog['publisher'][publisher_key] = status[status_key]
            except BaseException:
                logger.exception("""
                La clave '%s' no está en el endpoint de status. No se puede
                completar catalog['publisher'['%s'].""",
                                 status_key, publisher_key)
    else:
        logger.info("""
        No hay ninguna información sobre catalog['publisher'] en el endpoint
        de 'status'.""")

    catalog['superThemeTaxonomy'] = (
        'http://datos.gob.ar/superThemeTaxonomy.json')

    return catalog


def map_packages_to_datasets(packages, portal_url):
    """Mapea una lista de 'packages' de CKAN a 'datasets' de data.json."""
    return [map_package_to_dataset(pkg, portal_url)
            for pkg in packages]


def map_package_to_dataset(package, portal_url):
    """Mapea un diccionario con metadatos de cierto 'package' de CKAN a un
    diccionario con metadatos de un 'dataset' según el estándar data.json."""
    dataset = dict()
    resources = package["resources"]
    groups = package["groups"]
    tags = package["tags"]

    dataset_mapping = {
        'title': 'title',
        'notes': 'description',
        'metadata_created': 'issued',
        'metadata_modified': 'modified',
        'license_title': 'license',
        'id': 'identifier',
        'url': 'landingPage'
    }

    for package_key, dataset_key in iteritems(dataset_mapping):
        try:
            dataset[dataset_key] = package[package_key]
        except BaseException:
            logger.exception("""
            La clave '%s' no está en el endpoint 'package_show' para el
            package '%s'. No se puede completar dataset['%s'].""",
                             package_key, package['name'], dataset_key)

    publisher_mapping = {
        'author': 'name',
        'author_email': 'mbox'
    }

    if any([k in package for k in publisher_mapping.keys()]):
        dataset["publisher"] = dict()
        for package_key, publisher_key in iteritems(publisher_mapping):
            try:
                dataset['publisher'][publisher_key] = package[package_key]
            except BaseException:
                logger.exception("""
                La clave '%s' no está en el endpoint 'package_show' para el
                package '%s'. No se puede completar
                dataset['publisher']['%s'].""",
                                 package_key, package['name'], publisher_key)

    contact_point_mapping = {
        'maintainer': 'fn',
        'maintainer_email': 'hasEmail'
    }

    if any([k in package for k in contact_point_mapping.keys()]):
        dataset["contactPoint"] = dict()
        for package_key, contact_key in iteritems(contact_point_mapping):
            try:
                dataset['contactPoint'][contact_key] = package[package_key]
            except BaseException:
                logger.exception("""
                La clave '%s' no está en el endpoint 'package_show' para el
                package '%s'. No se puede completar
                dataset['contactPoint']['%s'].""",
                                 package_key, package['name'], contact_key)

    # Si existen campos extras en la información del package, busco las claves
    # "Frecuencia de actualización" y "Temática global" para completar los
    # campos "accrualPeriodicity" y "superTheme" del dataset, respectivamente.
    if "extras" in package:
        add_accrualPeriodicity(dataset, package)
        add_superTheme(dataset, package)
        add_temporal(dataset, package)

    dataset["distribution"] = map_resources_to_distributions(resources,
                                                             portal_url)
    dataset["theme"] = [grp['name'] for grp in groups]
    dataset['keyword'] = [tag['name'] for tag in tags]

    return dataset


def add_temporal(dataset, package):
    # "Cobertura temporal" => "temporal"
    temporal = [
        extra["value"] for extra in package["extras"] if
        title_to_name(extra["key"]) == title_to_name("Cobertura temporal")
    ]

    if len(temporal) > 1:
        logger.info("""
        Se encontro mas de un valor de cobertura temporal en 'extras' para el
        'package' '%s'. No se puede completar dataset['temporal'].\n %s""",
                    package['name'], temporal)
    elif len(temporal) == 1:
        try:
            dataset["temporal"] = temporal[0]
        except KeyError:
            logger.exception("""
            Se encontró '%s' como cobertura temporal, pero no es mapeable a un
            'temporal' conocido. La clave no se pudo completar.""",
                             temporal[0])

    # Busco claves que son casi "Cobertura temporal" para lanzar
    # advertencias si las hay.
    almost_temporal = [
        extra for extra in package["extras"] if
        clean_str(extra["key"]) == "cobertura temporal" and
        extra["key"] != "Cobertura temporal"]

    if almost_temporal:
        logger.warn("""
        Se encontraron claves con nombres similares pero no idénticos a
        "Cobertura temporal" en 'extras' para el 'package' '%s'.
        Por favor, considere corregirlas:
        \n%s""", package['name'], almost_temporal)


def add_superTheme(dataset, package):
    # "Temática global" => "superTheme"
    super_theme = [
        extra["value"] for extra in package["extras"] if
        title_to_name(extra["key"]) == title_to_name("Temática global")
    ]

    if len(super_theme) == 0:
        logger.info("""
        No se encontraron valores de temática global en 'extras' para el
        'package' '%s'. No se puede completar dataset['superTheme'].""",
                    package['name'])

    elif len(super_theme) > 1:
        logger.info("""
        Se encontro mas de un valor de temática global en 'extras' para el
        'package' '%s'. No se puede completar dataset['superTheme'].\n %s""",
                    package['name'], super_theme)
    else:
        try:
            dataset["superTheme"] = [SUPER_THEMES[super_theme[0]]]
        except KeyError:
            logger.exception("""
            Se encontró '%s' como temática global, pero no es mapeable a un
            'superTheme' conocido. La clave no se pudo completar.""",
                             super_theme[0])

    # Busco claves que son casi "Temática global" para lanzar
    # advertencias si las hay.
    almost_super_theme = [
        extra for extra in package["extras"] if
        clean_str(extra["key"]) == "tematica global" and
        extra["key"] != "Temática global"]

    if almost_super_theme:
        logger.warn("""
        Se encontraron claves con nombres similares pero no idénticos a
        "Temática global" en 'extras' para el 'package' '%s'. Por favor,
        considere corregirlas: \n%s""",
                    package['name'], almost_super_theme)


def add_accrualPeriodicity(dataset, package):
    # "Frecuencia de actualización" => "accrualPeriodicity"
    accrual = [
        extra["value"] for extra in package["extras"] if
        title_to_name(extra["key"]) == title_to_name(
            "Frecuencia de actualización")
    ]

    if len(accrual) == 0:
        logger.info("""
        No se encontraron valores de frecuencia de actualización en 'extras'
        para el 'package' '%s'. No se puede completar
        dataset['accrualPeriodicity'].""", package['name'])
    elif len(accrual) > 1:
        logger.info("""
        Se encontro mas de un valor de frecuencia de actualización en 'extras'
        para el 'package' '%s'. No se puede completar
        dataset['accrualPeriodicity'].\n %s""", package['name'], accrual)
    else:
        try:
            dataset["accrualPeriodicity"] = FREQUENCIES[accrual[0]]

        except KeyError:
            logger.exception("""
            Se encontró '%s' como frecuencia de actualización, pero no es
            mapeable a una 'accrualPeriodicity' conocida. La clave no se
            pudo completar.""", accrual[0])

    # Busco claves que son casi "Frecuencia de actualización" para lanzar
    # advertencias si las hay.
    almost_accrual = [
        extra for extra in package["extras"] if
        clean_str(extra["key"]) == "frecuencia de actualizacion" and
        extra["key"] != "Frecuencia de actualización"]

    if almost_accrual:
        logger.warn("""
        Se encontraron claves con nombres similares pero no idénticos a
        "Frecuencia de actualización" en 'extras' para el 'package' '%s'.
        Por favor, considere corregirlas:\n%s""",
                    package['name'], almost_accrual)


def map_resources_to_distributions(resources, portal_url):
    """Mapea una lista de 'resources' CKAN a 'distributions' de data.json."""
    return [map_resource_to_distribution(res, portal_url) for res in resources]


def map_resource_to_distribution(resource, portal_url):
    """Mapea un diccionario con metadatos de cierto 'resource' CKAN a dicts
    con metadatos de una 'distribution' según el estándar data.json."""
    distribution = dict()

    distribution_mapping = {
        'url': 'downloadURL',
        'name': 'title',
        'created': 'issued',
        'description': 'description',
        'format': 'format',
        'last_modified': 'modified',
        'mimetype': 'mediaType',
        'size': 'byteSize',
        'id': 'identifier'  # No es parte del estandar de PAD pero es relevante
    }

    for resource_key, distribution_key in iteritems(distribution_mapping):
        try:
            distribution[distribution_key] = resource[resource_key]
        except BaseException:
            logger.exception("""
            La clave '%s' no está en la metadata del 'resource' '%s'. No
            se puede completar distribution['%s'].""",
                             resource_key, resource['name'], distribution_key)

    if 'attributesDescription' in resource:
        try:
            distribution['field'] = json.loads(
                resource['attributesDescription'])

        except BaseException:
            logger.exception(
                "Error parseando los fields del resource '%s'",
                resource['name'])

    url_path = ['dataset', resource['package_id'], 'resource', resource['id']]
    distribution["accessURL"] = urljoin(portal_url, "/".join(url_path))

    return distribution


def map_groups_to_themes(groups):
    """Mapea una lista de 'groups' de CKAN a 'themes' de data.json."""
    return [map_group_to_theme(grp) for grp in groups]


def map_group_to_theme(group):
    """Mapea un diccionario con metadatos de cierto 'group' de CKAN a un
    diccionario con metadatos de un 'theme' según el estándar data.json."""
    theme = dict()

    theme_mapping = {
        'name': 'id',
        'title': 'label',
        'description': 'description'
    }

    for group_key, theme_key in iteritems(theme_mapping):
        try:
            theme[theme_key] = group[group_key]
        except BaseException:
            logger.exception("""
            La clave '%s' no está en la metadata del 'group' '%s'. No
            se puede completar theme['%s'].""",
                             group_key, theme['name'], theme_key)

    return theme
