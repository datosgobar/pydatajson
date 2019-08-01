#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'indicators' de Pydatajson

Contiene los métodos para monitorear y generar indicadores de un catálogo o de
una red de catálogos.
"""

from __future__ import print_function, absolute_import
from __future__ import unicode_literals, with_statement

import logging
import json
import os
from datetime import datetime
from collections import Counter

from six import string_types

from . import helpers
from . import readers
from .reporting import generate_datasets_summary
from .search import get_datasets, get_distributions
from .indicator_generators import FederationIndicatorsGenerator

CENTRAL_CATALOG = "http://datos.gob.ar/data.json"
ABSOLUTE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FIELDS_PATH = os.path.join(ABSOLUTE_PROJECT_DIR, "fields")


logger = logging.getLogger('pydatajson')


def generate_indicators(catalog, validator=None, only_numeric=False):
    return _generate_indicators(catalog, validator=validator,
                                only_numeric=only_numeric)[1]


def generate_numeric_indicators(catalog, validator=None):
    return _generate_indicators(catalog, validator=validator,
                                only_numeric=True)[1]


def generate_catalogs_indicators(catalogs, central_catalog=None,
                                 identifier_search=False,
                                 validator=None):
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
    assert isinstance(catalogs, string_types + (dict, list))
    # Si se pasa un único catálogo, genero una lista que lo contenga
    if isinstance(catalogs, string_types + (dict,)):
        catalogs = [catalogs]

    indicators_list = []
    # Cuenta la cantidad de campos usados/recomendados a nivel global
    fields = {}
    catalogs_cant = 0
    for catalog in catalogs:
        try:
            catalog = readers.read_catalog(catalog)
            catalogs_cant += 1
        except Exception as e:
            msg = u'Error leyendo catálogo de la lista: {}'.format(str(e))
            logger.warning(msg)
            continue

        fields_count, result = _generate_indicators(
            catalog, validator=validator)
        if central_catalog:
            result.update(_federation_indicators(
                catalog, central_catalog, identifier_search=identifier_search))
        if not indicators_list:
            # La primera iteracion solo copio el primer resultado
            network_indicators = result.copy()
        else:
            network_indicators = helpers.add_dicts(network_indicators,
                                                   result)
        # Sumo a la cuenta total de campos usados/totales
        fields = helpers.add_dicts(fields_count, fields)

        result['title'] = catalog.get('title', 'no-title')
        result['identifier'] = catalog.get('identifier', 'no-id')
        indicators_list.append(result)

    if not indicators_list:
        # No se pudo leer ningún catálogo
        return [], {}

    # Indicadores de la red entera
    network_indicators['catalogos_cant'] = catalogs_cant
    # Genero los indicadores de la red entera,
    _network_indicator_percentages(fields, network_indicators)

    return indicators_list, network_indicators


def _generate_indicators(catalog, validator=None, only_numeric=False):
    """Genera los indicadores de un catálogo individual.

    Args:
        catalog (dict): diccionario de un data.json parseado

    Returns:
        dict: diccionario con los indicadores del catálogo provisto
    """

    result = {}

    # Obtengo summary para los indicadores del estado de los metadatos
    result.update(_generate_status_indicators(catalog, validator=validator))

    # Genero los indicadores relacionados con fechas, y los agrego
    result.update(
        _generate_date_indicators(catalog, only_numeric=only_numeric))

    # Agrego la cuenta de los formatos de las distribuciones
    if not only_numeric:
        if 'dataset' in catalog:
            format_count = count_fields(get_distributions(catalog), 'format')
            type_count = count_fields(get_distributions(catalog), 'type')
            license_count = count_fields(get_datasets(catalog), 'license')
        else:
            format_count = type_count = license_count = {}

        result.update({
            'distribuciones_formatos_cant': format_count,
            'distribuciones_tipos_cant': type_count,
            'datasets_licencias_cant': license_count,
        })

    # Agrego porcentaje de campos recomendados/optativos usados
    fields_count = _count_required_and_optional_fields(catalog)
    recomendados_pct = float(fields_count['recomendado']) / \
        fields_count['total_recomendado']
    optativos_pct = float(fields_count['optativo']) / \
        fields_count['total_optativo']
    result.update({
        'campos_recomendados_pct': round(recomendados_pct, 4),
        'campos_optativos_pct': round(optativos_pct, 4)
    })
    return fields_count, result


def _federation_indicators(catalog, central_catalog,
                           identifier_search=False):
    """Cuenta la cantidad de datasets incluídos tanto en la lista
    'catalogs' como en el catálogo central, y genera indicadores a partir
    de esa información.

    Args:
        catalog (dict): catálogo ya parseado
        central_catalog (str o dict): ruta a catálogo central, o un dict
            con el catálogo ya parseado
    """
    result = {
        'datasets_federados_cant': None,
        'datasets_federados_pct': None,
        'datasets_no_federados_cant': None,
        'datasets_federados_eliminados_cant': None,
        'distribuciones_federadas_cant': None,
        'datasets_federados_eliminados': [],
        'datasets_no_federados': [],
        'datasets_federados': [],

    }
    try:
        central_catalog = readers.read_catalog(central_catalog)
    except Exception as e:
        msg = u'Error leyendo el catálogo central: {}'.format(str(e))
        logger.warning(msg)
        return result

    generator = FederationIndicatorsGenerator(central_catalog, catalog,
                                              id_based=identifier_search)
    result.update({
            'datasets_federados_cant':
            generator.datasets_federados_cant(),
            'datasets_no_federados_cant':
            generator.datasets_no_federados_cant(),
            'datasets_federados_eliminados_cant':
            generator.datasets_federados_eliminados_cant(),
            'datasets_federados_eliminados':
            generator.datasets_federados_eliminados(),
            'datasets_no_federados':
            generator.datasets_no_federados(),
            'datasets_federados':
            generator.datasets_federados(),
            'datasets_federados_pct':
            generator.datasets_federados_pct(),
            'distribuciones_federadas_cant':
            generator.distribuciones_federadas_cant()
        })
    return result


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
    percentages = {
        'datasets_meta_ok_pct':
            (network_indicators.get('datasets_meta_ok_cant'),
             network_indicators.get('datasets_meta_error_cant')),
        'datasets_actualizados_pct':
            (network_indicators.get('datasets_actualizados_cant'),
             network_indicators.get('datasets_desactualizados_cant')),
        'datasets_federados_pct':
            (network_indicators.get('datasets_federados_cant'),
             network_indicators.get('datasets_no_federados_cant')),
        'datasets_con_datos_pct':
            (network_indicators.get('datasets_con_datos_cant'),
             network_indicators.get('datasets_sin_datos_cant')),
    }

    for indicator in percentages:
        pct = 0.00
        partial = percentages[indicator][0] or 0
        total = partial + (percentages[indicator][1] or 0)
        # Evita division por 0
        if total:
            pct = float(partial) / total
        network_indicators[indicator] = round(pct, 4)

    # % de campos recomendados y optativos utilizados en el catálogo entero
    if fields:  # 'fields' puede estar vacío si ningún campo es válido
        rec_pct = float(fields['recomendado']) / \
            fields['total_recomendado']

        opt_pct = float(fields['optativo']) / fields['total_optativo']

        network_indicators.update({
            'campos_recomendados_pct': round(rec_pct, 4),
            'campos_optativos_pct': round(opt_pct, 4)
        })


def _generate_status_indicators(catalog, validator=None):
    """Genera indicadores básicos sobre el estado de un catálogo

    Args:
        catalog (dict): diccionario de un data.json parseado

    Returns:
        dict: indicadores básicos sobre el catálogo, tal como la cantidad
        de datasets, distribuciones y número de errores
    """
    result = {
        'datasets_cant': None,
        'distribuciones_cant': None,
        'datasets_meta_ok_cant': None,
        'datasets_meta_error_cant': None,
        'datasets_meta_ok_pct': None,
        'datasets_con_datos_cant': None,
        'datasets_sin_datos_cant': None,
        'datasets_con_datos_pct': None
    }
    try:
        summary = generate_datasets_summary(catalog, validator=validator)
    except Exception as e:
        msg = u'Error generando resumen del catálogo {}: {}'.format(
            catalog['title'], str(e))
        logger.warning(msg)
        return result

    cant_ok = 0
    cant_error = 0
    cant_data = 0
    cant_without_data = 0
    cant_distribuciones = 0
    datasets_total = len(summary)
    for dataset in summary:
        cant_distribuciones += dataset['cant_distribuciones']

        # chequea si el dataset tiene datos
        if dataset['tiene_datos'] == "SI":
            cant_data += 1
        else:  # == "ERROR"
            cant_without_data += 1

        # chequea estado de los metadatos
        if dataset['estado_metadatos'] == "OK":
            cant_ok += 1
        else:  # == "ERROR"
            cant_error += 1

    datasets_ok_pct = 0
    datasets_with_data_pct = 0
    if datasets_total:
        datasets_ok_pct = round(float(cant_ok) / datasets_total, 4)
        datasets_with_data_pct = round(float(cant_data) / datasets_total, 4)

    result.update({
        'datasets_cant': datasets_total,
        'distribuciones_cant': cant_distribuciones,
        'datasets_meta_ok_cant': cant_ok,
        'datasets_meta_error_cant': cant_error,
        'datasets_meta_ok_pct': datasets_ok_pct,
        'datasets_con_datos_cant': cant_data,
        'datasets_sin_datos_cant': cant_without_data,
        'datasets_con_datos_pct': datasets_with_data_pct

    })
    return result


def _generate_date_indicators(catalog, tolerance=0.2, only_numeric=False):
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
    result = {
        'datasets_desactualizados_cant': None,
        'datasets_actualizados_cant': None,
        'datasets_actualizados_pct': None,
        'catalogo_ultima_actualizacion_dias': None
    }
    if not only_numeric:
        result.update({
            'datasets_frecuencia_cant': {}
        })

    try:
        dias_ultima_actualizacion =\
            _days_from_last_update(catalog, "modified")
        if not dias_ultima_actualizacion:
            dias_ultima_actualizacion =\
                _days_from_last_update(catalog, "issued")

        result['catalogo_ultima_actualizacion_dias'] = \
            dias_ultima_actualizacion

    except Exception as e:
        msg = u'Error generando indicadores de fecha del catálogo {}: {}'\
            .format(catalog['title'], str(e))
        logger.warning(msg)
        return result

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
            try:
                date = helpers.parse_date_string(dataset['modified'])
                days_diff = float((datetime.now() - date).days)
                interval = helpers.parse_repeating_time_interval(
                    periodicity) * \
                    (1 + tolerance)
            except Exception as e:
                msg = u'Error generando indicadores'\
                      u'de fecha del dataset {} en {}: {}'
                msg.format(dataset['identifier'], catalog['title'], str(e))
                logger.warning(msg)
                # Asumo desactualizado
                desactualizados += 1
                continue

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
        'datasets_actualizados_pct': round(actualizados_pct, 4)
    })
    if not only_numeric:
        result.update({
            'datasets_frecuencia_cant': periodicity_amount
        })
    return result


def _days_from_last_update(catalog, date_field="modified"):
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
    if isinstance(date_modified, string_types):
        date = helpers.parse_date_string(date_modified)
        dias_ultima_actualizacion = (
            datetime.now() - date).days if date else None

    for dataset in catalog.get('dataset', []):
        date = helpers.parse_date_string(dataset.get(date_field, ""))
        days_diff = float((datetime.now() - date).days) if date else None

        # Actualizo el indicador de días de actualización si corresponde
        if not dias_ultima_actualizacion or \
                (days_diff and days_diff < dias_ultima_actualizacion):
            dias_ultima_actualizacion = days_diff

    if dias_ultima_actualizacion:
        return int(dias_ultima_actualizacion)
    else:
        return None


def _count_required_and_optional_fields(catalog):
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
    catalog_fields_path = os.path.join(CATALOG_FIELDS_PATH,
                                       'fields.json')
    with open(catalog_fields_path) as f:
        catalog_fields = json.load(f)

    # Armado recursivo del resultado
    return _count_fields_recursive(catalog, catalog_fields)


def _count_fields_recursive(dataset, fields):
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
                result = _count_fields_recursive(element, v)
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


def count_fields(targets, field):
    """Cuenta la cantidad de values en el key
    especificado de una lista de  diccionarios"""
    return Counter([target.get(field) or 'None' for target in targets])
