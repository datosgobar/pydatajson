#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo principal de pydatajson

Contiene la clase DataJson que reúne los métodos públicos para trabajar con
archivos data.json.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import sys
import os.path
from urlparse import urljoin, urlparse
import warnings
import json
from pprint import pprint
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

        format_checker = jsonschema.FormatChecker()

        validator = jsonschema.Draft4Validator(
            schema=schema, resolver=resolver, format_checker=format_checker)

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

        # La respuesta por default se devuelve si no hay errores
        default_response = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": datajson.get("title")
                },
                # "dataset" contiene lista de rtas default si el catálogo
                # contiene la clave "dataset" y además su valor es una lista.
                # En caso contrario "dataset" es None.
                "dataset": [
                    {
                        "status": "OK",
                        "title": dataset.get("title")
                    } for dataset in datajson["dataset"]
                ] if ("dataset" in datajson and
                      isinstance(datajson["dataset"], list)) else None
            }
        }

        def _update_response(validation_error, response):
            """Actualiza la respuesta por default acorde a un error de
            validación."""
            new_response = response.copy()

            # El status del catálogo entero será ERROR
            new_response["status"] = "ERROR"

            path = validation_error.path

            if len(path) >= 2 and path[0] == "dataset":
                # El error está a nivel de un dataset particular o inferior
                new_response["error"]["dataset"][path[1]]["status"] = "ERROR"
            else:
                # El error está a nivel de catálogo
                new_response["error"]["catalog"]["status"] = "ERROR"

            return new_response

        # Genero la lista de errores en la instancia a validar
        errors_iterator = self.validator.iter_errors(datajson)

        final_response = default_response.copy()
        for error in errors_iterator:
            final_response = _update_response(error, final_response)

        return final_response


def main():
    """Permite ejecutar el módulo por línea de comandos.

    Valida un path o url a un archivo data.json devolviendo True/False si es
    válido y luego el resultado completo.

    Example:
        python pydatajson.py http://181.209.63.71/data.json
        python pydatajson.py ~/github/pydatajson/tests/samples/full_data.json
    """
    datajson_file = sys.argv[1]
    dj = DataJson()
    bool_res = dj.is_valid_catalog(datajson_file)
    full_res = dj.validate_catalog(datajson_file)
    pprint(bool_res)
    pprint(full_res)


if __name__ == '__main__':
    main()
