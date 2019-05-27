#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'validator' de Pydatajson

Contiene los métodos para validar el perfil de metadatos de un catálogo.
"""

from __future__ import unicode_literals, print_function
from __future__ import with_statement, absolute_import

import os
import platform
import mimetypes
import logging
from collections import Counter

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import jsonschema

from . import custom_exceptions as ce
from . import readers

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ABSOLUTE_SCHEMA_DIR = os.path.join(ABSOLUTE_PROJECT_DIR, "schemas")
DEFAULT_CATALOG_SCHEMA_FILENAME = "catalog.json"
EXTENSIONS_EXCEPTIONS = ["zip", "php", "asp", "aspx"]

logger = logging.getLogger('pydatajson')


class Validator(object):

    def __init__(self, schema_filename=DEFAULT_CATALOG_SCHEMA_FILENAME,
                 schema_dir=ABSOLUTE_SCHEMA_DIR):
        self.jsonschema_validator = \
            self.init_jsonschema_validator(schema_dir, schema_filename)

    def init_jsonschema_validator(self, schema_dir, schema_filename):
        schema_path = os.path.join(schema_dir, schema_filename)
        schema = readers.read_json(schema_path)
        # Según https://github.com/Julian/jsonschema/issues/98
        # Permite resolver referencias locales a otros esquemas.
        if platform.system() == 'Windows':
            base_uri = "file:///" + schema_path.replace("\\", "/")
        else:
            base_uri = "file://" + schema_path
        resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema)
        format_checker = jsonschema.FormatChecker()
        return jsonschema.Draft4Validator(
            schema=schema, resolver=resolver, format_checker=format_checker)

    def is_valid(self, catalog):
        return not self._get_errors(catalog)

    def validate_catalog(self, catalog, only_errors=False):
        default_response = self._default_response(catalog)
        errors = self._get_errors(catalog)

        response = default_response.copy()
        for error in errors:
            response = self._update_validation_response(
                error, response)

        # filtra los resultados que están ok, para hacerlo más compacto
        if only_errors:
            response["error"]["dataset"] = [
                dataset for dataset in response["error"]["dataset"] if
                dataset["status"] == "ERROR"]

        return response

    def _get_errors(self, catalog):
        errors = list(
            self.jsonschema_validator.iter_errors(catalog)
        )
        try:
            for error in self._custom_errors(catalog):
                errors.append(error)
        except:
            logger.warning("Error de validación")
        return errors

    def _default_response(self, catalog):
        return {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": catalog.get("title"),
                    "errors": []
                },
                # "dataset" contiene lista de rtas default si el catálogo
                # contiene la clave "dataset" y además su valor es una lista.
                # En caso contrario "dataset" es None.
                "dataset": [
                    {
                        "status": "OK",
                        "title": dataset.get("title"),
                        "identifier": dataset.get("identifier"),
                        "list_index": index,
                        "errors": []
                    } for index, dataset in enumerate(catalog["dataset"])
                ] if ("dataset" in catalog and
                      isinstance(catalog["dataset"], list)) else None
            }
        }

    def _custom_errors(self, catalog):
        """Realiza validaciones sin usar el jsonschema.

        En esta función se agregan bloques de código en python que realizan
        validaciones complicadas o imposibles de especificar usando jsonschema
        """
        validators = self._validators()

        for validator in validators:
            for error in validator(catalog):
                yield error

    def _validators(self):
        return [
            self._theme_ids_not_repeated,
            self._consistent_distribution_fields
        ]

    def _theme_ids_not_repeated(self, catalog):
        if "themeTaxonomy" in catalog:
            theme_ids = [theme["id"] for theme in catalog["themeTaxonomy"]]
            dups = self._find_dups(theme_ids)
            if len(dups) > 0:
                yield ce.ThemeIdRepeated(dups)

    def _consistent_distribution_fields(self, catalog):
        for dataset_idx, dataset in enumerate(catalog["dataset"]):
            for distribution_idx, distribution in enumerate(
                    dataset["distribution"]):
                for attribute in ['downloadURL', 'fileName']:
                    if not self.format_matches_extension(distribution,
                                                         attribute):
                        yield ce.ExtensionError(dataset_idx, distribution_idx,
                                                distribution, attribute)

    def format_matches_extension(self, distribution, attribute):
        """Chequea si una extensión podría corresponder a un formato dado."""

        if attribute in distribution and "format" in distribution:
            if "/" in distribution['format']:
                possible_format_extensions = mimetypes.guess_all_extensions(
                    distribution['format'])
            else:
                possible_format_extensions = [
                    '.' + distribution['format'].lower()
                ]

            file_name = urlparse(distribution[attribute]).path
            extension = os.path.splitext(file_name)[-1].lower()

            if attribute == 'downloadURL' and not extension:
                return True

            # hay extensiones exceptuadas porque enmascaran otros formatos
            if extension.lower().replace(".", "") in EXTENSIONS_EXCEPTIONS:
                return True

            if extension not in possible_format_extensions:
                return False

        return True

    def _find_dups(self, elements):
        return [item for item, count in Counter(elements).items()
                if count > 1]

    def _update_validation_response(self, error, response):
        """Actualiza la respuesta por default acorde a un error de
        validación."""
        new_response = response.copy()

        # El status del catálogo entero será ERROR
        new_response["status"] = "ERROR"

        # Adapto la información del ValidationError recibido a los fines
        # del validador de DataJsons
        error_info = {
            # Error Code 1 para "campo obligatorio faltante"
            # Error Code 2 para "error en tipo o formato de campo"
            "error_code": 1 if error.validator == "required" else 2,
            "message": error.message,
            "validator": error.validator,
            "validator_value": error.validator_value,
            "path": list(error.path),
            # La instancia validada es irrelevante si el error es de tipo 1
            "instance": (None if error.validator == "required"
                         else error.instance)
        }

        # Identifico a qué nivel de jerarquía sucedió el error.
        if len(error.path) >= 2 and error.path[0] == "dataset":
            # El error está a nivel de un dataset particular o inferior
            position = new_response["error"]["dataset"][error.path[1]]
        else:
            # El error está a nivel de catálogo
            position = new_response["error"]["catalog"]

        position["status"] = "ERROR"
        position["errors"].append(error_info)

        return new_response


def is_valid_catalog(catalog, validator=None):
    """Valida que un archivo `data.json` cumpla con el schema definido.

    Chequea que el data.json tiene todos los campos obligatorios y que
    tanto los campos obligatorios como los opcionales siguen la estructura
    definida en el schema.

    Args:
        catalog (str o dict): Catálogo (dict, JSON o XLSX) a ser validado.

    Returns:
        bool: True si el data.json cumple con el schema, sino False.
    """
    catalog = readers.read_catalog(catalog)
    if not validator:
        if hasattr(catalog, "validator"):
            validator = catalog.validator
        else:
            validator = Validator()

    return validator.is_valid(catalog)


def validate_catalog(catalog, only_errors=False, fmt="dict",
                     export_path=None, validator=None):
    """Analiza un data.json registrando los errores que encuentra.

    Chequea que el data.json tiene todos los campos obligatorios y que
    tanto los campos obligatorios como los opcionales siguen la estructura
    definida en el schema.

    Args:
        catalog (str o dict): Catálogo (dict, JSON o XLSX) a ser validado.
        only_errors (bool): Si es True sólo se reportan los errores.
        fmt (str): Indica el formato en el que se desea el reporte.
            "dict" es el reporte más verborrágico respetando la
                estructura del data.json.
            "list" devuelve un dict con listas de errores formateados para
                generar tablas.
        export_path (str): Path donde exportar el reporte generado (en
            formato XLSX o CSV). Si se especifica, el método no devolverá
            nada, a pesar de que se pase algún argumento en `fmt`.

    Returns:
        dict: Diccionario resumen de los errores encontrados::

            {
                "status": "OK",  # resultado de la validación global
                "error": {
                    "catalog": {
                        "status": "OK",
                        "errors": []
                        "title": "Título Catalog"},
                    "dataset": [
                        {
                            "status": "OK",
                            "errors": [],
                            "title": "Titulo Dataset 1"
                        },
                        {
                            "status": "ERROR",
                            "errors": [error1_info, error2_info, ...],
                            "title": "Titulo Dataset 2"
                        }
                    ]
                }
            }

        Donde errorN_info es un dict con la información del N-ésimo
        error encontrado, con las siguientes claves: "path", "instance",
        "message", "validator", "validator_value", "error_code".

    """
    catalog = readers.read_catalog(catalog)

    # Genero la lista de errores en la instancia a validar
    if not validator:
        if hasattr(catalog, "validator"):
            validator = catalog.validator
        else:
            validator = Validator()

    return validator.validate_catalog(catalog, only_errors)
