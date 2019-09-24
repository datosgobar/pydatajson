#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'indicators' de Pydatajson

Contiene los métodos para monitorear y generar indicadores de un catálogo o de
una red de catálogos.
"""

from __future__ import print_function, absolute_import
from __future__ import unicode_literals, with_statement

from pydatajson.readers import read_catalog
from pydatajson.helpers import datasets_equal, filter_by_likely_publisher
from pydatajson.helpers import title_in_dataset_list


class FederationIndicatorsGenerator(object):
    def __init__(self, central_catalog, catalog, id_based=False):
        if id_based:
            calculator = IdBasedIndicatorCalculator
        else:
            calculator = TitleBasedIndicatorCalculator

        self.calculator = calculator(central_catalog, catalog)

    def datasets_federados(self):
        return self.calculator.datasets_federados()

    def datasets_federados_cant(self):
        return len(self.calculator.datasets_federados())

    def datasets_no_federados(self):
        return self.calculator.datasets_no_federados()

    def datasets_no_federados_cant(self):
        return len(self.calculator.datasets_no_federados())

    def distribuciones_federadas_cant(self):
        return self.calculator.distribuciones_federadas_cant()

    def datasets_federados_eliminados(self):
        return self.calculator.datasets_federados_eliminados()

    def datasets_federados_eliminados_cant(self):
        return len(self.datasets_federados_eliminados())

    def datasets_federados_pct(self):
        federados = self.datasets_federados_cant()
        no_federados = self.datasets_no_federados_cant()
        if federados or no_federados:  # Evita división por 0
            federados_pct = float(federados) / (federados + no_federados)
        else:
            federados_pct = 0
        return round(federados_pct, 4)


class AbstractCalculator(object):
    def __init__(self, central_catalog, catalog):
        self.central_catalog = read_catalog(central_catalog)
        self.catalog = read_catalog(catalog)
        self.filtered_central = filter_by_likely_publisher(
            self.central_catalog.get('dataset', []),
            self.catalog.get('dataset', []))

    def datasets_federados(self):
        raise NotImplementedError

    def datasets_no_federados(self):
        raise NotImplementedError

    def datasets_federados_eliminados(self):
        raise NotImplementedError

    def distribuciones_federadas_cant(self):
        raise NotImplementedError


class IdBasedIndicatorCalculator(AbstractCalculator):
    def __init__(self, central_catalog, catalog):
        super(IdBasedIndicatorCalculator, self).__init__(central_catalog,
                                                         catalog)
        self.central_datasets = {ds['identifier'] for ds in
                                 self.central_catalog.get('dataset', [])}
        self.catalog_datasets = {catalog['identifier'] + '_' + ds['identifier']
                                 for ds in catalog.get('dataset', [])}
        self.federated_ids = self.catalog_datasets & self.central_datasets

    def distribuciones_federadas_cant(self):
        return sum([len(ds.get('distribution', [])) for ds in
                    self.central_catalog.get('dataset', []) if
                    ds['identifier'] in self.federated_ids])

    def datasets_federados_eliminados(self):
        return [(ds.get('title'), ds.get('landingPage')) for ds in
                self.filtered_central if ds['identifier'] not in
                self.federated_ids]

    def datasets_no_federados(self):
        return [(ds.get('title'), ds.get('landingPage')) for
                ds in self.catalog.get('dataset', []) if
                self.catalog['identifier'] + '_' + ds['identifier']
                not in self.federated_ids]

    def datasets_federados(self):
        return [(ds.get('title'), ds.get('landingPage')) for
                ds in self.catalog.get('dataset', []) if
                self.catalog['identifier'] + '_' + ds['identifier']
                in self.federated_ids]


class TitleBasedIndicatorCalculator(AbstractCalculator):

    def __init__(self, central_catalog, catalog):
        super(TitleBasedIndicatorCalculator, self).__init__(central_catalog,
                                                            catalog)

    def datasets_federados(self):
        datasets_federados = []
        for dataset in self.catalog.get('dataset', []):
            for central_dataset in self.central_catalog.get('dataset', []):
                if (datasets_equal(dataset, central_dataset) and not
                        title_in_dataset_list(dataset, datasets_federados)):
                    datasets_federados.append((dataset.get('title'),
                                               dataset.get('landingPage')))
        return datasets_federados

    def datasets_no_federados(self):
        datasets_federados = self.datasets_federados()
        datasets_no_federados = []
        for dataset in self.catalog.get('dataset', []):
            if not title_in_dataset_list(dataset, datasets_federados):
                datasets_no_federados.append((dataset.get('title'),
                                              dataset.get('landingPage')))
        return datasets_no_federados

    def datasets_federados_eliminados(self):
        datasets_federados = self.datasets_federados()
        datasets_federados_eliminados = []
        for central_dataset in self.filtered_central:
            if not title_in_dataset_list(central_dataset, datasets_federados):
                    datasets_federados_eliminados.append(
                        (central_dataset.get('title'),
                         central_dataset.get('landingPage'))
                    )
        return datasets_federados_eliminados

    def distribuciones_federadas_cant(self):
        datasets_federados = self.datasets_federados()
        distribuciones_federadas = 0
        for dataset in self.catalog.get('dataset', []):
            if title_in_dataset_list(dataset, datasets_federados):
                distribuciones_federadas += len(dataset['distribution'])
        return distribuciones_federadas
