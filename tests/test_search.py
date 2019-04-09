#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests para las funcionalidades de el módulo 'search'
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from functools import wraps
import unittest
import nose
import os
import io
import json

from six import text_type

from tests.context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")
RESULTS_DIR = os.path.join("tests", "results")


def pprint(result):
    print(text_type(json.dumps(
        result, indent=4, separators=(",", ": "),
        ensure_ascii=False
    )))


class SearchTestCase(unittest.TestCase):

    def load_expected_result():

        def case_decorator(test):
            case_filename = test.__name__.split("test_")[-1]

            @wraps(test)
            def decorated_test(*args, **kwargs):
                result_path = os.path.join(
                    RESULTS_DIR, case_filename + ".json")

                with io.open(result_path, encoding='utf8') as result_file:
                    expected_result = json.load(result_file)

                kwargs["expected_result"] = expected_result
                test(*args, **kwargs)

            return decorated_test

        return case_decorator

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        cls.catalog = cls.get_sample("full_data.json")
        cls.catalog_ts = cls.get_sample("time_series_data.json")

    @load_expected_result()
    def test_datasets(self, expected_result):
        datasets = pydatajson.search.get_datasets(self.catalog)
        pprint(datasets)
        self.assertEqual(expected_result, datasets)

    @load_expected_result()
    def test_distributions(self, expected_result):
        distributions = pydatajson.search.get_distributions(self.catalog)
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_fields(self, expected_result):
        fields = pydatajson.search.get_fields(self.catalog)
        pprint(fields)
        self.assertEqual(expected_result, fields)

    @load_expected_result()
    def test_time_series(self, expected_result):
        time_series = pydatajson.search.get_time_series(self.catalog_ts)
        pprint(time_series)
        self.assertEqual(expected_result, time_series)

    @load_expected_result()
    def test_datasets_filter_in(self, expected_result):
        datasets = pydatajson.search.get_datasets(
            self.catalog,
            {"dataset": {
                "description":
                "Datos correspondientes al Sistema de Contrataciones "
                "Electrónicas (Argentina Compra)"
            }}
        )
        pprint(datasets)
        self.assertEqual(expected_result, datasets)

    @load_expected_result()
    def test_distributions_filter_in(self, expected_result):
        distributions = pydatajson.search.get_distributions(
            self.catalog,
            {"distribution": {"byteSize": 5120}}
        )
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_fields_filter_in(self, expected_result):
        fields = pydatajson.search.get_fields(
            self.catalog, {"field": {"title": "procedimiento_id"}})
        pprint(fields)
        self.assertEqual(expected_result, fields)

    @load_expected_result()
    def test_datasets_filter_out(self, expected_result):
        datasets = pydatajson.search.get_datasets(
            self.catalog,
            filter_out={"dataset": {
                "description":
                "Datos correspondientes al Sistema de Contrataciones "
                "Electrónicas (Argentina Compra)"
            }}
        )
        pprint(datasets)
        self.assertEqual(expected_result, datasets)

    @load_expected_result()
    def test_distributions_filter_out(self, expected_result):
        distributions = pydatajson.search.get_distributions(
            self.catalog,
            filter_out={"dataset": {
                "description":
                "Datos correspondientes al Sistema de Contrataciones "
                "Electrónicas (Argentina Compra)"
            }}
        )
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_distributions_only_time_series(self, expected_result):
        distributions = pydatajson.search.get_distributions(
            self.catalog, only_time_series=True
        )
        pprint(distributions)
        self.assertEqual([], distributions)

        distributions = pydatajson.search.get_distributions(
            self.catalog_ts, only_time_series=True
        )
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_fields_filter_out(self, expected_result):
        fields = pydatajson.search.get_fields(
            self.catalog,
            filter_out={"dataset": {
                "description":
                "Datos correspondientes al Sistema de Contrataciones "
                "Electrónicas (Argentina Compra)"
            }}
        )
        pprint(fields)
        self.assertEqual(expected_result, fields)

    @load_expected_result()
    def test_datasets_meta_field(self, expected_result):
        datasets = pydatajson.search.get_datasets(
            self.catalog, meta_field="title"
        )
        pprint(datasets)
        self.assertEqual(expected_result, datasets)

    @load_expected_result()
    def test_distributions_meta_field(self, expected_result):
        distributions = pydatajson.search.get_distributions(
            self.catalog, meta_field="accessURL"
        )
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_fields_meta_field(self, expected_result):
        fields = pydatajson.search.get_fields(
            self.catalog, meta_field="type"
        )
        pprint(fields)
        self.assertEqual(expected_result, fields)

    @load_expected_result()
    def test_get_dataset(self, expected_result):
        dataset = pydatajson.search.get_dataset(
            self.catalog, "99db6631-d1c9-470b-a73e-c62daa32c777"
        )
        pprint(dataset)
        self.assertEqual(expected_result, dataset)

    @load_expected_result()
    def test_get_distribution(self, expected_result):
        distribution = pydatajson.search.get_distribution(
            self.catalog,
            title="Convocatorias abiertas durante el año 2015"
        )
        pprint(distribution)
        self.assertEqual(expected_result, distribution)

    @load_expected_result()
    def test_get_field(self, expected_result):
        field = pydatajson.search.get_field(
            self.catalog,
            title="procedimiento_id"
        )
        pprint(field)
        self.assertEqual(expected_result, field)

    @load_expected_result()
    def test_get_theme(self, expected_result):
        theme = pydatajson.search.get_theme(
            self.catalog,
            identifier="adjudicaciones"
        )
        pprint(theme)
        self.assertEqual(expected_result, theme)

    @load_expected_result()
    def test_get_distribution_of_dataset(self, expected_result):
        distribution = pydatajson.search.get_distribution(
            self.catalog,
            title="Convocatorias abiertas durante el año 2015",
            dataset_identifier="99db6631-d1c9-470b-a73e-c62daa32c420"
        )
        pprint(distribution)
        self.assertEqual(expected_result, distribution)

    def test_get_field_of_distribution(self):
        field = pydatajson.search.get_field(
            self.catalog,
            title="procedimiento_id",
            distribution_identifier="id_que_no_existe"
        )
        pprint(field)
        self.assertEqual(None, field)

    def test_get_field_location(self):
        field_location = pydatajson.search.get_field_location(
            self.catalog, identifier="proc12"
        )
        pprint(field_location)
        self.assertEqual(field_location["dataset_identifier"],
                         "99db6631-d1c9-470b-a73e-c62daa32c777")
        self.assertEqual(field_location["dataset_title"],
                         "Sistema de contrataciones electrónicas")
        self.assertEqual(field_location["distribution_identifier"], "1.1")
        self.assertEqual(field_location["distribution_title"],
                         "Convocatorias abiertas durante el año 2015")


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
