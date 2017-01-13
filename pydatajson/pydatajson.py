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
from urlparse import urlparse
import warnings
import json
from collections import OrderedDict
import jsonschema
import requests
import unicodecsv as csv
import openpyxl as pyxl
import xlsx_to_json

ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def read_catalog(catalog):
    """Toma una representación cualquiera de un catálogo, y devuelve su
    representación interna (un diccionario de Python con su metadata.)

    Si recibe una representación _interna_ (un diccionario), lo devuelve
    intacto. Si recibe una representación _externa_ (path/URL a un archivo
    JSON/XLSX), devuelve su represetación interna, es decir, un diccionario.

    Args:
        catalog (dict or str): Representación externa/interna de un catálogo.
        Una representación _externa_ es un path local o una URL remota a un
        archivo con la metadata de un catálogo, en formato JSON o XLSX. La
        representación _interna_ de un catálogo es un diccionario.

    Returns:
        dict: Representación interna de un catálogo para uso en las funciones
        de esta librería.
    """
    unknown_catalog_repr_msg = """
No se pudo inferir una representación válida de un catálogo del parámetro
provisto: {}.""".format(catalog)
    assert isinstance(catalog, (dict, str, unicode)), unknown_catalog_repr_msg

    if isinstance(catalog, dict):
        catalog_dict = catalog
    else:
        # catalog es una URL remota o un path local
        suffix = catalog.split(".")[-1]
        unknown_suffix_msg = """
{} no es un sufijo conocido. Pruebe con 'json' o  'xlsx'""".format(suffix)
        assert suffix in ["json", "xlsx"], unknown_suffix_msg

        if suffix == "json":
            catalog_dict = read_json(catalog)
        else:
            # El archivo está en formato XLSX
            catalog_dict = read_xlsx_catalog(catalog)

    # Es 'pitonica' esta forma de retornar un valor? O debería ir retornando
    # los valores intermedios?
    return catalog_dict


def read_json(json_path_or_url):
    """Toma el path a un JSON y devuelve el diccionario que representa.

    Se asume que el parámetro es una URL si comienza con 'http' o 'https', o
    un path local de lo contrario.

    Args:
        json_path_or_url (str): Path local o URL remota a un archivo de texto
            plano en formato JSON.

    Returns:
        dict: El diccionario que resulta de deserializar json_path_or_url.

    """
    assert isinstance(json_path_or_url, (str, unicode))

    parsed_url = urlparse(json_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(json_path_or_url)
        json_dict = json.loads(res.content, encoding='utf-8')

    else:
        # Si json_path_or_url parece ser una URL remota, lo advierto.
        path_start = parsed_url.path.split(".")[0]
        if path_start == "www" or path_start.isdigit():
            warnings.warn("""
La dirección del archivo JSON ingresada parece una URL, pero no comienza
con 'http' o 'https' así que será tratada como una dirección local. ¿Tal vez
quiso decir 'http://{}'?""".format(json_path_or_url).encode("utf-8"))

        with io.open(json_path_or_url, encoding='utf-8') as json_file:
            json_dict = json.load(json_file)

    return json_dict


def read_xlsx_catalog(xlsx_path_or_url):
    """Toma el path a un catálogo en formato XLSX y devuelve el diccionario
    que representa.

    Se asume que el parámetro es una URL si comienza con 'http' o 'https', o
    un path local de lo contrario.

    Args:
        xlsx_path_or_url (str): Path local o URL remota a un libro XLSX de
            formato específico para guardar los metadatos de un catálogo.

    Returns:
        dict: El diccionario que resulta de procesar xlsx_path_or_url.

    """
    assert isinstance(xlsx_path_or_url, (str, unicode))

    parsed_url = urlparse(xlsx_path_or_url)
    if parsed_url.scheme in ["http", "https"]:
        res = requests.get(xlsx_path_or_url)
        tmpfilename = ".tmpfile.xlsx"
        with open(tmpfilename, 'wb') as tmpfile:
            tmpfile.write(res.content)
        catalog_dict = xlsx_to_json.read_local_xlsx_catalog(tmpfilename)
        os.remove(tmpfilename)
    else:
        # Si xlsx_path_or_url parece ser una URL remota, lo advierto.
        path_start = parsed_url.path.split(".")[0]
        if path_start == "www" or path_start.isdigit():
            warnings.warn("""
La dirección del archivo JSON ingresada parece una URL, pero no comienza
con 'http' o 'https' así que será tratada como una dirección local. ¿Tal vez
quiso decir 'http://{}'?
            """.format(xlsx_path_or_url).encode("utf8"))

        catalog_dict = xlsx_to_json.read_local_xlsx_catalog(xlsx_path_or_url)

    return catalog_dict


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
        schema = read_json(schema_path)

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

    @staticmethod
    def _traverse_dict(dicc, keys, default_value=None):
        """Recorre un diccionario siguiendo una lista de claves, y devuelve
        default_value en caso de que alguna de ellas no exista.

        Args:
            dicc (dict): Diccionario a ser recorrido.
            keys (list): Lista de claves a ser recorrida. Puede contener
                índices de listas y claves de diccionarios mezcladas.
            default_value: Valor devuelto en caso de que `dicc` no se pueda
                recorrer siguiendo secuencialmente la lista de `keys` hasta
                el final.

        Returns:
            object: El valor obtenido siguiendo la lista de `keys` dentro de
            `dicc`.
        """
        for key in keys:
            if isinstance(dicc, dict) and key in dicc:
                dicc = dicc[key]
            elif isinstance(dicc, list):
                dicc = dicc[key]
            else:
                return default_value

        return dicc

    def is_valid_catalog(self, datajson_path):
        """Valida que un archivo `data.json` cumpla con el schema definido.

        Chequea que el data.json tiene todos los campos obligatorios y que
        tanto los campos obligatorios como los opcionales siguen la estructura
        definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

        Returns:
            bool: True si el data.json cumple con el schema, sino False.
        """
        datajson = read_catalog(datajson_path)
        res = self.validator.is_valid(datajson)
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

    def validate_catalog(self, datajson_path):
        """Analiza un data.json registrando los errores que encuentra.

        Chequea que el data.json tiene todos los campos obligatorios y que
        tanto los campos obligatorios como los opcionales siguen la estructura
        definida en el schema.

        Args:
            datajson_path (str): Path al archivo data.json a ser validado.

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
        datajson = read_catalog(datajson_path)

        # La respuesta por default se devuelve si no hay errores
        default_response = {
            "status": "OK",
            "error": {
                "catalog": {
                    "status": "OK",
                    "title": datajson.get("title"),
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
                    } for dataset in datajson["dataset"]
                ] if ("dataset" in datajson and
                      isinstance(datajson["dataset"], list)) else None
            }
        }

        # Genero la lista de errores en la instancia a validar
        errors_iterator = self.validator.iter_errors(datajson)

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
        publisher_name = cls._traverse_dict(dataset, ["publisher", "name"])

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
        catalog = read_catalog(catalog)

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
            self._write(table=full_report, path=export_path)
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
                'valid' o 'report').
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
        if isinstance(catalogs, (str, unicode, dict)):
            catalogs = [catalogs]

        if harvest == 'report':
            if not report:
                raise ValueError("""
Usted eligio 'report' como criterio de harvest, pero no proveyo un valor para
el argumento 'report'. Por favor, intentelo nuevamente.""")
            datasets_report = self._read(report)
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

        if export_path:
            self._write(harvester_config, export_path)
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

        harvestable_catalogs = [read_catalog(c) for c in catalogs]
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
                file_str = json.dumps(catalog, ensure_ascii=False, indent=4,
                                      separators=(",", ": "), encoding="utf-8")
                with io.open(filename, 'w', encoding="utf-8") as target:
                    target.write(file_str)
        elif export_path:
            # Creo un único JSON con todos los catálogos
            file_str = json.dumps(harvestable_catalogs, ensure_ascii=False,
                                  indent=4, separators=(",", ": "),
                                  encoding="utf-8")
            with io.open(export_path, 'w', encoding="utf-8") as target:
                target.write(file_str)
        else:
            return harvestable_catalogs

    @staticmethod
    def _is_list_of_matching_dicts(list_of_dicts):
        """Comprueba que una lista esté compuesta únicamente por diccionarios,
        que comparten exactamente las mismas claves."""
        elements = (isinstance(d, dict) and d.keys() == list_of_dicts[0].keys()
                    for d in list_of_dicts)
        return all(elements)

    @classmethod
    def _read(cls, path):
        """Lee un archivo tabular (CSV o XLSX) a una lista de diccionarios.

        La extensión del archivo debe ser ".csv" o ".xlsx". En función de
        ella se decidirá el método a usar para leerlo.

        Si recibe una lista, comprueba que todos sus diccionarios tengan las
        mismas claves y de ser así, la devuelve intacta. Levanta una Excepción
        en caso contrario.

        Args:
            path(str o list): Como 'str', path a un archivo CSV o XLSX.

        Returns:
            list: Lista de diccionarios con claves idénticas representando el
            archivo original.
        """
        assert isinstance(path, (str, unicode, list)), """
{} no es un `path` valido""".format(path)

        # Si `path` es una lista, devolverla intacta si tiene formato tabular.
        # Si no, levantar una excepción.
        if isinstance(path, list):
            if cls._is_list_of_matching_dicts(path):
                return path
            else:
                raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

        # Deduzco el formato de archivo de `path` y redirijo según corresponda.
        suffix = path.split(".")[-1]
        if suffix == "csv":
            return cls._read_csv(path)
        elif suffix == "xlsx":
            return cls._read_xlsx(path)
        else:
            raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o .xlsx""".format(suffix))

    @staticmethod
    def _read_csv(path):
        with open(path) as csvfile:
            reader = csv.DictReader(csvfile)
            table = list(reader)
        return table

    @staticmethod
    def _read_xlsx(path):
        workbook = pyxl.load_workbook(path)
        worksheet = workbook.active
        table = xlsx_to_json.sheet_to_table(worksheet)

        return table

    @classmethod
    def _write(cls, table, path):
        """ Exporta una tabla en el formato deseado (CSV o XLSX).

        La extensión del archivo debe ser ".csv" o ".xlsx", y en función de
        ella se decidirá qué método usar para escribirlo.

        Args:
            table (list of dicts): Tabla a ser exportada.
            path (str): Path al archivo CSV o XLSX de exportación.
        """
        assert isinstance(path, (str, unicode)), "`path` debe ser un string"
        assert isinstance(table, list), "`table` debe ser una lista de dicts"

        # Sólo sabe escribir listas de diccionarios con información tabular
        if not cls._is_list_of_matching_dicts(table):
            raise ValueError("""
La lista ingresada no esta formada por diccionarios con las mismas claves.""")

        # Deduzco el formato de archivo de `path` y redirijo según corresponda.
        suffix = path.split(".")[-1]
        if suffix == "csv":
            return cls._write_csv(table, path)
        elif suffix == "xlsx":
            return cls._write_xlsx(table, path)
        else:
            raise ValueError("""
{} no es un sufijo reconocido. Pruebe con .csv o.xlsx""".format(suffix))

    @staticmethod
    def _write_csv(table, path):
        headers = table[0].keys()

        with open(path, 'w') as target_file:
            writer = csv.DictWriter(csvfile=target_file, fieldnames=headers,
                                    lineterminator="\n", encoding="utf-8")
            writer.writeheader()
            for row in table:
                writer.writerow(row)

    @staticmethod
    def _write_xlsx(table, path):
        headers = table[0].keys()
        workbook = pyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(headers)
        for row in table:
            worksheet.append(row.values())

        workbook.save(path)

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

        table = cls._read(report)
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
