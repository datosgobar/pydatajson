# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import re

try:
    from mock import patch, MagicMock
except ImportError:
    from unittest.mock import patch, MagicMock

from .context import pydatajson
from pydatajson.federation import *
from ckanapi.errors import NotFound

SAMPLES_DIR = os.path.join("tests", "samples")


class PushDatasetTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get('identifier', re.sub(
            r'[^a-z-_]+', '', cls.catalog['title']).lower())
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset['identifier']
        cls.minimum_catalog = pydatajson.DataJson(
            cls.get_sample('minimum_data.json'))
        cls.minimum_catalog_id = cls.minimum_catalog.get('identifier', re.sub(
            r'[^a-z-_]+', '', cls.minimum_catalog['title']).lower())
        cls.minimum_dataset = cls.minimum_catalog.datasets[0]
        # PATCH: minimum_data no tiene los identificadores obligatorios.
        # Se los agrego aca, pero hay que refactorizar
        # tests y samples desactualizados para cumplir con los perfiles nuevos
        cls.minimum_dataset['identifier'] = cls.dataset['identifier']
        cls.minimum_dataset['distribution'][0][
            'identifier'] = cls.dataset['distribution'][0]['identifier']

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_id_is_created_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                raise NotFound
            if action == 'package_create':
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(
            self.catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            catalog_id=self.catalog_id)
        self.assertEqual(self.catalog_id + '_' + self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_id_is_updated_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            if action == 'package_create':
                self.fail('should not be called')
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(
            self.catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            catalog_id=self.catalog_id)
        self.assertEqual(self.catalog_id + '_' + self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_dataset_id_is_preserved_if_catalog_id_is_not_passed(
            self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            if action == 'package_create':
                self.fail('should not be called')
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, 'owner', self.dataset_id,
                                      'portal', 'key')
        self.assertEqual(self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_tags_are_passed_correctly(self, mock_portal):
        themes = self.dataset['theme']
        keywords = [kw for kw in self.dataset['keyword']]
        for theme in themes:
            label = self.catalog.get_theme(identifier=theme)['label']
            label = re.sub(r'[^\w .-]+', '', label, flags=re.UNICODE)
            keywords.append(label)

        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                try:
                    self.assertItemsEqual(
                        keywords, [
                            tag['name'] for tag in data_dict['tags']])
                except AttributeError:
                    self.assertCountEqual(
                        keywords, [
                            tag['name'] for tag in data_dict['tags']])
                return data_dict
            if action == 'package_create':
                self.fail('should not be called')
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(
            self.catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            catalog_id=self.catalog_id)
        self.assertEqual(self.catalog_id + '_' + self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_licenses_are_interpreted_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'license_list':
                return [{'title': 'somelicense',
                         'url': 'somelicense.com', 'id': '1'},
                        {'title': 'otherlicense',
                         'url': 'otherlicense.com', 'id': '2'}]
            elif action == 'package_update':
                self.assertEqual('notspecified', data_dict['license_id'])
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, 'owner', self.dataset_id,
                             'portal', 'key', catalog_id=self.catalog_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_dataset_without_license_sets_notspecified(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'license_list':
                return [{'title': 'somelicense',
                         'url': 'somelicense.com', 'id': '1'},
                        {'title': 'otherlicense',
                         'url': 'otherlicense.com', 'id': '2'}]
            elif action == 'package_update':
                self.assertEqual('notspecified', data_dict['license_id'])
                return data_dict
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(
            self.minimum_catalog,
            'owner',
            self.minimum_dataset['identifier'],
            'portal',
            'key',
            catalog_id=self.minimum_catalog_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_dataset_level_wrappers(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        restored_id = restore_dataset_to_ckan(
            self.catalog, 'owner', self.dataset_id, 'portal', 'key')
        harvested_id = harvest_dataset_to_ckan(
            self.catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            self.catalog_id)
        self.assertEqual(self.dataset_id, restored_id)
        self.assertEqual(self.catalog_id + '_' + self.dataset_id, harvested_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_harvest_catalog_with_no_optional_parametres(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                self.assertTrue(
                    data_dict['id'].startswith(
                        self.catalog_id + '_'))
                self.assertTrue(
                    data_dict['name'].startswith(
                        self.catalog_id + '-'))
                self.assertEqual(self.catalog_id, data_dict['owner_org'])
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key', self.catalog_id)
        try:
            self.assertItemsEqual([self.catalog_id + '_' + ds['identifier']
                                   for ds in self.catalog.datasets],
                                  harvested_ids)
        except AttributeError:
            self.assertCountEqual([self.catalog_id + '_' + ds['identifier']
                                   for ds in self.catalog.datasets],
                                  harvested_ids)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_harvest_catalog_with_dataset_list(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action

        dataset_list = [ds['identifier'] for ds in self.catalog.datasets[:1]]
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key',
            self.catalog_id, dataset_list=dataset_list)
        try:
            self.assertItemsEqual(
                [self.catalog_id + '_' + ds_id for ds_id in dataset_list],
                harvested_ids)
        except AttributeError:
            self.assertCountEqual(
                [self.catalog_id + '_' + ds_id for ds_id in dataset_list],
                harvested_ids)

        dataset_list = [ds['identifier'] for ds in self.catalog.datasets]
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key',
            self.catalog_id, dataset_list=dataset_list)
        try:
            self.assertItemsEqual(
                [self.catalog_id + '_' + ds_id for ds_id in dataset_list],
                harvested_ids)
        except AttributeError:
            self.assertCountEqual(
                [self.catalog_id + '_' + ds_id for ds_id in dataset_list],
                harvested_ids)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_harvest_catalog_with_owner_org(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                self.assertEqual('owner', data_dict['owner_org'])
                return data_dict
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key', self.catalog_id, owner_org='owner')
        try:
            self.assertItemsEqual([self.catalog_id + '_' + ds['identifier']
                                   for ds in self.catalog.datasets],
                                  harvested_ids)
        except AttributeError:
            self.assertCountEqual([self.catalog_id + '_' + ds['identifier']
                                   for ds in self.catalog.datasets],
                                  harvested_ids)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_harvest_catalog_with_errors(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                if data_dict['id'][-3:] == '777':
                    return data_dict
                else:
                    raise Exception('some message')
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        _, errors = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key', self.catalog_id, owner_org='owner')
        self.assertDictEqual(
            {self.catalog.datasets[1]['identifier']: "some message"}, errors)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_harvest_catalog_with_empty_list(self, mock_portal):
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key', self.catalog_id,
            owner_org='owner', dataset_list=[])
        mock_portal.assert_not_called()
        self.assertEqual([], harvested_ids)


class RemoveDatasetTestCase(unittest.TestCase):

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_empty_search_doesnt_call_purge(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock()
        remove_datasets_from_ckan('portal', 'key')
        mock_portal.return_value.call_action.assert_not_called()

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_filter_in_datasets(self, mock_portal, mock_search):
        mock_portal.return_value.call_action = MagicMock()
        mock_search.return_value = ['some_id']
        filter_in = {'dataset': {'id': 'some_id'}}
        remove_datasets_from_ckan('portal', 'key', filter_in=filter_in)
        mock_portal.return_value.call_action.assert_called_with(
            'dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_filter_in_out_datasets(self, mock_portal, mock_search):
        mock_portal.return_value.call_action = MagicMock()
        mock_search.return_value = ['some_id', 'other_id']
        filter_out = {'dataset': {'id': 'some_id'}}
        remove_datasets_from_ckan('portal', 'key', filter_out=filter_out)
        mock_portal.return_value.call_action.assert_any_call(
            'dataset_purge', data_dict={'id': 'other_id'})
        mock_portal.return_value.call_action.assert_any_call(
            'dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_query_one_dataset(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'count': 1, 'results': [{'id': 'some_id'}]})
        remove_datasets_from_ckan('portal', 'key', organization='some_org')
        data_dict = {'q': 'organization:"some_org"', 'rows': 500, 'start': 0}
        mock_portal.return_value.call_action.assert_any_call(
            'package_search', data_dict=data_dict)
        mock_portal.return_value.call_action.assert_any_call(
            'dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_query_over_500_datasets(self, mock_portal):
        count = 1001
        # First, the query results. Then the "dataset_purge" None results
        side_effects = [{'count': count, 'results': [{'id': 'id_1'}]},
                        {'count': count, 'results': [{'id': 'id_2'}]},
                        {'count': count, 'results': [{'id': 'id_3'}]},
                        None, None, None
                        ]
        mock_portal.return_value.call_action = MagicMock(
            side_effect=side_effects)
        remove_datasets_from_ckan('portal', 'key', organization='some_org')
        for start in range(0, count, 500):
            data_dict = {'q': 'organization:"some_org"',
                         'rows': 500, 'start': start}
            mock_portal.return_value.call_action.assert_any_call(
                'package_search', data_dict=data_dict)
        for x in ['1', '2', '3']:
            mock_portal.return_value.call_action.assert_any_call(
                'dataset_purge', data_dict={'id': 'id_' + x})

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_remove_through_filters_and_organization(
            self, mock_portal, mock_search):
        filter_results = ['id_1', 'id_2']
        org_results = [{'id': 'id_2'}, {'id': 'id_3'}]
        mock_search.return_value = filter_results
        mock_portal.return_value.call_action = MagicMock(
            return_value={'count': 2, 'results': org_results})
        remove_datasets_from_ckan(
            'portal', 'key', only_time_series=True, organization='some_org')
        mock_portal.return_value.call_action.assert_called_with(
            'dataset_purge', data_dict={'id': 'id_2'})


class PushThemeTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_empty_theme_search_raises_exception(self, mock_portal):
        with self.assertRaises(AssertionError):
            push_theme_to_ckan(self.catalog, 'portal_url', 'apikey')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_function_pushes_theme_by_identifier(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'name': 'group_name'})
        result = push_theme_to_ckan(
            self.catalog,
            'portal_url',
            'apikey',
            identifier='compras')
        self.assertEqual('group_name', result)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_function_pushes_theme_by_label(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'name': 'other_name'})
        result = push_theme_to_ckan(
            self.catalog,
            'portal_url',
            'apikey',
            label='Adjudicaciones')
        self.assertEqual('other_name', result)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_ckan_portal_is_called_with_correct_parametres(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'name': u'contrataciones'})
        group = {'name': u'contrataciones',
                 'title': u'Contrataciones',
                 'description': u'Datasets sobre contrataciones.'}
        push_theme_to_ckan(
            self.catalog,
            'portal_url',
            'apikey',
            identifier='contrataciones')
        mock_portal.return_value.call_action.assert_called_once_with(
            'group_create', data_dict=group)


class PushCatalogThemesTestCase(unittest.TestCase):
    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_empty_portal_pushes_every_theme(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_list':
                return []
            elif action == 'group_create':
                return {'name': data_dict['name']}
            else:
                self.fail('should not be called')

        mock_portal.return_value.call_action = mock_call_action
        res_names = push_new_themes(self.catalog, 'portal_url', 'apikey')
        try:
            self.assertItemsEqual(
                [theme['id'] for theme in self.catalog['themeTaxonomy']],
                res_names)
        except AttributeError:
            self.assertCountEqual(
                [theme['id'] for theme in self.catalog['themeTaxonomy']],
                res_names)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_full_portal_pushes_nothing(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_list':
                return [theme['id'] for theme in self.catalog['themeTaxonomy']]
            else:
                self.fail('should not be called')

        mock_portal.return_value.call_action = mock_call_action
        res_names = push_new_themes(self.catalog, 'portal_url', 'apikey')
        try:
            self.assertItemsEqual([], res_names)
        except AttributeError:
            self.assertCountEqual([], res_names)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_non_empty_intersection_pushes_missing_themes(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_list':
                return [theme['id']
                        for theme in self.catalog['themeTaxonomy']][0:2]
            elif action == 'group_create':
                return {'name': data_dict['name']}
            else:
                self.fail('should not be called')

        mock_portal.return_value.call_action = mock_call_action
        res_names = push_new_themes(self.catalog, 'portal_url', 'apikey')
        try:
            self.assertItemsEqual(
                [theme['id'] for theme in self.catalog['themeTaxonomy']][2:],
                res_names)
        except AttributeError:
            self.assertCountEqual(
                [theme['id'] for theme in self.catalog['themeTaxonomy']][2:],
                res_names)
