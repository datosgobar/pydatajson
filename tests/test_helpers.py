#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
import nose
import openpyxl as pyxl
from .context import pydatajson


class HelpersTestCase(unittest.TestCase):

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
            actual_table = pydatajson.helpers.sheet_to_table(
                workbook[sheetname])
            expected_table = expected_tables[sheetname]
            self.assertEqual(actual_table, expected_table)

    def test_string_to_list_default_separator(self):
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
            actual_list = pydatajson.helpers.string_to_list(string)
            self.assertListEqual(actual_list, expected_list)

    def test_string_to_list_alternative_separator(self):
        """ string_to_list convierte una str separada por un separador
        alternativo (";") en una lista."""
        actual_list = pydatajson.helpers.string_to_list(
            string="un;;separador;;nuevo", sep=";;")
        expected_list = ["un", "separador", "nuevo"]

        self.assertListEqual(actual_list, expected_list)

    def test_traverse_dict_correct_keys(self):
        """traverse_dict devuelve un valor si toda clave buscada existe."""
        pass

    def test_traverse_dict_index_out_of_range(self):
        """traverse_dict devuelve el valor por omisión si un índice está fuera
        del rango de su lista."""
        pass

    def test_traverse_dict_missing_key(self):
        """traverse_dict devuelve el valor por omisión si una clave no existe
        en un diccionario."""
        pass

    def test_traverse_dict_string_index_for_list(self):
        """traverse_dict devuelve el valor por omisión si se pasa un string
        como índice de una lista."""
        pass

    def test_is_list_of_matching_dicts_bad_input(self):
        """is_list_of_matching_dicts levanta errores si el input no es una
        lista compuesta únicamente de diccionarios."""
        # input no lista
        # lista con elemns no dict
        pass

    def test_is_list_of_matching_dicts_with_matched_dicts(self):
        """is_list_of_matching_dicts devuelve True si todos los elementos del
        input tienen las mismas claves."""
        pass

    def test_is_list_of_matching_dicts_with_mismatched_dicts(self):
        """is_list_of_matching_dicts devuelve False si no todos los elementos
        del input tienen las mismas claves."""
        pass


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
