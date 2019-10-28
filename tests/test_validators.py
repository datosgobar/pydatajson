#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement

import json
import os.path
import unittest

import requests_mock
from requests import Timeout, ConnectionError

from pydatajson.validators \
    .consistent_distribution_fields_validator \
    import ConsistentDistributionFieldsValidator
from pydatajson.validators.distribution_urls_validator \
    import DistributionUrlsValidator
from pydatajson.validators.landing_pages_validator \
    import LandingPagesValidator
from pydatajson.validators.theme_ids_not_repeated_validator \
    import ThemeIdsNotRepeatedValidator
from pydatajson.validators.url_validator import UrlValidator

try:
    import mock
except ImportError:
    from unittest import mock

import pydatajson.constants

pydatajson.constants.CANT_THREADS_BROKEN_URL_VALIDATOR = 1


class ValidatorsTestCase(unittest.TestCase):
    SAMPLES_DIR = os.path.join("tests", "samples")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    def setUp(self):
        catalog_path = self.get_sample("full_data.json")
        self.catalog = json.load(open(catalog_path))
        self.test_url = "http://www.test.com/"
        self.cdf_validator = \
            ConsistentDistributionFieldsValidator(self.catalog)
        self.tinr_validator = \
            ThemeIdsNotRepeatedValidator(self.catalog)
        self.ddu_validator = \
            DistributionUrlsValidator(self.catalog, True, 1)
        self.lp_validator = \
            LandingPagesValidator(self.catalog, True, 1)

    @requests_mock.Mocker()
    def test_is_working_url_valid_url(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 1)
        req_mock.head(self.test_url)
        self.assertEqual(
            (True, 200), url_validator.is_working_url(self.test_url))

    @requests_mock.Mocker()
    def test_is_working_url_invalid_url(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 1)
        req_mock.head(self.test_url, status_code=400)
        self.assertEqual(
            (False, 400), url_validator.is_working_url(self.test_url))

    @requests_mock.Mocker()
    def test_is_working_url_too_many_requests_response(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 1)
        too_many_request_status_code = 429
        req_mock.head(self.test_url,
                      status_code=too_many_request_status_code)
        self.assertEqual(
            (True, too_many_request_status_code),
            url_validator.is_working_url(self.test_url))

    @requests_mock.Mocker()
    def test_is_working_url_url_with_exception(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 1)
        req_mock.head(self.test_url, exc=ConnectionError)
        self.assertEqual(
            (False, None), url_validator.is_working_url(self.test_url))

    @requests_mock.Mocker()
    def test_is_working_url_url_with_timeout(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 1)
        req_mock.head(self.test_url, exc=Timeout)
        self.assertEqual(
            (False, 408), url_validator.is_working_url(self.test_url))

    def test_is_working_url_malformed_values(self):
        url_validator = UrlValidator(self.catalog, True, 1)
        self.assertEqual(
            (False, None), url_validator.is_working_url('malformed_value'))
        self.assertEqual(
            (False, None), url_validator.is_working_url(''))
        self.assertEqual(
            (False, None), url_validator.is_working_url(None))

    def test_valid_landing_page_validator(self):
        lp_validator = \
            LandingPagesValidator(self.catalog, True, 1)
        with mock.patch(
                'pydatajson'
                '.validators'
                '.url_validator.UrlValidator.is_working_url',
                return_value=(True, 200)):
            res = lp_validator.validate()
            self.assertEqual(0, len(list(res)))

    def test_invalid_landing_page_validator(self):
        lp_validator = \
            LandingPagesValidator(self.catalog, True, 1)
        with mock.patch(
                'pydatajson'
                '.validators'
                '.url_validator.UrlValidator.is_working_url',
                return_value=(False, 400)):
            res = lp_validator.validate()
            self.assertNotEqual(0, len(list(res)))

    def test_valid_distribution_url_validator(self):
        ddu_validator = \
            DistributionUrlsValidator(self.catalog, True, 1)
        with mock.patch(
                'pydatajson'
                '.validators'
                '.url_validator.UrlValidator.is_working_url',
                return_value=(True, 200)):
            res = ddu_validator.validate()
            self.assertEqual(0, len(list(res)))

    def test_invalid_distribution_url_validator(self):
        ddu_validator = \
            DistributionUrlsValidator(self.catalog, True, 1)
        with mock.patch(
                'pydatajson'
                '.validators'
                '.url_validator.UrlValidator.is_working_url',
                return_value=(False, 400)):
            res = ddu_validator.validate()
            self.assertNotEqual(0, len(list(res)))

    def test_valid_consistent_distribution_fields_validator(self):
        cdf_validator = \
            ConsistentDistributionFieldsValidator(self.catalog)
        with mock.patch(
                'pydatajson.validators.'
                'consistent_distribution_fields_validator.'
                'ConsistentDistributionFieldsValidator'
                '._format_matches_extension',
                return_value=True):
            res = cdf_validator.validate()
            self.assertEqual(0, len(list(res)))

    def test_invalid_consistent_distribution_fields_validator(self):
        cdf_validator = \
            ConsistentDistributionFieldsValidator(self.catalog)
        with mock.patch(
                'pydatajson.validators.'
                'consistent_distribution_fields_validator.'
                'ConsistentDistributionFieldsValidator'
                '._format_matches_extension',
                return_value=False):
            res = cdf_validator.validate()
            self.assertNotEqual(0, len(list(res)))

    def test_valid_theme_ids_not_repeated_validator(self):
        tinr_validator = \
            ThemeIdsNotRepeatedValidator(self.catalog)
        with mock.patch(
                'pydatajson.validators.'
                'theme_ids_not_repeated_validator.'
                'ThemeIdsNotRepeatedValidator'
                '._find_dups',
                return_value=[]):
            res = tinr_validator.validate()
            self.assertEqual(0, len(list(res)))

    def test_invalid_theme_ids_not_repeated_validator(self):
        tinr_validator = \
            ThemeIdsNotRepeatedValidator(self.catalog)
        with mock.patch(
                'pydatajson.validators.'
                'theme_ids_not_repeated_validator.'
                'ThemeIdsNotRepeatedValidator'
                '._find_dups',
                return_value=['convocatorias']):
            res = tinr_validator.validate()
            self.assertNotEqual(0, len(list(res)))

    @requests_mock.Mocker()
    def test_url_check_timeout(self, req_mock):
        url_validator = UrlValidator(self.catalog, True, 100)
        req_mock.head(self.test_url)
        url_validator.is_working_url(self.test_url)
        self.assertEqual(100, req_mock.request_history[0].timeout)
