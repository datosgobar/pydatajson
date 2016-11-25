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
import requests

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
    def _deserialize_json(json_path_or_url):
        """ Toma el path a un JSON y devuelve el diccionario que representa."""
        # Se entiende que es una URL aquello que empieza con "http"
        if json_path_or_url.startswith("http"):
            req = requests.get(json_path_or_url)
            json_string = req.content
        # Todo lo demás se resulve localmente
        else:
            with open(json_path_or_url) as json_file:
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
            bool: True si el data.json sigue el schema, sino False.
        """
        datajson = self._deserialize_json(datajson_path)
        res = self.validator.is_valid(datajson)
        return res


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

        # Respuesta por default si no hay errores
        res = {
            "status": "OK",
            "error": {
                "catalog": [],
                "dataset": []
            }
        }

        # Genero árbol de errores para explorarlo
        error_tree = jsonschema.ErrorTree(self.validator.iter_errors(datajson))

        # Extraigo títulos del catálogo y los datasets para reportar errores:
        catalog_title = datajson["title"]
        dataset_titles = [dataset["title"] for dataset in datajson["dataset"]]

        # Si hay algún error propio del catálogo, lo reporto como erróneo
        if error_tree.errors != {}:
            res["status"] = "ERROR"
            res["error"]["catalog"].append(catalog_title)

        # Si total_errors a nivel de un cierto dataset es !=0, lo reporto
        for idx, title in enumerate(dataset_titles):
            if error_tree["dataset"][idx].total_errors != 0:
                res["status"] = "ERROR"
                res["error"]["dataset"].append(title)

        return res


def main():
    """ En caso de ejecutar el módulo como script, se corre esta función"""
    pass

if __name__ == '__main__':
    main()
