#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'readers' de Pydatajson

Contiene los métodos auxiliares para leer archivos con información tabular y
catálogos de metadatos, en distintos fomatos.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import io
import os.path
from urlparse import urlparse
import warnings
import json
import requests
import unicodecsv as csv
import openpyxl as pyxl
from . import helpers


def read_catalog(catalog):
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
    unknown_catalog_repr_msg = """
No se pudo inferir una representación válida de un catálogo del parámetro
provisto: {}.""".format(catalog)
    assert isinstance(catalog, (dict, str, unicode)), unknown_catalog_repr_msg

    if isinstance(catalog, dict):
        catalog_dict = catalog
    else:
        # catalog es una URL remota o un path local
        suffix = catalog.split(".")[-1]
        unknown_suffix_msg = """
{} no es un sufijo conocido. Pruebe con 'json' o  'xlsx'""".format(suffix)
        assert suffix in ["json", "xlsx"], unknown_suffix_msg

        if suffix == "json":
            catalog_dict = read_json(catalog)
        else:
            # El archivo está en formato XLSX
            catalog_dict = read_xlsx_catalog(catalog)

    # Es 'pitonica' esta forma de retornar un valor? O debería ir retornando
    # los valores intermedios?
    return catalog_dict


def read_json(json_path_or_url):
    """Toma el path a un JSON y devuelve el diccionario que representa.

    Se asume que el parámetro es una URL si comienza con 'http' o 'https', o
    un path local de lo contrario.

    Args:
        json_path_or_url (str): Path local o URL remota a un archivo de texto
            plano en formato JSON.

    Returns:
        dict: El diccionario que resulta de deserializar json_path_or_url.

    """
    assert isinstance(json_path_or_url, (str, unicode))

    parsed_url = urlparse(json_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(json_path_or_url)
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


def read_xlsx_catalog(xlsx_path_or_url):
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
    assert isinstance(xlsx_path_or_url, (str, unicode))

    parsed_url = urlparse(xlsx_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(xlsx_path_or_url)
        tmpfilename = ".tmpfile.xlsx"
        with io.open(tmpfilename, 'wb') as tmpfile:
            tmpfile.write(res.content)
        catalog_dict = read_local_xlsx_catalog(tmpfilename)
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


def _get_dataset_index(catalog, dataset_identifier):
    """Devuelve el índice de un dataset en el catálogo en función de su
    identificador"""
    matching_datasets = [
        idx for idx, dataset in enumerate(catalog["catalog_dataset"])
        if dataset["dataset_identifier"] == dataset_identifier
    ]

    # Debe haber exactamente un dataset con el identificador provisto.
    no_dsets_msg = "No hay ningún dataset con el identifier {}".format(
        dataset_identifier)
    many_dsets_msg = "Hay más de un dataset con el identifier {}: {}".format(
        dataset_identifier, matching_datasets)
    assert len(matching_datasets) != 0, no_dsets_msg
    assert len(matching_datasets) < 2, many_dsets_msg

    dataset_index = matching_datasets[0]
    return dataset_index


def _get_distribution_indexes(catalog, dataset_identifier, distribution_title):
    """Devuelve el índice de una distribución en su dataset en función de su
    título, junto con el índice de su dataset padre en el catálogo, en
    función de su identificador"""
    dataset_index = _get_dataset_index(catalog, dataset_identifier)
    dataset = catalog["catalog_dataset"][dataset_index]

    matching_distributions = [
        idx for idx, distribution in enumerate(dataset["dataset_distribution"])
        if distribution["distribution_title"] == distribution_title
    ]

    # Debe haber exactamente una distribución con los identicadores provistos
    no_dists_msg = """
No hay ninguna distribución de título {} en el dataset con identificador {}.
""".format(distribution_title, dataset_identifier)
    many_dists_msg = """
Hay más de una distribución de título {} en el dataset con identificador {}:
{}""".format(distribution_title, dataset_identifier, matching_distributions)
    assert len(matching_distributions) != 0, no_dists_msg
    assert len(matching_distributions) < 2, many_dists_msg

    distribution_index = matching_distributions[0]
    return dataset_index, distribution_index


def read_local_xlsx_catalog(xlsx_path):
    """Genera un diccionario de metadatos de catálogo a partir de un XLSX bien
    formado.

    Args:
        xlsx_path (str): Path a un archivo XLSX "template" para describir la
            metadata de un catálogo.

    Returns:
        dict: Diccionario con los metadatos de un catálogo.
    """
    assert xlsx_path.endswith(".xlsx"), """
El archivo a leer debe tener extensión XLSX."""

    workbook = pyxl.load_workbook(xlsx_path)

    catalogs = helpers.sheet_to_table(workbook["Catalog"])
    # Debe haber exactamente un catálogo en la hoja 'Catalog'
    assert (len(catalogs) != 0), "No hay ningún catálogo en la hoja 'Catalog'"
    assert (len(catalogs) < 2), "Hay más de un catálogo en la hoja 'Catalog'"
    # Genero el catálogo base
    catalog = catalogs[0]

    # Agrego themes y datasets al catálogo
    catalog["catalog_dataset"] = helpers.sheet_to_table(workbook["Dataset"])
    catalog["catalog_themeTaxonomy"] = (
        helpers.sheet_to_table(workbook["Theme"]))

    # Agrego lista de distribuciones vacía a cada dataset
    for dataset in catalog["catalog_dataset"]:
        dataset["dataset_distribution"] = []

    # Ubico cada distribución en su datasets
    distributions = helpers.sheet_to_table(workbook["Distribution"])
    for distribution in distributions:
        dataset_index = _get_dataset_index(
            catalog, distribution["dataset_identifier"])
        dataset = catalog["catalog_dataset"][dataset_index]
        dataset["dataset_distribution"].append(distribution)

    # Ubico cada campo en su distribución
    fields = helpers.sheet_to_table(workbook["Field"])
    for field in fields:
        dataset_index, distribution_index = _get_distribution_indexes(
            catalog, field["dataset_identifier"], field["distribution_title"])
        dataset = catalog["catalog_dataset"][dataset_index]
        distribution = dataset["dataset_distribution"][distribution_index]

        if "distribution_field" in distribution:
            distribution["distribution_field"].append(field)
        else:
            distribution["distribution_field"] = [field]

    # Transformo campos de texto separado por comas en listas
    if "catalog_language" in catalog:
        catalog["catalog_language"] = helpers.string_to_list(
            catalog["catalog_language"])

    for dataset in catalog["catalog_dataset"]:
        array_fields = ["dataset_superTheme", "dataset_theme", "dataset_tags",
                        "dataset_keyword", "dataset_language"]
        for field in array_fields:
            if field in dataset:
                dataset[field] = helpers.string_to_list(dataset[field])

    # Elimino los prefijos de los campos a nivel catálogo
    for old_key in catalog.keys():
        if old_key.startswith("catalog_"):
            new_key = old_key.replace("catalog_", "")
            catalog[new_key] = catalog.pop(old_key)
        else:
            catalog.pop(old_key)

    # Elimino los prefijos de los campos a nivel tema
    for theme in catalog["themeTaxonomy"]:
        for old_key in theme.keys():
            if old_key.startswith("theme_"):
                new_key = old_key.replace("theme_", "")
                theme[new_key] = theme.pop(old_key)
            else:
                theme.pop(old_key)

    # Elimino los prefijos de los campos a nivel dataset
    for dataset in catalog["dataset"]:
        for old_key in dataset.keys():
            if old_key.startswith("dataset_"):
                new_key = old_key.replace("dataset_", "")
                dataset[new_key] = dataset.pop(old_key)
            else:
                dataset.pop(old_key)

    # Elimino los campos auxiliares y los prefijos de los campos a nivel
    # distribución
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            for old_key in distribution.keys():
                if old_key.startswith("distribution_"):
                    new_key = old_key.replace("distribution_", "")
                    distribution[new_key] = distribution.pop(old_key)
                else:
                    distribution.pop(old_key)

    # Elimino campos auxiliares y los prefijos de los campos a nivel "campo"
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            if "field" in distribution:
                for field in distribution["field"]:
                    for old_key in field.keys():
                        if old_key.startswith("field_"):
                            new_key = old_key.replace("field_", "")
                            field[new_key] = field.pop(old_key)
                        else:
                            field.pop(old_key)

    # Agrupo las claves de "publisher" y "contactPoint" en sendos diccionarios
    catalog = _make_publisher(catalog)
    for dataset in catalog["dataset"]:
        dataset = _make_publisher(dataset)
        dataset = _make_contact_point(dataset)

    return catalog


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
    assert isinstance(path, (str, unicode, list)), """
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
    with open(path) as csvfile:
        reader = csv.DictReader(csvfile)
        table = list(reader)
    return table


def _read_xlsx_table(path):
    """Lee la hoja activa de un archivo XLSX a una lista de diccionarios."""
    workbook = pyxl.load_workbook(path)
    worksheet = workbook.active
    table = helpers.sheet_to_table(worksheet)

    return table
