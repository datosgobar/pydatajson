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
    ABSOLUTE_SCHEMA_DIR = os.path.join(os.getcwd(), "pydatajson/schemas")
    DEFAULT_CATALOG_SCHEMA_FILENAME = "catalog.json"


    def __init__(self, schema_filename=None, schema_dir=None):
        """
        Args:
            schema_filename (str)   : Si se desea sobreescribir el validador por
        """
        schema_filename = (schema_filename or
                           self.DEFAULT_CATALOG_SCHEMA_FILENAME)
        schema_dir = schema_dir or self.ABSOLUTE_SCHEMA_DIR

        self.validator = self._create_validator(schema_filename, schema_dir)

    @classmethod
    def _create_validator(cls, schema_filename, schema_dir):

        schema_path = os.path.join(schema_dir, schema_filename)
        schema = cls._deserialize_json(schema_path)

        # Según https://github.com/Julian/jsonschema/issues/98
        # Permite resolver referencias locales a otros esquemas.
        resolver = jsonschema.RefResolver(
            base_uri=("file://" + schema_dir + '/'), referrer=schema)

        validator = jsonschema.Draft4Validator(
            schema=schema, resolver=resolver)

        return validator


    @staticmethod
    def _deserialize_json(json_path):
        """ Deserializa el archivo `json_path` y lo devuelve como
        diccionario."""
        with open(json_path) as json_file:
            return json.load(json_file, encoding="utf8")

    def is_valid_catalog(self, datajson_path):
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
            self.validate_catalog(datajson_path)
        except jsonschema.ValidationError:
            return False
        else:
            return True


    def validate_catalog(self, datajson_path):
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
        datajson = self._deserialize_json(datajson_path)
        self.validator.validate(datajson)


def main():
    pass

if __name__ == '__main__':
    main()
