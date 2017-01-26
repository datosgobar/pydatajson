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


    @classmethod
    def _write(cls, table, path):
        """ Exporta una tabla en el formato deseado (CSV o XLSX).

        La extensión del archivo debe ser ".csv" o ".xlsx", y en función de
        ella se decidirá qué método usar para escribirlo.

        Args:
            table (list of dicts): Tabla a ser exportada.
            path (str): Path al archivo CSV o XLSX de exportación.
        """
        assert isinstance(path, (str, unicode)), "`path` debe ser un string"
        assert isinstance(table, list), "`table` debe ser una lista de dicts"

        # Sólo sabe escribir listas de diccionarios con información tabular
        if not cls._is_list_of_matching_dicts(table):
            raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

        # Deduzco el formato de archivo de `path` y redirijo según corresponda.
        suffix = path.split(".")[-1]
        if suffix == "csv":
            return cls._write_csv(table, path)
        elif suffix == "xlsx":
            return cls._write_xlsx(table, path)
        else:
            raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o.xlsx""".format(suffix))

    @staticmethod
    def _write_csv(table, path):
        headers = table[0].keys()

        with open(path, 'w') as target_file:
            writer = csv.DictWriter(csvfile=target_file, fieldnames=headers,
                                    lineterminator="\n", encoding="utf-8")
            writer.writeheader()
            for row in table:
                writer.writerow(row)

    @staticmethod
    def _write_xlsx(table, path):
        headers = table[0].keys()
        workbook = pyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(headers)
        for row in table:
            worksheet.append(row.values())

        workbook.save(path)

def write_json_catalog(catalog, target_file):
    """Escribo un catálogo a un archivo JSON con codificación UTF-8."""
    catalog_str = json.dumps(catalog, indent=4, separators=(",", ": "),
                             encoding="utf-8", ensure_ascii=False)
    with io.open(target_file, "w", encoding='utf-8') as target:
        target.write(catalog_str)


