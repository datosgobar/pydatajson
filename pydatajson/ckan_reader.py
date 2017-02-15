#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extensión de pydatajson para leer catálogos de metadatos a través de la API
de CKAN v3.
"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os.path
import logging
import json
from urlparse import urljoin
from ckanapi import RemoteCKAN

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ABSOLUTE_PROJECT_DIR, "schemas",
                       "accrualPeriodicity.json")) as frequencies:
    FREQUENCIES = json.load(frequencies)

with open(os.path.join(ABSOLUTE_PROJECT_DIR, "schemas",
                       "superThemeTaxonomy.json")) as super_themes:
    SUPER_THEMES = json.load(super_themes)


def try_stuff():
    print(FREQUENCIES)
    print(SUPER_THEMES)


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S')


def read_ckan_catalog(portal_url, super_theme=None):
    portal = RemoteCKAN(portal_url)
    catalog = {}

    if super_theme is None:
        logging.warn("""
No se proveyó un valor para 'superTheme', que es una propiedad requerida de
todos los datasets, y no se encuentra en la API de CKAN.""")

    try:
        status = portal.call_action('status_show')
        packages_list = portal.call_action('package_list')
        groups_list = portal.call_action('group_list')

        packages = [portal.call_action('package_show', {'name_or_id': pkg})
                    for pkg in packages_list]

        groups = [portal.call_action('group_show', {'id': grp})
                  for grp in groups_list]

        catalog = map_status_to_catalog(status)
        catalog["dataset"] = map_packages_to_datasets(
            packages, portal_url, super_theme)
        catalog["themeTaxonomy"] = map_groups_to_themes(groups)
    except:
        logging.error(
            'Error al procesar el portal %s', portal_url, exc_info=True)

    return catalog


def map_status_to_catalog(status):
    """Convierte el resultado de action.status_show() en metadata a nivel de
    catálogo."""
    catalog = dict()

    catalog_mapping = {
        "site_title": "title",
        "site_description": "description"
    }

    for status_key, catalog_key in catalog_mapping.iteritems():
        try:
            catalog[catalog_key] = status[status_key]
        except:
            logging.info("""
La clave '%s' no está en el endpoint de status. No se puede completar
catalog['%s'].""", status_key, catalog_key)

    publisher_mapping = {
        "site_title": "name",
        "error_emails_to": "mbox"
    }

    if any([k in status for k in publisher_mapping.keys()]):
        catalog["publisher"] = dict()
        for status_key, publisher_key in publisher_mapping.iteritems():
            try:
                catalog['publisher'][publisher_key] = status[status_key]
            except:
                logging.info("""
La clave '%s' no está en el endpoint de status. No se puede completar
catalog['publisher'['%s'].""", status_key, publisher_key)
    else:
        logging.info("""
No hay ninguna información sobre catalog['publisher'] en el endpoint
de 'status'.""")

    catalog['superThemeTaxonomy'] = (
        'http://datos.gob.ar/superThemeTaxonomy.json')

    return catalog


def map_packages_to_datasets(packages, portal_url, super_theme):
    return [map_package_to_dataset(pkg, portal_url, super_theme)
            for pkg in packages]


def map_package_to_dataset(package, portal_url, super_theme=None):
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

    for package_key, dataset_key in dataset_mapping.iteritems():
        try:
            dataset[dataset_key] = package[package_key]
        except:
            logging.info("""
La clave '%s' no está en el endpoint 'package_show' para el package '%s'. No
se puede completar dataset['%s'].""",
                         package_key, package['name'], dataset_key)

    publisher_mapping = {
        'author': 'name',
        'author_email': 'mbox'
    }

    if any([k in package for k in publisher_mapping.keys()]):
        dataset["publisher"] = dict()
        for package_key, publisher_key in publisher_mapping.iteritems():
            try:
                dataset['publisher'][publisher_key] = package[package_key]
            except:
                logging.info("""
La clave '%s' no está en el endpoint 'package_show' para el package '%s'. No
se puede completar dataset['publisher']['%s'].""",
                             package_key, package['name'], publisher_key)

    contact_point_mapping = {
        'maintainer': 'fn',
        'maintainer_email': 'hasEmail'
    }

    if any([k in package for k in contact_point_mapping.keys()]):
        dataset["contactPoint"] = dict()
        for package_key, contact_key in contact_point_mapping.iteritems():
            try:
                dataset['contactPoint'][contact_key] = package[package_key]
            except:
                logging.info("""
La clave '%s' no está en el endpoint 'package_show' para el package '%s'. No
se puede completar dataset['contactPoint']['%s'].""",
                             package_key, package['name'], contact_key)

    interval_mapping = {
        "diaria": "R/P1D",
        "mensual": "R/P1M",
        "eventual": "eventual",
        "quincenal": "R/P15D",
        "trimestral": "R/P3M",
        "anual": "R/P1Y"
    }

    if "extras" in package:
        accrual = [extra["value"].lower() for extra in package["extras"] if
                   extra["key"].lower().startswith("frecuencia")]

        if len(accrual) == 0:
            logging.info("""
No se encontraron valores de frecuencia de actualización en 'extras' para el
'package' '%s'. No se puede completar dataset['accrualPeriodicity'].""",
                         package['name'])
        elif len(accrual) > 1:
            logging.info("""
Se encontro mas de un valor de frecuencia de actualización en 'extras' para el
'package' '%s'. No se puede completar dataset['accrualPeriodicity'].\n %s""",
                         package['name'], accrual)
        else:
            try:
                dataset["accrualPeriodicity"] = interval_mapping[accrual[0]]
            except KeyError:
                logging.warn("""
Se encontró '%s' como frecuencia de actualización, pero no es mapeable a una
'accrualPeriodicity' conocida. La clave no se pudo completar.""", accrual[0])

    if super_theme:
        dataset["superTheme"] = super_theme

    if 'landingPage' not in dataset or dataset['landingPage'] == '':
        url_path = ["dataset", dataset["identifier"]]
        dataset['landingPage'] = urljoin(portal_url, "/".join(url_path))

    dataset["distribution"] = map_resources_to_distributions(resources,
                                                             portal_url)
    dataset["theme"] = [grp['name'] for grp in groups]
    dataset['keyword'] = [tag['name'] for tag in tags]

    return dataset


def map_resources_to_distributions(resources, portal_url):
    return [map_resource_to_distribution(res, portal_url) for res in resources]


def map_resource_to_distribution(resource, portal_url):
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

    for resource_key, distribution_key in distribution_mapping.iteritems():
        try:
            distribution[distribution_key] = resource[resource_key]
        except:
            logging.info("""
La clave '%s' no está en la metadata del 'resource' '%s'. No
se puede completar distribution['%s'].""",
                         resource_key, resource['name'], distribution_key)

    url_path = ['dataset', resource['package_id'], 'resource', resource['id']]
    distribution["accessURL"] = urljoin(portal_url, "/".join(url_path))

    return distribution


def map_groups_to_themes(groups):
    return [map_group_to_theme(grp) for grp in groups]


def map_group_to_theme(group):
    theme = dict()

    theme_mapping = {
        'name': 'id',
        'display_name': 'label',
        'description': 'description'
    }

    for group_key, theme_key in theme_mapping.iteritems():
        try:
            theme[theme_key] = group[group_key]
        except:
            logging.info("""
La clave '%s' no está en la metadata del 'group' '%s'. No
se puede completar theme['%s'].""",
                         group_key, theme['name'], theme_key)

    return theme
