import unittest
import os
import re
import vcr
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .context import pydatajson
from pydatajson.federation import push_dataset_to_ckan, remove_dataset_from_ckan

SAMPLES_DIR = os.path.join("tests", "samples")


class PushTestCase(unittest.TestCase):
    CKAN_VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                       cassette_library_dir=os.path.join("tests", "cassetes", "ckan_integration", "push_dataset"),
                       filter_headers=['Authorization', 'X-CKAN-API-Key'],
                       record_mode='once')
    
    portal_url = 'http://localhost:8080'
    apikey = '581e91ff-5c9b-4d44-bc9e-2d08fcd85b88'

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @CKAN_VCR.use_cassette()
    def setUp(self):
        self.portal = RemoteCKAN(self.portal_url, apikey=self.apikey)
        self.full_catalog = pydatajson.DataJson(self.get_sample('full_data.json'))
        self.justice_catalog = pydatajson.DataJson(self.get_sample('catalogo_justicia.json'))

    @CKAN_VCR.use_cassette()
    def tearDown(self):
        full_dataset = self.full_catalog.datasets[0]
        full_name = re.sub(r'[^a-z-_]+', '', full_dataset['title'].lower())
        justice_dataset = self.justice_catalog.datasets[0]
        justice_name = re.sub(r'[^a-z-_]+', '', justice_dataset['title'].lower())

        package_list = self.portal.call_action('package_list')
        for package_name in package_list:
            if package_name == full_name or package_name == justice_name:
                self.portal.call_action('dataset_purge', data_dict={'id': package_name})

        self.portal.close()

    @CKAN_VCR.use_cassette()
    def test_dataset_is_created_correctly(self):
        catalog = self.full_catalog
        catalog_id = catalog.get('identifier', re.sub(r'[^a-z-_]+', '', catalog['title'].lower()))
        dataset = catalog.datasets[0]
        dataset_id = dataset['identifier']
        return_id = push_dataset_to_ckan(catalog, catalog_id, "oficina-de-muestra", dataset_id,
                                         self.portal_url, self.apikey)
        self.assertEqual(return_id, catalog_id+'_'+dataset_id)

    @CKAN_VCR.use_cassette()
    def test_dataset_is_updated_correctly(self):
        catalog = self.full_catalog
        catalog_id = catalog.get('identifier', re.sub(r'[^a-z-_]+', '', catalog['title'].lower()))
        dataset_id = catalog.datasets[0]['identifier']
        push_dataset_to_ckan(catalog, catalog_id, "oficina-de-muestra", dataset_id,
                             self.portal_url, self.apikey)

        catalog.datasets[0]['description'] = 'updated description'
        return_id = push_dataset_to_ckan(catalog, catalog_id, "oficina-de-muestra", dataset_id,
                                         self.portal_url, self.apikey)

        data_dict = {'id': catalog_id+'_'+dataset_id}
        package = self.portal.call_action('package_show', data_dict=data_dict)
        self.assertEqual(return_id, catalog_id+'_'+dataset_id)
        self.assertEqual('updated description', package['notes'])

    @CKAN_VCR.use_cassette()
    def test_groups_are_created(self):
        catalog = self.full_catalog
        catalog_id = catalog.get('identifier', re.sub(r'[^a-z-_]+', '', catalog['title'].lower()))
        dataset_id = catalog.datasets[0]['identifier']
        super_themes = catalog.datasets[0]['superTheme']
        super_themes = set(map(lambda x: x.lower(), super_themes))

        for s_theme in super_themes:
            try:
                self.portal.call_action('group_delete', data_dict={'id': s_theme})
            except NotFound:
                continue

        push_dataset_to_ckan(catalog, catalog_id, "oficina-de-muestra", dataset_id,
                             self.portal_url, self.apikey)

        groups = set(self.portal.call_action('group_list'))
        self.assertTrue(super_themes.issubset(groups))

    @CKAN_VCR.use_cassette()
    def test_resources_swapped_correctly(self):
        catalog_id = 'same-catalog-id'
        full_dataset = self.full_catalog.datasets[0]
        full_dataset_id = full_dataset['identifier']
        push_dataset_to_ckan(self.full_catalog, catalog_id, 'oficina-de-muestra', full_dataset_id,
                             self.portal_url, self.apikey)

        justice_dataset = self.justice_catalog.datasets[0]
        justice_dataset_id = justice_dataset['identifier']
        push_dataset_to_ckan(self.justice_catalog, catalog_id, 'oficina-de-muestra', justice_dataset_id,
                             self.portal_url, self.apikey)
        # Switch them and update
        full_dataset['distribution'], justice_dataset['distribution'] = \
            justice_dataset['distribution'], full_dataset['distribution']

        full_package_id = push_dataset_to_ckan(self.full_catalog, catalog_id, 'oficina-de-muestra', full_dataset_id,
                                               self.portal_url, self.apikey)
        justice_package_id = push_dataset_to_ckan(self.justice_catalog, catalog_id, 'oficina-de-muestra',
                                                  justice_dataset_id, self.portal_url, self.apikey)
        # Switch them back
        full_dataset['distribution'], justice_dataset['distribution'] = \
            justice_dataset['distribution'], full_dataset['distribution']

        data_dict = {'id': full_package_id}
        full_package = self.portal.call_action('package_show', data_dict=data_dict)
        data_dict = {'id': justice_package_id}
        justice_package = self.portal.call_action('package_show', data_dict=data_dict)

        self.assertEqual(len(full_package['resources']), len(justice_dataset['distribution']))
        self.assertEqual(len(justice_package['resources']), len(full_dataset['distribution']))

        for resource, justice_distribution in zip(full_package['resources'], justice_dataset['distribution']):
            self.assertEqual('same-catalog-id_'+justice_distribution['identifier'], resource['id'])

        for resource, full_distribution in zip(justice_package['resources'], full_dataset['distribution']):
            self.assertEqual('same-catalog-id_'+full_distribution['identifier'], resource['id'])


class RemoveTestCase(unittest.TestCase):
    CKAN_VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                       cassette_library_dir=os.path.join("tests", "cassetes", "ckan_integration", "remove_dataset"),
                       filter_headers=['Authorization', 'X-CKAN-API-Key'],
                       record_mode='once')

    test_datasets = [{'id': '1.1', 'owner_org': 'org-1', 'author': 'author_a', 'name': 'data1_1'},
                     {'id': '2.1', 'owner_org': 'org-2', 'author': 'author_a', 'name': 'data2_1'},
                     {'id': '2.2', 'owner_org': 'org-2', 'author': 'author_b', 'name': 'data2_2'},
                     {'id': '3.1', 'owner_org': 'org-3', 'author': 'author_a', 'name': 'data3_1'},
                     {'id': '3.2', 'owner_org': 'org-3', 'author': 'author_b', 'name': 'data3_2'},
                     {'id': '3.3', 'owner_org': 'org-3', 'author': 'author_c', 'name': 'data3_3'}]

    portal_url = 'http://localhost:8080'
    apikey = '581e91ff-5c9b-4d44-bc9e-2d08fcd85b88'

    @CKAN_VCR.use_cassette()
    def setUp(self):
        self.ckan_portal = RemoteCKAN(self.portal_url, apikey=self.apikey)
        for dataset in self.test_datasets:
            try:
                self.ckan_portal.call_action('dataset_purge', data_dict={'id': dataset['id']})
            except NotFound:
                continue
        for dataset in self.test_datasets:
            try:
                self.ckan_portal.call_action('dataset_purge', data_dict={'id': dataset['id']})
            except NotFound:
                continue
        for dataset in self.test_datasets:
            self.ckan_portal.call_action('package_create', data_dict=dataset)

    @CKAN_VCR.use_cassette()
    def tearDown(self):
        for dataset in self.test_datasets:
            try:
                self.ckan_portal.call_action('dataset_purge', data_dict={'id': dataset['id']})
            except NotFound:
                continue

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_id(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='1.1')
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='3.3')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data1_1' not in package_list)
        self.assertTrue('data3_3' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_organization(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, organization='org-2')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data2_1' not in package_list)
        self.assertTrue('data2_2' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_publisher(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, publisher='author_b')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data2_2' not in package_list)
        self.assertTrue('data3_2' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_id_and_organization(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='2.2', organization='org-1')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data2_2' not in package_list)
        self.assertTrue('data1_1' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_organization_and_publisher(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, organization='org-1', publisher='author_c')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data3_3' not in package_list)
        self.assertTrue('data1_1' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_id_and_publisher(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='2.1', publisher='author_c')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(4, len(package_list))
        self.assertTrue('data2_1' not in package_list)
        self.assertTrue('data3_3' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_all_three(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='2.2',
                                 organization='org-3', publisher='author_a')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(0, len(package_list))

    @CKAN_VCR.use_cassette()
    def test_empty_query_result(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey, identifier='4.1',
                                 organization='org-4', publisher='author_d')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(6, len(package_list))

    @CKAN_VCR.use_cassette()
    def test_with_no_parametres(self):
        remove_dataset_from_ckan(self.portal_url, self.apikey)
        package_list = self.ckan_portal.call_action('package_list')
        self.assertEqual(6, len(package_list))
