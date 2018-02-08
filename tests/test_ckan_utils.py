import unittest
import os
import re
import json
from dateutil import parser, tz
from .context import pydatajson
from pydatajson.ckan_utils import map_dataset_to_package, map_distributions_to_resources, convert_iso_string_to_utc

SAMPLES_DIR = os.path.join("tests", "samples")


class DatasetConversionTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get('identifier', re.sub(r'[^a-z-_]+', '', cls.catalog['title'].lower()))
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset.get('identifier')
        cls.distributions = cls.dataset['distribution']

    def test_replicated_plain_attributes_are_corrext(self):
        package = map_dataset_to_package(self.dataset, self.catalog_id)
        plain_replicated_attributes = [('title', 'title'),
                                       ('notes', 'description'),
                                       ('url', 'landingPage')]
        for fst, snd in plain_replicated_attributes:
            self.assertEqual(self.dataset.get(snd), package.get(fst))
        self.assertEqual(self.catalog_id+'_'+self.dataset_id, package['id'])

    def test_dataset_nested_replicated_attributes_stay_the_same(self):
        package = map_dataset_to_package(self.dataset, self.catalog_id)
        contact_point_nested = [('maintainer', 'fn'),
                                ('maintainer_email', 'hasEmail')]
        for fst, snd in contact_point_nested:
            self.assertEqual(self.dataset.get('contactPoint', {}).get(snd), package.get(fst))
        publisher_nested = [('author', 'name'),
                            ('author_email', 'mbox')]
        for fst, snd in publisher_nested:
            self.assertEqual(self.dataset.get('publisher').get(snd), package.get(fst))

    def test_dataset_array_attributes_are_correct(self):
        package = map_dataset_to_package(self.dataset, self.catalog_id)
        groups = [group['name'] for group in package.get('groups', [])]
        super_themes = [re.sub(r'[^a-z-_]+', '', s_theme.lower()) for s_theme in self.dataset.get('superTheme')]
        try:
            self.assertItemsEqual(super_themes, groups)
        except AttributeError:
            self.assertCountEqual(super_themes, groups)

        tags = [tag['name'] for tag in package['tags']]
        themes_and_keywords = self.dataset.get('theme', []) + self.dataset.get('keyword', [])
        try:
            self.assertItemsEqual(themes_and_keywords, tags)
        except AttributeError:
            self.assertCountEqual(themes_and_keywords, tags)

    def test_dataset_extra_attributes_are_correct(self):
        package = map_dataset_to_package(self.dataset, self.catalog_id)
#       extras are included in dataset
        if package['extras']:
            for extra in package['extras']:
                if extra['key'] == 'super_theme':
                    dataset_value = self.dataset['superTheme']
                else:
                    dataset_value = self.dataset[extra['key']]
                if type(dataset_value) is list:
                    extra_value = json.loads(extra['value'])
                    try:
                        self.assertItemsEqual(dataset_value, extra_value)
                    except AttributeError:
                        self.assertCountEqual(dataset_value, extra_value)
                else:
                    extra_value = extra['value']
                    self.assertEqual(dataset_value, extra_value)

    def test_dataset_extra_attributes_are_complete(self):
        package = map_dataset_to_package(self.dataset, self.catalog_id)
#       dataset attributes are included in extras
        extra_attrs = ['issued', 'modified', 'accrualPeriodicity', 'temporal', 'language', 'spatial']
        for key in extra_attrs:
            value = self.dataset.get(key)
            if value:
                if type(value) is list:
                    value = json.dumps(value)
                resulting_dict = {'key': key, 'value': value}
                self.assertTrue(resulting_dict in package['extras'])

        self.assertTrue({'key': 'super_theme', 'value': json.dumps(self.dataset['superTheme'])})

    def test_resources_replicated_attributes_stay_the_same(self):
        resources = map_distributions_to_resources(self.distributions, self.catalog_id+'_'+self.dataset_id)
        for resource in resources:
            distribution = next(x for x in self.dataset['distribution'] if x['title'] == resource['name'])
            replicated_attributes = [('url', 'downloadURL'),
                                     ('mimetype', 'mediaType'),
                                     ('description', 'description'),
                                     ('format', 'format'),
                                     ('size', 'byteSize')]
            for fst, snd in replicated_attributes:
                if distribution.get(snd):
                    self.assertEqual(distribution.get(snd), resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))
            self.assertEqual(self.catalog_id+'_'+self.dataset_id+'_'+distribution['identifier'], resource['id'])

    def test_resources_transformed_attributes_are_correct(self):
        resources = map_distributions_to_resources(self.distributions, self.catalog_id+'_'+self.dataset_id)
        for resource in resources:
            distribution = next(x for x in self.dataset['distribution'] if x['title'] == resource['name'])
            time_attributes = [('created', 'issued'), ('last_modified', 'modified')]
            for fst, snd in time_attributes:
                if distribution.get(snd):
                    dist_time = parser.parse(distribution.get(snd)).astimezone(tz.tzutc())
                    dist_time = dist_time.replace(tzinfo=None).isoformat()
                    self.assertEqual(dist_time, resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))

    def test_resources_extra_attributes_are_created_correctly(self):
        resources = map_distributions_to_resources(self.distributions, self.catalog_id+'_'+self.dataset_id)
        for resource in resources:
            distribution = next(x for x in self.dataset['distribution'] if x['title'] == resource['name'])
            self.assertEqual(distribution.get('accessURL'), resource.get('accessURL'))
            dist_fields = distribution.get('field')
            if dist_fields:
                res_fields = json.loads(resource.get('attributesDescription'))
                for dist_field, res_field in zip(dist_fields, res_fields):
                    self.assertDictEqual(dist_field, res_field)
            else:
                self.assertIsNone(resource.get('attributesDescription'))


class DatetimeConversionTests(unittest.TestCase):

    def test_timezones_are_handled_correctly(self):
        buenos_aires = '2018-01-29T14:14:09.291510-03:00'
        buenos_aires_utc = '2018-01-29T17:14:09.291510'
        res = convert_iso_string_to_utc(buenos_aires)
        self.assertEqual(buenos_aires_utc, res)

        moscow = '2018-01-29T14:14:09.291510+03:00'
        moscow_utc = '2018-01-29T11:14:09.291510'
        res = convert_iso_string_to_utc(moscow)
        self.assertEqual(moscow_utc, res)

    def test_dates_change_correctly(self):
        buenos_aires = '2018-01-29T22:14:09.291510-03:00'
        buenos_aires_utc = '2018-01-30T01:14:09.291510'
        res = convert_iso_string_to_utc(buenos_aires)
        self.assertEqual(buenos_aires_utc, res)

        moscow = '2018-01-29T01:14:09.291510+03:00'
        moscow_utc = '2018-01-28T22:14:09.291510'
        res = convert_iso_string_to_utc(moscow)
        self.assertEqual(moscow_utc, res)

    def test_datetimes_without_timezones_stay_the_same(self):
        no_timezone_string = '2018-01-29T22:14:09.291510'
        res = convert_iso_string_to_utc(no_timezone_string)
        self.assertEqual(no_timezone_string, res)

    def test_datetimes_without_microseconds_are_handled_correctly(self):
        buenos_aires = '2018-01-29T14:14:09-03:00'
        buenos_aires_utc = '2018-01-29T17:14:09'
        res = convert_iso_string_to_utc(buenos_aires)
        self.assertEqual(buenos_aires_utc, res)

        moscow = '2018-01-29T14:14:09+03:00'
        moscow_utc = '2018-01-29T11:14:09'
        res = convert_iso_string_to_utc(moscow)
        self.assertEqual(moscow_utc, res)

    def test_datetimes_without_seconds_are_handled_correctly(self):
        buenos_aires = '2018-01-29T14:14-03:00'
        buenos_aires_utc = '2018-01-29T17:14:00'
        res = convert_iso_string_to_utc(buenos_aires)
        self.assertEqual(buenos_aires_utc, res)

        moscow = '2018-01-29T14:14+03:00'
        moscow_utc = '2018-01-29T11:14:00'
        res = convert_iso_string_to_utc(moscow)
        self.assertEqual(moscow_utc, res)

    def test_dates_stay_the_same(self):
        date = '2018-01-29'
        res = convert_iso_string_to_utc(date)
        self.assertEqual(date, res)
