#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'validator' de Pydatajson

Contiene los métodos para validar el perfil de metadatos de un catálogo.
"""

from __future__ import unicode_literals, print_function
from __future__ import with_statement, absolute_import

import os
import platform
import requests
import mimetypes
import logging
from collections import Counter
from pprint import pprint

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import jsonschema
from openpyxl.styles import Alignment, Font

from . import custom_exceptions as ce
from . import readers
from . import writers

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ABSOLUTE_SCHEMA_DIR = os.path.join(ABSOLUTE_PROJECT_DIR, "schemas")
DEFAULT_CATALOG_SCHEMA_FILENAME = "catalog.json"
EXTENSIONS_EXCEPTIONS = ["zip", "php", "asp", "aspx"]

logger = logging.getLogger('pydatajson')


def create_validator(schema_filename=None, schema_dir=None):
    """Crea el validador necesario para inicializar un objeto DataJson.

    Para poder resolver referencias inter-esquemas, un Validador requiere
    que se especifique un RefResolver (Resolvedor de Referencias) con el
    directorio base (absoluto) y el archivo desde el que se referencia el
    directorio.

    Para poder validar formatos, un Validador requiere que se provea
    explícitamente un FormatChecker. Actualmente se usa el default de la
    librería, jsonschema.FormatChecker().

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
    schema_filename = schema_filename or DEFAULT_CATALOG_SCHEMA_FILENAME
    schema_dir = schema_dir or ABSOLUTE_SCHEMA_DIR
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

    validator = jsonschema.Draft4Validator(
        schema=schema, resolver=resolver, format_checker=format_checker)

    return validator


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
            validator = create_validator()

    jsonschema_res = validator.is_valid(catalog)
    custom_errors = iter_custom_errors(catalog)

    return jsonschema_res and len(list(custom_errors)) == 0


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

    # La respuesta por default se devuelve si no hay errores
    default_response = {
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

    # Genero la lista de errores en la instancia a validar
    if not validator:
        if hasattr(catalog, "validator"):
            validator = catalog.validator
        else:
            validator = create_validator()
    jsonschema_errors = list(validator.iter_errors(catalog))
    custom_errors = list(iter_custom_errors(catalog))

    errors = jsonschema_errors + custom_errors

    response = default_response.copy()
    for error in errors:
        response = _update_validation_response(
            error, response)

    # filtra los resultados que están ok, para hacerlo más compacto
    if only_errors:
        response["error"]["dataset"] = filter(
            lambda dataset: dataset["status"] == "ERROR",
            response["error"]["dataset"]
        )

    # elige el formato del resultado
    if export_path:
        validation_lists = _catalog_validation_to_list(response)

        # config styles para reportes en excel
        alignment = Alignment(
            wrap_text=True,
            shrink_to_fit=True,
            vertical="center"
        )
        column_styles = {
            "catalog": {
                "catalog_status": {"width": 20},
                "catalog_error_location": {"width": 40},
                "catalog_error_message": {"width": 40},
                "catalog_title": {"width": 20},
            },
            "dataset": {
                "dataset_error_location": {"width": 20},
                "dataset_identifier": {"width": 40},
                "dataset_status": {"width": 20},
                "dataset_title": {"width": 40},
                "dataset_list_index": {"width": 20},
                "dataset_error_message": {"width": 40},
            }
        }
        cell_styles = {
            "catalog": [
                {"alignment": Alignment(vertical="center")},
                {"row": 1, "font": Font(bold=True)},
            ],
            "dataset": [
                {"alignment": Alignment(vertical="center")},
                {"row": 1, "font": Font(bold=True)},
            ]
        }

        # crea tablas en un sólo excel o varios CSVs
        writers.write_tables(
            tables=validation_lists, path=export_path,
            column_styles=column_styles, cell_styles=cell_styles
        )

    elif fmt == "dict":
        return response

    elif fmt == "list":
        return _catalog_validation_to_list(response)

    # Comentado porque requiere una extensión pesada nueva para pydatajson
    # elif fmt == "df":
    #     validation_lists = self._catalog_validation_to_list(response)
    #     return {
    #         "catalog": pd.DataFrame(validation_lists["catalog"]),
    #         "dataset": pd.DataFrame(validation_lists["dataset"])
    #     }

    else:
        raise Exception("No se reconoce el formato {}".format(fmt))


def iter_custom_errors(catalog):
    """Realiza validaciones sin usar el jsonschema.

    En esta función se agregan bloques de código en python que realizan
    validaciones complicadas o imposibles de especificar usando jsonschema.
    """

    try:
        # chequea que no se repiten los ids de la taxonomía específica
        if "themeTaxonomy" in catalog:
            theme_ids = [theme["id"] for theme in catalog["themeTaxonomy"]]
            dups = _find_dups(theme_ids)
            if len(dups) > 0:
                yield ce.ThemeIdRepeated(dups)

        # chequea que un dataset no use un theme que no exista en la taxonomía
        # TODO: hay que implementarlo

        # chequea que un dataset no use theme con id esté repetido en taxonomía
        # TODO: hay que implementarlo

        # chequea que la extensión de fileName, downloadURL y format sean
        # consistentes
        for dataset_idx, dataset in enumerate(catalog["dataset"]):
            for distribution_idx, distribution in enumerate(
                    dataset["distribution"]):
                for attribute in ['downloadURL', 'fileName']:
                    if not format_matches_extension(distribution, attribute):
                        yield ce.ExtensionError(dataset_idx, distribution_idx,
                                                distribution, attribute)

        # chequea que no haya duplicados en los downloadURL de las
        # distribuciones
        # urls = []
        # for dataset in catalog["dataset"]:
        #     urls += [distribution['downloadURL']
        #              for distribution in dataset['distribution']
        #              if distribution.get('downloadURL')]
        # dups = _find_dups(urls)
        # if len(dups) > 0:
        #     yield ce.DownloadURLRepetitionError(dups)

        # chequea que las URLs de las distribuciones estén operativas
        # hay que revisar
        # for distribution in catalog.distributions:
        #     url = distribution.get("downloadURL")
        #     status_code = requests.head(url).status_code
        #     if status_code != 200:
        #         yield ce.DownloadURLBrokenError(
        #             distribution.get("identifier"), url, status_code)

    except Exception:
        logger.exception("Error de validación.")


def _find_dups(elements):
    return [item for item, count in Counter(elements).items()
            if count > 1]


def _update_validation_response(error, response):
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
        "instance": (None if error.validator == "required" else error.instance)
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


def _catalog_validation_to_list(response):
    """Formatea la validación de un catálogo a dos listas de errores.

    Una lista de errores para "catalog" y otra para "dataset".
    """

    # crea una lista de dicts para volcarse en una tabla  (catalog)
    rows_catalog = []
    validation_result = {
        "catalog_title": response["error"]["catalog"]["title"],
        "catalog_status": response["error"]["catalog"]["status"],
    }
    for error in response["error"]["catalog"]["errors"]:
        catalog_result = dict(validation_result)
        catalog_result.update({
            "catalog_error_message": error["message"],
            "catalog_error_location": ", ".join(error["path"]),
        })
        rows_catalog.append(catalog_result)

    if len(response["error"]["catalog"]["errors"]) == 0:
        catalog_result = dict(validation_result)
        catalog_result.update({
            "catalog_error_message": None,
            "catalog_error_location": None
        })
        rows_catalog.append(catalog_result)

    # crea una lista de dicts para volcarse en una tabla (dataset)
    rows_dataset = []
    for dataset in response["error"]["dataset"]:
        validation_result = {
            "dataset_title": dataset["title"],
            "dataset_identifier": dataset["identifier"],
            "dataset_list_index": dataset["list_index"],
            "dataset_status": dataset["status"]
        }
        for error in dataset["errors"]:
            dataset_result = dict(validation_result)
            dataset_result.update({
                "dataset_error_message": error["message"],
                "dataset_error_location": error["path"][-1]
            })
            rows_dataset.append(dataset_result)

        if len(dataset["errors"]) == 0:
            dataset_result = dict(validation_result)
            dataset_result.update({
                "dataset_error_message": None,
                "dataset_error_location": None
            })
            rows_dataset.append(dataset_result)

    return {"catalog": rows_catalog, "dataset": rows_dataset}


def format_matches_extension(distribution, attribute):
    """Chequea si una extensión podría corresponder a un formato dado."""

    if attribute in distribution and "format" in distribution:
        if "/" in distribution['format']:
            possible_format_extensions = mimetypes.guess_all_extensions(
                distribution['format'])
        else:
            possible_format_extensions = ['.' + distribution['format'].lower()]

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


def main(catalog):
    """Permite validar un catálogo por línea de comandos.

    Args:
        catalog (str): Path local o URL a un catálogo.
    """
    res = validate_catalog(catalog, only_errors=True, fmt="list",
                           export_path=None, validator=None)
    print("")
    print("=== Errores a nivel de CATALOGO ===")
    pprint(res["catalog"])

    print("")
    print("=== Errores a nivel de DATASET ===")
    pprint(res["dataset"])


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv > 1) else []
    main(*args)
