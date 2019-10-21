#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import requests_mock
from nose.tools import assert_true, assert_false
from requests import Timeout

import pydatajson
from .support.decorators import RESULTS_DIR


class TestDataJsonTestCase(object):
    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = RESULTS_DIR
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    def setUp(self):
        self.dj = pydatajson.DataJson(self.get_sample("full_data.json"))
        self.catalog = pydatajson.readers.read_catalog(
            self.get_sample("full_data.json"))
        self.maxDiff = None
        self.longMessage = True
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.requests_mock.get(requests_mock.ANY, real_http=True)
        self.requests_mock.head(requests_mock.ANY, status_code=200)

    def tearDown(self):
        del self.dj
        self.requests_mock.stop()

    def test_urls_with_status_code_200_is_valid(self):
        assert_true(self.dj.is_valid_catalog(broken_links=True))

    def test_urls_with_status_code_203_is_valid(self):
        self.requests_mock.head(requests_mock.ANY, status_code=203)
        assert_true(self.dj.is_valid_catalog(broken_links=True))

    def test_urls_with_status_code_302_is_valid(self):
        self.requests_mock.head(requests_mock.ANY, status_code=302)
        assert_true(self.dj.is_valid_catalog(broken_links=True))

    def test_urls_with_invalid_status_codes_are_not_valid(self):
        self.requests_mock.head(requests_mock.ANY, status_code=404)
        assert_false(self.dj.is_valid_catalog(broken_links=True))

    def test_throws_exception(self):
        self.requests_mock.head(requests_mock.ANY, exc=Timeout)
        assert_false(self.dj.is_valid_catalog(broken_links=True))

    def test_validation_without_flag_does_not_validate_urls(self):
        assert_true(self.dj.is_valid_catalog())

    def test_validation_with_flag_does_validate_urls(self):
        self.requests_mock.head(requests_mock.ANY, status_code=404)
        assert_false(self.dj.is_valid_catalog(broken_links=True))
