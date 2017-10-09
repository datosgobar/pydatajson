#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo `time_series` de pydatajson

Contiene funciones auxiliares para analizar catálogos con series de tiempo,
definidas según la extensión del perfil de metadatos para series de tiempo.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os


def distribution_has_time_index(distribution):
    for field in distribution.get('field', []):
        if field.get('specialType') == 'time_index':
            return True
    return False


def dataset_has_time_series(dataset):
    for distribution in dataset.get('distribution', []):
        if distribution_has_time_index(distribution):
            return True
    return False
