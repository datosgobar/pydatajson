#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo principal de pydatajson

Contiene la clase DataJson que reúne los métodos públicos para trabajar con
archivos data.json.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
from urlparse import urljoin, urlparse
import warnings
import json
import jsonschema
import requests

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


class DataJson(object):
    """Métodos para trabajar con archivos data.json."""

    # Variables por default
    ABSOLUTE_SCHEMA_DIR = os.path.join(ABSOLUTE_PROJECT_DIR, "schemas")
    DEFAULT_CATALOG_SCHEMA_FILENAME = "catalog.json"

    def __init__(self,
                 schema_filename=DEFAULT_CATALOG_SCHEMA_FILENAME,
                 schema_dir=ABSOLUTE_SCHEMA_DIR):
        """Crea un manipulador de `data.json`s.

        Salvo que se indique lo contrario, el validador de esquemas asociado
        es el definido por default en las constantes de clase.

        Args:
            schema_filename (str): Nombre del archivo que contiene el esquema
                validador.
            schema_dir (str): Directorio (absoluto) donde se encuentra el
                esquema validador (y sus referencias, de tenerlas).
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
            Draft4Validator: Un validador de JSONSchema Draft #4. El validador
                se crea con un RefResolver que resuelve referencias de
                `schema_filename` dentro de `schema_dir`.
        """
        schema_path = os.path.join(schema_dir, schema_filename)
        schema = cls._json_to_dict(schema_path)

        # Según https://github.com/Julian/jsonschema/issues/98
        # Permite resolver referencias locales a otros esquemas.
        resolver = jsonschema.RefResolver(
            base_uri=urljoin('file:', schema_path), referrer=schema)

        validator = jsonschema.Draft4Validator(
            schema=schema, resolver=resolver)

        return validator

    @staticmethod
    def _json_to_dict(dict_or_json_path):
        """Toma el path a un JSON y devuelve el diccionario que representa.

        Si el argumento es un dict, lo deja pasar. Si es un string asume que el
        parámetro es una URL si comienza con 'http' o 'https', o un path local
        de lo contrario.

        Args:
            dict_or_json_path (dict or str): Si es un str, path local o URL
                remota a un archivo de texto plano en formato JSON.

        Returns:
            dict: El diccionario que resulta de deserializar
                dict_or_json_path.

        """
        assert isinstance(dict_or_json_path, (dict, str, unicode))

        if isinstance(dict_or_json_path, dict):
            return dict_or_json_path

        parsed_url = urlparse(dict_or_json_path)

        if parsed_url.scheme in ["http", "https"]:
            req = requests.get(dict_or_json_path)
            json_string = req.content

        else:
            # En caso de que dict_or_json_path parezca ser una URL remota,
            # advertirlo
            path_start = parsed_url.path.split(".")[0]
            if path_start == "www" or path_start.isdigit():
                warnings.warn("""
La dirección del archivo JSON ingresada parece una URL, pero no comienza
con 'http' o 'https' así que será tratada como una dirección local. ¿Tal vez
quiso decir 'http://{}'?
                """.format(dict_or_json_path).encode("utf8"))

            with open(dict_or_json_path) as json_file:
                json_string = json_file.read()

        json_dict = json.loads(json_string, encoding="utf8")

        return json_dict

    def is_valid_catalog(self, datajson_path):
        """Valida que un archivo `data.json` cumpla con el schema definido.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

        Returns:
            bool: True si el data.json cumple con el schema, sino False.
        """
        datajson = self._json_to_dict(datajson_path)
        res = self.validator.is_valid(datajson)
        return res

    def validate_catalog(self, datajson_path):
        """Analiza un data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        siguen la estructura definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

        Returns:
            dict: Diccionario resumen de los errores encontrados::

                {
                    "status": "OK",  # resultado de la validación global
                    "error": {
                        "catalog": {"status": "OK", "title": "Título Catalog"},
                        "dataset": [
                            {"status": "OK", "title": "Titulo Dataset 1"},
                            {"status": "ERROR", "title": "Titulo Dataset 2"}
                        ]
                    }
                }
        """
        datajson = self._json_to_dict(datajson_path)

        # Genero árbol de errores para explorarlo
        errors_iterator = self.validator.iter_errors(datajson)
        error_tree = jsonschema.ErrorTree(errors_iterator)

        global_status = "OK" if error_tree.total_errors == 0 else "ERROR"

        catalog_status = "OK" if (error_tree.errors == {} and
                                  "publisher" not in error_tree) else "ERROR"

        def _dataset_result(idx, dataset):
            """Dado un dataset y su índice en el data.json, devuelve una
            diccionario con el resultado de su validación. """
            if "dataset" not in error_tree:
                result = {
                    "status": "OK",
                    "title": dataset.get("title")
                }
            else:
                dataset_total_errors = error_tree["dataset"][idx].total_errors
                result = {
                    "status": "OK" if dataset_total_errors == 0 else "ERROR",
                    "title": dataset.get("title")
                }

            return result

        datasets_results = [
            _dataset_result(i, ds) for i, ds in enumerate(datajson["dataset"])
        ]

        res = {
            "status": global_status,
            "error": {
                "catalog": {
                    "status": catalog_status,
                    "title": datajson.get("title")
                },
                "dataset": datasets_results
            }
        }

        return res


def main():
    """En caso de ejecutar el módulo como script, se corre esta función."""
    pass


if __name__ == '__main__':
    main()
