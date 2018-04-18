#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Decorador auxiliar

Debe instalarse 'graphviz' en el sistema para que funcione.

    Ubuntu: sudo apt-get install graphviz
    Mac: brew install graphviz
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os
import sys
import vcr

from functools import wraps
from pycallgraph import PyCallGraph
from pycallgraph import Config
from pycallgraph import GlobbingFilter
from pycallgraph.output import GraphvizOutput

# módulo de ejemplo que se quiere analizar
import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")
TEMP_DIR = os.path.join("tests", "temp")
PROFILING_DIR = os.path.join("tests", "profiling")
os.makedirs(PROFILING_DIR) if not os.path.exists(PROFILING_DIR) else None

VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
              cassette_library_dir=os.path.join(
                  "tests", "cassetes", "profiling"),
              record_mode='once')


def profile(profiling_result_path):
    """Decorador de una función para que se corra haciendo profiling."""

    def fn_decorator(fn):
        """Decora una función con el análisis de profiling."""

        @wraps(fn)
        def fn_decorated(*args, **kwargs):
            """Crea la función decorada."""

            graphviz = GraphvizOutput()
            graphviz.output_file = profiling_result_path

            with PyCallGraph(output=graphviz, config=None):
                fn(*args, **kwargs)

        return fn_decorated
    return fn_decorator


@VCR.use_cassette()
@profile("tests/profiling/profiling_test.png")
def main():
    """Hace un profiling de la función para guarda un catálogo en Excel"""

    # ejemplo liviano
    # original_catalog = pydatajson.DataJson(
    #     os.path.join(SAMPLES_DIR, "catalogo_justicia.json"))

    # ejemplo grande
    datasets_cant = 200
    original_catalog = pydatajson.DataJson(
        "http://infra.datos.gob.ar/catalog/sspm/data.json")
    original_catalog["dataset"] = original_catalog["dataset"][:datasets_cant]

    tmp_xlsx = os.path.join(TEMP_DIR, "xlsx_catalog.xlsx")
    original_catalog.to_xlsx(tmp_xlsx)


if __name__ == '__main__':
    main()
