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
import io
import platform
import os.path
import warnings
import re
import json
from collections import OrderedDict
from datetime import datetime
import jsonschema
from . import readers
from . import helpers
from . import writers

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CENTRAL_CATALOG = "http://datos.gob.ar/data.json"


class DataJson(object):
    """Métodos para trabajar con archivos data.json."""

    # Variables por default
    ABSOLUTE_SCHEMA_DIR = os.path.join(ABSOLUTE_PROJECT_DIR, "schemas")
    DEFAULT_CATALOG_SCHEMA_FILENAME = "catalog.json"

    CATALOG_FIELDS_PATH = os.path.join(ABSOLUTE_PROJECT_DIR, "fields")

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

    def is_valid_catalog(self, catalog):
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
        res = self.validator.is_valid(catalog)
        return res

    @staticmethod
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
            "instance": (None if error.validator == "required" else
                         error.instance)
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

    def validate_catalog(self, catalog):
        """Analiza un data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        tanto los campos obligatorios como los opcionales siguen la estructura
        definida en el schema.

        Args:
            catalog (str o dict): Catálogo (dict, JSON o XLSX) a ser validado.

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
                        "errors": []
                    } for dataset in catalog["dataset"]
                ] if ("dataset" in catalog and
                      isinstance(catalog["dataset"], list)) else None
            }
        }

        # Genero la lista de errores en la instancia a validar
        errors_iterator = self.validator.iter_errors(catalog)

        final_response = default_response.copy()
        for error in errors_iterator:
            final_response = self._update_validation_response(error,
                                                              final_response)

        return final_response

    @classmethod
    def _dataset_report_helper(cls, dataset):
        """Toma un dict con la metadata de un dataset, y devuelve un dict coni
        los valores que dataset_report() usa para reportar sobre él.

        Args:
            dataset (dict): Diccionario con la metadata de un dataset.

        Returns:
            dict: Diccionario con los campos a nivel dataset que requiere
            dataset_report().
        """
        publisher_name = helpers.traverse_dict(dataset, ["publisher", "name"])

        super_themes = None
        if isinstance(dataset.get("superTheme"), list):
            strings = [s for s in dataset.get("superTheme")
                       if isinstance(s, (str, unicode))]
            super_themes = ", ".join(strings)

        themes = None
        if isinstance(dataset.get("theme"), list):
            strings = [s for s in dataset.get("theme")
                       if isinstance(s, (str, unicode))]
            themes = ", ".join(strings)

        def _stringify_distribution(distribution):
            title = distribution.get("title")
            url = distribution.get("downloadURL")

            return "\"{}\": {}".format(title, url)

        distributions = [d for d in dataset["distribution"]
                         if isinstance(d, dict)]

        distributions_list = None
        if isinstance(distributions, list):
            distributions_strings = [
                _stringify_distribution(d) for d in distributions
            ]
            distributions_list = "\n".join(distributions_strings)

        fields = OrderedDict()
        fields["dataset_title"] = dataset.get("title")
        fields["dataset_accrualPeriodicity"] = dataset.get(
            "accrualPeriodicity")
        fields["dataset_description"] = dataset.get("description")
        fields["dataset_publisher_name"] = publisher_name
        fields["dataset_superTheme"] = super_themes
        fields["dataset_theme"] = themes
        fields["dataset_landingPage"] = dataset.get("landingPage")
        fields["distributions_list"] = distributions_list

        return fields

    @staticmethod
    def _catalog_report_helper(catalog, catalog_validation, url):
        """Toma un dict con la metadata de un catálogo, y devuelve un dict con
        los valores que catalog_report() usa para reportar sobre él.

        Args:
            catalog (dict): Diccionario con la metadata de un catálogo.
            validation (dict): Resultado, únicamente a nivel catálogo, de la
                validación completa de `catalog`.

        Returns:
            dict: Diccionario con los campos a nivel catálogo que requiere
            catalog_report().
        """
        fields = OrderedDict()
        fields["catalog_metadata_url"] = url
        fields["catalog_title"] = catalog.get("title")
        fields["catalog_description"] = catalog.get("description")
        fields["valid_catalog_metadata"] = (
            1 if catalog_validation["status"] == "OK" else 0)

        return fields

    def _dataset_report(self, dataset, dataset_validation, dataset_index,
                        catalog_fields, harvest='none', report=None):
        """ Genera una línea del `catalog_report`, correspondiente a un dataset
        de los que conforman el catálogo analizado."""

        dataset_report = OrderedDict(catalog_fields)
        dataset_report["valid_dataset_metadata"] = (
            1 if dataset_validation["status"] == "OK" else 0)
        dataset_report["dataset_index"] = dataset_index

        if harvest == 'all':
            dataset_report["harvest"] = 1
        elif harvest == 'none':
            dataset_report["harvest"] = 0
        elif harvest == 'valid':
            dataset_report["harvest"] = (
                int(dataset_report["valid_dataset_metadata"]))
        elif harvest == 'report':
            if not report:
                raise ValueError("""
Usted eligio 'report' como criterio de harvest, pero no proveyo un valor para
el argumento 'report'. Por favor, intentelo nuevamente.""")

            datasets_to_harvest = self._extract_datasets_to_harvest(report)
            dataset_report["harvest"] = (
                1 if (dataset_report["catalog_metadata_url"],
                      dataset.get("title")) in datasets_to_harvest
                else 0)
        else:
            raise ValueError("""
{} no es un criterio de harvest reconocido. Pruebe con 'all', 'none', 'valid' o
'report'.""".format(harvest))

        dataset_report.update(self._dataset_report_helper(dataset))

        return dataset_report.copy()

    def catalog_report(self, catalog, harvest='none', report=None):
        """Genera un reporte sobre los datasets de un único catálogo.

        Args:
            catalog (dict, str o unicode): Representación externa (path/URL) o
                interna (dict) de un catálogo.
            harvest (str): Criterio de cosecha ('all', 'none',
                'valid' o 'report').

        Returns:
            list: Lista de diccionarios, con un elemento por cada dataset
                presente en `catalog`.
        """

        url = catalog if isinstance(catalog, (str, unicode)) else None
        catalog = readers.read_catalog(catalog)

        validation = self.validate_catalog(catalog)
        catalog_validation = validation["error"]["catalog"]
        datasets_validations = validation["error"]["dataset"]

        catalog_fields = self._catalog_report_helper(
            catalog, catalog_validation, url)

        if "dataset" in catalog and isinstance(catalog["dataset"], list):
            datasets = [d if isinstance(d, dict) else {} for d in
                        catalog["dataset"]]
        else:
            datasets = []

        catalog_report = [
            self._dataset_report(
                dataset, datasets_validations[index], index,
                catalog_fields, harvest, report=report
            ) for index, dataset in enumerate(datasets)
        ]

        return catalog_report

    def generate_datasets_report(self, catalogs, harvest='valid',
                                 report=None, export_path=None):
        """Genera un reporte sobre las condiciones de la metadata de los
        datasets contenidos en uno o varios catálogos.

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) catálogos.
            harvest (str): Criterio a utilizar para determinar el valor del
                campo "harvest" en el reporte generado ('all', 'none',
                'valid' o 'report').
            report (str): Path a un reporte/config especificando qué
                datasets marcar con harvest=1 (sólo si harvest=='report').
            export_path (str): Path donde exportar el reporte generado (en
                formato XLSX o CSV). Si se especifica, el método no devolverá
                nada.

        Returns:
            list: Contiene tantos dicts como datasets estén presentes en
            `catalogs`, con la data del reporte generado.
        """
        assert isinstance(catalogs, (str, unicode, dict, list))
        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, (str, unicode, dict)):
            catalogs = [catalogs]

        catalogs_reports = [self.catalog_report(catalog, harvest, report)
                            for catalog in catalogs]
        full_report = []
        for report in catalogs_reports:
            full_report.extend(report)

        if export_path:
            writers.write_table(table=full_report, path=export_path)
        else:
            return full_report

    def generate_harvester_config(self, catalogs=None, harvest='valid',
                                  report=None, frequency='R/P1D',
                                  export_path=None):
        """Genera un archivo de configuración del harvester a partir de un
        reporte, o de un conjunto de catálogos y un criterio de cosecha
        (`harvest`).

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) catálogos.
            harvest (str): Criterio para determinar qué datasets incluir en el
                archivo de configuración generado  ('all', 'none',
                'valid' o 'report').
            report (list o str): Tabla de reporte generada por
                generate_datasets_report() como lista de diccionarios o archivo
                en formato XLSX o CSV. Sólo se usa cuando `harvest=='report'`,
                en cuyo caso `catalogs` se ignora.
            frequency (str): Frecuencia de búsqueda de actualizaciones en los
                datasets a cosechar. Todo intervalo de frecuencia válido según
                ISO 8601 es válido. Es 'R/P1D' (diariamiente) por omisión, y
                si se pasa`None`, se conservará el valor de original de cada
                dataset, `dataset["accrualPeriodicity"]`.
            export_path (str): Path donde exportar el reporte generado (en
                formato XLSX o CSV). Si se especifica, el método no devolverá
                nada.

        Returns:
            list of dicts: Un diccionario con variables de configuración
            por cada dataset a cosechar.
        """
        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, (str, unicode, dict)):
            catalogs = [catalogs]

        if harvest == 'report':
            if not report:
                raise ValueError("""
Usted eligio 'report' como criterio de harvest, pero no proveyo un valor para
el argumento 'report'. Por favor, intentelo nuevamente.""")
            datasets_report = readers.read_table(report)
        elif harvest in ['valid', 'none', 'all']:
            # catalogs no puede faltar para estos criterios
            assert isinstance(catalogs, (str, unicode, dict, list))
            datasets_report = self.generate_datasets_report(catalogs, harvest)
        else:
            raise ValueError("""
{} no es un criterio de harvest reconocido. Pruebe con 'all', 'none', 'valid' o
'report'.""".format(harvest))

        config_keys = ["catalog_metadata_url", "dataset_title",
                       "dataset_accrualPeriodicity"]

        harvester_config = [
            OrderedDict(
                # Retengo únicamente los campos que necesita el harvester
                [(k, v) for (k, v) in dataset.items() if k in config_keys]
            )
            # Para aquellost datasets marcados con 'harvest'==1
            for dataset in datasets_report if bool(int(dataset["harvest"]))
        ]

        if frequency:
            valid_patterns = [
                "^R/P\\d+(\\.\\d+)?[Y|M|W|D]$",
                "^R/PT\\d+(\\.\\d+)?[H|M|S]$"
            ]

            if any([re.match(pat, frequency) for pat in valid_patterns]):
                for dataset in harvester_config:
                    dataset["dataset_accrualPeriodicity"] = frequency
            else:
                warnings.warn("""
{} no es una frecuencia de cosecha valida. Se conservara la frecuencia de
actualizacion original de cada dataset.""".format(frequency))

        if export_path:
            writers.write_table(harvester_config, export_path)
        else:
            return harvester_config

    def generate_harvestable_catalogs(self, catalogs, harvest='all',
                                      report=None, export_path=None):
        """Filtra los catálogos provistos según el criterio determinado en
        `harvest`.

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) catálogos.
            harvest (str): Criterio para determinar qué datasets conservar de
                cada catálogo ('all', 'none', 'valid' o 'report').
            report (list o str): Tabla de reporte generada por
                generate_datasets_report() como lista de diccionarios o archivo
                en formato XLSX o CSV. Sólo se usa cuando `harvest=='report'`.
            export_path (str): Path a un archivo JSON o directorio donde
                exportar los catálogos filtrados. Si termina en ".json" se
                exportará la lista de catálogos a un único archivo. Si es un
                directorio, se guardará en él un JSON por catálogo. Si se
                especifica `export_path`, el método no devolverá nada.

        Returns:
            list of dicts: Lista de catálogos.
        """
        assert isinstance(catalogs, (str, unicode, dict, list))
        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, (str, unicode, dict)):
            catalogs = [catalogs]

        harvestable_catalogs = [readers.read_catalog(c) for c in catalogs]
        catalogs_urls = [catalog if isinstance(catalog, (str, unicode))
                         else None for catalog in catalogs]

        # aplica los criterios de cosecha
        if harvest == 'all':
            pass
        elif harvest == 'none':
            for catalog in harvestable_catalogs:
                catalog["dataset"] = []
        elif harvest == 'valid':
            report = self.generate_datasets_report(catalogs, harvest)
            return self.generate_harvestable_catalogs(
                catalogs=catalogs, harvest='report', report=report,
                export_path=export_path)
        elif harvest == 'report':
            if not report:
                raise ValueError("""
Usted eligio 'report' como criterio de harvest, pero no proveyo un valor para
el argumento 'report'. Por favor, intentelo nuevamente.""")
            datasets_to_harvest = self._extract_datasets_to_harvest(report)
            for idx_cat, catalog in enumerate(harvestable_catalogs):
                catalog_url = catalogs_urls[idx_cat]
                if ("dataset" in catalog and
                        isinstance(catalog["dataset"], list)):
                    catalog["dataset"] = [
                        dataset for dataset in catalog["dataset"]
                        if (catalog_url, dataset.get("title")) in
                        datasets_to_harvest
                    ]
                else:
                    catalog["dataset"] = []
        else:
            raise ValueError("""
{} no es un criterio de harvest reconocido. Pruebe con 'all', 'none', 'valid' o
'report'.""".format(harvest))

        # devuelve los catálogos harvesteables
        if export_path and os.path.isdir(export_path):
            # Creo un JSON por catálogo
            for idx, catalog in enumerate(harvestable_catalogs):
                filename = os.path.join(export_path, "catalog_{}".format(idx))
                writers.write_json(catalog, filename)
        elif export_path:
            # Creo un único JSON con todos los catálogos
            writers.write_json(harvestable_catalogs, export_path)
        else:
            return harvestable_catalogs

    def generate_datasets_summary(self, catalog, export_path=None):
        """Genera un informe sobre los datasets presentes en un catálogo,
        indicando para cada uno:
            - Índice en la lista catalog["dataset"]
            - Título
            - Identificador
            - Cantidad de distribuciones
            - Estado de sus metadatos ["OK"|"ERROR"]

        Es utilizada por la rutina diaria de `libreria-catalogos` para reportar
        sobre los datasets de los catálogos mantenidos.

        Args:
            catalog (str o dict): Path a un catálogo en cualquier formato,
                JSON, XLSX, o diccionario de python.
            export_path (str): Path donde exportar el informe generado (en
                formato XLSX o CSV). Si se especifica, el método no devolverá
                nada.

        Returns:
            list: Contiene tantos dicts como datasets estén presentes en
            `catalogs`, con los datos antes mencionados.
        """
        catalog = readers.read_catalog(catalog)

        # Trato de leer todos los datasets bien formados de la lista
        # catalog["dataset"], si existe.
        if "dataset" in catalog and isinstance(catalog["dataset"], list):
            datasets = [d if isinstance(d, dict) else {} for d in
                        catalog["dataset"]]
        else:
            # Si no, considero que no hay datasets presentes
            datasets = []

        validation = self.validate_catalog(catalog)["error"]["dataset"]

        def info_dataset(index, dataset):
            """Recolecta información básica de un dataset."""
            info = OrderedDict()
            info["indice"] = index
            info["titulo"] = dataset.get("title")
            info["identificador"] = dataset.get("identifier")
            info["estado_metadatos"] = validation[index]["status"]
            info["cant_errores"] = len(validation[index]["errors"])
            info["cant_distribuciones"] = len(dataset["distribution"])

            return info

        summary = [info_dataset(i, ds) for i, ds in enumerate(datasets)]
        if export_path:
            writers.write_table(summary, export_path)
        else:
            return summary

    def generate_catalog_readme(self, catalog, export_path=None):
        """Genera una descripción textual en formato Markdown sobre los
        metadatos generales de un catálogo (título, editor, fecha de
        publicación, et cetera), junto con:
            - estado de los metadatos a nivel catálogo,
            - estado global de los metadatos,
            - cantidad de datasets federados y no federados,
            - detalles de los datasets no federados
            - cantidad de datasets y distribuciones incluidas

        Es utilizada por la rutina diaria de `libreria-catalogos` para generar
        un README con información básica sobre los catálogos mantenidos.

        Args:
            catalog (str o dict): Path a un catálogo en cualquier formato,
                JSON, XLSX, o diccionario de python.
            export_path (str): Path donde exportar el texto generado (en
                formato Markdown). Si se especifica, el método no devolverá
                nada.

        Returns:
            str: Texto de la descripción generada.
        """
        # Si se paso una ruta, guardarla
        if isinstance(catalog, (str, unicode)):
            catalog_path_or_url = catalog
        else:
            catalog_path_or_url = None

        catalog = readers.read_catalog(catalog)
        validation = self.validate_catalog(catalog)
        # Solo necesito indicadores para un catalogo
        indicators = self.generate_catalogs_indicators(
            catalog, CENTRAL_CATALOG)[0][0]

        readme_template = """
# Catálogo: {title}

## Información General

- **Autor**: {publisher_name}
- **Correo Electrónico**: {publisher_mbox}
- **Ruta del catálogo**: {catalog_path_or_url}
- **Nombre del catálogo**: {title}
- **Descripción**:

> {description}

## Estado de los metadatos y cantidad de recursos

- **Estado metadatos globales**: {global_status}
- **Estado metadatos catálogo**: {catalog_status}
- **Cantidad Total de Datasets**: {no_of_datasets}
- **Cantidad Total de Distribuciones**: {no_of_distributions}

- **Cantidad de Datasets Federados**: {federated_datasets}
- **Cantidad de Datasets NO Federados**: {not_federated_datasets}
- **Porcentaje de Datasets NO Federados**: {not_federated_datasets_pct}%

## Datasets no federados:

{not_federated_datasets_list}

## Datasets incluidos

Por favor, consulte el informe [`datasets.csv`](datasets.csv).
"""

        not_federated_datasets_list = "\n".join([
            "- [{}]({})".format(dataset[0], dataset[1])
            for dataset in indicators["datasets_no_federados"]
        ])

        content = {
            "title": catalog.get("title"),
            "publisher_name": helpers.traverse_dict(
                catalog, ["publisher", "name"]),
            "publisher_mbox": helpers.traverse_dict(
                catalog, ["publisher", "mbox"]),
            "catalog_path_or_url": catalog_path_or_url,
            "description": catalog.get("description"),
            "global_status": validation["status"],
            "catalog_status": validation["error"]["catalog"]["status"],
            "no_of_datasets": len(catalog["dataset"]),
            "no_of_distributions": sum([len(dataset["distribution"]) for
                                        dataset in catalog["dataset"]]),
            "federated_datasets": indicators["datasets_federados_cant"],
            "not_federated_datasets": indicators["datasets_no_federados_cant"],
            "not_federated_datasets_pct": (
                100.0 - indicators["datasets_federados_pct"]),
            "not_federated_datasets_list": not_federated_datasets_list
        }

        catalog_readme = readme_template.format(**content)

        if export_path:
            with io.open(export_path, 'w', encoding='utf-8') as target:
                target.write(catalog_readme)
        else:
            return catalog_readme

    @classmethod
    def _extract_datasets_to_harvest(cls, report):
        """Extrae de un reporte los datos necesarios para reconocer qué
        datasets marcar para cosecha en cualquier generador.

        Args:
            report (str o list): Reporte (lista de dicts) o path a uno.

        Returns:
            list: Lista de tuplas con los títulos de catálogo y dataset de cada
            reporte extraído.
        """
        assert isinstance(report, (str, unicode, list))

        # Si `report` es una lista de tuplas con longitud 2, asumimos que es un
        # reporte procesado para extraer los datasets a harvestear. Se devuelve
        # intacta.
        if (isinstance(report, list) and all([isinstance(x, tuple) and
                                              len(x) == 2 for x in report])):
            return report

        table = readers.read_table(report)
        table_keys = table[0].keys()
        expected_keys = ["catalog_metadata_url", "dataset_title",
                         "dataset_accrualPeriodicity"]

        # Verifico la presencia de las claves básicas de un config de harvester
        for key in expected_keys:
            if key not in table_keys:
                raise KeyError("""
El reporte no contiene la clave obligatoria {}. Pruebe con otro archivo.
""".format(key))

        if "harvest" in table_keys:
            # El archivo es un reporte de datasets.
            datasets_to_harvest = [
                (row["catalog_metadata_url"], row["dataset_title"]) for row in
                table if int(row["harvest"])]
        else:
            # El archivo es un config de harvester.
            datasets_to_harvest = [
                (row["catalog_metadata_url"], row["dataset_title"]) for row in
                table]

        return datasets_to_harvest

    def generate_catalogs_indicators(self, catalogs, central_catalog=None):
        """Genera una lista de diccionarios con varios indicadores sobre
        los catálogos provistos, tales como la cantidad de datasets válidos,
        días desde su última fecha actualizada, entre otros.

        Args:
            catalogs (str o list): uno o más catalogos sobre los que se quiera
                obtener indicadores
            central_catalog (str): catálogo central sobre el cual comparar los
                datasets subidos en la lista anterior. De no pasarse no se
                generarán indicadores de federación de datasets.

        Returns:
            tuple: 2 elementos, el primero una lista de diccionarios con los
                indicadores esperados, uno por catálogo pasado, y el segundo
                un diccionario con indicadores a nivel global,
                datos sobre la lista entera en general.
        """
        assert isinstance(catalogs, (str, unicode, dict, list))
        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, (str, unicode, dict)):
            catalogs = [catalogs]

        # Leo todos los catálogos
        catalogs = [readers.read_catalog(catalog) for catalog in catalogs]

        indicators_list = []
        # Cuenta la cantidad de campos usados/recomendados a nivel global
        fields = {}
        for catalog in catalogs:
            catalog = readers.read_catalog(catalog)

            fields_count, result = self._generate_indicators(catalog)
            if central_catalog:
                result.update(self._federation_indicators(catalog,
                                                          central_catalog))

            indicators_list.append(result)
            # Sumo a la cuenta total de campos usados/totales
            fields = helpers.add_dicts(fields_count, fields)

        # Indicadores de la red entera
        network_indicators = {
            'catalogos_cant': len(catalogs)
        }

        # Sumo los indicadores individuales al total
        indicators_total = indicators_list[0].copy()
        for i in range(1, len(indicators_list)):
            indicators_total = helpers.add_dicts(indicators_total,
                                                 indicators_list[i])
        network_indicators.update(indicators_total)
        # Genero los indicadores de la red entera,
        self._network_indicator_percentages(fields, network_indicators)

        return indicators_list, network_indicators

    @staticmethod
    def _network_indicator_percentages(fields, network_indicators):
        """Encapsula el cálculo de indicadores de porcentaje (de errores,
        de campos recomendados/optativos utilizados, de datasets actualizados)
        sobre la red de nodos entera.

        Args:
            fields (dict): Diccionario con claves 'recomendado', 'optativo',
                'total_recomendado', 'total_optativo', cada uno con valores
                que representan la cantidad de c/u en la red de nodos entera.

            network_indicators (dict): Diccionario de la red de nodos, con
                las cantidades de datasets_meta_ok y datasets_(des)actualizados
                calculados previamente. Se modificará este argumento con los
                nuevos indicadores.
        """

        # Los porcentuales no se pueden sumar, tienen que ser recalculados

        # % de datasets cuya metadata está ok
        meta_ok = network_indicators['datasets_meta_ok_cant']
        meta_error = network_indicators['datasets_meta_error_cant']
        total_pct = 0.0
        if meta_ok or meta_error:  # Evita división por cero
            total_pct = 100 * float(meta_ok) / (meta_error + meta_ok)
        network_indicators['datasets_meta_ok_pct'] = round(total_pct, 2)

        # % de campos recomendados y optativos utilizados en todo el catálogo
        if fields:  # 'fields' puede estar vacío si ningún campo es válido
            rec_pct = 100 * float(fields['recomendado']) / \
                fields['total_recomendado']

            opt_pct = 100 * float(fields['optativo']) / \
                fields['total_optativo']

            network_indicators.update({
                'campos_recomendados_pct': round(rec_pct, 2),
                'campos_optativos_pct': round(opt_pct, 2)
            })

        # % de datasets actualizados
        act = network_indicators['datasets_actualizados_cant']
        desact = network_indicators['datasets_desactualizados_cant']
        updated_pct = 0
        if act or desact:  # Evita división por cero
            updated_pct = 100 * act / float(act + desact)
        network_indicators['datasets_actualizados_pct'] = round(updated_pct, 2)

        # % de datasets federados
        federados = network_indicators.get('datasets_federados_cant')
        no_federados = network_indicators.get('datasets_no_federados_cant')

        if federados or no_federados:
            federados_pct = 100 * float(federados) / (federados + no_federados)
            network_indicators['datasets_federados_pct'] = \
                round(federados_pct, 2)

    def _generate_indicators(self, catalog):
        """Genera los indicadores de un catálogo individual.

        Args:
            catalog (dict): diccionario de un data.json parseado

        Returns:
            dict: diccionario con los indicadores del catálogo provisto
        """
        result = {}
        # Obtengo summary para los indicadores del estado de los metadatos
        result.update(self._generate_status_indicators(catalog))
        # Genero los indicadores relacionados con fechas, y los agrego
        result.update(self._generate_date_indicators(catalog))
        # Agrego la cuenta de los formatos de las distribuciones
        count = self._count_distribution_formats(catalog)
        result.update({
            'distribuciones_formatos_cant': count
        })
        # Agrego porcentaje de campos recomendados/optativos usados
        fields_count = self._count_required_and_optional_fields(catalog)
        recomendados_pct = 100 * float(fields_count['recomendado']) / \
            fields_count['total_recomendado']
        optativos_pct = 100 * float(fields_count['optativo']) / \
            fields_count['total_optativo']
        result.update({
            'campos_recomendados_pct': round(recomendados_pct, 2),
            'campos_optativos_pct': round(optativos_pct, 2)
        })
        return fields_count, result

    def _generate_status_indicators(self, catalog):
        """Genera indicadores básicos sobre el estado de un catálogo

        Args:
            catalog (dict): diccionario de un data.json parseado

        Returns:
            dict: indicadores básicos sobre el catálogo, tal como la cantidad
            de datasets, distribuciones y número de errores
        """
        summary = self.generate_datasets_summary(catalog)
        cant_ok = 0
        cant_error = 0
        cant_distribuciones = 0
        datasets_total = len(summary)
        for dataset in summary:
            cant_distribuciones += dataset['cant_distribuciones']

            if dataset['estado_metadatos'] == "OK":
                cant_ok += 1
            else:  # == "ERROR"
                cant_error += 1

        datasets_ok_pct = 0
        if datasets_total:
            datasets_ok_pct = round(100 * float(cant_ok) / datasets_total, 2)
        result = {
            'datasets_cant': datasets_total,
            'distribuciones_cant': cant_distribuciones,
            'datasets_meta_ok_cant': cant_ok,
            'datasets_meta_error_cant': cant_error,
            'datasets_meta_ok_pct': datasets_ok_pct
        }
        return result

    def _federation_indicators(self, catalog, central_catalog):
        """Cuenta la cantidad de datasets incluídos tanto en la lista
        'catalogs' como en el catálogo central, y genera indicadores a partir
        de esa información.

        Args:
            catalog (dict): catálogo ya parseado
            central_catalog (str o dict): ruta a catálogo central, o un dict
                con el catálogo ya parseado
        """
        central_catalog = readers.read_catalog(central_catalog)
        federados = 0  # En ambos catálogos
        no_federados = 0
        datasets_federados_eliminados_cant = 0
        datasets_no_federados = []
        datasets_federados_eliminados = []

        # busca c/dataset del catálogo específico a ver si está en el central
        for dataset in catalog.get('dataset', []):
            found = False
            for central_dataset in central_catalog.get('dataset', []):
                if self._datasets_equal(dataset, central_dataset):
                    found = True
                    federados += 1
                    break
            if not found:
                no_federados += 1
                datasets_no_federados.append((dataset.get('title'),
                                              dataset.get('landingPage')))

        # busca c/dataset del central cuyo publisher podría pertenecer al
        # catálogo específico, a ver si está en el catálogo específico
        # si no está, probablemente signifique que fue eliminado
        filtered_central = self._filter_by_likely_publisher(
            central_catalog.get('dataset', []),
            catalog.get('dataset', [])
        )
        for central_dataset in filtered_central:
            found = False
            for dataset in catalog.get('dataset', []):
                if self._datasets_equal(dataset, central_dataset):
                    found = True
                    break
            if not found:
                datasets_federados_eliminados_cant += 1
                datasets_federados_eliminados.append(
                    (central_dataset.get('title'),
                     central_dataset.get('landingPage'))
                )

        if federados or no_federados:  # Evita división por 0
            federados_pct = 100 * float(federados) / (federados + no_federados)
        else:
            federados_pct = 0

        result = {
            'datasets_federados_cant': federados,
            'datasets_no_federados_cant': no_federados,
            'datasets_federados_eliminados_cant': datasets_federados_eliminados_cant,
            'datasets_federados_eliminados': datasets_federados_eliminados,
            'datasets_no_federados': datasets_no_federados,
            'datasets_federados_pct': round(federados_pct, 2)
        }
        return result

    @staticmethod
    def _filter_by_likely_publisher(central_datasets, catalog_datasets):
        publisher_names = [
            catalog_dataset["publisher"]["name"]
            for catalog_dataset in catalog_datasets
            if "name" in catalog_dataset["publisher"]
        ]

        filtered_central_datasets = []
        for central_dataset in central_datasets:
            if "name" in central_dataset["publisher"] and \
                    central_dataset["publisher"]["name"] in publisher_names:
                filtered_central_datasets.append(central_dataset)

        return filtered_central_datasets

    @staticmethod
    def _datasets_equal(dataset, other):
        """Función de igualdad de dos datasets: se consideran iguales si
        los valores de los campos 'title', 'publisher.name',
        'accrualPeriodicity' e 'issued' son iguales en ambos.

        Args:
            dataset (dict): un dataset, generado por la lectura de un catálogo
            other (dict): idem anterior

        Returns:
            bool: True si son iguales, False en caso contrario
        """

        # Campos a comparar. Si es un campo anidado escribirlo como lista
        fields = [
            'title',
            ['publisher', 'name']
        ]

        for field in fields:
            if isinstance(field, list):
                value = helpers.traverse_dict(dataset, field)
                other_value = helpers.traverse_dict(other, field)
            else:
                value = dataset.get(field)
                other_value = other.get(field)

            if value != other_value:
                return False

        return True

    @staticmethod
    def _parse_date_string(date_string):
        """Parsea un string de una fecha con el formato de la norma
        ISO 8601 (es decir, las fechas utilizadas en los catálogos) en un
        objeto datetime de la librería estándar de python. Se tiene en cuenta
        únicamente la fecha y se ignora completamente la hora.

        Args:
            date_string (str): fecha con formato ISO 8601.

        Returns:
            datetime: objeto fecha especificada por date_string.
        """

        if not date_string:
            return None

        # La fecha cumple con la norma ISO 8601: YYYY-mm-ddThh-MM-ss.
        # Nos interesa solo la parte de fecha, y no la hora. Se hace un
        # split por la letra 'T' y nos quedamos con el primer elemento.
        date_string = date_string.split('T')[0]

        # Crea un objeto datetime a partir del formato especificado
        return datetime.strptime(date_string, "%Y-%m-%d")

    @classmethod
    def _days_from_last_update(cls, catalog, date_field="modified"):
        """Calcula días desde la última actualización del catálogo.

        Args:
            catalog (dict): Un catálogo.
            date_field (str): Campo de metadatos a utilizar para considerar
                los días desde la última actualización del catálogo.

        Returns:
            int or None: Cantidad de días desde la última actualización del
                catálogo o None, si no pudo ser calculada.
        """

        # el "date_field" se busca primero a nivel catálogo, luego a nivel
        # de cada dataset, y nos quedamos con el que sea más reciente
        date_modified = catalog.get(date_field, None)
        dias_ultima_actualizacion = None
        # "date_field" a nivel de catálogo puede no ser obligatorio,
        # si no está pasamos
        if isinstance(date_modified, (unicode, str)):
            date = cls._parse_date_string(date_modified)
            dias_ultima_actualizacion = (datetime.now() - date).days

        for dataset in catalog.get('dataset', []):
            date = cls._parse_date_string(dataset.get(date_field, ""))
            days_diff = float((datetime.now() - date).days) if date else None

            # Actualizo el indicador de días de actualización si corresponde
            if not dias_ultima_actualizacion or \
                    (days_diff and days_diff < dias_ultima_actualizacion):
                dias_ultima_actualizacion = days_diff

        if dias_ultima_actualizacion:
            return int(dias_ultima_actualizacion)
        else:
            return None

    def _generate_date_indicators(self, catalog, tolerance=0.2):
        """Genera indicadores relacionados a las fechas de publicación
        y actualización del catálogo pasado por parámetro. La evaluación de si
        un catálogo se encuentra actualizado o no tiene un porcentaje de
        tolerancia hasta que se lo considere como tal, dado por el parámetro
        tolerance.

        Args:
            catalog (dict o str): path de un catálogo en formatos aceptados,
                o un diccionario de python

            tolerance (float): porcentaje de tolerancia hasta que se considere
                un catálogo como desactualizado, por ejemplo un catálogo con
                período de actualización de 10 días se lo considera como
                desactualizado a partir de los 12 con una tolerancia del 20%.
                También acepta valores negativos.

        Returns:
            dict: diccionario con indicadores
        """
        result = {}

        dias_ultima_actualizacion = self._days_from_last_update(
            catalog, "modified")
        if not dias_ultima_actualizacion:
            dias_ultima_actualizacion = self._days_from_last_update(
                catalog, "issued")

        result['catalogo_ultima_actualizacion_dias'] = \
            dias_ultima_actualizacion

        actualizados = 0
        desactualizados = 0
        periodicity_amount = {}

        for dataset in catalog.get('dataset', []):
            # Parseo la fecha de publicación, y la frecuencia de actualización
            periodicity = dataset.get('accrualPeriodicity')
            if not periodicity:
                continue
            # Si la periodicity es eventual, se considera como actualizado
            if periodicity == 'eventual':
                actualizados += 1
                prev_periodicity = periodicity_amount.get(periodicity, 0)
                periodicity_amount[periodicity] = prev_periodicity + 1
                continue

            # dataset sin fecha de última actualización es desactualizado
            if "modified" not in dataset:
                desactualizados += 1
            else:
                # Calculo el período de días que puede pasar sin actualizarse
                # Se parsea el período especificado por accrualPeriodicity,
                # cumple con el estándar ISO 8601 para tiempos con repetición
                date = self._parse_date_string(dataset['modified'])
                days_diff = float((datetime.now() - date).days)
                interval = helpers.parse_repeating_time_interval(
                    periodicity) * \
                    (1 + tolerance)

                if days_diff < interval:
                    actualizados += 1
                else:
                    desactualizados += 1

            prev_periodicity = periodicity_amount.get(periodicity, 0)
            periodicity_amount[periodicity] = prev_periodicity + 1

        datasets_total = len(catalog.get('dataset', []))
        actualizados_pct = 0
        if datasets_total:
            actualizados_pct = float(actualizados) / datasets_total
        result.update({
            'datasets_desactualizados_cant': desactualizados,
            'datasets_actualizados_cant': actualizados,
            'datasets_actualizados_pct': 100 * round(actualizados_pct, 2),
            'datasets_frecuencia_cant': periodicity_amount
        })
        return result

    @staticmethod
    def _count_distribution_formats(catalog):
        """Cuenta los formatos especificados por el campo 'format' de cada
        distribución de un catálogo.

        Args:
            catalog (str o dict): path a un catálogo, o un dict de python que
            contenga a un catálogo ya leído.

        Returns:
            dict: diccionario con los formatos de las distribuciones
            encontradas como claves, con la cantidad de ellos en sus valores.
        """

        # Leo catálogo
        catalog = readers.read_catalog(catalog)
        formats = {}
        for dataset in catalog.get('dataset', []):
            for distribution in dataset['distribution']:
                # 'format' es recomendado, no obligatorio. Puede no estar.
                distribution_format = distribution.get('format', None)

                if distribution_format:
                    # Si no está en el diccionario, devuelvo 0
                    count = formats.get(distribution_format, 0)

                    formats[distribution_format] = count + 1

        return formats

    def _count_required_and_optional_fields(self, catalog):
        """Cuenta los campos obligatorios/recomendados/requeridos usados en
        'catalog', junto con la cantidad máxima de dichos campos.

        Args:
            catalog (str o dict): path a un catálogo, o un dict de python que
                contenga a un catálogo ya leído

        Returns:
            dict: diccionario con las claves 'recomendado', 'optativo',
                'requerido', 'recomendado_total', 'optativo_total',
                'requerido_total', con la cantidad como valores.
        """

        catalog = readers.read_catalog(catalog)

        # Archivo .json con el uso de cada campo. Lo cargamos a un dict
        catalog_fields_path = os.path.join(self.CATALOG_FIELDS_PATH,
                                           'fields.json')
        with open(catalog_fields_path) as f:
            catalog_fields = json.load(f)

        # Armado recursivo del resultado
        return self._count_fields_recursive(catalog, catalog_fields)

    def _count_fields_recursive(self, dataset, fields):
        """Cuenta la información de campos optativos/recomendados/requeridos
        desde 'fields', y cuenta la ocurrencia de los mismos en 'dataset'.

        Args:
            dataset (dict): diccionario con claves a ser verificadas.
            fields (dict): diccionario con los campos a verificar en dataset
                como claves, y 'optativo', 'recomendado', o 'requerido' como
                valores. Puede tener objetios anidados pero no arrays.

        Returns:
            dict: diccionario con las claves 'recomendado', 'optativo',
                'requerido', 'recomendado_total', 'optativo_total',
                'requerido_total', con la cantidad como valores.
        """

        key_count = {
            'recomendado': 0,
            'optativo': 0,
            'requerido': 0,
            'total_optativo': 0,
            'total_recomendado': 0,
            'total_requerido': 0
        }

        for k, v in fields.items():
            # Si la clave es un diccionario se implementa recursivamente el
            # mismo algoritmo
            if isinstance(v, dict):
                # dataset[k] puede ser o un dict o una lista, ej 'dataset' es
                # list, 'publisher' no. Si no es lista, lo metemos en una.
                # Si no es ninguno de los dos, dataset[k] es inválido
                # y se pasa un diccionario vacío para poder comparar
                elements = dataset.get(k)
                if not isinstance(elements, (list, dict)):
                    elements = [{}]

                if isinstance(elements, dict):
                    elements = [dataset[k].copy()]
                for element in elements:
                    # Llamada recursiva y suma del resultado al nuestro
                    result = self._count_fields_recursive(element, v)
                    for key in result:
                        key_count[key] += result[key]
            # Es un elemento normal (no iterable), se verifica si está en
            # dataset o no. Se suma 1 siempre al total de su tipo
            else:
                # total_requerido, total_recomendado, o total_optativo
                key_count['total_' + v] += 1

                if k in dataset:
                    key_count[v] += 1

        return key_count

    def dataset_is_updated(self, catalog, dataset):
        catalog = readers.read_catalog(catalog)

        for catalog_dataset in catalog.get('dataset', []):
            if catalog_dataset.get('title') == dataset:
                periodicity = catalog_dataset.get('accrualPeriodicity')
                if not periodicity:
                    return False

                if periodicity == 'eventual':
                    return True

                if "modified" not in catalog_dataset:
                    return False

                date = self._parse_date_string(catalog_dataset['modified'])
                days_diff = float((datetime.now() - date).days)
                interval = helpers.parse_repeating_time_interval(periodicity)

                if days_diff < interval:
                    return True
                return False

        return False


def main():
    """Permite ejecutar el módulo por línea de comandos.

    Valida un path o url a un archivo data.json devolviendo True/False si es
    válido y luego el resultado completo.

    Example:
        python pydatajson.py http://181.209.63.71/data.json
        python pydatajson.py ~/github/pydatajson/tests/samples/full_data.json
    """
    try:
        datajson_file = sys.argv[1]
        dj_instance = DataJson()
        bool_res = dj_instance.is_valid_catalog(datajson_file)
        full_res = dj_instance.validate_catalog(datajson_file)
        pretty_full_res = json.dumps(
            full_res, indent=4, separators=(",", ": "))
        print(bool_res)
        print(pretty_full_res)
    except IndexError as errmsg:
        format_str = """
{}: pydatajson.py fue ejecutado como script sin proveer un argumento
"""
        print(format_str.format(errmsg))


if __name__ == '__main__':
    main()
