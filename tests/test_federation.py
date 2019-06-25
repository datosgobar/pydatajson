# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import re
import json

try:
    from mock import patch, MagicMock, ANY
except ImportError:
    from unittest.mock import patch, MagicMock, ANY

from .context import pydatajson
from pydatajson.federation import *
from pydatajson.helpers import is_local_andino_resource
from ckanapi.errors import NotFound, CKANAPIError

SAMPLES_DIR = os.path.join("tests", "samples")


class FederationSuite(unittest.TestCase):
    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)


@patch('pydatajson.federation.RemoteCKAN')
class PushDatasetTestCase(FederationSuite):

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get('identifier', re.sub(
            r'[^a-z-_]+', '', cls.catalog['title']).lower())
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset['identifier']
        cls.distribution = cls.catalog.distributions[0]
        cls.distribution_id = cls.distribution['identifier']
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

    def test_harvest_catalog_with_empty_list(self, mock_portal):
        harvested_ids, _ = harvest_catalog_to_ckan(
            self.catalog, 'portal', 'key', self.catalog_id,
            owner_org='owner', dataset_list=[])
        mock_portal.assert_not_called()
        self.assertEqual([], harvested_ids)

    def test_resource_upload_succesfully(self, mock_portal):
        mock_portal.return_value.action.resource_patch = MagicMock(
            return_value={'id': 'an_id',
                          'resource_type': 'file.upload'})
        resources = {self.distribution_id: 'tests/samples/resource_sample.csv'}
        res = resources_update('portal', 'key', self.catalog.distributions,
                               resources)
        mock_portal.return_value.action.resource_patch.assert_called_with(
            id=self.distribution_id,
            resource_type='file.upload',
            upload=ANY
        )
        self.assertEqual(['an_id'], res)

    def test_resource_upload_error(self, mock_portal):
        mock_portal.return_value.action.resource_patch = MagicMock(
            side_effect=CKANAPIError('broken resource'))
        resources = {self.distribution_id: 'tests/samples/resource_sample.csv'}
        res = resources_update('portal', 'key', self.catalog.distributions,
                               resources)
        mock_portal.return_value.action.resource_patch.assert_called_with(
            id=self.distribution_id,
            resource_type='file.upload',
            upload=ANY
        )
        self.assertEqual([], res)

    @patch('pydatajson.helpers.download_to_file')
    def test_push_dataset_upload_strategy(self, mock_download, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(
            self.catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            download_strategy=(lambda _, x: x['identifier'] == '1.1'))
        mock_portal.return_value.action.resource_patch.assert_called_with(
            id='1.1',
            resource_type='file.upload',
            upload=ANY
        )

    def test_push_dataset_upload_empty_strategy(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(
            self.minimum_catalog,
            'owner',
            self.dataset_id,
            'portal',
            'key',
            download_strategy=is_local_andino_resource)
        mock_portal.return_value.action.resource_patch.not_called()

    def test_push_dataset_regenerate_accessurl_all(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        identifiers = [dist['identifier'] for dist in
                       self.dataset['distribution']]

        def side_effect(**kwargs):
            self.assertTrue(kwargs['id'] in identifiers)
            self.assertEqual('', kwargs['accessURL'])
            return {'id': kwargs['id']}

        mock_portal.return_value.action.resource_patch.side_effect =\
            side_effect

        pushed = push_dataset_to_ckan(self.catalog, 'owner',
                                      self.dataset_id,
                                      'portal', 'key',
                                      generate_new_access_url=identifiers)
        self.assertEqual(self.dataset_id, pushed)

    def test_push_dataset_regenerate_accessurl_none(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return data_dict
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action

        def side_effect(**kwargs):
            self.fail('should not be called')

        mock_portal.return_value.action.resource_patch.side_effect =\
            side_effect

        pushed = push_dataset_to_ckan(self.catalog, 'owner',
                                      self.dataset_id,
                                      'portal', 'key',
                                      generate_new_access_url=None)
        self.assertEqual(self.dataset_id, pushed)


class RemoveDatasetTestCase(FederationSuite):

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


@patch('pydatajson.federation.RemoteCKAN', autospec=True)
class PushThemeTestCase(FederationSuite):
    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))

    def test_empty_theme_search_raises_exception(self, mock_portal):
        with self.assertRaises(AssertionError):
            push_theme_to_ckan(self.catalog, 'portal_url', 'apikey')

    def test_function_pushes_theme_by_identifier(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'name': 'group_name'})
        result = push_theme_to_ckan(
            self.catalog,
            'portal_url',
            'apikey',
            identifier='compras')
        self.assertEqual('group_name', result)

    def test_function_pushes_theme_by_label(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(
            return_value={'name': 'other_name'})
        result = push_theme_to_ckan(
            self.catalog,
            'portal_url',
            'apikey',
            label='Adjudicaciones')
        self.assertEqual('other_name', result)

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


@patch('pydatajson.federation.RemoteCKAN', autospec=True)
class PushCatalogThemesTestCase(FederationSuite):

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))

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


@patch('pydatajson.federation.RemoteCKAN', autospec=True)
class OrganizationsTestCase(FederationSuite):

    def setUp(self):
        self.portal_url = 'portal_url'
        self.apikey = 'apikey'
        self.org_tree = json.load(open(
            self.get_sample('organization_tree.json')))

    def check_hierarchy(self, node, parent=None):
        if not node['success']:
            self.assertTrue('children' not in node)
            return
        if parent is None:
            self.assertTrue('groups' not in node)
        else:
            self.assertEqual(1, len(node['groups']))
            self.assertDictEqual(node['groups'][0],
                                 {'name': parent})

        for child in node['children']:
            self.check_hierarchy(child, parent=node['name'])

    def test_get_organizations_calls_api_correctly(self, mock_portal):
        get_organizations_from_ckan(self.portal_url)
        mock_portal.return_value.call_action.assert_called_with(
            'group_tree', data_dict={'type': 'organization'})

    def test_get_organization_calls_api_correctly(self, mock_portal):
        get_organization_from_ckan(self.portal_url, 'test_id')
        mock_portal.return_value.call_action.assert_called_with(
            'organization_show', data_dict={'id': 'test_id'})

    def test_push_organization_sets_correct_attributes_on_success(
            self, mock_portal):
        mock_portal.return_value.call_action = (lambda _, data_dict: data_dict)
        pushed_org = push_organization_to_ckan(self.portal_url,
                                               self.apikey,
                                               self.org_tree[0])
        self.assertTrue(pushed_org['success'])

    def test_push_organization_assigns_parent_correctly(self, mock_portal):
        mock_portal.return_value.call_action = (lambda _, data_dict: data_dict)
        pushed_org = push_organization_to_ckan(self.portal_url,
                                               self.apikey,
                                               self.org_tree[0],
                                               parent='parent')
        self.assertEqual(1, len(pushed_org['groups']))
        self.assertDictEqual(pushed_org['groups'][0], {'name': 'parent'})

    def test_push_organization_sets_correct_attributes_on_failures(
            self, mock_portal):
        def broken_call(_, __):
            raise Exception('broken api call')
        mock_portal.return_value.call_action = broken_call
        pushed_org = push_organization_to_ckan(self.portal_url,
                                               self.apikey,
                                               self.org_tree[0])
        self.assertFalse(pushed_org['success'])

    def test_push_organizations_sends_correct_hierarchy(self, mock_portal):
        mock_portal.return_value.call_action = (lambda _, data_dict: data_dict)
        pushed_tree = push_organization_tree_to_ckan(self.portal_url,
                                                     self.apikey,
                                                     self.org_tree)
        for node in pushed_tree:
            self.check_hierarchy(node)

    def test_push_organizations_cuts_trees_on_failures(self, mock_portal):
        def mock_org_create(_action, data_dict):
            broken_orgs = ('acumar', 'modernizacion', 'hacienda')
            if data_dict['name'] in broken_orgs:
                raise Exception('broken org on each level')
            else:
                return data_dict

        mock_portal.return_value.call_action = mock_org_create
        pushed_tree = push_organization_tree_to_ckan(self.portal_url,
                                                     self.apikey,
                                                     self.org_tree)
        for node in pushed_tree:
            self.check_hierarchy(node)

    def test_remove_organization_sends_correct_parameters(self, mock_portal):
        remove_organization_from_ckan(self.portal_url, self.apikey, 'test_id')
        mock_portal.return_value.call_action.assert_called_with(
            'organization_purge', data_dict={'id': 'test_id'})

    def test_remove_organizations(self, mock_portal):
        ids = ['id1', 'id2', 'id3']
        remove_organizations_from_ckan(self.portal_url, self.apikey, ids)
        for test_id in ids:
            mock_portal.return_value.call_action.assert_any_call(
                'organization_purge', data_dict={'id': test_id})

    @patch('logging.Logger.exception')
    def test_remove_organization_logs_failures(self, mock_logger, mock_portal):
        mock_portal.return_value.call_action.side_effect = Exception('test')
        remove_organization_from_ckan(self.portal_url, self.apikey, 'test_id')
        mock_portal.return_value.call_action.assert_called_with(
            'organization_purge', data_dict={'id': 'test_id'})
        mock_logger.assert_called_with(
            'Ocurrió un error borrando la organización test_id: test')


@patch('pydatajson.federation.push_dataset_to_ckan')
class RestoreToCKANTestCase(FederationSuite):

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get('identifier', re.sub(
            r'[^a-z-_]+', '', cls.catalog['title']).lower())
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset['identifier']

    def test_restore_dataset_to_ckan(self, mock_push):
        def test_strategy(_catalog, _dist):
            return False
        restore_dataset_to_ckan(self.catalog, 'owner_org', self.dataset_id,
                                'portal', 'apikey', test_strategy)
        mock_push.assert_called_with(self.catalog, 'owner_org',
                                     self.dataset_id, 'portal', 'apikey', None,
                                     False, False, test_strategy, None)

    def test_restore_with_numeric_distribution_identifier(self, mock_push):
        bad_catalog = pydatajson.DataJson(self.get_sample(
            'numeric_distribution_identifier.json'))
        bad_dataset_id = '99db6631-d1c9-470b-a73e-c62daa32c777'
        with self.assertRaises(NumericDistributionIdentifierError):
            restore_dataset_to_ckan(bad_catalog, 'owner_org',
                                    bad_dataset_id, 'portal', 'apikey')

    @patch('pydatajson.federation.push_new_themes')
    def test_restore_organization_to_ckan(self, mock_push_thm, mock_push_dst):
        identifiers = [ds['identifier'] for ds in self.catalog.datasets]
        mock_push_dst.side_effect = identifiers
        pushed = restore_organization_to_ckan(self.catalog, 'owner_org',
                                              'portal', 'apikey', identifiers)
        self.assertEqual(identifiers, pushed)
        mock_push_thm.assert_called_with(self.catalog, 'portal', 'apikey')
        for identifier in identifiers:
            mock_push_dst.assert_any_call(self.catalog, 'owner_org',
                                          identifier, 'portal', 'apikey', None,
                                          False, False, None, None)

    @patch('pydatajson.federation.push_new_themes')
    def test_restore_failing_organization_to_ckan(self, mock_push_thm,
                                                  mock_push_dst):
        # Continua subiendo el segundo dataset a pesar que el primero falla
        effects = [CKANAPIError('broken dataset'),
                   self.catalog.datasets[1]['identifier']]
        mock_push_dst.side_effect = effects
        identifiers = [ds['identifier'] for ds in self.catalog.datasets]
        pushed = restore_organization_to_ckan(self.catalog, 'owner_org',
                                              'portal', 'apikey', identifiers)
        self.assertEqual([identifiers[1]], pushed)
        mock_push_thm.assert_called_with(self.catalog, 'portal', 'apikey')
        mock_push_dst.assert_called_with(self.catalog, 'owner_org',
                                         identifiers[1], 'portal', 'apikey',
                                         None, False, False, None, None)

    @patch('pydatajson.federation.push_new_themes')
    @patch('ckanapi.remoteckan.ActionShortcut')
    def test_restore_catalog_to_ckan(self, mock_action, mock_push_thm,
                                     mock_push_dst):
        identifiers = [ds['identifier'] for ds in self.catalog.datasets]
        mock_action.return_value.organization_list.return_value = \
            ['org_1', 'org_2']
        mock_action.return_value.organization_show.side_effect = [
            {'packages': [{'id': identifiers[0]}]},
            {'packages': [{'id': identifiers[1]}]},
        ]
        mock_push_dst.side_effect = (lambda *args, **kwargs: args[2])
        pushed = restore_catalog_to_ckan(self.catalog, 'origin',
                                         'destination', 'apikey')
        mock_push_dst.assert_any_call(self.catalog, 'org_1',
                                      identifiers[0], 'destination', 'apikey',
                                      None, False, False, None, None)
        mock_push_dst.assert_any_call(self.catalog, 'org_2',
                                      identifiers[1], 'destination', 'apikey',
                                      None, False, False, None, None)
        expected = {'org_1': [identifiers[0]],
                    'org_2': [identifiers[1]]}
        self.assertDictEqual(expected, pushed)

    @patch('pydatajson.federation.push_new_themes')
    @patch('ckanapi.remoteckan.ActionShortcut')
    def test_restore_catalog_failing_origin_portal(
            self, mock_action, mock_push_thm, mock_push_dst):
        mock_action.return_value.organization_list.side_effect = \
            CKANAPIError('Broken origin portal')
        pushed = restore_catalog_to_ckan(self.catalog, 'origin',
                                         'destination', 'apikey')
        self.assertDictEqual({}, pushed)
        mock_push_thm.assert_not_called()
        mock_push_dst.assert_not_called()

    @patch('pydatajson.federation.push_new_themes')
    @patch('ckanapi.remoteckan.ActionShortcut')
    def test_restore_catalog_failing_destination_portal(
            self, mock_action, mock_push_thm, mock_push_dst):

        identifiers = [ds['identifier'] for ds in self.catalog.datasets]
        mock_action.return_value.organization_list.return_value = \
            ['org_1', 'org_2']
        mock_action.return_value.organization_show.side_effect = [
            {'packages': [{'id': identifiers[0]}]},
            {'packages': [{'id': identifiers[1]}]},
        ]
        mock_push_dst.side_effect = CKANAPIError('Broken destination portal')

        pushed = restore_catalog_to_ckan(self.catalog, 'origin',
                                         'destination', 'apikey')
        mock_push_dst.assert_any_call(self.catalog, 'org_1',
                                      identifiers[0], 'destination', 'apikey',
                                      None, False, False, None, None)
        mock_push_dst.assert_any_call(self.catalog, 'org_2',
                                      identifiers[1], 'destination', 'apikey',
                                      None, False, False, None, None)
        expected = {'org_1': [],
                    'org_2': []}
        self.assertDictEqual(expected, pushed)
