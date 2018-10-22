#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'reporting' de Pydatajson

Contiene los métodos para generar reportes sobre un catálogo.
"""

from __future__ import unicode_literals, print_function,\
    with_statement, absolute_import

from collections import OrderedDict

from pydatajson import writers
from .validation import validate_catalog

from . import readers
from . import helpers


def generate_datasets_summary(catalog, export_path=None, validator=None):
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

    validation = validate_catalog(
        catalog, validator=validator)["error"]["dataset"]

    def info_dataset(index, dataset):
        """Recolecta información básica de un dataset."""
        info = OrderedDict()
        info["indice"] = index
        info["titulo"] = dataset.get("title")
        info["identificador"] = dataset.get("identifier")
        info["estado_metadatos"] = validation[index]["status"]
        info["cant_errores"] = len(validation[index]["errors"])
        info["cant_distribuciones"] = len(dataset["distribution"])
        if helpers.dataset_has_data_distributions(dataset):
            info["tiene_datos"] = "SI"
        else:
            info["tiene_datos"] = "NO"

        return info

    summary = [info_dataset(i, ds) for i, ds in enumerate(datasets)]
    if export_path:
        writers.write_table(summary, export_path)
    else:
        return summary
