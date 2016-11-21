#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo principal de pydatajson

Contiene la clase DataJson que reúne los métodos públicos para trabajar con
archivos data.json.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os
import json


class DataJson(object):
    """Métodos para trabajar con archivos data.json."""

    def __init__(self, datajson_file):
        """
        Args:
            datajson_file (str): Path a un data.json.
        """
        self.datajson = json.loads(datajson_file)

    def is_valid_structure(self, datajson_schema=None):
        """Valida que el data.json cumple el datajson_schema.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_schema (dict or str): Opcional. Diccionario o path a un
                JSON con el schema definido.

        Returns:
            bool: True si el data.json sigue el schema, sino False.
        """
        pass

    def validate_structure(self, datajson_schema=None):
        """Analiza el data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        TODO: Todavía hay que definir bien la estructura de la respuesta de
            esta función.

        Args:
            datajson_schema (dict or str): Opcional. Diccionario o path a un
                JSON con el schema definido.

        Returns:
            TODO: A definir.
        """
        pass


def main():
    pass

if __name__ == '__main__':
    main()
