#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'search' de Pydatajson

Contiene los métodos para navegar un data.json iterando y buscando entidades de
un catálogo.
"""

from __future__ import with_statement, absolute_import
from __future__ import unicode_literals, print_function

from six import iteritems
from pydatajson.custom_exceptions import ThemeIdRepeated, ThemeLabelRepeated
from . import custom_exceptions as ce
from .readers import read_catalog_obj
from .time_series import distribution_has_time_index
from .time_series import dataset_has_time_series, field_is_time_series


def get_themes(catalog):
    """Devuelve la lista de temas del catálogo (taxonomía temática)."""
    catalog = read_catalog_obj(catalog)
    return catalog.get("themeTaxonomy")


def get_datasets(catalog, filter_in=None, filter_out=None, meta_field=None,
                 exclude_meta_fields=None, only_time_series=False):
    """Devuelve una lista de datasets del catálogo o de uno de sus metadatos.

    Args:
        catalog (dict, str or DataJson): Representación externa/interna de un
            catálogo. Una representación _externa_ es un path local o una
            URL remota a un archivo con la metadata de un catálogo, en
            formato JSON o XLSX. La representación _interna_ de un catálogo
            es un diccionario. Ejemplos: http://datos.gob.ar/data.json,
            http://www.ign.gob.ar/descargas/geodatos/catalog.xlsx,
            "/energia/catalog.xlsx".
        filter_in (dict): Devuelve los datasets cuyos atributos coinciden con
            los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los datasets de ese publisher_name.
        filter_out (dict): Devuelve los datasets cuyos atributos no coinciden
            con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los datasets que no sean de ese publisher_name.
        meta_field (str): Nombre de un metadato de Dataset. En lugar de
            devolver los objetos completos "Dataset", devuelve una lista de
            valores para ese metadato presentes en el catálogo.
        exclude_meta_fields (list): Metadatos de Dataset que se quieren excluir
            de los objetos Dataset devueltos.
        only_time_series (bool): Si es verdadero, sólo devuelve datasets que
            tengan por lo menos una distribución de series de tiempo.
    """

    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog_obj(catalog)

    if filter_in or filter_out:
        filtered_datasets = [
            dataset for dataset in catalog["dataset"] if
            _filter_dictionary(dataset, filter_in.get(
                "dataset"), filter_out.get("dataset"))
        ]
    else:
        filtered_datasets = catalog["dataset"]

    # realiza filtros especiales
    if only_time_series:
        filtered_datasets = [
            dataset for dataset in filtered_datasets
            if dataset_has_time_series(dataset)]

    if meta_field:
        return [dataset[meta_field] for dataset in filtered_datasets
                if meta_field in dataset]

    if exclude_meta_fields:
        meta_filtered_datasets = []
        for dataset in filtered_datasets:
            dataset_meta_filtered = dataset.copy()
            for excluded_meta_field in exclude_meta_fields:
                dataset_meta_filtered.pop(excluded_meta_field, None)
            meta_filtered_datasets.append(dataset_meta_filtered)

        return meta_filtered_datasets

    else:
        return filtered_datasets


def get_distributions(catalog, filter_in=None, filter_out=None,
                      meta_field=None, exclude_meta_fields=None,
                      only_time_series=False):
    """Devuelve lista de distribuciones del catálogo o de uno de sus metadatos.

    Args:
        catalog (dict, str or DataJson): Representación externa/interna de un
            catálogo. Una representación _externa_ es un path local o una
            URL remota a un archivo con la metadata de un catálogo, en
            formato JSON o XLSX. La representación _interna_ de un catálogo
            es un diccionario. Ejemplos: http://datos.gob.ar/data.json,
            http://www.ign.gob.ar/descargas/geodatos/catalog.xlsx,
            "/energia/catalog.xlsx".
        filter_in (dict): Devuelve los distribuciones cuyos atributos
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los distribuciones que pertenezcan a un dataset
            de ese publisher_name.
        filter_out (dict): Devuelve los distribuciones cuyos atributos no
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los distribuciones que no pertenezcan a un
            dataset de ese publisher_name.
        meta_field (str): Nombre de un metadato de Distribution. En lugar de
            devolver los objetos completos Distribution, devuelve una lista de
            valores para ese metadato presentes en el catálogo.
        exclude_meta_fields (list): Metadatos de Distribution que se quieren
            excluir de los objetos Distribution devueltos.
        only_time_series (bool): Si es verdadero, sólo devuelve distribuciones
            que sean distribuciones de series de tiempo.
    """

    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog_obj(catalog)

    distributions = []
    for dataset in get_datasets(catalog, filter_in, filter_out):
        for distribution in dataset.get("distribution", []):
            # agrega el id del dataset
            distribution["dataset_identifier"] = dataset["identifier"]
            distributions.append(distribution)

    filtered_distributions = [
        distribution for distribution in distributions if
        _filter_dictionary(distribution, filter_in.get("distribution"),
                           filter_out.get("distribution"))
    ]

    # realiza filtros especiales
    if only_time_series:
        filtered_distributions = [distribution for distribution in
                                  filtered_distributions if
                                  distribution_has_time_index(distribution)]

    if meta_field:
        return [distribution[meta_field]
                for distribution in filtered_distributions
                if meta_field in distribution]

    if exclude_meta_fields:
        meta_filtered_distributions = []
        for distribution in filtered_distributions:
            distribution_meta_filtered = distribution.copy()
            for excluded_meta_field in exclude_meta_fields:
                distribution_meta_filtered.pop(excluded_meta_field, None)
            meta_filtered_distributions.append(distribution_meta_filtered)

        return meta_filtered_distributions

    else:
        return filtered_distributions


def get_fields(catalog, filter_in=None, filter_out=None, meta_field=None,
               only_time_series=False, distribution_identifier=None):
    """Devuelve lista de campos del catálogo o de uno de sus metadatos.

    Args:
        catalog (dict, str or DataJson): Representación externa/interna de un
            catálogo. Una representación _externa_ es un path local o una
            URL remota a un archivo con la metadata de un catálogo, en
            formato JSON o XLSX. La representación _interna_ de un catálogo
            es un diccionario. Ejemplos: http://datos.gob.ar/data.json,
            http://www.ign.gob.ar/descargas/geodatos/catalog.xlsx,
            "/energia/catalog.xlsx".
        filter_in (dict): Devuelve los campos cuyos atributos
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los campos que pertenezcan a un dataset
            de ese publisher_name.
        filter_out (dict): Devuelve los campos cuyos atributos no
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán los campos que no pertenezcan a un
            dataset de ese publisher_name.
        meta_field (str): Nombre de un metadato de Field. En lugar de
            devolver los objetos completos "Field", devuelve una lista de
            valores para ese metadato presentes en el catálogo.
        exclude_meta_fields (list): Metadatos de Field que se quieren
            excluir de los objetos Field devueltos.
        only_time_series (bool): Si es verdadero, sólo devuelve campos
            que sean series de tiempo.
    """

    filter_in = filter_in or {}
    filter_out = filter_out or {}
    catalog = read_catalog_obj(catalog)

    # agrego atajos para filtros
    if distribution_identifier:
        if "distribution" not in filter_in:
            filter_in["distribution"] = {}
        filter_in["distribution"]["identifier"] = distribution_identifier

    fields = []
    for distribution in get_distributions(catalog, filter_in, filter_out,
                                          only_time_series=only_time_series):

        distribution_fields = distribution.get("field", [])
        if isinstance(distribution_fields, list):
            for field in distribution_fields:
                if not only_time_series or field_is_time_series(field,
                                                                distribution):
                    # agrega el id del dataset
                    field["dataset_identifier"] = distribution[
                        "dataset_identifier"]
                    # agrega el id de la distribución
                    field["distribution_identifier"] = distribution.get(
                        "identifier")

                    fields.append(field)

    filtered_fields = [field for field in fields if
                       _filter_dictionary(field, filter_in.get("field"),
                                          filter_out.get("field"))]

    if meta_field:
        return [field[meta_field] for field in filtered_fields
                if meta_field in field]
    else:
        return filtered_fields


def get_time_series(catalog, **kwargs):
    """Devuelve lista de series de tiempo del catálogo o uno de sus metadatos.

    Args:
        catalog (dict, str or DataJson): Representación externa/interna de un
            catálogo. Una representación _externa_ es un path local o una
            URL remota a un archivo con la metadata de un catálogo, en
            formato JSON o XLSX. La representación _interna_ de un catálogo
            es un diccionario. Ejemplos: http://datos.gob.ar/data.json,
            http://www.ign.gob.ar/descargas/geodatos/catalog.xlsx,
            "/energia/catalog.xlsx".
        filter_in (dict): Devuelve las series cuyos atributos
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán las series que pertenezcan a un dataset
            de ese publisher_name.
        filter_out (dict): Devuelve las series cuyos atributos no
            coinciden con los pasados en este diccionario. Ejemplo::
                {
                    "dataset": {
                        "publisher": {"name": "Ministerio de Ambiente"}
                    }
                }
            Sólo se devolverán las series que no pertenezcan a un
            dataset de ese publisher_name.
        meta_field (str): Nombre de un metadato de Field. En lugar de
            devolver los objetos completos "Field", devuelve una lista de
            valores para ese metadato presentes en el catálogo.
        exclude_meta_fields (list): Metadatos de Field que se quieren excluir
            de los objetos Field devueltos.
    """

    kwargs["only_time_series"] = True
    return get_fields(catalog, **kwargs)


def _get_dataset_by_identifier(catalog, identifier):
    dataset_index = catalog._datasets_index[identifier]["dataset_index"]
    dataset = catalog.datasets[dataset_index]
    assert dataset["identifier"] == identifier
    return dataset


def get_dataset(catalog, identifier=None, title=None):
    """Devuelve un Dataset del catálogo."""

    msg = "Se requiere un 'identifier' o 'title' para buscar el dataset."
    assert identifier or title, msg
    catalog = read_catalog_obj(catalog)

    # búsqueda optimizada por identificador
    if identifier:
        try:
            return _get_dataset_by_identifier(catalog, identifier)
        except BaseException:
            try:
                catalog._build_index()
                return _get_dataset_by_identifier(catalog, identifier)
            except BaseException:
                filtered_datasets = get_datasets(
                    catalog, {"dataset": {"identifier": identifier}})
    elif title:  # TODO: is this required?
        filtered_datasets = get_datasets(
            catalog, {"dataset": {"title": title}})

    if len(filtered_datasets) > 1:
        if identifier:
            raise ce.DatasetIdRepetitionError(
                identifier, filtered_datasets)
        elif title:
            # TODO: Improve exceptions module!
            raise ce.DatasetTitleRepetitionError(title, filtered_datasets)
    elif len(filtered_datasets) == 0:
        return None
    else:
        return filtered_datasets[0]


def _get_distribution_by_identifier(catalog, identifier):
    dataset_identifier = catalog._distributions_index[
        identifier]["dataset_identifier"]
    distribution_index = catalog._distributions_index[
        identifier]["distribution_index"]
    distribution = _get_dataset_by_identifier(catalog, dataset_identifier)[
        "distribution"][distribution_index]
    assert distribution["identifier"] == identifier
    return distribution


def get_distribution(catalog, identifier=None, title=None,
                     dataset_identifier=None):
    """Devuelve una Distribution del catálogo."""

    msg = "Se requiere un 'identifier' o 'title' para buscar el distribution."
    assert identifier or title, msg
    catalog = read_catalog_obj(catalog)

    # 1. BUSCA las distribuciones en el catálogo
    # toma la distribution que tenga el id único
    # búsqueda optimizada por identificador
    if identifier:
        try:
            return _get_distribution_by_identifier(catalog, identifier)
        except BaseException:
            try:
                catalog._build_index()
                return _get_distribution_by_identifier(catalog, identifier)
            except BaseException:
                filtered_distributions = get_distributions(
                    catalog, {"distribution": {"identifier": identifier}})
    # toma la distribution que tenga el título único, dentro de un dataset
    elif title and dataset_identifier:
        filtered_distributions = get_distributions(
            catalog, {
                "dataset": {"identifier": dataset_identifier},
                "distribution": {"title": title}
            }
        )
    # toma las distribution que tengan el título (puede haber más de una)
    elif title:
        filtered_distributions = get_distributions(
            catalog, {"distribution": {"title": title}})

    # 2. CHEQUEA que la cantidad de distribuciones es consistente
    if len(filtered_distributions) > 1:
        if identifier:
            raise ce.DistributionIdRepetitionError(
                identifier, filtered_distributions)
        elif title and dataset_identifier:
            # el título de una distribution no puede repetirse en un dataset
            raise ce.DistributionTitleRepetitionError(
                title, filtered_distributions)
        elif title:
            # el título de una distribution puede repetirse en el catalogo
            return filtered_distributions
    elif len(filtered_distributions) == 0:
        return None
    else:
        return filtered_distributions[0]


def get_field_location(catalog, identifier=None, title=None,
                       distribution_identifier=None):
    catalog = read_catalog_obj(catalog)

    field_location = None

    for dataset in catalog["dataset"]:
        for distribution in dataset["distribution"]:
            if (not distribution_identifier or
                    distribution_identifier == distribution["identifier"]):
                if "field" in distribution and isinstance(
                        distribution["field"], list):
                    for field in distribution["field"]:
                        if (identifier and "id" in field and
                                field["id"] == identifier
                                or title and field["title"] == title):
                            field_location = {
                                "dataset_identifier": dataset["identifier"],
                                "dataset_title": dataset["title"],
                                "distribution_identifier": distribution[
                                    "identifier"],
                                "distribution_title": distribution["title"],
                                "field_id": field["id"],
                                "field_title": field["title"]
                            }

                            return field_location

    return field_location


def _get_field_by_identifier(catalog, identifier):
    distribution_identifier = catalog._fields_index[
        identifier]["distribution_identifier"]
    field_index = catalog._fields_index[identifier]["field_index"]
    field = _get_distribution_by_identifier(catalog, distribution_identifier)[
        "field"][field_index]
    assert field["id"] == identifier
    return field


def get_field(catalog, identifier=None, title=None,
              distribution_identifier=None):
    """Devuelve un Field del catálogo."""

    msg = "Se requiere un 'id' o 'title' para buscar el field."
    assert identifier or title, msg

    # 1. BUSCA los fields en el catálogo
    # búsqueda optimizada por identificador
    if identifier:
        try:
            return _get_field_by_identifier(catalog, identifier)
        except BaseException:
            try:
                catalog._build_index()
                return _get_field_by_identifier(catalog, identifier)
            except BaseException:
                filtered_fields = get_fields(
                    catalog, {"field": {"id": identifier}})
    elif title and distribution_identifier:
        filtered_fields = get_fields(
            catalog, {
                "distribution": {"identifier": distribution_identifier},
                "field": {"title": title}
            }
        )
    elif title:
        filtered_fields = get_fields(
            catalog, {"field": {"title": title}})

    # 2. CHEQUEA que la cantidad de fields es consistente
    if len(filtered_fields) > 1:
        if identifier:
            raise ce.FieldIdRepetitionError(
                identifier, filtered_fields)
        elif title and distribution_identifier:
            # el título de un field no puede repetirse en una distribution
            raise ce.FieldTitleRepetitionError(
                title, filtered_fields)
        elif title:
            # el título de un field puede repetirse
            return filtered_fields
    elif len(filtered_fields) == 0:
        return None
    else:
        return filtered_fields[0]


def get_theme(catalog, identifier=None, label=None):
    msg = "Se requiere un 'id' o 'label' para buscar el theme."
    assert identifier or label, msg

    themes = get_themes(catalog)

    if not themes:
        raise ce.ThemeTaxonomyNonExistentError()

    # filtra por id (preferentemente) o label
    if identifier:
        filtered_themes = [theme for theme in themes if theme[
            "id"].lower() == identifier.lower()]
        if len(filtered_themes) > 1:
            raise ThemeIdRepeated([x["id"] for x in filtered_themes])

    elif label:
        filtered_themes = [
            theme for theme in themes if theme["label"] == label]
        if len(filtered_themes) > 1:
            raise ThemeLabelRepeated([x["label"] for x in filtered_themes])

    else:
        raise Exception(msg)

    if len(filtered_themes) == 0:
        return None
    else:
        return filtered_themes[0]


def get_catalog_metadata(catalog, exclude_meta_fields=None):
    """Devuelve sólo la metadata de nivel catálogo."""
    exclude_meta_fields = exclude_meta_fields or []
    catalog_dict_copy = catalog.copy()
    del catalog_dict_copy["dataset"]

    for excluded_meta_field in exclude_meta_fields:
        catalog_dict_copy.pop(excluded_meta_field, None)

    return catalog_dict_copy


def _filter_dictionary(dictionary, filter_in=None, filter_out=None):
    if filter_in:
        # chequea que el objeto tenga las propiedades de filtro positivo
        for key, value in iteritems(filter_in):
            if dictionary.get(key) != value:
                return False

    if filter_out:
        # chequea que el objeto NO tenga las propiedades de filtro negativo
        for key, value in iteritems(filter_out):
            if dictionary.get(key) == value:
                return False

    return True
