#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'search' de Pydatajson

Contiene los métodos para navegar un data.json iterando y buscando entidades de
un catálogo.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from readers import read_catalog


def iter_datasets(catalog):
    catalog = read_catalog(catalog)
    return (dataset for dataset in catalog["dataset"])


def iter_distributions(catalog):
    catalog = read_catalog(catalog)
    for dataset in iter_datasets(catalog):
        for distribution in dataset["distribution"]:
            yield distribution


def iter_fields(catalog):
    catalog = read_catalog(catalog)
    for distribution in iter_distributions(catalog):
        # el campo "field" no es obligatorio en una distribucion
        if "field" in distribution:
            for field in distribution["field"]:
                yield field
