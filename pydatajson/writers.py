#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'writers' de pydatajson

Contiene los métodos para escribir
- diccionarios con metadatos de catálogos a formato JSON, así como
- listas de diccionarios ("tablas") en formato CSV o XLSX
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import io
import json
import unicodecsv as csv
import openpyxl as pyxl
from . import helpers


def write_table(table, path):
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
    if not helpers.is_list_of_matching_dicts(table):
        raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

    # Deduzco el formato de archivo de `path` y redirijo según corresponda.
    suffix = path.split(".")[-1]
    if suffix == "csv":
        return _write_csv_table(table, path)
    elif suffix == "xlsx":
        return _write_xlsx_table(table, path)
    else:
        raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o.xlsx""".format(suffix))


def _write_csv_table(table, path):
    headers = table[0].keys()

    with open(path, 'w') as target_file:
        writer = csv.DictWriter(csvfile=target_file, fieldnames=headers,
                                lineterminator="\n", encoding='utf-8')
        writer.writeheader()
        for row in table:
            writer.writerow(row)


def _write_xlsx_table(table, path):
    headers = table[0].keys()
    workbook = pyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in table:
        worksheet.append(row.values())

    workbook.save(path)


def write_json(obj, path):
    """Escribo un objeto a un archivo JSON con codificación UTF-8."""
    obj_str = unicode(json.dumps(obj, indent=4, separators=(",", ": "),
                                 ensure_ascii=False))
    with io.open(path, "w", encoding='utf-8') as target:
        target.write(obj_str)


def write_json_catalog(catalog, path):
    """Función de compatibilidad con releases anteriores."""
    write_json(catalog, path)
