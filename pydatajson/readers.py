#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo principal de pydatajson

Contiene la clase DataJson que reúne los métodos públicos para trabajar con
archivos data.json.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import sys
import io
import platform
import os.path
from urlparse import urlparse
import warnings
import json
from collections import OrderedDict
import jsonschema
import requests
import unicodecsv as csv
import openpyxl as pyxl
import xlsx_to_json


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
        with open(tmpfilename, 'wb') as tmpfile:
            tmpfile.write(res.content)
        catalog_dict = xlsx_to_json.read_local_xlsx_catalog(tmpfilename)
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

        catalog_dict = xlsx_to_json.read_local_xlsx_catalog(xlsx_path_or_url)

    return catalog_dict


    @classmethod
    def _read(cls, path):
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
            if cls._is_list_of_matching_dicts(path):
                return path
            else:
                raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

        # Deduzco el formato de archivo de `path` y redirijo según corresponda.
        suffix = path.split(".")[-1]
        if suffix == "csv":
            return cls._read_csv(path)
        elif suffix == "xlsx":
            return cls._read_xlsx(path)
        else:
            raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o .xlsx""".format(suffix))

    @staticmethod
    def _read_csv(path):
        with open(path) as csvfile:
            reader = csv.DictReader(csvfile)
            table = list(reader)
        return table

    @staticmethod
    def _read_xlsx(path):
        workbook = pyxl.load_workbook(path)
        worksheet = workbook.active
        table = xlsx_to_json.sheet_to_table(worksheet)

        return table


