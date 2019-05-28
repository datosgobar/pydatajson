#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'readers' de Pydatajson

Contiene los métodos auxiliares para leer archivos con información tabular y
catálogos de metadatos, en distintos fomatos.
"""

from __future__ import unicode_literals, print_function
from __future__ import with_statement, absolute_import

import io
import json
import logging
import os.path
import warnings

import openpyxl as pyxl
import requests
import unicodecsv as csv
from zipfile import BadZipfile
from openpyxl.utils.exceptions import *
from six import string_types, text_type, iteritems
from six.moves.urllib_parse import urlparse
from unidecode import unidecode

import pydatajson
from . import custom_exceptions as ce
from . import helpers, constants
from .ckan_reader import read_ckan_catalog

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

pydj_logger = logging.getLogger('pydatajson.readers')

openpyxl_exceptions = (CellCoordinatesException, IllegalCharacterError,
                       NamedRangeException, SheetTitleException,
                       # InsufficientCoordinatesException,
                       InvalidFileException,
                       ReadOnlyWorkbookException, WorkbookAlreadySaved)


def read_catalog_obj(catalog):
    try:
        if getattr(catalog, "has_catalog"):
            return catalog
        else:
            return pydatajson.DataJson(catalog)
    except BaseException:
        return pydatajson.DataJson(catalog)


def read_catalog(catalog, default_values=None, catalog_format=None,
                 verify=False, timeout=constants.REQUESTS_TIMEOUT):
    """Toma una representación cualquiera de un catálogo, y devuelve su
    representación interna (un diccionario de Python con su metadata.)

    Si recibe una representación _interna_ (un diccionario), lo devuelve
    intacto. Si recibe una representación _externa_ (path/URL a un archivo
    JSON/XLSX), devuelve su represetación interna, es decir, un diccionario.

    Args:
        catalog (dict or str): Representación externa/interna de un catálogo.
            Una representación _externa_ es un path local o una URL remota a un
            archivo con la metadata de un catálogo, en formato JSON o XLSX. La
            representación _interna_ de un catálogo es un diccionario.

    Returns:
        dict: Representación interna de un catálogo para uso en las funciones
        de esta librería.
    """
    unknown_catalog_repr_msg = \
        """No se pudo inferir una representación válida de un catálogo del
        parámetro provisto: {}.""".format(catalog)
    assert isinstance(catalog, string_types + (dict,)
                      ), unknown_catalog_repr_msg

    if isinstance(catalog, dict):
        catalog_dict = catalog

    else:
        # catalog es una URL remota o un path local
        suffix = catalog.split(".")[-1].strip("/")
        if suffix in ('json', 'xlsx'):
            catalog_format = catalog_format or suffix
        if catalog_format == "xlsx":
            try:
                catalog_dict = read_xlsx_catalog(catalog,
                                                 verify=verify,
                                                 timeout=timeout)
            except openpyxl_exceptions + \
                    (ValueError, AssertionError, IOError, BadZipfile) as e:
                raise ce.NonParseableCatalog(catalog, str(e))
        elif catalog_format == "json":
            try:
                catalog_dict = read_json(catalog,
                                         verify=verify,
                                         timeout=timeout)
            except(ValueError, TypeError, IOError) as e:
                raise ce.NonParseableCatalog(catalog, str(e))
        elif catalog_format == "ckan":
            catalog_dict = read_ckan_catalog(catalog)
        else:
            catalog_dict = read_suffixless_catalog(catalog)

    # si se pasaron valores default, los aplica al catálogo leído
    if default_values:
        _apply_default_values(catalog_dict, default_values)

    return catalog_dict


def _apply_default_values(catalog, default_values):
    """Aplica valores default a los campos de un catálogo.

    Si el campo está vacío, aplica el default. Si tiene un valor, deja el valor
    que estaba. Sólo soporta defaults para las siguientes clases:
        catalog
        dataset
        distribution
        field

    Args:
        catalog (dict): Un catálogo.
        default_values (dict): Valores default para algunos de los campos del
            catálogo.
            {
                "dataset_issued": "2017-06-22",
                "distribution_issued": "2017-06-22"
            }
    """

    for field, default_value in iteritems(default_values):
        class_metadata = field.split("_")[0]
        field_json_path = field.split("_")[1:]

        # valores default de catálogo
        if class_metadata == "catalog":
            _set_default_value(catalog, field_json_path, default_value)

        # valores default de dataset
        elif class_metadata == "dataset":
            for dataset in catalog["dataset"]:
                _set_default_value(dataset, field_json_path, default_value)

        # valores default de distribución
        elif class_metadata == "distribution":
            for dataset in catalog["dataset"]:
                for distribution in dataset["distribution"]:
                    _set_default_value(
                        distribution, field_json_path, default_value)

        # valores default de field
        elif class_metadata == "field":
            for dataset in catalog["dataset"]:
                for distribution in dataset["distribution"]:

                    # campo "field" en una "distribution" no es obligatorio
                    if distribution.get("field"):
                        for field in distribution["field"]:
                            _set_default_value(
                                field, field_json_path, default_value)


def _set_default_value(dict_obj, keys, value):
    """Setea valor en diccionario anidado, siguiendo lista de keys.

    Args:
        dict_obj (dict): Un diccionario anidado.
        keys (list): Una lista de keys para navegar el diccionario.
        value (any): Un valor para reemplazar.
    """
    variable = dict_obj

    if len(keys) == 1:
        if not variable.get(keys[0]):
            variable[keys[0]] = value

    else:
        for idx, field in enumerate(keys):
            if idx < len(keys) - 1:
                variable = variable[field]

        if not variable.get(keys[-1]):
            variable[keys[-1]] = value


def read_json(json_path_or_url, verify=False,
              timeout=constants.REQUESTS_TIMEOUT):
    """Toma el path a un JSON y devuelve el diccionario que representa.

    Se asume que el parámetro es una URL si comienza con 'http' o 'https', o
    un path local de lo contrario.

    Args:
        json_path_or_url (str): Path local o URL remota a un archivo de texto
            plano en formato JSON.

    Returns:
        dict: El diccionario que resulta de deserializar json_path_or_url.

    """
    assert isinstance(json_path_or_url, string_types)

    parsed_url = urlparse(json_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(json_path_or_url, verify=verify, timeout=timeout)
        json_dict = json.loads(res.content, encoding='utf-8')

    else:
        # Si json_path_or_url parece ser una URL remota, lo advierto.
        path_start = parsed_url.path.split(".")[0]
        if path_start == "www" or path_start.isdigit():
            warnings.warn("""
La dirección del archivo JSON ingresada parece una URL, pero no comienza
con 'http' o 'https' así que será tratada como una dirección local. ¿Tal vez
quiso decir 'http://{}'?""".format(json_path_or_url).encode("utf-8"))

        with io.open(json_path_or_url, encoding='utf-8') as json_file:
            json_dict = json.load(json_file)

    return json_dict


def read_xlsx_catalog(xlsx_path_or_url, logger=None, verify=False,
                      timeout=constants.REQUESTS_TIMEOUT):
    """Toma el path a un catálogo en formato XLSX y devuelve el diccionario
    que representa.

    Se asume que el parámetro es una URL si comienza con 'http' o 'https', o
    un path local de lo contrario.

    Args:
        xlsx_path_or_url (str): Path local o URL remota a un libro XLSX de
            formato específico para guardar los metadatos de un catálogo.

    Returns:
        dict: El diccionario que resulta de procesar xlsx_path_or_url.

    """
    logger = logger or pydj_logger
    assert isinstance(xlsx_path_or_url, string_types)

    parsed_url = urlparse(xlsx_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(xlsx_path_or_url, verify=verify, timeout=timeout)
        tmpfilename = ".tmpfile.xlsx"
        with io.open(tmpfilename, 'wb') as tmpfile:
            tmpfile.write(res.content)
        catalog_dict = read_local_xlsx_catalog(tmpfilename, logger)
        os.remove(tmpfilename)
    else:
        # Si xlsx_path_or_url parece ser una URL remota, lo advierto.
        path_start = parsed_url.path.split(".")[0]
        if path_start == "www" or path_start.isdigit():
            warnings.warn("""
La dirección del archivo JSON ingresada parece una URL, pero no comienza
con 'http' o 'https' así que será tratada como una dirección local. ¿Tal vez
quiso decir 'http://{}'?
            """.format(xlsx_path_or_url).encode("utf8"))

        catalog_dict = read_local_xlsx_catalog(xlsx_path_or_url)

    return catalog_dict


def _make_publisher(catalog_or_dataset):
    """De estar presentes las claves necesarias, genera el diccionario
    "publisher" a nivel catálogo o dataset."""
    level = catalog_or_dataset
    keys = [k for k in ["publisher_name", "publisher_mbox"] if k in level]
    if keys:
        level["publisher"] = {
            key.replace("publisher_", ""): level.pop(key) for key in keys
        }
    return level


def _make_contact_point(dataset):
    """De estar presentes las claves necesarias, genera el diccionario
    "contactPoint" de un dataset."""
    keys = [k for k in ["contactPoint_fn", "contactPoint_hasEmail"]
            if k in dataset]
    if keys:
        dataset["contactPoint"] = {
            key.replace("contactPoint_", ""): dataset.pop(key) for key in keys
        }
    return dataset


def _get_dataset_index(catalog, dataset_identifier, dataset_title,
                       logger=None):
    """Devuelve el índice de un dataset en el catálogo en función de su
    identificador"""
    logger = logger or pydj_logger
    matching_datasets = []

    for idx, dataset in enumerate(catalog["catalog_dataset"]):
        if dataset["dataset_identifier"] == dataset_identifier:
            if dataset["dataset_title"] == dataset_title:
                matching_datasets.append(idx)
            else:
                logger.warning(
                    ce.DatasetUnexpectedTitle(
                        dataset_identifier,
                        dataset["dataset_title"],
                        dataset_title
                    )
                )

    # Debe haber exactamente un dataset con el identificador provisto.
    no_dsets_msg = "No hay ningun dataset con el identifier {}".format(
        dataset_identifier)
    many_dsets_msg = "Hay mas de un dataset con el identifier {}: {}".format(
        dataset_identifier, matching_datasets)
    if len(matching_datasets) == 0:
        logger.warning(no_dsets_msg)
        return None
    elif len(matching_datasets) > 1:
        logger.warning(many_dsets_msg)
        return None
    else:
        return matching_datasets[0]


def _get_distribution_indexes(catalog, dataset_identifier, dataset_title,
                              distribution_identifier, distribution_title,
                              logger=None):
    """Devuelve el índice de una distribución en su dataset en función de su
    título, junto con el índice de su dataset padre en el catálogo, en
    función de su identificador"""
    logger = logger or pydj_logger
    dataset_index = _get_dataset_index(
        catalog, dataset_identifier, dataset_title)
    if dataset_index is None:
        return None, None
    else:
        dataset = catalog["catalog_dataset"][dataset_index]

    matching_distributions = []

    for idx, distribution in enumerate(dataset["dataset_distribution"]):
        if distribution["distribution_identifier"] == distribution_identifier:
            if distribution["distribution_title"] == distribution_title:
                matching_distributions.append(idx)
            else:
                logger.warning(
                    ce.DistributionUnexpectedTitle(
                        distribution_identifier,
                        distribution["distribution_title"],
                        distribution_title
                    )
                )

    # Debe haber exactamente una distribución con los identicadores provistos
    if len(matching_distributions) == 0:
        logger.warning(
            ce.DistributionTitleNonExistentError(
                distribution_title, dataset_identifier
            )
        )
        return dataset_index, None
    elif len(matching_distributions) > 1:
        logger.warning(
            ce.DistributionTitleRepetitionError(
                distribution_title, dataset_identifier, matching_distributions)
        )
        return dataset_index, None
    else:
        distribution_index = matching_distributions[0]
        return dataset_index, distribution_index


def read_local_xlsx_catalog(xlsx_path, logger=None):
    """Genera un diccionario de metadatos de catálogo a partir de un XLSX bien
    formado.

    Args:
        xlsx_path (str): Path a un archivo XLSX "template" para describir la
            metadata de un catálogo.

    Returns:
        dict: Diccionario con los metadatos de un catálogo.
    """
    logger = logger or pydj_logger

    wb = pyxl.load_workbook(open(xlsx_path, 'rb'), data_only=True,
                            read_only=True)

    # Toma las hojas del modelo, resistente a mayúsuculas/minúsculas
    ws_catalog = helpers.get_ws_case_insensitive(wb, "catalog")
    ws_dataset = helpers.get_ws_case_insensitive(wb, "dataset")
    ws_distribution = helpers.get_ws_case_insensitive(wb, "distribution")
    ws_theme = helpers.get_ws_case_insensitive(wb, "theme")
    ws_field = helpers.get_ws_case_insensitive(wb, "field")

    catalogs = helpers.sheet_to_table(ws_catalog)
    # Debe haber exactamente un catálogo en la hoja 'Catalog'
    assert (len(catalogs) != 0), "No hay ningun catálogo en la hoja 'Catalog'"
    assert (len(catalogs) < 2), "Hay mas de un catálogo en la hoja 'Catalog'"
    # Genero el catálogo base
    catalog = catalogs[0]

    # Agrego themes y datasets al catálogo
    catalog["catalog_dataset"] = helpers.sheet_to_table(ws_dataset)

    # Me aseguro que los identificadores de dataset se guarden como cadenas
    for dataset in catalog["catalog_dataset"]:
        dataset["dataset_identifier"] = text_type(
            dataset["dataset_identifier"])

    catalog["catalog_themeTaxonomy"] = (
        helpers.sheet_to_table(ws_theme))

    # Agrego lista de distribuciones vacía a cada dataset
    for dataset in catalog["catalog_dataset"]:
        dataset["dataset_distribution"] = []

    # Ubico cada distribución en su dataset
    distributions = helpers.sheet_to_table(ws_distribution)
    for distribution in distributions:
        # Me aseguro que los identificadores se guarden como cadenas
        distribution["dataset_identifier"] = text_type(
            distribution["dataset_identifier"])
        distribution["distribution_identifier"] = text_type(
            distribution["distribution_identifier"])

        dataset_index = _get_dataset_index(
            catalog, distribution["dataset_identifier"],
            distribution["dataset_title"], logger)
        if dataset_index is None:
            logger.warning("""La distribucion con ID '{}' y titulo '{}' no se
pudo asignar a un dataset, y no figurara en el data.json de salida.""".format(
                distribution["distribution_identifier"],
                distribution["distribution_title"]))
        else:
            dataset = catalog["catalog_dataset"][dataset_index]
            dataset["dataset_distribution"].append(distribution)

    # Ubico cada campo en su distribución
    fields = helpers.sheet_to_table(ws_field)
    for idx, field in enumerate(fields):
        # Me aseguro que los identificadores se guarden como cadenas
        field["dataset_identifier"] = text_type(field["dataset_identifier"])
        field["distribution_identifier"] = text_type(
            field["distribution_identifier"])

        dataset_index, distribution_index = _get_distribution_indexes(
            catalog, field["dataset_identifier"], field["dataset_title"],
            field["distribution_identifier"], field["distribution_title"],
            logger)

        if dataset_index is None:
            logger.warning(
                """No se encontro el dataset '{}' especificado para el campo
                '{}' (fila #{} de la hoja "Field"). Este campo no figurara en
                el data.json de salida.""".format(
                    unidecode(field["dataset_title"]),
                    unidecode(field["field_title"]), idx + 2))

        elif distribution_index is None:
            logger.warning(
                """No se encontro la distribucion '{}' especificada para el
                campo'{}' (fila #{} de la hoja "Field"). Este campo no figurara
                en el data.json de salida.""".format(
                    unidecode(field["distribution_title"]),
                    unidecode(field["field_title"]), idx + 2))

        else:
            dataset = catalog["catalog_dataset"][dataset_index]
            distribution = dataset["dataset_distribution"][distribution_index]

            if "distribution_field" in distribution:
                distribution["distribution_field"].append(field)
            else:
                distribution["distribution_field"] = [field]

    # Transformo campos de texto separado por comas en listas
    if "catalog_language" in catalog:
        catalog["catalog_language"] = helpers.string_to_list(
            catalog["catalog_language"], filter_empty=True)

    for dataset in catalog["catalog_dataset"]:
        array_fields = ["dataset_superTheme", "dataset_theme", "dataset_tags",
                        "dataset_keyword", "dataset_language"]
        for field in array_fields:
            if field in dataset:
                dataset[field] = helpers.string_to_list(
                    dataset[field], filter_empty=True)

    # Elimino los prefijos de los campos a nivel catálogo
    _remove_prefixes_and_unprefixed_fields(catalog, 'catalog_')

    # Elimino los prefijos de los campos a nivel tema
    for theme in catalog["themeTaxonomy"]:
        _remove_prefixes_and_unprefixed_fields(theme, 'theme_')

    # Elimino los prefijos de los campos a nivel dataset
    for dataset in catalog["dataset"]:
        _remove_prefixes_and_unprefixed_fields(dataset, 'dataset_')

    # Elimino los campos auxiliares y los prefijos de los campos a nivel
    # distribución
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            _remove_prefixes_and_unprefixed_fields(
                distribution, 'distribution_')

    # Elimino campos auxiliares y los prefijos de los campos a nivel "campo"
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            if "field" in distribution:
                for field in distribution["field"]:
                    _remove_prefixes_and_unprefixed_fields(field, "field_")

    # Agrupo las claves de "publisher" y "contactPoint" en sendos diccionarios
    catalog = _make_publisher(catalog)
    for dataset in catalog["dataset"]:
        dataset = _make_publisher(dataset)
        dataset = _make_contact_point(dataset)

    return catalog


def read_suffixless_catalog(catalog):
    try:
        catalog_dict = read_ckan_catalog(catalog)
        return catalog_dict
    except ce.NonParseableCatalog:
        pass
    try:
        catalog_dict = read_json(catalog)
        return catalog_dict
    except(ValueError, TypeError, IOError):
        pass
    try:
        catalog_dict = read_xlsx_catalog(catalog)
        return catalog_dict
    except openpyxl_exceptions + (ValueError, AssertionError,
                                  IOError, BadZipfile):
        raise ce.NonParseableCatalog(
            catalog, 'No es posible discernir el formato del catalogo')


def read_table(path):
    """Lee un archivo tabular (CSV o XLSX) a una lista de diccionarios.

    La extensión del archivo debe ser ".csv" o ".xlsx". En función de
    ella se decidirá el método a usar para leerlo.

    Si recibe una lista, comprueba que todos sus diccionarios tengan las
    mismas claves y de ser así, la devuelve intacta. Levanta una Excepción
    en caso contrario.

    Args:
        path(str o list): Como 'str', path a un archivo CSV o XLSX.

    Returns:
        list: Lista de diccionarios con claves idénticas representando el
        archivo original.
    """
    assert isinstance(path, string_types + (list,)), """
{} no es un `path` valido""".format(path)

    # Si `path` es una lista, devolverla intacta si tiene formato tabular.
    # Si no, levantar una excepción.
    if isinstance(path, list):
        if helpers.is_list_of_matching_dicts(path):
            return path
        else:
            raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

    # Deduzco el formato de archivo de `path` y redirijo según corresponda.
    suffix = path.split(".")[-1]
    if suffix == "csv":
        return _read_csv_table(path)
    elif suffix == "xlsx":
        return _read_xlsx_table(path)
    else:
        raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o .xlsx""".format(suffix))


def _read_csv_table(path):
    """Lee un CSV a una lista de diccionarios."""
    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        table = list(reader)
    return table


def _read_xlsx_table(path):
    """Lee la hoja activa de un archivo XLSX a una lista de diccionarios."""
    workbook = pyxl.load_workbook(path)
    worksheet = workbook.active
    table = helpers.sheet_to_table(worksheet)

    return table


def _remove_prefixes_and_unprefixed_fields(dictionary, prefix):
    for old_key in list(dictionary):
        if old_key.startswith(prefix):
            new_key = old_key.replace(prefix, "")
            dictionary[new_key] = dictionary.pop(old_key)
        else:
            dictionary.pop(old_key)
