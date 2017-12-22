#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
xl_methods

Métodos ligeramente modificados a partir de abenassi/xlseries para manipular
archivos en formato XLSX (https://github.com/abenassi/xlseries).
"""
from six import string_types, text_type


def compare_cells(wb1, wb2):
    """Compare two excels based on row iteration."""

    # compare each cell of each worksheet
    for ws1, ws2 in zip(wb1.worksheets, wb2.worksheets):
        compare_cells_ws(ws1, ws2)
    return True


def compare_cells_ws(ws1, ws2):
    """Compare two worksheets based on row iteration."""

    # compare each cell of each worksheet
    for row1, row2 in zip(ws1.rows, ws2.rows):
        for cell1, cell2 in zip(row1, row2):

            msg = "".join([_safe_str(cell1.value), " != ",
                           _safe_str(cell2.value), "\nrow: ",
                           _safe_str(cell1.row),
                           " column: ", _safe_str(cell1.column)])

            value1 = normalize_value(cell1.value)
            value2 = normalize_value(cell2.value)

            assert value1 == value2, msg

    return True


def normalize_value(value):
    """Strip spaces if the value is a string, convert None to empty string or
    let it pass otherwise."""

    if isinstance(value, string_types):
        return value.strip()
    elif value is None:
        return ""
    else:
        return value


def _safe_str(value):
    return text_type(value)
