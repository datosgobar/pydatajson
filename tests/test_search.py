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

from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")
RESULTS_DIR = os.path.join("tests", "results")


def pprint(result):
    print(unicode(json.dumps(
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

    @load_expected_result()
    def test_iter_datasets(self, expected_result):
        datasets = list(pydatajson.search.iter_datasets(self.catalog))
        pprint(datasets)
        self.assertEqual(expected_result, datasets)

    @load_expected_result()
    def test_iter_distributions(self, expected_result):
        distributions = list(
            pydatajson.search.iter_distributions(self.catalog))
        pprint(distributions)
        self.assertEqual(expected_result, distributions)

    @load_expected_result()
    def test_iter_fields(self, expected_result):
        fields = list(pydatajson.search.iter_fields(self.catalog))
        pprint(fields)
        self.assertEqual(expected_result, fields)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
