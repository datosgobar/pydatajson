#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import io
import os
import logging

from six import string_types

from pydatajson.helpers import traverse_dict
from pydatajson.readers import read_catalog
from pydatajson.indicators import generate_catalogs_indicators
from pydatajson.validation import validate_catalog

logger = logging.getLogger('pydatajson')

CENTRAL_CATALOG = "http://datos.gob.ar/data.json"
ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(ABSOLUTE_PROJECT_DIR, "templates")


def generate_catalog_readme(_datajson, catalog, export_path=None):
    """Este método está para mantener retrocompatibilidad con versiones
    anteriores. Se ignora el argumento _data_json."""
    return generate_readme(catalog, export_path)


def generate_readme(catalog, export_path=None):
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
    if isinstance(catalog, string_types):
        catalog_path_or_url = catalog
    else:
        catalog_path_or_url = None

    catalog = read_catalog(catalog)
    validation = validate_catalog(catalog)
    # Solo necesito indicadores para un catalogo
    indicators = generate_catalogs_indicators(
        catalog, CENTRAL_CATALOG)[0][0]

    with io.open(os.path.join(TEMPLATES_PATH, 'catalog_readme.txt'), 'r',
                 encoding='utf-8') as template_file:
        readme_template = template_file.read()

        not_federated_datasets_list = "\n".join([
            "- [{}]({})".format(dataset[0], dataset[1])
            for dataset in indicators["datasets_no_federados"]
        ])
        federated_removed_datasets_list = "\n".join([
            "- [{}]({})".format(dataset[0], dataset[1])
            for dataset in indicators["datasets_federados_eliminados"]
        ])
        federated_datasets_list = "\n".join([
            "- [{}]({})".format(dataset[0], dataset[1])
            for dataset in indicators["datasets_federados"]
        ])
        non_federated_pct = 1.0 - indicators["datasets_federados_pct"] if \
            indicators["datasets_federados_pct"] is not None else \
            indicators["datasets_federados_pct"]
        content = {
            "title": catalog.get("title"),
            "publisher_name": traverse_dict(
                catalog, ["publisher", "name"]),
            "publisher_mbox": traverse_dict(
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
            "not_federated_datasets_pct": non_federated_pct,
            "not_federated_datasets_list": not_federated_datasets_list,
            "federated_removed_datasets_list": federated_removed_datasets_list,
            "federated_datasets_list": federated_datasets_list,
        }

        catalog_readme = readme_template.format(**content)

    if export_path:
        with io.open(export_path, 'w+', encoding='utf-8') as target:
            target.write(catalog_readme)
    else:
        return catalog_readme
