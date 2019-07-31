# -*- coding: utf-8 -*-
"""
Módulo pydatajson
Conjunto de herramientas para validar y manipular la información presente en
el archivo `data.json` de un Portal de Datos
"""

from __future__ import absolute_import
from .core import DataJson
from .helpers import parse_repeating_time_interval
from . import helpers
import logging

__author__ = """Datos Argentina"""
__email__ = 'datos@modernizacion.gob.ar'
__version__ = '0.4.44'

"""
Logger base para librería pydatajson
https://docs.python.org/2/howto/logging.html#configuring-logging-for-a-library
"""
logger = logging.getLogger('pydatajson')
logger.addHandler(logging.NullHandler())
