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
import jsonschema

DEFAULT_DATAJSON_SCHEMA = "schemas/empty_schema.json"

class DataJsonValidator(jsonschema.Draft4Validator):
    """Validador de archivos data.json"""

    def __init__(self, schema_definition_file=DEFAULT_DATAJSON_SCHEMA):
        """
        Args:
            schema_definition_file (str): Path al esquema contra el que se
            desea validar.
        """
        with open(schema_definition_file) as schema_file_buffer:
            deserialized_schema = json.load(schema_file_buffer,
                                            encoding="utf8")
            jsonschema.Draft4Validator.__init__(self, schema=deserialized_schema)


class DataJson(object):
    """Métodos para trabajar con archivos data.json."""

    def __init__(self, datajson_file, datajson_validator=None):
        """
        Args:
            datajson_file (str): Path a un data.json.
            datajson_validator: Nombre de un objeto DataJsonValidator. Si no se
                                       provee se creará uno.
            datajson_schema_file (str): Path a un JSON Schema.
        """

        with open(datajson_file) as datajson_file_buffer:
            self.datajson = json.load(datajson_file_buffer)

        if isinstance(datajson_validator, DataJsonValidator):
            self.validator = datajson_validator
        else:
            self.validator = DataJsonValidator()


    def is_valid_structure(self):
        """Valida que el data.json cumple el datajson_schema.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_schema (dict or str): Opcional. Diccionario o path a un
                JSON con el schema definido.

        Returns:
            bool: True si el data.json sigue el schema, sino False.
        """
        try:
            self.validate_structure()
            return True
        except jsonschema.ValidationError:
            return False

        pass

    def validate_structure(self):
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
        self.validator.validate(self.datajson)
        pass


def main():
    pass

if __name__ == '__main__':
    main()
