#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo principal de pydatajson

Contiene la clase DataJson que reúne los métodos públicos para trabajar con
archivos data.json.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import json
import os.path
import sys
import logging
from collections import OrderedDict
from datetime import datetime

from openpyxl.styles import Alignment, Font
from six import string_types, iteritems
from six.moves.urllib_parse import urljoin

from pydatajson.response_formatters import format_response
from pydatajson.validation import Validator, \
    DEFAULT_CATALOG_SCHEMA_FILENAME, ABSOLUTE_SCHEMA_DIR
from . import documentation, constants
from . import helpers
from . import indicators
from . import readers
from . import search
from . import time_series
from . import writers
from . import federation
from . import transformation
from . import backup
from . import catalog_readme

logger = logging.getLogger('pydatajson')

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CENTRAL_CATALOG = "http://datos.gob.ar/data.json"
MIN_DATASET_TITLE = 10
MIN_DATASET_DESCRIPTION = 20


class DataJson(dict):
    """Objeto que representa un catálogo de activos de datos."""

    # Variables por default
    CATALOG_FIELDS_PATH = os.path.join(ABSOLUTE_PROJECT_DIR, "fields")

    def __init__(self, catalog=None, schema_filename=None, schema_dir=None,
                 default_values=None, catalog_format=None,
                 validator_class=Validator, verify_ssl=False,
                 requests_timeout=constants.REQUESTS_TIMEOUT):
        """Lee un catálogo y crea un objeto con funciones para manipularlo.

        Salvo que se indique lo contrario, se utiliza como default el schema
        de la versión 1.1 del Perfil de Metadatos de Argentina.

        Args:
            catalog (dict or str): Representación externa/interna de un
                catálogo. Una representación _externa_ es un path local o una
                URL remota a un archivo con la metadata de un catálogo, en
                formato JSON o XLSX. La representación _interna_ de un catálogo
                es un diccionario. Ejemplos: http://datos.gob.ar/data.json,
                http://www.ign.gob.ar/descargas/geodatos/catalog.xlsx,
                "/energia/catalog.xlsx".
            schema_filename (str): Nombre del archivo que contiene el esquema
                validador.
            schema_dir (str): Directorio (absoluto) donde se encuentra el
                esquema validador (y sus referencias, de tenerlas).
            default_values (dict): Valores default para algunos de los campos
                del catálogo::
                    {
                        "dataset_issued": "2017-06-22",
                        "distribution_issued": "2017-06-22"
                    }
        """
        self.verify_ssl = verify_ssl
        self.requests_timeout = requests_timeout
        # se construye el objeto DataJson con la interfaz de un dicconario
        if catalog:

            # lee representaciones de un catálogo hacia un diccionario
            catalog = readers.read_catalog(catalog,
                                           default_values=default_values,
                                           catalog_format=catalog_format,
                                           verify=self.verify_ssl,
                                           timeout=self.requests_timeout)

            # copia todos los atributos del diccionario hacia el objeto
            for key, value in iteritems(catalog):
                self[key] = value

            self.has_catalog = True

            # indexa los ids de datasets, distribuciones y fields
            self._build_index()

        else:
            self.has_catalog = False
        schema_filename = schema_filename or DEFAULT_CATALOG_SCHEMA_FILENAME
        schema_dir = schema_dir or ABSOLUTE_SCHEMA_DIR

        self.validator = validator_class(schema_filename, schema_dir)

        # asigno docstrings de los métodos modularizados
        fn_doc = indicators.generate_catalogs_indicators.__doc__
        self.generate_catalogs_indicators.__func__.__doc__ = fn_doc

    # metodos para buscar entidades cuando DataJson tiene catalogo cargado
    get_themes = search.get_themes
    themes = property(get_themes)
    get_datasets = search.get_datasets
    datasets = property(get_datasets)
    get_distributions = search.get_distributions
    distributions = property(get_distributions)
    get_fields = search.get_fields
    fields = property(get_fields)
    get_time_series = search.get_time_series
    time_series = property(get_time_series)
    get_dataset = search.get_dataset
    get_distribution = search.get_distribution
    get_field = search.get_field
    get_theme = search.get_theme
    get_field_location = search.get_field_location
    get_catalog_metadata = search.get_catalog_metadata

    # metodos para realizar operaciones de transformación de metadatos
    generate_distribution_ids = transformation.generate_distribution_ids

    # metodos para guardar el catálogo en otros formatos
    to_xlsx = writers.write_xlsx_catalog
    to_json = writers.write_json_catalog

    # metodos para generar indicadores
    generate_indicators = indicators.generate_indicators

    # metodos para hacer backups
    make_catalog_backup = backup.make_catalog_backup

    # metodos para interactuar con un portal de CKAN
    push_dataset_to_ckan = federation.push_dataset_to_ckan
    harvest_dataset_to_ckan = federation.harvest_dataset_to_ckan
    restore_dataset_to_ckan = federation.restore_dataset_to_ckan
    harvest_catalog_to_ckan = federation.harvest_catalog_to_ckan
    restore_catalog_to_ckan = federation.restore_catalog_to_ckan
    push_theme_to_ckan = federation.push_theme_to_ckan
    push_new_themes = federation.push_new_themes
    remove_harvested_ds_from_ckan = federation.remove_harvested_ds_from_ckan

    # metodos de README
    generate_catalog_readme = catalog_readme.generate_catalog_readme

    def _build_index(self):
        """Itera todos los datasets, distribucioens y fields indexandolos."""

        datasets_index = {}
        distributions_index = {}
        fields_index = {}

        # recorre todos los datasets
        for dataset_index, dataset in enumerate(self.datasets):
            if "identifier" in dataset:
                datasets_index[dataset["identifier"]] = {
                    "dataset_index": dataset_index
                }
                # recorre las distribuciones del dataset
                for distribution_index, distribution in enumerate(
                        dataset.get("distribution", [])):
                    if "identifier" in distribution:
                        distributions_index[distribution["identifier"]] = {
                            "distribution_index": distribution_index,
                            "dataset_identifier": dataset["identifier"]
                        }
                        # recorre los fields de la distribucion
                        for field_index, field in enumerate(
                                distribution.get("field", [])):
                            if "id" in field:
                                fields_index[field["id"]] = {
                                    "field_index":
                                        field_index,
                                    "dataset_identifier":
                                        dataset["identifier"],
                                    "distribution_identifier":
                                        distribution["identifier"]
                                }

        setattr(self, "_distributions_index", distributions_index)
        setattr(self, "_datasets_index", datasets_index)
        setattr(self, "_fields_index", fields_index)

    def get_distribution_time_index(self, distribution):
        if isinstance(distribution, dict):
            distribution = distribution
        else:
            distribution = self.get_distribution(distribution)

        return time_series.get_distribution_time_index(distribution)

    def get_distribution_time_index_frequency(self, distribution):
        if isinstance(distribution, dict):
            distribution = distribution
        else:
            distribution = self.get_distribution(distribution)

        return time_series.get_distribution_time_index_frequency(distribution)

    def remove_dataset(self, identifier):
        for index, dataset in enumerate(self["dataset"]):
            if dataset["identifier"] == identifier:
                self["dataset"].pop(index)
                logger.info("Dataset {} en posicion {} fue eliminado.".format(
                    identifier, index))
                return

        logger.warning("No se encontro el dataset {}.".format(identifier))

    def remove_distribution(self, identifier, dataset_identifier=None):
        for dataset in self["dataset"]:
            for index, distribution in enumerate(dataset["distribution"]):
                if (distribution["identifier"] == identifier and
                        (not dataset_identifier or
                         dataset["identifier"] == dataset_identifier)):
                    dataset["distribution"].pop(index)
                    logger.info("Distribution {} del dataset {}"
                                "en posicion {} fue eliminada.".format(
                                    identifier, dataset["identifier"], index))
                    return

        logger.warning("No se encontro la distribucion {}.".format(identifier))

    def is_valid_catalog(self, catalog=None):
        """Valida que un archivo `data.json` cumpla con el schema definido.

        Chequea que el data.json tiene todos los campos obligatorios y que
        tanto los campos obligatorios como los opcionales siguen la estructura
        definida en el schema.

        Args:
            catalog (str o dict): Catálogo (dict, JSON o XLSX) a ser validado.
                Si no se pasa, valida este catálogo.

        Returns:
            bool: True si el data.json cumple con el schema, sino False.
        """
        catalog = self._read_catalog(catalog) if catalog else self
        return self.validator.is_valid(catalog)

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

    def validate_catalog(self, catalog=None, only_errors=False, fmt="dict",
                         export_path=None):
        """Analiza un data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        tanto los campos obligatorios como los opcionales siguen la estructura
        definida en el schema.

        Args:
            catalog (str o dict): Catálogo (dict, JSON o XLSX) a ser validado.
                Si no se pasa, valida este catálogo.
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
        catalog = self._read_catalog(catalog) if catalog else self

        validation = self.validator.validate_catalog(catalog, only_errors)
        if export_path:
            fmt = 'table'

        return format_response(validation, export_path, fmt)

    @staticmethod
    def _stringify_list(str_or_list):

        if isinstance(str_or_list, list):
            strings = [s for s in str_or_list
                       if isinstance(s, string_types)]
            stringified_list = ", ".join(strings)
        elif isinstance(str_or_list, string_types):
            stringified_list = str_or_list
        else:
            stringified_list = None

        return stringified_list

    @classmethod
    def _dataset_report_helper(cls, dataset, catalog_homepage=None):
        """Toma un dict con la metadata de un dataset, y devuelve un dict coni
        los valores que dataset_report() usa para reportar sobre él.

        Args:
            dataset (dict): Diccionario con la metadata de un dataset.

        Returns:
            dict: Diccionario con los campos a nivel dataset que requiere
            dataset_report().
        """
        publisher_name = helpers.traverse_dict(dataset, ["publisher", "name"])

        languages = cls._stringify_list(dataset.get("language"))
        super_themes = cls._stringify_list(dataset.get("superTheme"))
        themes = cls._stringify_list(dataset.get("theme"))

        def _stringify_distribution(distribution):
            title = distribution.get("title")
            url = distribution.get("downloadURL")

            return "\"{}\": {}".format(title, url)

        distributions = [d for d in dataset["distribution"]
                         if isinstance(d, dict)]

        # crea lista de distribuciones
        distributions_list = None
        if isinstance(distributions, list):
            distributions_strings = [
                _stringify_distribution(d) for d in distributions
            ]
            distributions_list = "\n\n".join(distributions_strings)

        # crea lista de formatos
        distributions_formats = json.dumps(
            helpers.count_distribution_formats_dataset(dataset))

        fields = OrderedDict()
        fields["dataset_identifier"] = dataset.get("identifier")
        fields["dataset_title"] = dataset.get("title")
        fields["dataset_accrualPeriodicity"] = dataset.get(
            "accrualPeriodicity")
        fields["dataset_description"] = dataset.get("description")
        fields["dataset_publisher_name"] = publisher_name
        fields["dataset_superTheme"] = super_themes
        fields["dataset_theme"] = themes
        fields["dataset_landingPage"] = dataset.get("landingPage")
        fields["dataset_landingPage_generated"] = cls._generate_landingPage(
            catalog_homepage, dataset.get("identifier")
        )
        fields["dataset_issued"] = dataset.get("issued")
        fields["dataset_modified"] = dataset.get("modified")
        fields["distributions_formats"] = distributions_formats
        fields["distributions_list"] = distributions_list
        fields["dataset_license"] = dataset.get("license")
        fields["dataset_language"] = languages
        fields["dataset_spatial"] = dataset.get("spatial")
        fields["dataset_temporal"] = dataset.get("temporal")

        return fields

    @classmethod
    def _generate_landingPage(cls, catalog_homepage, dataset_identifier):
        return urljoin(catalog_homepage,
                       "dataset/{}".format(dataset_identifier))

    @staticmethod
    def _catalog_report_helper(catalog, catalog_validation, url, catalog_id,
                               catalog_org):
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
        fields["catalog_federation_id"] = catalog_id
        fields["catalog_federation_org"] = catalog_org
        fields["catalog_title"] = catalog.get("title")
        fields["catalog_description"] = catalog.get("description")
        fields["valid_catalog_metadata"] = (
            1 if catalog_validation["status"] == "OK" else 0)

        return fields

    def _dataset_report(
            self, dataset, dataset_validation, dataset_index,
            catalog_fields, harvest='none', report=None, catalog_homepage=None
    ):
        """ Genera una línea del `catalog_report`, correspondiente a un dataset
        de los que conforman el catálogo analizado."""

        # hace un breve análisis de qa al dataset
        good_qa, notes = self._dataset_qa(dataset)

        dataset_report = OrderedDict(catalog_fields)
        dataset_report["valid_dataset_metadata"] = (
            1 if dataset_validation["status"] == "OK" else 0)
        dataset_report["dataset_index"] = dataset_index

        if isinstance(harvest, list):
            dataset_report["harvest"] = 1 if dataset["title"] in harvest else 0
        elif harvest == 'all':
            dataset_report["harvest"] = 1
        elif harvest == 'none':
            dataset_report["harvest"] = 0
        elif harvest == 'valid':
            dataset_report["harvest"] = (
                int(dataset_report["valid_dataset_metadata"]))
        elif harvest == 'good':
            valid_metadata = int(dataset_report["valid_dataset_metadata"]) == 1
            dataset_report["harvest"] = 1 if valid_metadata and good_qa else 0

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

        dataset_report.update(
            self._dataset_report_helper(
                dataset, catalog_homepage=catalog_homepage)
        )

        dataset_report["notas"] = "\n\n".join(notes)

        return dataset_report.copy()

    def _dataset_qa(self, dataset):
        """Chequea si el dataset tiene una calidad mínima para cosechar."""

        # 1. VALIDACIONES
        # chequea que haya por lo menos algún formato de datos reconocido
        has_data_format = helpers.dataset_has_data_distributions(dataset)

        # chequea que algunos campos tengan longitudes mínimas
        has_title = "title" in dataset
        has_description = "description" in dataset
        if has_title:
            has_min_title = len(dataset["title"]) >= MIN_DATASET_TITLE
        else:
            has_min_title = False
        if has_description:
            has_min_desc = len(
                dataset["description"]) >= MIN_DATASET_DESCRIPTION
        else:
            has_min_desc = False

        # 2. EVALUACION DE COSECHA: evalua si se cosecha o no el dataset
        harvest = (has_title and has_description and
                   has_data_format and has_min_title and has_min_desc)

        # 3. NOTAS: genera notas de validación
        notes = []
        if not has_data_format:
            notes.append("No tiene distribuciones con datos.")
        if not has_title:
            notes.append("Dataset sin titulo {}".format(dataset))
        else:
            if not has_min_title:
                notes.append("Titulo tiene menos de {} caracteres".format(
                    MIN_DATASET_TITLE))
        if not has_description:
            notes.append("Dataset sin descripcion {}".format(dataset))
        else:
            if not has_min_desc:
                notes.append("Descripcion tiene menos de {} caracteres".format(
                    MIN_DATASET_DESCRIPTION))

        return harvest, notes

    def catalog_report(self, catalog, harvest='none', report=None,
                       catalog_id=None, catalog_homepage=None,
                       catalog_org=None):
        """Genera un reporte sobre los datasets de un único catálogo.

        Args:
            catalog (dict, str o unicode): Representación externa (path/URL) o
                interna (dict) de un catálogo.
            harvest (str): Criterio de cosecha ('all', 'none',
                'valid', 'report' o 'good').

        Returns:
            list: Lista de diccionarios, con un elemento por cada dataset
                presente en `catalog`.
        """

        url = catalog if isinstance(catalog, string_types) else None
        catalog = self._read_catalog(catalog)

        validation = self.validate_catalog(catalog)
        catalog_validation = validation["error"]["catalog"]
        datasets_validations = validation["error"]["dataset"]

        catalog_fields = self._catalog_report_helper(
            catalog, catalog_validation, url, catalog_id, catalog_org
        )

        if "dataset" in catalog and isinstance(catalog["dataset"], list):
            datasets = [d if isinstance(d, dict) else {} for d in
                        catalog["dataset"]]
        else:
            datasets = []

        catalog_report = [
            self._dataset_report(
                dataset, datasets_validations[index], index,
                catalog_fields, harvest, report=report,
                catalog_homepage=catalog_homepage
            )
            for index, dataset in enumerate(datasets)
        ]

        return catalog_report

    def generate_datasets_report(
            self, catalogs, harvest='valid', report=None,
            export_path=None, catalog_ids=None, catalog_homepages=None,
            catalog_orgs=None
    ):
        """Genera un reporte sobre las condiciones de la metadata de los
        datasets contenidos en uno o varios catálogos.

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) catálogos.
            harvest (str): Criterio a utilizar para determinar el valor del
                campo "harvest" en el reporte generado ('all', 'none',
                'valid', 'report' o 'good').
            report (str): Path a un reporte/config especificando qué
                datasets marcar con harvest=1 (sólo si harvest=='report').
            export_path (str): Path donde exportar el reporte generado (en
                formato XLSX o CSV). Si se especifica, el método no devolverá
                nada.
            catalog_id (str): Nombre identificador del catálogo para federación
            catalog_homepage (str): URL del portal de datos donde está
                implementado el catálogo. Sólo se pasa si el portal es un CKAN
                o respeta la estructura:
                    https://datos.{organismo}.gob.ar/dataset/{dataset_identifier}

        Returns:
            list: Contiene tantos dicts como datasets estén presentes en
                `catalogs`, con la data del reporte generado.
        """
        assert isinstance(catalogs, string_types + (dict, list))
        if isinstance(catalogs, list):
            assert not catalog_ids or len(catalogs) == len(catalog_ids)
            assert not catalog_orgs or len(catalogs) == len(catalog_orgs)
            assert not catalog_homepages or len(
                catalogs) == len(catalog_homepages)

        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, string_types + (dict,)):
            catalogs = [catalogs]

        # convierto los catalogos a objetos DataJson
        catalogs = list(map(readers.read_catalog_obj, catalogs))

        if not catalog_ids:
            catalog_ids = []
            for catalog in catalogs:
                catalog_ids.append(catalog.get("identifier", ""))
        if isinstance(catalog_ids, string_types + (dict,)):
            catalog_ids = [catalog_ids] * len(catalogs)
        if not catalog_orgs or \
                isinstance(catalog_orgs, string_types + (dict,)):
            catalog_orgs = [catalog_orgs] * len(catalogs)
        if not catalog_homepages or isinstance(catalog_homepages,
                                               string_types + (dict,)):
            catalog_homepages = [catalog_homepages] * len(catalogs)

        catalogs_reports = [
            self.catalog_report(
                catalog, harvest, report, catalog_id=catalog_id,
                catalog_homepage=catalog_homepage, catalog_org=catalog_org
            )
            for catalog, catalog_id, catalog_org, catalog_homepage in
            zip(catalogs, catalog_ids, catalog_orgs, catalog_homepages)
        ]

        full_report = []
        for report in catalogs_reports:
            full_report.extend(report)

        if export_path:
            # config styles para reportes en excel
            alignment = Alignment(
                wrap_text=True,
                shrink_to_fit=True,
                vertical="center"
            )
            column_styles = {
                "dataset_title": {"width": 35},
                "dataset_description": {"width": 35},
                "dataset_publisher_name": {"width": 35},
                "dataset_issued": {"width": 20},
                "dataset_modified": {"width": 20},
                "distributions_formats": {"width": 15},
                "distributions_list": {"width": 90},
                "notas": {"width": 50},
            }
            cell_styles = [
                {"alignment": Alignment(vertical="center")},
                {"row": 1, "font": Font(bold=True)},
                {"col": "dataset_title", "alignment": alignment},
                {"col": "dataset_description", "alignment": alignment},
                {"col": "dataset_publisher_name", "alignment": alignment},
                {"col": "distributions_formats", "alignment": alignment},
                {"col": "distributions_list", "alignment": alignment},
                {"col": "notas", "alignment": alignment},
            ]

            # crea tabla
            writers.write_table(table=full_report, path=export_path,
                                column_styles=column_styles,
                                cell_styles=cell_styles)
        else:
            return full_report

    def generate_harvester_config(self, catalogs=None, harvest='valid',
                                  report=None, export_path=None):
        """Genera un archivo de configuración del harvester a partir de un
        reporte, o de un conjunto de catálogos y un criterio de cosecha
        (`harvest`).

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) catálogos.
            harvest (str): Criterio para determinar qué datasets incluir en el
                archivo de configuración generado  ('all', 'none',
                'valid', 'report' o 'good').
            report (list o str): Tabla de reporte generada por
                generate_datasets_report() como lista de diccionarios o archivo
                en formato XLSX o CSV. Sólo se usa cuando `harvest=='report'`,
                en cuyo caso `catalogs` se ignora.
            export_path (str): Path donde exportar el reporte generado (en
                formato XLSX o CSV). Si se especifica, el método no devolverá
                nada.

        Returns:
            list of dicts: Un diccionario con variables de configuración
                por cada dataset a cosechar.
        """

        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, string_types + (dict,)):
            catalogs = [catalogs]

        if harvest == 'report':
            if not report:
                raise ValueError("""
Usted eligio 'report' como criterio de harvest, pero no proveyo un valor para
el argumento 'report'. Por favor, intentelo nuevamente.""")
            datasets_report = readers.read_table(report)
        elif harvest in ['valid', 'none', 'all']:
            # catalogs no puede faltar para estos criterios
            assert isinstance(catalogs, string_types + (dict, list))
            datasets_report = self.generate_datasets_report(catalogs, harvest)
        else:
            raise ValueError("""
{} no es un criterio de harvest reconocido. Pruebe con 'all', 'none', 'valid' o
'report'.""".format(harvest))

        # define los campos del reporte que mantiene para el config file
        config_keys = [
            "catalog_federation_id", "catalog_federation_org",
            "dataset_identifier"
        ]
        # cambia algunos nombres de estos campos para el config file
        config_translator = {
            "catalog_federation_id": "catalog_id",
            "catalog_federation_org": "dataset_organization"
        }
        translated_keys = [config_translator.get(k, k) for k in config_keys]

        harvester_config = [
            OrderedDict(
                # Retengo únicamente los campos que necesita el harvester
                [(config_translator.get(k, k), v)
                 for (k, v) in dataset.items() if k in config_keys]
            )
            # Para aquellost datasets marcados con 'harvest'==1
            for dataset in datasets_report if bool(int(dataset["harvest"]))
        ]

        # chequea que el archivo de configuración tiene todos los campos
        required_keys = set(translated_keys)
        for row in harvester_config:
            row_keys = set(row.keys())
            msg = "Hay una fila con claves {} y debe tener claves {}".format(
                row_keys, required_keys)
            assert row_keys == required_keys, msg

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
        assert isinstance(catalogs, string_types + (dict, list))
        # Si se pasa un único catálogo, genero una lista que lo contenga
        if isinstance(catalogs, string_types + (dict,)):
            catalogs = [catalogs]

        harvestable_catalogs = [self._read_catalog(c) for c in catalogs]
        catalogs_urls = [catalog if isinstance(catalog, string_types)
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
        catalog = self._read_catalog(catalog)

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
        assert isinstance(report, string_types + (list,))

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

    def generate_catalogs_indicators(self, catalogs=None,
                                     central_catalog=None,
                                     identifier_search=False):
        catalogs = catalogs or self
        return indicators.generate_catalogs_indicators(
            catalogs, central_catalog, identifier_search=identifier_search,
            validator=self.validator)

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
        catalog = self._read_catalog(catalog)

        for catalog_dataset in catalog.get('dataset', []):
            if catalog_dataset.get('title') == dataset:
                periodicity = catalog_dataset.get('accrualPeriodicity')
                if not periodicity:
                    return False

                if periodicity == 'eventual':
                    return True

                if "modified" not in catalog_dataset:
                    return False

                date = helpers.parse_date_string(catalog_dataset['modified'])
                days_diff = float((datetime.now() - date).days)
                interval = helpers.parse_repeating_time_interval(periodicity)

                if days_diff < interval:
                    return True
                return False

        return False

    def generate_dataset_documentation(self, dataset_identifier,
                                       export_path=None, catalog=None):
        """Genera texto en markdown a partir de los metadatos de una `dataset`.

        Args:
            dataset_identifier (str): Identificador único de un dataset.
            export_path (str): Path donde exportar el texto generado. Si se
                especifica, el método no devolverá nada.
            catalog (dict, str o unicode): Representación externa (path/URL) o
                interna (dict) de un catálogo. Si no se especifica se usa el
                catálogo cargado en `self` (el propio objeto DataJson).

        Returns:
            str: Texto que describe una `dataset`.
        """

        catalog = DataJson(catalog) or self
        dataset = catalog.get_dataset(dataset_identifier)
        text = documentation.dataset_to_markdown(dataset)

        if export_path:
            with open(export_path, "wb") as f:
                f.write(text.encode("utf-8"))
        else:
            return text

    def make_catalogs_backup(self, catalogs=None,
                             local_catalogs_dir=".",
                             copy_metadata=True, copy_data=True):
        """Realiza copia de los datos y metadatos de uno o más catálogos.

        Args:
            catalogs (list or dict): Lista de catálogos (elementos que pueden
                ser interpretados por DataJson como catálogos) o diccionario
                donde las keys se interpretan como los catalog_identifier:
                {
                "modernizacion":
                "http://infra.datos.gob.ar/catalog/modernizacion/data.json"
                }
                Cuando es una lista, los ids se toman de catalog_identifer, y
                se ignoran los catálogos que no tengan catalog_identifier.
                Cuando se pasa un diccionario, los keys reemplazan a los
                catalog_identifier (estos no se leeen).
            local_catalogs_dir (str): Directorio local en el cual se va a crear
                la carpeta "catalog/..." con todos los catálogos.
            copy_metadata (bool): Si es verdadero, se generan los archivos
                data.json y catalog.xlsx.
            copy_data (bool): Si es verdadero, se descargan todas las
                distribuciones de todos los catálogos.

        Return:
            None
        """

        # TODO: implementar función
        pass

    def _read_catalog(self, catalog):
        return readers.read_catalog(catalog,
                                    verify=self.verify_ssl,
                                    timeout=self.requests_timeout)


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
        logger.info(bool_res)
        logger.info(pretty_full_res)
    except IndexError as errmsg:
        format_str = """
{}: pydatajson.py fue ejecutado como script sin proveer un argumento
"""
        logger.error(format_str.format(errmsg))


if __name__ == '__main__':
    main()
