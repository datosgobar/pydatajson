# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import unittest

from pydatajson.ckan_utils import *
from pydatajson.helpers import title_to_name
from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")


class DatasetConversionTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get(
            'identifier', title_to_name(
                cls.catalog['title']))
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset.get('identifier')
        cls.distributions = cls.dataset['distribution']

    def test_catalog_id_is_prepended_to_dataset_id_and_name_if_passed(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
        self.assertEqual(
            self.catalog_id +
            '_' +
            self.dataset_id,
            package['id'])
        self.assertEqual(
            title_to_name(
                self.catalog_id +
                '-' +
                self.dataset['title']),
            package['name'])

    def test_dataset_id_and_name_are_preserved_if_catalog_id_is_not_passed(
            self):
        package = map_dataset_to_package(self.catalog, self.dataset, 'owner')
        self.assertEqual(self.dataset_id, package['id'])
        self.assertEqual(title_to_name(self.dataset['title']), package['name'])

    def test_replicated_plain_attributes_are_corrext(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
        plain_replicated_attributes = [('notes', 'description'),
                                       ('url', 'landingPage')]
        for fst, snd in plain_replicated_attributes:
            self.assertEqual(self.dataset.get(snd), package.get(fst))
        self.assertEqual('owner', package['owner_org'])

    def test_dataset_nested_replicated_attributes_stay_the_same(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
        contact_point_nested = [('maintainer', 'fn'),
                                ('maintainer_email', 'hasEmail')]
        for fst, snd in contact_point_nested:
            self.assertEqual(
                self.dataset.get(
                    'contactPoint',
                    {}).get(snd),
                package.get(fst))
        publisher_nested = [('author', 'name'),
                            ('author_email', 'mbox')]
        for fst, snd in publisher_nested:
            self.assertEqual(
                self.dataset.get('publisher').get(snd),
                package.get(fst))

    def test_dataset_array_attributes_are_correct(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
        groups = [group['name'] for group in package.get('groups', [])]
        super_themes = [title_to_name(s_theme.lower())
                        for s_theme in self.dataset.get('superTheme')]
        try:
            self.assertItemsEqual(super_themes, groups)
        except AttributeError:
            self.assertCountEqual(super_themes, groups)

        tags = [tag['name'] for tag in package['tags']]
        keywords = self.dataset.get('keyword', [])

        themes = self.dataset.get('theme', [])
        theme_labels = []
        for theme in themes:
            label = self.catalog.get_theme(identifier=theme)['label']
            label = re.sub(r'[^\w .-]+', '', label, flags=re.UNICODE)
            theme_labels.append(label)

        try:
            self.assertItemsEqual(keywords + theme_labels, tags)
        except AttributeError:
            self.assertCountEqual(keywords + theme_labels, tags)

    def test_themes_are_preserved_if_not_demoted(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id,
            demote_themes=False)
        groups = [group['name'] for group in package.get('groups', [])]
        super_themes = [title_to_name(s_theme.lower())
                        for s_theme in self.dataset.get('superTheme')]
        themes = self.dataset.get('theme', [])
        tags = [tag['name'] for tag in package['tags']]
        keywords = self.dataset.get('keyword', [])

        try:
            self.assertItemsEqual(super_themes + themes, groups)
        except AttributeError:
            self.assertCountEqual(super_themes + themes, groups)
        try:
            self.assertItemsEqual(keywords, tags)
        except AttributeError:
            self.assertCountEqual(keywords, tags)

    def test_superThemes_dont_impact_groups_if_not_demoted(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id,
            demote_superThemes=False)
        groups = [group['name'] for group in package.get('groups', [])]
        tags = [tag['name'] for tag in package['tags']]
        keywords = self.dataset.get('keyword', [])
        themes = self.dataset.get('theme', [])
        theme_labels = []
        for theme in themes:
            label = self.catalog.get_theme(identifier=theme)['label']
            label = re.sub(r'[^\wá-úÁ-ÚñÑ .-]+', '', label, flags=re.UNICODE)
            theme_labels.append(label)
        try:
            self.assertItemsEqual([], groups)
        except AttributeError:
            self.assertCountEqual([], groups)
        try:
            self.assertItemsEqual(keywords + theme_labels, tags)
        except AttributeError:
            self.assertCountEqual(keywords + theme_labels, tags)

    def test_preserve_themes_and_superThemes(self):
        package = map_dataset_to_package(self.catalog, self.dataset, 'owner',
                                         self.catalog_id, False, False)
        groups = [group['name'] for group in package.get('groups', [])]
        tags = [tag['name'] for tag in package['tags']]
        keywords = self.dataset.get('keyword', [])
        themes = self.dataset.get('theme', [])
        try:
            self.assertItemsEqual(themes, groups)
        except AttributeError:
            self.assertCountEqual(themes, groups)
        try:
            self.assertItemsEqual(keywords, tags)
        except AttributeError:
            self.assertCountEqual(keywords, tags)

    def test_dataset_extra_attributes_are_correct(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
#       extras are included in dataset
        if package['extras']:
            for extra in package['extras']:
                dataset_value = self.dataset[extra['key']]
                if isinstance(dataset_value, list):
                    extra_value = json.loads(extra['value'])
                    try:
                        self.assertItemsEqual(dataset_value, extra_value)
                    except AttributeError:
                        self.assertCountEqual(dataset_value, extra_value)
                else:
                    extra_value = extra['value']
                    self.assertEqual(dataset_value, extra_value)

    def test_dataset_extra_attributes_are_complete(self):
        package = map_dataset_to_package(
            self.catalog,
            self.dataset,
            'owner',
            catalog_id=self.catalog_id)
        #       dataset attributes are included in extras
        extra_attrs = [
            'issued',
            'modified',
            'accrualPeriodicity',
            'temporal',
            'language',
            'spatial',
            'superTheme']
        for key in extra_attrs:
            value = self.dataset.get(key)
            if value:
                if isinstance(value, list):
                    value = json.dumps(value)
                resulting_dict = {'key': key, 'value': value}
                self.assertTrue(resulting_dict in package['extras'])

    def test_catalog_id_is_prefixed_in_resource_id_if_passed(self):
        resources = map_distributions_to_resources(
            self.distributions, self.catalog_id)
        for resource in resources:
            distribution = next(
                x for x in self.dataset['distribution'] if
                x['title'] == resource['name'])
            self.assertEqual(
                self.catalog_id +
                '_' +
                distribution['identifier'],
                resource['id'])

    def test_resource_id_is_preserved_if_catalog_id_is_not_passed(self):
        resources = map_distributions_to_resources(self.distributions)
        for resource in resources:
            distribution = next(
                x for x in self.dataset['distribution'] if
                x['title'] == resource['name'])
            self.assertEqual(distribution['identifier'], resource['id'])

    def test_resources_replicated_attributes_stay_the_same(self):
        resources = map_distributions_to_resources(
            self.distributions, self.catalog_id)
        for resource in resources:
            distribution = next(
                x for x in self.dataset['distribution'] if
                x['title'] == resource['name'])
            replicated_attributes = [('url', 'downloadURL'),
                                     ('mimetype', 'mediaType'),
                                     ('description', 'description'),
                                     ('format', 'format'),
                                     ('size', 'byteSize'),
                                     ('fileName', 'fileName'),
                                     ('resource_type', 'type')]
            for fst, snd in replicated_attributes:
                if distribution.get(snd):
                    self.assertEqual(distribution.get(snd), resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))

    def test_resources_transformed_attributes_are_correct(self):
        resources = map_distributions_to_resources(
            self.distributions, self.catalog_id + '_' + self.dataset_id)
        for resource in resources:
            distribution = next(
                x for x in self.dataset['distribution'] if
                x['title'] == resource['name'])
            time_attributes = [
                ('created', 'issued'), ('last_modified', 'modified')]
            for fst, snd in time_attributes:
                if distribution.get(snd):
                    dist_time = parser.parse(distribution.get(snd)) \
                        .replace(tzinfo=None)
                    self.assertEqual(dist_time.isoformat(), resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))

    def test_resources_extra_attributes_are_created_correctly(self):
        resources = map_distributions_to_resources(
            self.distributions, self.catalog_id + '_' + self.dataset_id)
        for resource in resources:
            distribution = next(
                x for x in self.dataset['distribution'] if
                x['title'] == resource['name'])
            self.assertEqual(
                distribution.get('accessURL'),
                resource.get('accessURL'))
            dist_fields = distribution.get('field')
            if dist_fields:
                res_fields = json.loads(resource.get('attributesDescription'))
                for dist_field, res_field in zip(dist_fields, res_fields):
                    self.assertDictEqual(dist_field, res_field)
            else:
                self.assertIsNone(resource.get('attributesDescription'))


class ThemeConversionTests(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.theme = catalog.get_theme(identifier='adjudicaciones')

    def test_all_attributes_are_replicated_if_present(self):
        group = map_theme_to_group(self.theme)
        self.assertEqual('adjudicaciones', group['name'])
        self.assertEqual('Adjudicaciones', group['title'])
        self.assertEqual(
            'Datasets sobre licitaciones adjudicadas.',
            group['description'])

    def test_label_is_used_as_name_if_id_not_present(self):
        missing_id = dict(self.theme)
        missing_id['label'] = u'#Will be used as name#'
        missing_id.pop('id')
        group = map_theme_to_group(missing_id)
        self.assertEqual('will-be-used-as-name', group['name'])
        self.assertEqual('#Will be used as name#', group['title'])
        self.assertEqual(
            'Datasets sobre licitaciones adjudicadas.',
            group['description'])

    def test_theme_missing_label(self):
        missing_label = dict(self.theme)
        missing_label.pop('label')
        group = map_theme_to_group(missing_label)
        self.assertEqual('adjudicaciones', group['name'])
        self.assertIsNone(group.get('title'))
        self.assertEqual(
            'Datasets sobre licitaciones adjudicadas.',
            group['description'])

    def test_theme_missing_description(self):
        missing_description = dict(self.theme)
        missing_description.pop('description')
        group = map_theme_to_group(missing_description)
        self.assertEqual('adjudicaciones', group['name'])
        self.assertEqual('Adjudicaciones', group['title'])
        self.assertIsNone(group['description'])

    def test_id_special_characters_are_removed(self):
        special_char_id = dict(self.theme)
        special_char_id['id'] = u'#Théme& $id?'
        group = map_theme_to_group(special_char_id)
        self.assertEqual('theme-id', group['name'])
        self.assertEqual('Adjudicaciones', group['title'])
        self.assertEqual(
            'Datasets sobre licitaciones adjudicadas.',
            group['description'])


class DatetimeConversionTests(unittest.TestCase):
    dates = {
        'tz_bs_as': 'America/Buenos_Aires',  # GMT-3
        'tz_new_york': 'America/New_York',  # GMT-4
        'tz_london': 'Europe/London',  # GMT+1
    }

    def test_timezone_is_set_to_default_if_none_given(self):
        date = '2018-01-29T17:14:09.291510'
        expected_date = '2018-01-29T17:14:09.291510'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_maintained_if_given(self):
        date = '2018-01-29T14:14:09.291510+03:00'
        expected_date = '2018-01-29T08:14:09.291510'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_is_set_to_default_if_none_given_without_ms(self):
        date = '2018-01-29T17:14:09'
        expected_date = '2018-01-29T17:14:09'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_maintained_if_given_without_ms(self):
        date = '2018-01-29T14:14:09-06:00'
        expected_date = '2018-01-29T17:14:09'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_is_set_to_default_if_none_given_without_seconds(self):
        date = '2018-01-29T17:14'
        expected_date = '2018-01-29T17:14:00'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_maintained_if_given_without_seconds(self):
        date = '2018-01-29T14:14+04:00'
        expected_date = '2018-01-29T07:14:00'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_is_set_to_default_if_none_given_without_time(self):
        date = '2018-01-29'
        expected_date = '2018-01-29T00:00:00'
        res = convert_iso_string_to_dst_timezone(date)
        self.assertEqual(res, expected_date)

    def test_timezone_is_set_to_dst_tz_with_default_origin_tz(self):
        date = '2018-06-29T17:14:09.291510'
        expected_date_bs_as = '2018-06-29T17:14:09.291510'
        expected_date_new_york = '2018-06-29T16:14:09.291510'
        expected_date_london = '2018-06-29T21:14:09.291510'

        res_bs_as = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_bs_as']
        )
        res_new_york = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_new_york']
        )
        res_london = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_london']
        )

        self.assertEqual(expected_date_bs_as, res_bs_as)
        self.assertEqual(expected_date_new_york, res_new_york)
        self.assertEqual(expected_date_london, res_london)

    def test_timezone_is_set_to_dst_tz_with_date_tz(self):
        date = '2018-06-29T17:14:09.291510+04:00'
        expected_date_bs_as = '2018-06-29T10:14:09.291510'
        expected_date_new_york = '2018-06-29T09:14:09.291510'
        expected_date_london = '2018-06-29T14:14:09.291510'

        res_bs_as = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_bs_as']
        )
        res_new_york = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_new_york']
        )
        res_london = convert_iso_string_to_dst_timezone(
            date, dst_tz=self.dates['tz_london']
        )

        self.assertEqual(expected_date_bs_as, res_bs_as)
        self.assertEqual(expected_date_new_york, res_new_york)
        self.assertEqual(expected_date_london, res_london)

    def test_date_timezone_is_set_to_given_origin_tz_without_date_tz(self):
        date = '2018-06-29T17:14:09.291510'
        expected_date_bs_as = '2018-06-29T13:14:09.291510'
        expected_date_new_york = '2018-06-29T12:14:09.291510'
        expected_date_london = '2018-06-29T17:14:09.291510'

        res_bs_as = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_bs_as']
        )
        res_new_york = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_new_york']
        )
        res_london = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_london']
        )

        self.assertEqual(expected_date_bs_as, res_bs_as)
        self.assertEqual(expected_date_new_york, res_new_york)
        self.assertEqual(expected_date_london, res_london)

    def test_date_timezone_is_set_to_date_tz_despite_the_origin_tz(self):
        date = '2018-06-29T17:14:09.291510-03:00'
        expected_date_bs_as = '2018-06-29T17:14:09.291510'
        expected_date_new_york = '2018-06-29T16:14:09.291510'
        expected_date_london = '2018-06-29T21:14:09.291510'

        res_bs_as = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_bs_as']
        )
        res_new_york = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_new_york']
        )
        res_london = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_london'],  # GMT+1,
            dst_tz=self.dates['tz_london']
        )

        self.assertEqual(expected_date_bs_as, res_bs_as)
        self.assertEqual(expected_date_new_york, res_new_york)
        self.assertEqual(expected_date_london, res_london)

    def test_res_date_is_congruent_to_given_origin_and_dst_tzs(self):
        date = '2018-06-29T15:14:09.291510'
        expected_date_bs_as = '2018-06-29T16:14:09.291510'
        expected_date_new_york = '2018-06-29T15:14:09.291510'
        expected_date_london = '2018-06-29T20:14:09.291510'

        res_bs_as = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_new_york'],  # GMT-4,
            dst_tz=self.dates['tz_bs_as']
        )
        res_new_york = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_new_york'],  # GMT-4,
            dst_tz=self.dates['tz_new_york']
        )
        res_london = convert_iso_string_to_dst_timezone(
            date,
            origin_tz=self.dates['tz_new_york'],  # GMT-4,
            dst_tz=self.dates['tz_london']
        )

        self.assertEqual(expected_date_bs_as, res_bs_as)
        self.assertEqual(expected_date_new_york, res_new_york)
        self.assertEqual(expected_date_london, res_london)
