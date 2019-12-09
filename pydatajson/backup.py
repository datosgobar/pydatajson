#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo con funciones auxiliares para hacer backups de catálogos.

pydatajson backup https://monitoreo.datos.gob.ar/nodes.json
~/datos-argentina-backup/
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os
import time
import argparse
import logging
import requests
import zipfile

import pydatajson
from pydatajson.helpers import ensure_dir_exists
from pydatajson.download import download_to_file

CATALOGS_DIR = ""
CATALOGS_URL = 'http://monitoreo.datos.gob.ar/nodes.json'

logger = logging.getLogger('pydatajson')


def make_catalogs_backup(catalog, catalog_id, local_catalogs_dir="",
                         include_metadata=True, include_data=True,
                         include_metadata_xlsx=False, use_short_path=False):
    """Realiza una copia local de los datos y metadatos de un catálogo.

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
        catalog_id (str): Si se especifica, se usa este identificador para el
            backup. Si no se espedifica, se usa catalog["identifier"].
        local_catalogs_dir (str): Directorio local en el cual se va a crear
            la carpeta "catalog/..." con todos los catálogos.
        include_metadata (bool): Si es verdadero, se generan los archivos
            data.json y catalog.xlsx.
        include_data (bool): Si es verdadero, se descargan todas las
            distribuciones de todos los catálogos.

    Return:
        None
    """
    print("Haciendo backup de '{}'...".format(catalog_id))
    try:
        make_catalog_backup(
            catalog, catalog_id,
            local_catalogs_dir=local_catalogs_dir,
            include_metadata=include_metadata,
            include_metadata_xlsx=include_metadata_xlsx,
            include_data=include_data,
            use_short_path=use_short_path)
        print("Backup de '{}' finalizado.".format(catalog_id))
    except Exception as e:
        logger.exception(
            "ERROR en {} ({})".format(catalog, catalog_id))
        print(e)
        print(
            "Backup de '{}' terminó con errores.".format(catalog_id))


def make_catalog_backup(catalog, catalog_id=None, local_catalogs_dir="",
                        include_metadata=True, include_data=True,
                        include_datasets=None,
                        include_distribution_formats=None,
                        include_metadata_xlsx=True, use_short_path=False):
    """Realiza una copia local de los datos y metadatos de un catálogo.

    Args:
        catalog (dict or str): Representación externa/interna de un catálogo.
            Una representación _externa_ es un path local o una URL remota a un
            archivo con la metadata de un catálogo, en formato JSON o XLSX. La
            representación _interna_ de un catálogo es un diccionario.
        catalog_id (str): Si se especifica, se usa este identificador para el
            backup. Si no se especifica, se usa catalog["identifier"].
        local_catalogs_dir (str): Directorio local en el cual se va a crear
            la carpeta "catalog/..." con todos los catálogos.
        include_metadata (bool): Si es verdadero, se generan los archivos
            data.json y catalog.xlsx.
        include_data (bool): Si es verdadero, se descargan todas las
            distribuciones de todos los catálogos.
        include_datasets (list): Si se especifica, se descargan únicamente los
            datasets indicados. Si no, se descargan todos.
        include_distribution_formats (list): Si se especifica, se descargan
            únicamente las distribuciones de los formatos indicados. Si no, se
            descargan todas.
        use_short_path (bool): No implementado. Si es verdadero, se utiliza una
            jerarquía de directorios simplificada. Caso contrario, se replica
            la existente en infra.
    Return:
        None
    """

    try:
        catalog = pydatajson.DataJson(
            catalog, catalog_format="json", verify_ssl=False)
    except:
        catalog = pydatajson.DataJson(
            catalog, catalog_format="xlsx", verify_ssl=False)
    catalog_identifier = catalog_id if catalog_id else catalog["identifier"]

    if include_metadata:
        download_metadata(catalog, catalog_identifier, include_metadata_xlsx,
                          local_catalogs_dir)

    if include_data:
        download_data(catalog, catalog_identifier, include_datasets,
                      include_distribution_formats, local_catalogs_dir,
                      use_short_path)


def download_metadata(catalog, catalog_identifier, include_metadata_xlsx,
                      local_catalogs_dir):
    logger.info(
        "Descargando catálogo {}".format(
            catalog_identifier.ljust(30)))
    # catálogo en json
    catalog_path = get_catalog_path(catalog_identifier, local_catalogs_dir)
    ensure_dir_exists(os.path.dirname(catalog_path))
    catalog.to_json(catalog_path)
    if include_metadata_xlsx:
        # catálogo en xlsx
        catalog_path = get_catalog_path(
            catalog_identifier, local_catalogs_dir, fmt="xlsx")
        ensure_dir_exists(os.path.dirname(catalog_path))
        catalog.to_xlsx(catalog_path)


def download_data(catalog, catalog_identifier, include_datasets,
                  include_distribution_formats, local_catalogs_dir,
                  use_short_path, delay=0.3):
    distributions = catalog.distributions
    distributions_num = len(distributions)
    success_download = 0
    failed_download = 0
    for index, distribution in enumerate(distributions):
        print("Descargando distribución {} de {} ({})".format(
            index + 1, distributions_num, catalog_identifier), end="\r")

        dataset_id = distribution["dataset_identifier"]

        if include_datasets and (dataset_id not in include_datasets):
            continue
        distribution_id = distribution["identifier"]
        if "downloadURL" in distribution:
            distribution_download_url = distribution["downloadURL"]

            # si no se especifica un file name, se toma de la URL
            idx = distribution_download_url.rfind("/") + 1
            distribution_file_name = distribution.get(
                "fileName",
                distribution_download_url[idx:]
            )

            # si no especifica un formato, toma de distribution_file_name
            # asume que formato está al menos en distribution_file_name
            distribution_format = distribution.get(
                "format",
                distribution_file_name[distribution_file_name.rfind(".") + 1:]
            )
            if (include_distribution_formats and
                    (distribution_format
                     not in include_distribution_formats)):
                continue

            if distribution.get('type', 'file') not in ('file', 'file.upload'):
                continue

            import socket
            # genera el path local donde descargar el archivo
            file_path = get_distribution_path(
                catalog_identifier, dataset_id, distribution_id,
                distribution_file_name, local_catalogs_dir,
                use_short_path=use_short_path)
            ensure_dir_exists(os.path.dirname(file_path))

            # decarga el archivo
            try:
                download_to_file(distribution_download_url, file_path)
                success_download += 1
                print("Descarga de {} OK".format(distribution_download_url))
            except Exception as e:
                print("No se pudo descargar exitosamente {}".format(
                    distribution_download_url))
                print("Error: {}".format(e))
                failed_download += 1
        else:
            print("La distribucion '{}' del catalogo '{}' no tiene URL".format(
                catalog_identifier, distribution_id))

        # evita sobrecargar al servidor en la iteración de requests
        time.sleep(delay)

    print("Se descargaron {} distribuciones de '{}' exitosamente.".format(
        success_download, catalog_identifier))
    print("No se descargaron {} distribuciones de '{}' exitosamente."
          .format(failed_download, catalog_identifier))


def get_distribution_dir(catalog_id, dataset_id, distribution_id,
                         catalogs_dir=CATALOGS_DIR, use_short_path=False):
    """Genera el path estándar de un catálogo en un filesystem."""
    if use_short_path:
        catalog_path = os.path.join(catalogs_dir, "catalog", catalog_id)
        distribution_dir = os.path.join(catalog_path, dataset_id)
    else:
        catalog_path = os.path.join(catalogs_dir, "catalog", catalog_id)
        dataset_path = os.path.join(catalog_path, "dataset", dataset_id)
        distribution_dir = os.path.join(
            dataset_path, "distribution", distribution_id)

    return os.path.abspath(distribution_dir)


def get_distribution_path(catalog_id, dataset_id, distribution_id,
                          distribution_file_name, catalogs_dir=CATALOGS_DIR,
                          use_short_path=False):
    """Genera el path estándar de un catálogo en un filesystem."""
    if use_short_path:
        distribution_dir = get_distribution_dir(
            catalog_id, dataset_id, distribution_id, catalogs_dir,
            use_short_path=True)
        distribution_file_path = os.path.join(
            distribution_dir, distribution_file_name)
    else:
        distribution_dir = get_distribution_dir(
            catalog_id, dataset_id, distribution_id, catalogs_dir,
            use_short_path=False)
        distribution_file_path = os.path.join(
            distribution_dir, "download", distribution_file_name)

    return os.path.abspath(distribution_file_path)


def get_catalog_path(catalog_id, catalogs_dir=CATALOGS_DIR, fmt="json"):
    """Genera el path estándar de un catálogo en un filesystem."""

    base_path = os.path.join(catalogs_dir, "catalog", catalog_id)
    if fmt == "json":
        return os.path.join(base_path, "data.json")
    elif fmt == "xlsx":
        return os.path.join(base_path, "catalog.xlsx")
    else:
        raise NotImplementedError("El formato {} no está implementado.".format(
            fmt))


def download_all(catalogs_url, backup_dir, include_data=True,
                 use_short_path=True):
    include_data = bool(int(include_data))
    nodos = requests.get(catalogs_url, verify=False).json()

    nodos_dict = {
        catalog["id"]: catalog["url_json"]
        for jurisdiction in nodos["jurisdictions"]
        for catalog in jurisdiction["catalogs"]
    }

    import multiprocessing
    pool = multiprocessing.pool.ThreadPool(processes=len(nodos_dict))
    pool.map(lambda catalog_id: (make_catalogs_backup(
        nodos_dict[catalog_id], catalog_id,
        local_catalogs_dir=backup_dir,
        include_data=include_data,
        use_short_path=use_short_path,
        include_metadata_xlsx=True)),
        nodos_dict.keys())


def main(*args):
    backup_dir = os.path.join(os.getcwd(), 'backup')

    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true')
    parser.add_argument('catalog', nargs='?')
    parser.add_argument('--zip', action='store_true', required=False)

    import sys
    if sys.argv[1] == 'backup':
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    args = parser.parse_args(args=args)
    if (not args.all and not args.catalog) and not args.zip:
        return print("Uso: backup.py --all ó backup.py <catalog_url>")

    if (args.all and args.catalog) and not args.zip:
        return print("Solo se puede especificar uno de :--all o catalog")

    if args.all:
        download_all(CATALOGS_URL, backup_dir)

    elif args.catalog:
        make_catalog_backup(args.catalog, local_catalogs_dir=backup_dir)

    def zipdir(path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                ziph.write(os.path.join(root, file))

    if args.zip:
        print("Comprimiendo...")
        catalog_dir = os.path.join(backup_dir, "catalog")
        zipf = zipfile.ZipFile(catalog_dir + ".zip", 'w', zipfile.ZIP_DEFLATED)
        zipdir(catalog_dir, zipf)
        zipf.close()


if __name__ == '__main__':
    main()
