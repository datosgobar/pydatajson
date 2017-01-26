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


    @staticmethod
    def _traverse_dict(dicc, keys, default_value=None):
        """Recorre un diccionario siguiendo una lista de claves, y devuelve
        default_value en caso de que alguna de ellas no exista.

        Args:
            dicc (dict): Diccionario a ser recorrido.
            keys (list): Lista de claves a ser recorrida. Puede contener
                índices de listas y claves de diccionarios mezcladas.
            default_value: Valor devuelto en caso de que `dicc` no se pueda
                recorrer siguiendo secuencialmente la lista de `keys` hasta
                el final.

        Returns:
            object: El valor obtenido siguiendo la lista de `keys` dentro de
            `dicc`.
        """
        for key in keys:
            if isinstance(dicc, dict) and key in dicc:
                dicc = dicc[key]
            elif isinstance(dicc, list):
                dicc = dicc[key]
            else:
                return default_value

        return dicc


    @staticmethod
    def _is_list_of_matching_dicts(list_of_dicts):
        """Comprueba que una lista esté compuesta únicamente por diccionarios,
        que comparten exactamente las mismas claves."""
        elements = (isinstance(d, dict) and d.keys() == list_of_dicts[0].keys()
                    for d in list_of_dicts)
        return all(elements)


def sheet_to_table(worksheet):
    """Transforma una hoja del libro en una lista de diccionarios."""
    def value(cell):
        """Extrae el valor de una celda de Excel."""
        value = cell.value
        if isinstance(value, (str, unicode)):
            value = value.strip()
        return value

    worksheet_rows = list(worksheet.rows)
    headers = [value(cell) for cell in worksheet_rows[0]]
    value_rows = [
        [value(cell) for cell in row] for row in worksheet_rows[1:]
        # Únicamente considero filas con al menos un campo no-nulo
        if any([value(cell) for cell in row])
    ]
    table = [
        # Ignoro los campos con valores nulos (None)
        {k: v for (k, v) in zip(headers, row) if v is not None}
        for row in value_rows
    ]

    return table


def string_to_list(string, sep=","):
    """Transforma una string con elementos separados por `sep` en una lista."""
    return [value.strip() for value in string.split(sep)]

