import unittest
import os
import re
try:
    from mock import patch, MagicMock
except ImportError:
    from unittest.mock import patch, MagicMock

from .context import pydatajson
from pydatajson.federation import push_dataset_to_ckan, remove_dataset_from_ckan
from ckanapi.errors import NotFound

SAMPLES_DIR = os.path.join("tests", "samples")


class PushDatasetTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.catalog_id = cls.catalog.get('identifier', re.sub(r'[^a-z-_]+', '', cls.catalog['title']).lower())
        cls.dataset = cls.catalog.datasets[0]
        cls.dataset_id = cls.dataset['identifier']
        cls.minimum_catalog = pydatajson.DataJson(cls.get_sample('minimum_data.json'))
        cls.minimum_catalog_id = cls.minimum_catalog.get('identifier',
                                                         re.sub(r'[^a-z-_]+', '', cls.minimum_catalog['title']).lower())
        cls.minimum_dataset = cls.minimum_catalog.datasets[0]
        # PATCH: minimum_data no tiene los identificadores obligatorios. Se los agrego aca, pero hay que refactorizar
        # tests y samples desactualizados para cumplir con los perfiles nuevos
        cls.minimum_dataset['identifier'] = cls.dataset['identifier']
        cls.minimum_dataset['distribution'][0]['identifier'] = cls.dataset['distribution'][0]['identifier']

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_id_is_created_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                raise NotFound
            if action == 'package_create':
                return {'id': data_dict['id']}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, self.catalog_id, 'owner',
                                      self.dataset['identifier'], 'portal', 'key')
        self.assertEqual(self.catalog_id+'_'+self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_id_is_updated_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return {'id': data_dict['id']}
            if action == 'package_create':
                self.fail('should not be called')
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, self.catalog_id, 'owner',
                                      self.dataset['identifier'], 'portal', 'key')
        self.assertEqual(self.catalog_id+'_'+self.dataset_id, res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_new_groups_are_created(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_create':
                self.assertEqual('econ', data_dict['name'])
                return None
            elif action == 'package_update':
                return {'id': data_dict['id']}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, self.catalog_id, 'owner',
                             self.dataset['identifier'], 'portal', 'key')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_if_group_exists_is_not_created(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_list':
                return ['econ']
            elif action == 'group_create':
                self.fail("should not be called")
            elif action == 'package_update':
                return {'id': data_dict['id']}
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, self.catalog_id, 'owner',
                             self.dataset['identifier'], 'portal', 'key')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_licenses_are_interpreted_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'license_list':
                return [{'title': 'somelicense', 'url': 'somelicense.com', 'id': '1'},
                        {'title': 'otherlicense', 'url': 'otherlicense.com', 'id': '2'}]
            elif action == 'package_update':
                self.assertEqual('notspecified', data_dict['license_id'])
                return {'id': data_dict['id']}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, self.catalog_id, 'owner',
                             self.dataset['identifier'], 'portal', 'key')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_dataset_without_license_sets_notspecified(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'license_list':
                return [{'title': 'somelicense', 'url': 'somelicense.com', 'id': '1'},
                        {'title': 'otherlicense', 'url': 'otherlicense.com', 'id': '2'}]
            elif action == 'package_update':
                self.assertEqual('notspecified', data_dict['license_id'])
                return {'id': data_dict['id']}
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.minimum_catalog, self.minimum_catalog_id, 'owner',
                             self.minimum_dataset['identifier'], 'portal', 'key')


class RemoveDatasetTestCase(unittest.TestCase):

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_empty_search_doesnt_call_purge(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock()
        remove_dataset_from_ckan('portal', 'key')
        mock_portal.return_value.call_action.assert_not_called()

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_filter_in_datasets(self, mock_portal, mock_search):
        mock_portal.return_value.call_action = MagicMock()
        mock_search.return_value = ['some_id']
        filter_in = {'dataset': {'id': 'some_id'}}
        remove_dataset_from_ckan('portal', 'key',  filter_in=filter_in)
        mock_portal.return_value.call_action.assert_called_with('dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_filter_in_out_datasets(self, mock_portal, mock_search):
        mock_portal.return_value.call_action = MagicMock()
        mock_search.return_value = ['some_id', 'other_id']
        filter_out = {'dataset': {'id': 'some_id'}}
        remove_dataset_from_ckan('portal', 'key', filter_out=filter_out)
        mock_portal.return_value.call_action.assert_any_call('dataset_purge', data_dict={'id': 'other_id'})
        mock_portal.return_value.call_action.assert_any_call('dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_query_one_dataset(self, mock_portal):
        mock_portal.return_value.call_action = MagicMock(return_value={'count': 1, 'results': [{'id': 'some_id'}]})
        remove_dataset_from_ckan('portal', 'key',  organization='some_org')
        data_dict = {'q': 'organization:"some_org"', 'rows': 500, 'start': 0}
        mock_portal.return_value.call_action.assert_any_call('package_search', data_dict=data_dict)
        mock_portal.return_value.call_action.assert_any_call('dataset_purge', data_dict={'id': 'some_id'})

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_query_over_500_datasets(self, mock_portal):
        count = 1001
        # First, the query results. Then the "dataset_purge" None results
        side_effects = [{'count': count, 'results': [{'id': 'id_1'}]},
                        {'count': count, 'results': [{'id': 'id_2'}]},
                        {'count': count, 'results': [{'id': 'id_3'}]},
                        None, None, None
                        ]
        mock_portal.return_value.call_action = MagicMock(side_effect=side_effects)
        remove_dataset_from_ckan('portal', 'key', organization='some_org')
        for start in range(0, count, 500):
            data_dict = {'q': 'organization:"some_org"', 'rows': 500, 'start': start}
            mock_portal.return_value.call_action.assert_any_call('package_search', data_dict=data_dict)
        for x in ['1', '2', '3']:
            mock_portal.return_value.call_action.assert_any_call('dataset_purge', data_dict={'id': 'id_'+x})

    @patch('pydatajson.federation.get_datasets')
    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_remove_through_filters_and_organization(self, mock_portal, mock_search):
        filter_results = ['id_1', 'id_2']
        org_results = [{'id': 'id_2'}, {'id': 'id_3'}]
        mock_search.return_value = filter_results
        mock_portal.return_value.call_action = MagicMock(return_value={'count': 2, 'results': org_results})
        remove_dataset_from_ckan('portal', 'key', only_time_series=True, organization='some_org')
        mock_portal.return_value.call_action.assert_called_with('dataset_purge', data_dict={'id': 'id_2'})