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
from functools import partial


def datasets(catalog, filter_in=None, filter_out=None):
    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog(catalog)

    return filter(
        lambda x: _filter_dictionary(
            x, filter_in.get("dataset"), filter_out.get("dataset")),
        catalog["dataset"]
    )


def distributions(catalog, filter_in=None, filter_out=None):
    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog(catalog)

    distributions_generator = (
        distribution for dataset in datasets(catalog, filter_in, filter_out)
        for distribution in dataset["distribution"]
    )

    return filter(
        lambda x: _filter_dictionary(
            x, filter_in.get("distribution"), filter_out.get("distribution")),
        distributions_generator
    )


def fields(catalog, filter_in=None, filter_out=None):
    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog(catalog)

    fields_generator = (
        field for distribution in distributions(catalog, filter_in, filter_out)
        if "field" in distribution
        for field in distribution["field"]
    )

    return filter(
        lambda x: _filter_dictionary(
            x, filter_in.get("field"), filter_out.get("field")),
        fields_generator
    )


def get_dataset(catalog, dataset_identifier):
    datasets = filter(lambda x: x.get("identifier") == dataset_identifier,
                      catalog["dataset"])

    if len(datasets) > 1:
        raise ce.DatasetIdRepetitionError(dataset_identifier, datasets)
    elif len(datasets) == 0:
        return None
    else:
        return datasets[0]


def _filter_dictionary(dictionary, filter_in=None, filter_out=None):
    filter_in = filter_in or {}
    filter_out = filter_out or {}

    # chequea que el objeto tenga las propiedades de filtro positivo
    for key, value in filter_in.iteritems():
        if dictionary.get(key) != value:
            return False

    # chequea que el objeto NO tenga las propiedades de filtro negativo
    for key, value in filter_out.iteritems():
        if dictionary.get(key) == value:
            return False

    return True
