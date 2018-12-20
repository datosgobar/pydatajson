#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'reporting' de Pydatajson

Contiene los métodos para generar reportes sobre un catálogo.
"""

from __future__ import unicode_literals, print_function,\
    with_statement, absolute_import

from collections import OrderedDict

import markdown
import pandas as pd
import chardet
import csv
import glob

from pydatajson import writers
from .validation import validate_catalog
from .backup import make_catalog_backup

from . import readers
from . import helpers

# configuración para no truncar los datos en los arreglos de pandas
pd.set_option('display.max_colwidth', -1)

# templates
TPL_CATALOG_REPORT = """
# Catálogo: _{r_catalog_id}_
{r_dataset_report}
"""
TPL_DATASET_REPORT = """
## Dataset: _{r_dataset_title}_
{r_distribution_report}
"""
TPL_DISTRIBUTION_REPORT = """
### Distribución: _{r_d_title}_

    {r_d_profiling}

    {r_d_preview}

"""

ROWS_TO_READ = 10


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


def get_catalog_report(catalog, catalog_id, catalog_url=None,
                       include_datasets=None, backup_catalog=False):

    include_datasets = include_datasets or []

    if catalog is None:
        if catalog_url is None:
            raise Exception("Ambos parámetros de catálogo vacíos")
            return
        else:
            catalog = DataJson(catalog_url)

    catalog.generate_distribution_ids()

    if backup_catalog is True:
        make_catalog_backup(catalog, catalog_id, include_data=True,
                            include_datasets=include_datasets,
                            use_short_path=True)

    publisher_name = catalog['publisher']['name']

    if publisher_name is '':
        publisher_name = catalog_id

    datasets_report = ""
    # iteracion entre datasets del catálogo

    if not include_datasets:
        datasets_id = catalog.get_datasets(meta_field='identifier')
    else:
        datasets_id = include_datasets

    # for dataset in catalog.get_datasets():
    for dataset_id in datasets_id:
        datasets_report += get_dataset_report(catalog, dataset_id, catalog_id)

    c_report = TPL_CATALOG_REPORT.format(r_catalog_id=publisher_name,
                                         r_dataset_report=datasets_report)

    html = markdown.markdown(c_report)
    return html


def get_dataset_report(catalog, dataset_id, catalog_id):
    d_report = ''
    # iteracion entre distribuciones
    filter_dataset = {"dataset": {"identifier": dataset_id}}

    for distribution in catalog.get_distributions(filter_in=filter_dataset):
        d_report += get_distribution_report(catalog,
                                            distribution['identifier'],
                                            catalog_id)
    if d_report is '':
        d_report = 'Dataset sin distribuciones válidas.'

    title = catalog.get_dataset(identifier=dataset_id)[
        'title'].strip()  # .encode('utf-8')

    dataset_report = TPL_DATASET_REPORT.format(r_dataset_title=title,
                                               r_distribution_report=d_report)
    return dataset_report


def get_distribution_report(catalog, distribution_id, catalog_id):

    # validaciones: tamaño, formato...
    if not basic_validations(catalog, distribution_id):
        return ""

    d_profiling = distribution_profiling(
        catalog, distribution_id, catalog_id)

    if d_profiling is None:
        return ''

    # COSAS
    # TABLA_PROFILING = ''
    TABLA_PROFILING = d_profiling[0]
    # .encode('utf-8')
    TABLA_PREVIEW = distribution_preview(
        catalog, distribution_id, catalog_id, d_profiling[1])
    # .encode('utf-8')
    # , 'latin-1')  # encoding)

    title = catalog.get_distribution(identifier=distribution_id)[
        'title'].strip()

    return TPL_DISTRIBUTION_REPORT.format(r_d_title=title,
                                          r_d_profiling=TABLA_PROFILING,
                                          r_d_preview=TABLA_PREVIEW)


def basic_validations(catalog, distribution_id):
    # sólo valido formato por ahora
    d_format = catalog.get_distribution(identifier=distribution_id)[
        'format'].upper()

    if d_format is not 'CSV':
        return True
    else:
        return False


def distribution_preview(catalog, distribution_id, catalog_id,
                         encoding='utf8'):
    distribution = catalog.get_distribution(identifier=distribution_id)
    ds_org = catalog_id
    ds_id = distribution['dataset_identifier']  # .decode("utf-8")
    # d_id = distribution_id

    distribution_download_url = distribution["downloadURL"]

    # si no se especifica un file name, se toma de la URL
    d_file_name = distribution.get(
        "fileName",
        distribution_download_url[
            distribution_download_url.rfind("/") + 1:]
    )
    d_file_name = d_file_name[:d_file_name.rfind(".")]  # .decode("utf-8")

    distribution_path = glob.glob(
        './catalog/{}/{}/{}.csv'.format(ds_org, ds_id, d_file_name))
    if len(distribution_path) > 0:
        distribution_path = distribution_path[0]

        df_file = pd.read_csv(
            distribution_path, memory_map=True, encoding=encoding)

        n_rows, n_cols = df_file.shape
        n_rows = ROWS_TO_READ if n_rows > ROWS_TO_READ else n_rows

        df_head = df_file.head(5)
        df_sample = df_file.sample(n=n_rows)
        df_tail = df_file.tail(5)

        df_concat = pd.concat([df_head, df_sample, df_tail], sort=False)

        return '\r' + df_concat.to_html() + '\r'
    else:
        return


def distribution_profiling(catalog, distribution_id, catalog_id):
    distribution = catalog.get_distribution(identifier=distribution_id)
    ds_org = catalog_id
    ds_id = distribution['dataset_identifier']
    # ds_title = distribution['title']
    # d_id = distribution_id
    distribution_download_url = distribution["downloadURL"]

    # si no se especifica un file name, se toma de la URL
    d_file_name = distribution.get(
        "fileName",
        distribution_download_url[
            distribution_download_url.rfind("/") + 1:]
    )
    d_file_name = d_file_name[:d_file_name.rfind(".")]

    distribucion_path = glob.glob(
        './catalog/{}/{}/{}.csv'.format(ds_org, ds_id, d_file_name))

    if len(distribucion_path) > 0:
        distribucion_path = distribucion_path[0]

        d_encoding = find_encoding(distribucion_path)
        d_delimiter, d_quotechar = find_dialect(distribucion_path)
        # d_broken_lines = broken_lines(distribucion_path)
        d_broken_lines = []

        if (d_delimiter is not 'no identificado' and
                d_quotechar is not 'no identificado'):
            pd_file = pd.read_csv(distribucion_path, memory_map=True,
                                  sep=d_delimiter, quotechar=d_quotechar,
                                  encoding=d_encoding,
                                  error_bad_lines=False,
                                  skiprows=d_broken_lines,
                                  nrows=ROWS_TO_READ)
        else:
            pd_file = pd.read_csv(distribucion_path, memory_map=True,
                                  skiprows=d_broken_lines,
                                  nrows=ROWS_TO_READ)

        # d_col_names = pd_file.columns.values

        # with open(distribucion_path) as fp:
        #     for (d_rows, _) in enumerate(fp, 1):
        #         pass

        # d_cols = len(pd_file.columns.values)
        d_rows, d_cols = pd_file.shape

        lista = [d_encoding,
                 d_delimiter,
                 d_quotechar,
                 d_rows,
                 d_cols,
                 distribucion_path]

        report_columns = ['d_encoding',
                          'd_delimiter',
                          'd_quotechar',
                          'd_rows',
                          'd_cols',
                          'file_path']

        df_report = pd.DataFrame([lista], columns=report_columns)

        df_report['file_path'] = df_report['file_path'].apply(
            lambda x: '<a href="{}">link</a>'.format(x))

        html_report = df_report.to_html(index_names=False,
                                        justify='center',
                                        escape=False)
        # return '\r' + html_report + '\r'
        return [u'\r' + html_report + u'\r', d_encoding]
    else:
        return


def find_encoding(f_path):
    """Identifica el encoding en un archivo CSV.

    Args:
        f_path (str): Path al archivo

    Returns:
        str: Encoding o mensaje 'no identificado'
    """
    r_file = open(f_path, 'rb').read()
    try:
        return chardet.detect(r_file)['encoding']
    except Exception:
        return 'no identificado'


def find_dialect(f_path):
    """Identifica el dialecto de un archivo CSV (caracter delimitador de campos
     y de texto).

    Args:
        f_path (str): Path al archivo

    Returns:
        tuple: Caracter delimitador de campos y caracter delimitador de texto,
        o mensaje 'no identificado'
    """
    with open(f_path, 'rb') as csvfile:
        # try:
        line = csvfile.readline().decode('utf-8', errors='ignore')
        # except UnicodeDecodeError():
        # line = csvfile.readline().decode('latin-1')

        dialect = csv.Sniffer().sniff(line)

        return dialect.delimiter, dialect.quotechar
        # return 'no identificado', 'no identificado'
##


def broken_lines(f_path):
    """Identifica las líneas que generan error de parseo en un archivo CSV.

    Args:
        f_path (str): Path al archivo

    Returns:
        list: Lista con los números de línea con error de parseo
    """
    rows_skipped = []
    cont = True

    while cont is True:
        try:
            pd.read_csv(f_path, skiprows=rows_skipped, nrows=10)
#             data = pd.read_csv(f_path,memory_map=True,skiprows=rows_skipped)
            cont = False
        except Exception as e:
            errortype = e.message.split('.')[0].strip()
            if errortype == 'Error tokenizing data':
                cerror = e.message.split(':')[1].strip().replace(',', '')
                nums = [n for n in cerror.split(' ') if str.isdigit(n)]
                if len(nums) >= 2:
                    rows_skipped.append(int(nums[1]) - 1)
            else:
                cerror = 'Unknown'
                print(e.message)
                cont = False

    return rows_skipped
