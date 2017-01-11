#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo para transcribir de metadatos catálogos en formato XLSX a JSON"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import sys
import io
import json
import openpyxl as pyxl


def sheet_to_table(worksheet):
    """Transforma una hoja del libro en una lista de diccionarios."""
    def value(cell):
        """Extrae el valor de una celda de Excel."""
        value = cell.value
        if isinstance(value, (str, unicode)):
            value = value.strip()
        return value

    worksheet_rows = list(worksheet.rows)
    headers = [value(cell) for cell in worksheet_rows[0]]
    value_rows = [
        [value(cell) for cell in row] for row in worksheet_rows[1:]
        # Únicamente considero filas con al menos un campo no-nulo
        if any([value(cell) for cell in row])
    ]
    table = [
        # Ignoro los campos con valores nulos (None)
        {k: v for (k, v) in zip(headers, row) if v is not None}
        for row in value_rows
    ]

    return table


def string_to_list(string, sep=","):
    """Transforma una string con elementos separados por `sep` en una lista."""
    return [value.strip() for value in string.split(sep)]


def make_publisher(catalog_or_dataset):
    """De estar presentes las claves necesarias, genera el diccionario
    "publisher" a nivel catálogo o dataset."""
    level = catalog_or_dataset
    keys = [k for k in ["publisher_name", "publisher_mbox"] if k in level]
    if keys:
        level["publisher"] = {
            key.replace("publisher_", ""): level.pop(key) for key in keys
        }
    return level


def make_contactPoint(dataset):
    """De estar presentes las claves necesarias, genera el diccionario
    "contactPoint" de un dataset."""
    keys = [k for k in ["contactPoint_fn", "contactPoint_hasEmail"]
            if k in dataset]
    if keys:
        dataset["contactPoint"] = {
            key.replace("contactPoint_", ""): dataset.pop(key) for key in keys
        }
    return dataset


def get_dataset_index(catalog, dataset_identifier):
    """Devuelve el índice de un dataset en el catálogo en función de su
    identificador"""
    matching_datasets = [
        idx for idx, dataset in enumerate(catalog["catalog_dataset"])
        if dataset["dataset_identifier"] == dataset_identifier
    ]

    # Debe haber exactamente un dataset con el identificador provisto.
    no_dsets_msg = "No hay ningún dataset con el identifier {}".format(
        dataset_identifier)
    many_dsets_msg = "Hay más de un dataset con el identifier {}: {}".format(
        dataset_identifier, matching_datasets)
    assert len(matching_datasets) != 0, no_dsets_msg
    assert len(matching_datasets) < 2, many_dsets_msg

    dataset_index = matching_datasets[0]
    return dataset_index


def get_distribution_indexes(catalog, dataset_identifier, distribution_title):
    """Devuelve el índice de una distribución en su dataset en función de su
    título, junto con el índice de su dataset padre en el catálogo, en
    función de su identificador"""
    dataset_index = get_dataset_index(catalog, dataset_identifier)
    dataset = catalog["catalog_dataset"][dataset_index]

    matching_distributions = [
        idx for idx, distribution in enumerate(dataset["dataset_distribution"])
        if distribution["distribution_title"] == distribution_title
    ]

    # Debe haber exactamente una distribución con los identicadores provistos
    no_dists_msg = """
No hay ninguna distribución de título {} en el dataset con identificador {}.
""".format(distribution_title, dataset_identifier)
    many_dists_msg = """
Hay más de una distribución de título {} en el dataset con identificador {}:
{}""".format(distribution_title, dataset_identifier, matching_distributions)
    assert len(matching_distributions) != 0, no_dists_msg
    assert len(matching_distributions) < 2, many_dists_msg

    distribution_index = matching_distributions[0]
    return dataset_index, distribution_index


def read_local_xlsx_catalog(filename):
    """Genera un diccionario de metadatos de catálogo a partir de un XLSX bien
    formado.

    Args:
        filename (str): Path a un archivo XLSX "template" para describir la
            metadata de un catálogo.

    Returns:
        dict: Diccionario con los metadatos de un catálogo.
    """
    assert_xlsx_msg = "El archivo a leer debe tener extensión XLSX."
    assert filename.endswith(".xlsx"), assert_xlsx_msg

    workbook = pyxl.load_workbook(filename)

    catalogs = sheet_to_table(workbook["Catalog"])
    # Debe haber exactamente un catálogo en la hoja 'Catalog'
    assert (len(catalogs) != 0), "No hay ningún catálogo en la hoja 'Catalog'"
    assert (len(catalogs) < 2), "Hay más de un catálogo en la hoja 'Catalog'"
    # Genero el catálogo base
    catalog = catalogs[0]

    # Agrego themes y datasets al catálogo
    catalog["catalog_dataset"] = sheet_to_table(workbook["Dataset"])
    catalog["catalog_themeTaxonomy"] = sheet_to_table(workbook["Theme"])

    # Agrego lista de distribuciones vacía a cada dataset
    for dataset in catalog["catalog_dataset"]:
        dataset["dataset_distribution"] = []

    # Ubico cada distribución en su datasets
    distributions = sheet_to_table(workbook["Distribution"])
    for distribution in distributions:
        dataset_index = get_dataset_index(
            catalog, distribution["dataset_identifier"])
        dataset = catalog["catalog_dataset"][dataset_index]
        dataset["dataset_distribution"].append(distribution)

    # Ubico cada campo en su distribución
    fields = sheet_to_table(workbook["Field"])
    for field in fields:
        dataset_index, distribution_index = get_distribution_indexes(
            catalog, field["dataset_identifier"], field["distribution_title"])
        dataset = catalog["catalog_dataset"][dataset_index]
        distribution = dataset["dataset_distribution"][distribution_index]

        if "distribution_field" in distribution:
            distribution["distribution_field"].append(field)
        else:
            distribution["distribution_field"] = [field]

    # Transformo campos de texto separado por comas en listas
    if "catalog_language" in catalog:
        catalog["catalog_language"] = string_to_list(
            catalog["catalog_language"])

    for dataset in catalog["catalog_dataset"]:
        array_fields = ["dataset_superTheme", "dataset_theme", "dataset_tags",
                        "dataset_keyword", "dataset_language"]
        for field in array_fields:
            if field in dataset:
                dataset[field] = string_to_list(dataset[field])

    # Elimino los prefijos de los campos a nivel catálogo
    for old_key in catalog.keys():
        if old_key.startswith("catalog_"):
            new_key = old_key.replace("catalog_", "")
            catalog[new_key] = catalog.pop(old_key)
        else:
            catalog.pop(old_key)

    # Elimino los prefijos de los campos a nivel tema
    for theme in catalog["themeTaxonomy"]:
        for old_key in theme.keys():
            if old_key.startswith("theme_"):
                new_key = old_key.replace("theme_", "")
                theme[new_key] = theme.pop(old_key)
            else:
                theme.pop(old_key)

    # Elimino los prefijos de los campos a nivel dataset
    for dataset in catalog["dataset"]:
        for old_key in dataset.keys():
            if old_key.startswith("dataset_"):
                new_key = old_key.replace("dataset_", "")
                dataset[new_key] = dataset.pop(old_key)
            else:
                dataset.pop(old_key)

    # Elimino los campos auxiliares y los prefijos de los campos a nivel
    # distribución
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            for old_key in distribution.keys():
                if old_key.startswith("distribution_"):
                    new_key = old_key.replace("distribution_", "")
                    distribution[new_key] = distribution.pop(old_key)
                else:
                    distribution.pop(old_key)

    # Elimino campos auxiliares y los prefijos de los campos a nivel "campo"
    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            if "field" in distribution:
                for field in distribution["field"]:
                    for old_key in field.keys():
                        if old_key.startswith("field_"):
                            new_key = old_key.replace("field_", "")
                            field[new_key] = field.pop(old_key)
                        else:
                            field.pop(old_key)

    # Agrupo las claves de "publisher" y "contactPoint" en sendos diccionarios
    catalog = make_publisher(catalog)
    for dataset in catalog["dataset"]:
        dataset = make_publisher(dataset)
        dataset = make_contactPoint(dataset)

    return catalog


def write_json_catalog(catalog, target_file):
    """Escribo un catálogo a un archivo JSON con codificación UTF-8."""
    catalog_str = json.dumps(catalog, indent=4, separators=(",", ": "),
                             encoding="utf-8", ensure_ascii=False)
    with io.open(target_file, "w", encoding='utf-8') as target:
        target.write(catalog_str)


def main():
    """ Convierte un catálogo en formato XLSX a JSON.

    Example:
        python pydatajson/xlsx_to_json.py input_file [output_file]
        python pydatajson/xlsx_to_json.py path/to/data.xlsx path/to/data.json
    """
    args = sys.argv[1:]
    if args:
        # Asumo que el primer parámeto no obligatorio es el path a un XLSX que
        # se quiere transformar a JSON
        data_xlsx = args.pop(0)
        # Si hay un segundo parámetro no obligatorio, se asume que ese es el
        # path de destino. Si no se provee, se reutiliza el path de input con
        # la extensión cambiada.
        data_json = args.pop(0) if args else data_xlsx.replace(".xlsx",
                                                               ".json")

        catalog = read_local_xlsx_catalog(data_xlsx)
        write_json_catalog(catalog, data_json)
    else:
        print("""
xlsx_to_json.py se ejecutó desde la terminal sin proveer argumentos.""")

if __name__ == "__main__":
    main()


