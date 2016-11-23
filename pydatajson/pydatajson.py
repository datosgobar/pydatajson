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


class DataJson(object):
    """Métodos para trabajar con archivos data.json."""

    # Variables por default
    ABSOLUTE_PATH_TO_BASE_SCHEMA_DIR = os.path.join(os.getcwd(),
                                                    "pydatajson/schemas")
    DEFAULT_DATAJSON_SCHEMA_FILENAME = "required_fields_schema.json"
    ABSOLUTE_PATH_TO_DEFAULT_SCHEMA_FILE = \
            os.path.join(ABSOLUTE_PATH_TO_BASE_SCHEMA_DIR,
                         DEFAULT_DATAJSON_SCHEMA_FILENAME)


    def __init__(self, validator=None):
        """
        Args:
            validator (object): Si se desea sobreescribir el validador por
            default, se puede pasar uno a través de este parámetro.
        """
        self.validator = (validator or
                          self._create_validator(
                              self.ABSOLUTE_PATH_TO_DEFAULT_SCHEMA_FILE))


    def _create_validator(self, schema_file):
        with open(schema_file) as schema_file_buffer:
            deserialized_schema = json.load(schema_file_buffer,
                                            encoding="utf8")
        # Según https://github.com/Julian/jsonschema/issues/98
        # Permite resolver referencias locales a otros esquemas.
        resolver = jsonschema.RefResolver(
            base_uri=("file://" + self.ABSOLUTE_PATH_TO_DEFAULT_SCHEMA_FILE),
            referrer=deserialized_schema)

        validator = jsonschema.Draft4Validator(
            schema=deserialized_schema,
            resolver=resolver)

        return validator


    def _deserialize_datajson(self, datajson_file):
        with open(datajson_file) as datajson_file_buffer:
            datajson = json.load(datajson_file_buffer, encoding="utf8")

        return datajson


    def is_valid_catalog(self, datajson_file):
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
            self.validate_catalog(datajson_file)
        except jsonschema.ValidationError as e:
            print(e)
            return False
        else:
            return True


    def validate_catalog(self, datajson_file):
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
        datajson = self._deserialize_datajson(datajson_file)
        self.validator.validate(datajson)


def main():
    pass

if __name__ == '__main__':
    main()
