#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
import json
import nose
import openpyxl as pyxl
from pydatajson import xlsx_to_json


class XlsxToJsonTestCase(unittest.TestCase):

    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = os.path.join("tests", "results")

    def test_sheet_to_table(self):
        """sheet_to_table convierte hojas de un libro en listas de
        diccionarios"""
        workbook_path = os.path.join(self.SAMPLES_DIR,
                                     "prueba_sheet_to_table.xlsx")
        workbook = pyxl.load_workbook(workbook_path)

        expected_tables = {
            "Imperio": [
                {"Nombre": "Darth Vader", "Jedi": "Poderoso"},
                {"Nombre": "Kylo Ren", "Jedi": "Mas o Menos"}
            ],
            "Rebeldes": [
                {"Nombre": "Luke", "Edad": 56},
                {"Nombre": "Han", "Edad": 122},
                {"Nombre": "Yoda", "Edad": 0}
            ]
        }

        for sheetname in ["Imperio", "Rebeldes"]:
            actual_table = xlsx_to_json.sheet_to_table(workbook[sheetname])
            expected_table = expected_tables[sheetname]
            self.assertEqual(actual_table, expected_table)

    def test_string_to_list(self):
        """string_to_list convierte una str separada por "," en una
        lista"""
        strings = [
            " pan , vino,gorriones ,23",
            "economía,\t\tturismo,salud\n",
            """uno,,
            dos,
            tres"""
        ]
        lists = [
            ["pan", "vino", "gorriones", "23"],
            ["economía", "turismo", "salud"],
            ["uno", "", "dos", "tres"]
        ]
        for (string, expected_list) in zip(strings, lists):
            actual_list = xlsx_to_json.string_to_list(string)
            self.assertListEqual(actual_list, expected_list)

        # Pruebo con un separador especial
        actual_list = xlsx_to_json.string_to_list(
            string="un;;separador;;nuevo", sep=";;")
        expected_list = ["un", "separador", "nuevo"]

        self.assertListEqual(actual_list, expected_list)

    def test_read_local_xlsx_catalog(self):
        workbook_path = os.path.join(self.SAMPLES_DIR,
                                     "catalogo_justicia.xlsx")
        actual_dict = xlsx_to_json.read_local_xlsx_catalog(workbook_path)

        result_path = os.path.join(self.RESULTS_DIR, "catalogo_justicia.json")
        with open(result_path) as result_file:
            expected_dict = json.load(result_file, encoding='utf-8')

        self.assertDictEqual(actual_dict, expected_dict)

if __name__ == '__main__':
    nose.run(defaultTest=__name__)
