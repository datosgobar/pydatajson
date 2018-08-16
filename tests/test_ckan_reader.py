# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import unittest

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from pydatajson.core import DataJson
from pydatajson.ckan_utils import map_dataset_to_package, map_theme_to_group

from pydatajson.ckan_reader import read_ckan_catalog

SAMPLES_DIR = os.path.join("tests", "samples")


def get_sample(sample_filename):
    return os.path.join(SAMPLES_DIR, sample_filename)


class MockPortal(object):

    def __init__(self, sample):
        self.data_json = DataJson(get_sample(sample))

    def call_action(self, action, data_dict=None, requests_kwargs=None):
        return getattr(self, action)(data_dict)

    def status_show(self, data_dict):
        return {'site_title': self.data_json['title'],
                'site_description': self.data_json['description'],
                'error_emails_to': self.data_json['publisher']['mbox']}

    def package_list(self, data_dict):
        return [dataset['title'] for dataset in self.data_json.datasets]

    def group_list(self, data_dict):
        return [theme['label'] for theme in self.data_json['themeTaxonomy']]

    def package_show(self, data_dict):
        catalog = self.data_json
        dataset = catalog.get_dataset(title=data_dict['id'])
        package = map_dataset_to_package(
            catalog,
            dataset,
            'owner',
            demote_superThemes=False,
            demote_themes=False)
        for resource in package['resources']:
            resource['package_id'] = package['id']
        return package

    def group_show(self, data_dict):
        catalog = self.data_json
        theme = catalog.get_theme(label=data_dict['id'])
        return map_theme_to_group(theme)


class CKANReaderTestCase(unittest.TestCase):

    @classmethod
    @patch('pydatajson.ckan_reader.RemoteCKAN', new=MockPortal)
    def setUpClass(cls):
        cls.expected_dj = DataJson(get_sample('full_data.json'))
        cls.dj = DataJson(read_ckan_catalog('full_data.json'))

    def test_read_ckan_catalog_attributes(self):
        self.assertEqual(self.expected_dj['title'], self.dj['title'])
        self.assertEqual(
            self.expected_dj['description'],
            self.dj['description'])
        self.assertEqual(
            self.expected_dj['superThemeTaxonomy'],
            self.dj['superThemeTaxonomy'])
        self.assertEqual(
            self.expected_dj['publisher']['mbox'],
            self.dj['publisher']['mbox'])

    def test_read_ckan_catalog_theme_taxonomy(self):
        self.assertEqual(len(self.expected_dj['themeTaxonomy']),
                         len(self.dj['themeTaxonomy']))
        for expected_theme, theme in zip(
                self.expected_dj['themeTaxonomy'], self.dj['themeTaxonomy']):
            self.assertDictEqual(expected_theme, theme)

    def test_read_ckan_dataset_attributes(self):
        self.assertEqual(len(self.expected_dj.datasets),
                         len(self.dj.datasets))
        for expected_dataset, dataset in zip(
                self.expected_dj.datasets, self.dj.datasets):
            attributes = ['description', 'identifier', 'title', 'landingPage']
            for attribute in attributes:
                self.assertEqual(
                    expected_dataset[attribute],
                    dataset[attribute])
            self.assertDictEqual(
                expected_dataset['contactPoint'],
                dataset['contactPoint'])
            self.assertDictEqual(
                expected_dataset['publisher'],
                dataset['publisher'])
            self.assertSetEqual(
                set(expected_dataset['keyword']), set(dataset['keyword']))

    def test_read_ckan_distribution_attributes(self):
        self.assertEqual(len(self.expected_dj.distributions),
                         len(self.dj.distributions))
        for expected_dataset, distributions in zip(
                self.expected_dj.distributions, self.dj.distributions):
            attributes = ['mediaType', 'byteSize', 'identifier', 'description',
                          'format', 'title', 'downloadURL']
            for attribute in attributes:
                self.assertEqual(
                    expected_dataset[attribute],
                    distributions[attribute])

    def test_read_ckan_field_attributes(self):
        self.assertEqual(len(self.expected_dj.fields),
                         len(self.dj.fields))
        for expected_field, field in zip(
                self.expected_dj.fields, self.dj.fields):
            self.assertDictEqual(expected_field, field)
