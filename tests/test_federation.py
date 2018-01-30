import unittest
import os
from mock import patch
from .context import pydatajson
from pydatajson.federation import push_dataset_to_ckan
from ckanapi.errors import NotFound

SAMPLES_DIR = os.path.join("tests", "samples")


class FederationTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        cls.catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.dataset = cls.catalog.datasets[0]

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_default_id_created_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_create':
                return {'id': 'default_id'}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, self.dataset['identifier'], 'portal', 'key', 'owner')
        self.assertEqual('default_id', res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_specific_id_updated_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                return {'id': data_dict['id']}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, self.dataset['identifier'], 'portal', 'key', 'owner',
                                      dataset_destination_identifier='specified_id')
        self.assertEqual('specified_id', res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_specific_id_created_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'package_update':
                raise NotFound
            elif action == 'package_create':
                return {'id': data_dict['id']}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        res_id = push_dataset_to_ckan(self.catalog, self.dataset['identifier'], 'portal', 'key', 'owner',
                                      dataset_destination_identifier='specified_id')
        self.assertEqual('specified_id', res_id)

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_new_groups_are_created(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_create':
                self.assertEqual('econ', data_dict['name'])
                return None
            elif action == 'package_create':
                return {'id': 'default_id'}
            else:
                return []
        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, self.dataset['identifier'], 'portal', 'key', 'owner')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_if_group_exists_is_not_created(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'group_list':
                return ['econ']
            elif action == 'group_create':
                self.fail("should not be called")
            elif action == 'package_create':
                return {'id': 'default_id'}
            else:
                return []

        mock_portal.return_value.call_action = mock_call_action
        push_dataset_to_ckan(self.catalog, self.dataset['identifier'], 'portal', 'key', 'owner')

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_licenses_are_interpreted_correctly(self, mock_portal):
        def mock_call_action(action, data_dict=None):
            if action == 'license_list':
                return [{'title': 'somelicense', 'url': 'somelicense.com', 'id': '1'},
                        {'title': 'Open Data Commons Open Database License 1.0',
                         'url': 'someUrl', 'id': '2'}]
            elif action == 'package_create':
                self.assertEqual('2', data_dict['license_id'])
                return {'id': 'default_id'}
            else:
                return []

    @patch('pydatajson.federation.RemoteCKAN', autospec=True)
    def test_invalid_catalogs_are_rejected(self, mock_portal):
        invalid_sample = self.get_sample('missing_catalog_description.json')
        invalid_catalog = pydatajson.DataJson(invalid_sample)
        with self.assertRaises(ValueError):
            push_dataset_to_ckan(invalid_catalog, self.dataset['identifier'], 'portal', 'key', 'owner',
                                 dataset_destination_identifier='specified_id')


if __name__ == '__main__':
    unittest.main()