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
from openpyxl.utils import column_index_from_string
import logging
from . import helpers


def write_table(table, path, column_styles=None, cell_styles=None):
    """ Exporta una tabla en el formato deseado (CSV o XLSX).

    La extensión del archivo debe ser ".csv" o ".xlsx", y en función de
    ella se decidirá qué método usar para escribirlo.

    Args:
        table (list of dicts): Tabla a ser exportada.
        path (str): Path al archivo CSV o XLSX de exportación.
    """
    assert isinstance(path, (str, unicode)), "`path` debe ser un string"
    assert isinstance(table, list), "`table` debe ser una lista de dicts"

    # si la tabla está vacía, no escribe nada
    if len(table) == 0:
        logging.warning("Tabla vacia: no se genera ninguna archivo.")
        return

    # Sólo sabe escribir listas de diccionarios con información tabular
    if not helpers.is_list_of_matching_dicts(table):
        raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

    # Deduzco el formato de archivo de `path` y redirijo según corresponda.
    suffix = path.split(".")[-1]
    if suffix == "csv":
        return _write_csv_table(table, path)
    elif suffix == "xlsx":
        return _write_xlsx_table(table, path, column_styles, cell_styles)
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


def _apply_styles_to_ws(ws, column_styles=None, cell_styles=None):

    # aplica estilos de columnas
    if column_styles:
        for col, properties in column_styles.iteritems():
            for prop_name, prop_value in properties.iteritems():
                setattr(ws.column_dimensions[col], prop_name, prop_value)

    # aplica estilos de celdas
    if cell_styles:
        for i in xrange(1, ws.max_row + 1):
            for j in xrange(1, ws.max_column + 1):
                cell = ws.cell(row=i, column=j)

                for cell_style in cell_styles:
                    match_all = (
                        "col" not in cell_style and
                        "row" not in cell_style
                    )
                    match_row = (
                        "row" in cell_style and
                        cell_style["row"] == i
                    )
                    match_col = (
                        "col" in cell_style and
                        column_index_from_string(cell_style["col"]) == j
                    )
                    if match_all or match_row or match_col:
                        for prop_name, prop_value in cell_style.iteritems():
                            if prop_name != "col" and prop_name != "row":
                                setattr(cell, prop_name, prop_value)


def _write_xlsx_table(table, path, column_styles=None, cell_styles=None):

    workbook = pyxl.Workbook()
    worksheet = workbook.active

    headers = table[0].keys()
    worksheet.append(headers)

    for index, row in enumerate(table):
        worksheet.append(row.values())

    _apply_styles_to_ws(worksheet, column_styles, cell_styles)

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
