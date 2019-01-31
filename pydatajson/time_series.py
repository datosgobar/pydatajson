#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo `time_series` de pydatajson

Contiene funciones auxiliares para analizar catálogos con series de tiempo,
definidas según la extensión del perfil de metadatos para series de tiempo.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from . import custom_exceptions as ce


def field_is_time_series(field, distribution=None):
    field_may_be_ts = (
        not field.get("specialType") and
        not field.get("specialTypeDetail") and
        (
            field.get("type", "").lower() == "number" or
            field.get("type", "").lower() == "integer"
        ) and
        field.get("id")
    )
    distribution_may_has_ts = (
        not distribution or distribution_has_time_index(distribution)
    )
    return field_may_be_ts and distribution_may_has_ts


def get_distribution_time_index(distribution):
    for field in distribution.get('field', []):
        if field.get('specialType') == 'time_index':
            return field.get('title')

    raise ce.DistributionTimeIndexNonExistentError(
        distribution.get("title"),
        distribution.get("dataset_identifier"),
        "no tiene índice de tiempo."
    )


def get_distribution_time_index_frequency(distribution):
    for field in distribution.get('field', []):
        if field.get('specialType') == 'time_index':
            return field.get('specialTypeDetail')

    raise ce.DistributionTimeIndexNonExistentError(
        distribution.get("title"),
        distribution.get("dataset_identifier"),
        "no tiene índice de tiempo."
    )


def distribution_has_time_index(distribution):
    try:
        return any([field.get('specialType') ==
                    'time_index' for field in distribution.get('field', [])])
    except AttributeError:
        return False


def dataset_has_time_series(dataset):
    for distribution in dataset.get('distribution', []):
        if distribution_has_time_index(distribution):
            return True
    return False
