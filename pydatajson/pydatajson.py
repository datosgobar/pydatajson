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


    def __init__(self,
                 schema_filename=DEFAULT_CATALOG_SCHEMA_FILENAME,
                 schema_dir=ABSOLUTE_SCHEMA_DIR):
        """Crea un manipulador de `data.json`s.

        Salvo que se indique lo contrario, el validador de esquemas asociado
        es el definido por default con las constantes de clase.

        Args:
            schema_filename (str): Nombre del archivo que contiene el esquema
            validador
            schema_dir (str): Directorio (absoluto) donde se encuentra el
            esquema validador (y sus referencias, de tenerlas).

        Returns:
            DataJson: Objeto para manipular archivos data.json.
        """
        self.validator = self._create_validator(schema_filename, schema_dir)

    @classmethod
    def _create_validator(cls, schema_filename, schema_dir):
        """Crea el validador necesario para inicializar un objeto DataJson.

        Para poder resolver referencias inter-esquemas, un Validador requiere
        que se especifique un RefResolver (Resolvedor de Referencias) con el
        directorio base (absoluto) y el archivo desde el que se referencia el
        directorio.

        Args:
            schema_filename (str): Nombre del archivo que contiene el esquema
            validador "maestro".
            schema_dir (str): Directorio (absoluto) donde se encuentra el
            esquema validador maestro y sus referencias, de tenerlas.

        Returns:
            validator (Draft4Validator): Un validador de JSONSchema Draft #4.
            El validador especifica se crea con un RefResolver que resuelve
            referencias de `schema_filename` dentro de `schema_dir`.
        """
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
        """ Toma el path a un JSON y devuelve el diccionario que representa."""
        with open(json_path) as json_file:
            return json.load(json_file, encoding="utf8")

    def is_valid_catalog(self, datajson_path):
        """Valida que un archivo `data.json` cumpla con el schema definido.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

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
        """Analiza un data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

        Returns:
            validation_result (dict): Diccionario resumen de los errores
            encontrados. Las claves principales son:
                "status": ("OK"|"ERROR")
                "error"["catalog"]: El título del catálogo con errores.
                "error"["dataset"]: Los títulos de los dataset con errores.

        """
        datajson = self._deserialize_json(datajson_path)
        self.validator.validate(datajson)


def main():
    """ En caso de ejecutar el módulo como script, se corre esta función"""
    pass

if __name__ == '__main__':
    main()
