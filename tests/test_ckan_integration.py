import unittest
import os
import re
import vcr
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from .context import pydatajson
from pydatajson.federation import push_dataset_to_ckan

SAMPLES_DIR = os.path.join("tests", "samples")

CKAN_VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                   cassette_library_dir=os.path.join("tests", "cassetes", "ckan_integration"),
                   filter_headers=['Authorization', 'X-CKAN-API-Key'],
                   record_mode='once')


class FederationTestCase(unittest.TestCase):
    
    portal_url = 'http://181.209.63.239'
    apikey = 'una_apikey'

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
