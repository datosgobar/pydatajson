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
import jsonschema
import requests
import unicodecsv as csv
import openpyxl as pyxl

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

    @staticmethod
    def _traverse_dict(dicc, keys, default_value=None):
        """Recorre un diccionario siguiendo una lista de claves, y devuelve
        default_value en caso de que alguna de ellas no exista."""
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
        datajson = self._json_to_dict(datajson_path)
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
        datajson = self._json_to_dict(datajson_path)

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
        """Toma un dict con la metadata de un dataset, y devuelve un dict con los
        valores que generate_datasets_report() usa para reportar sobre él."""

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

        dataset_report = {
            "dataset_title": dataset.get("title"),
            "dataset_accrualPeriodicity": dataset.get("accrualPeriodicity"),
            "dataset_description": dataset.get("description"),
            "dataset_publisher_name": publisher_name,
            "dataset_superTheme": super_themes,
            "dataset_theme": themes,
            "dataset_landingPage": dataset.get("landingPage"),
            "distributions_list": distributions_list
        }

        return dataset_report

    @staticmethod
    def _catalog_report_helper(catalog, catalog_validation, url):
        fields = {
            "catalog_metadata_url": url,
            "catalog_title": catalog.get("title"),
            "catalog_description": catalog.get("description"),
            "valid_catalog_metadata": (
                1 if catalog_validation["status"] == "OK" else 0)
        }

        return fields

    def dataset_report(self, dataset, dataset_validation, dataset_index,
                       catalog_fields={}, harvest='none', report=None):
        dataset_report = {}
        dataset_report.update(catalog_fields)
        dataset_report.update({
            "dataset_index": dataset_index,
            "valid_dataset_metadata": (
                1 if dataset_validation["status"] == "OK" else 0)
        })
        dataset_report.update(self._dataset_report_helper(dataset))

        if harvest == 'all':
            dataset_report["harvest"] = 1
        elif harvest == 'none':
            dataset_report["harvest"] = 0
        elif harvest == 'valid':
            dataset_report["harvest"] = (
                1 if (
                    int(dataset_report["valid_catalog_metadata"]) and
                    int(dataset_report["valid_dataset_metadata"])) else 0)
        elif harvest == 'report':
            if not report:
                raise ValueError("""
Usted especificó harvest='report', pero `report` está vacía. Inténtelo
nuevamente, con un reporte de datasets o el path a uno en `report`.""")

            datasets_to_harvest = self._extract_datasets_to_harvest(report)
            dataset_report["harvest"] = (
                1 if (dataset_report["catalog_metadata_url"],
                      dataset_report["dataset_title"]) in datasets_to_harvest
                else 0)
        else:
            raise ValueError("""
{} no es un criterio de harvest reconocido. Pruebe con 'all', 'none', 'valid' o
'report'.""".format(harvest))

        return dataset_report.copy()

    def catalog_report(self, catalog, harvest='none', report=None):

        url = catalog if isinstance(catalog, (str, unicode)) else None
        catalog = self._json_to_dict(catalog)

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
            self.dataset_report(
                dataset, datasets_validations[index], index,
                catalog_fields, harvest, report=report
            ) for index, dataset in enumerate(datasets)
        ]

        return catalog_report

    @staticmethod
    def generate_harvester_config(report_path, config_path):
        """Genera un archivo de configuración del harvester según el reporte
        provisto.

        Se espera que `report_path` apunte a un archivo producido por
        `generate_datasets_report(catalogs, report_path)`, al cual se le
        modificaron algunos 0 (ceros) por 1 (unos) en la columna "harvest".

        Este método no devuelve nada. Como efecto sencudario, genera un
        archivo de configuración en `config_path` manteniendo de `report_path`
        únicamente los campos necesarios para el harvester, **de aquellos
        datasets para los cuales el valor de "harvest" es igual a 1**.

        Args:
            report_path (str): Path a un reporte de datasets procesado.
            config_path (str): Path donde se generará el archivo de
                configuración del harvester.

        Returns:
            None
        """
        with open(report_path) as report_file:
            reader = csv.DictReader(report_file)

            with open(config_path, 'w') as config_file:
                config_fieldnames = ["catalog_metadata_url", "dataset_title",
                                     "dataset_accrualPeriodicity"]
                writer = csv.DictWriter(config_file,
                                        fieldnames=config_fieldnames,
                                        lineterminator="\n",
                                        extrasaction='ignore',
                                        encoding='utf-8')
                writer.writeheader()

                for row in reader:
                    if row["harvest"] == "1":
                        writer.writerow(row)

    def generate_datasets_report(self, catalogs, harvest='none',
                                 report=None, export_path=None):
        """Genera un reporte sobre las condiciones de la metadata de los
        datasets contenidos en uno o varios catálogos.

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) elementos con la metadata de un catálogo.
                Tienen que poder ser interpretados por self._json_to_dict()
            harvest (str): Criterio a utilizar para determinar el valor del
                campo "harvest" en el reporte generado.
            report_path (str): Path a un reporte/config especificando qué
                datasets marcar con harvest=1 (sólo si harvest=='report').
            export_path (str): Path donde exportar el reporte generado. Si se
                especifica, el método no devolverá nada.

        Returns:
            list: Contiene tantos dicts como datasets estén presentes en
            `catalogs`, con la data del reporte generado.
        """
        catalogs_reports = [self.catalog_report(catalog, harvest, report)
                            for catalog in catalogs]
        full_report = []
        for report in catalogs_reports:
            full_report.extend(report)

        if export_path:
            self._write(table=full_report, path=export_path)
            return None
        else:
            return full_report

    def _generate_harvester_config(self, harvest='report', report=None,
                                   catalogs=None, export_path=None):
        """Genera un archivo de configuración del harvester a partir de un
        reporte, o un conjunto de catálogos y un criterio de cosecha
        (_harvest_).


        Args:
            harvest (str): Criterio a utilizar para determinar qué datasets
                incluir en el archivo de configuración generado.
            report (list o str): Lista-reporte generada por
                _generate_datasets_report(), o path a la exportación de ese
                mismo reporte. Sólo se usa cuando `harvest=='report'`, en cuyo
                caso `catalogs` se ignora.
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) elementos con la metadata de un catálogo.
                Tienen que poder ser interpretados por self._json_to_dict()
            export_parth (str): Path donde exportar el archivo de configuración
                generado. Si se especifica, el método no devolverá nada.

        Returns:
            list: Contiene diccionarios con la data necesaria para que el
            harvester los coseche.
        """
        return NotImplemented

    def _generate_harvestable_catalogs(self, catalogs, harvest='all',
                                       report=None, export_path=None):
        """Filtra los catálogos provistos según el criterio determinado en
        `harvest`.

        Args:
            catalogs (str, dict o list): Uno (str o dict) o varios (list de
                strs y/o dicts) elementos con la metadata de un catálogo.
                Tienen que poder ser interpretados por self._json_to_dict()
            harvest (str): Criterio a utilizar para determina qué datasets
                conservar de cada catálogo.
            report (list o str): En caso de que `harvest=='report'`, objeto
            con un reporte de _generate_datasets_report según el cual filtrar
                los catálogos provistos.
            export_path: Path a un archivo JSON o directorio donde exportar
                los catálogos filtrados, si así se desea. Si termina en ".json"
                se exportará la lista de catálogos a un único archivo. Si es un
                directorio, se guardará en él un JSON por catálogo.
        """
        return NotImplemented

    @staticmethod
    def _is_list_of_matching_dicts(list_of_dicts):
        elements = [isinstance(d, dict) and d.keys() == list_of_dicts[0].keys()
                    for d in list_of_dicts]
        return all(elements)

    @classmethod
    def _read(cls, path):
        """Lee un archivo tabular (CSV o XLSX) a una lista de diccionarios.

        La extensión del archivo debe ser ".csv" o ".xlsx", y en función de
        ella se decidirá qué método usar par leerlo.

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
{} no es un sufijo reconocido. Pruebe con .csv o.xlsx""".format(suffix))

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

        # Asumo que la primera fila contiene los encabezados
        keys = [cell.value for cell in worksheet.rows[0]]
        # Compruebo que todas las filas sean tan largas como la de encabezados
        assert all([len(keys) == len(row) for row in worksheet.rows])

        table = []
        for cells in worksheet.rows[1:]:
            table_row = dict(zip(keys, [cell.value for cell in cells]))
            table.append(table_row)

        return table

    @classmethod
    def _write(cls, table, path):
        """ Exporta una tabla en el formato deseado (CSV o XLSX).

        La extensión del archivo debe ser ".csv" o ".xlsx", y en función de
        ella se decidirá qué método usar par leerlo.

        Args:
            table (list): Lista "tabular" a ser exportada.
            path (str): Path al destino de la exportación.

        Returns:
            None
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
        print(bool_res)
        print(full_res)
    except IndexError as errmsg:
        format_str = """
{}: pydatajson.py fue ejecutado como script sin proveer un argumento
"""
        print(format_str.format(errmsg))

if __name__ == '__main__':
    main()
