import unittest
import os
import re
import vcr
from ckanapi import RemoteCKAN
from .context import pydatajson
from pydatajson.federation import push_dataset_to_ckan

SAMPLES_DIR = os.path.join("tests", "samples")

ckan_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                   cassette_library_dir=os.path.join("tests", "cassetes", "ckan_integration"),
                   record_mode='once')


class FederationTestCase(unittest.TestCase):
    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    def setUp(self):
        self.full_catalog = pydatajson.DataJson(self.get_sample('full_data.json'))
        self.justice_catalog = pydatajson.DataJson(self.get_sample('catalogo_justicia.json'))
        self.catalogs = [self.full_catalog, self.justice_catalog]
        self.portal = RemoteCKAN('http://localhost:8080', apikey='153a648e-eed1-47a6-b53e-d3e30dc030b3')
        package_list = self.portal.call_action('package_list')
        for package in package_list:
            data_dict = {'id': package}
            self.portal.call_action('dataset_purge', data_dict=data_dict)
        group_list = self.portal.call_action('group_list')
        for group in group_list:
            data_dict = {'id': group}
            self.portal.call_action('group_delete', data_dict=data_dict)
        tag_list = self.portal.call_action('tag_list')
        for tag in tag_list:
            data_dict = {'id': tag}
            self.portal.call_action('tag_delete', data_dict=data_dict)

    @ckan_vcr.use_cassette()
    def test_dataset_is_created_correctly(self):
        for catalog in self.catalogs:
            catalog_id = catalog.get('identifier', re.sub(r'[^\w-]+', '', catalog['title']).lower())
            dataset_id = catalog.datasets[0]['identifier']
            return_id = push_dataset_to_ckan(catalog, catalog_id, 'org-test', dataset_id, 'http://localhost:8080',
                                             '153a648e-eed1-47a6-b53e-d3e30dc030b3')
            self.assertEqual(return_id, catalog_id+'_'+dataset_id)

    @ckan_vcr.use_cassette()
    def test_dataset_is_updated_correctly(self):
        for catalog in self.catalogs:
            catalog_id = catalog.get('identifier', re.sub(r'[^\w-]+', '', catalog['title']).lower())
            dataset_id = catalog.datasets[0]['identifier']
            push_dataset_to_ckan(catalog, catalog_id, 'org-test', dataset_id, 'http://localhost:8080',
                                 '153a648e-eed1-47a6-b53e-d3e30dc030b3')

            catalog.datasets[0]['description'] = 'updated description'
            return_id = push_dataset_to_ckan(catalog, catalog_id, 'org-test', dataset_id, 'http://localhost:8080',
                                             '153a648e-eed1-47a6-b53e-d3e30dc030b3')

            data_dict = {'id': catalog_id+'_'+dataset_id}
            package = self.portal.call_action('package_show', data_dict=data_dict)
            self.assertEqual(return_id, catalog_id+'_'+dataset_id)
            self.assertEqual('updated description', package['notes'])

    @ckan_vcr.use_cassette()
    def test_groups_are_created(self):
        super_themes = []
        for catalog in self.catalogs:
            catalog_id = catalog.get('identifier', re.sub(r'[^\w-]+', '', catalog['title']).lower())
            dataset_id = catalog.datasets[0]['identifier']
            push_dataset_to_ckan(catalog, catalog_id, 'org-test', dataset_id, 'http://localhost:8080',
                                 '153a648e-eed1-47a6-b53e-d3e30dc030b3')
            super_themes += catalog.datasets[0]['superTheme']

        super_themes = map(lambda x: x.lower(), super_themes)
        super_themes = list(set(super_themes))
        group_list = self.portal.call_action('group_list')
        try:
            self.assertItemsEqual(super_themes, group_list)
        except AttributeError:
            self.assertCountEqual(super_themes, group_list)

    @ckan_vcr.use_cassette()
    def test_resources_swapped_correctly(self):
        catalog_id = 'same-catalog-id'
        full_dataset = self.full_catalog.datasets[0]
        full_dataset_id = full_dataset['identifier']
        push_dataset_to_ckan(self.full_catalog, catalog_id, 'org-test', full_dataset_id,
                             'http://localhost:8080', '153a648e-eed1-47a6-b53e-d3e30dc030b3')

        justice_dataset = self.justice_catalog.datasets[0]
        justice_dataset_id = justice_dataset['identifier']
        push_dataset_to_ckan(self.justice_catalog, catalog_id, 'org-test', justice_dataset_id,
                             'http://localhost:8080', '153a648e-eed1-47a6-b53e-d3e30dc030b3')
#       Switch them and update
        full_dataset['distribution'], justice_dataset['distribution'] = justice_dataset['distribution'],\
                                                                        full_dataset['distribution']

        full_package_id = push_dataset_to_ckan(self.full_catalog, catalog_id, 'org-test', full_dataset_id,
                                               'http://localhost:8080', '153a648e-eed1-47a6-b53e-d3e30dc030b3')
        justice_package_id = push_dataset_to_ckan(self.justice_catalog, catalog_id, 'org-test', justice_dataset_id,
                                                  'http://localhost:8080', '153a648e-eed1-47a6-b53e-d3e30dc030b3')
#       Switch them back
        full_dataset['distribution'], justice_dataset['distribution'] = justice_dataset['distribution'], \
                                                                        full_dataset['distribution']

        data_dict = {'id': full_package_id}
        full_package = self.portal.call_action('package_show', data_dict=data_dict)
        data_dict = {'id': justice_package_id}
        justice_package = self.portal.call_action('package_show', data_dict=data_dict)

        self.assertEqual(len(full_package['resources']), len(justice_dataset['distribution']))
        self.assertEqual(len(justice_package['resources']), len(full_dataset['distribution']))

        for resource, justice_distribution in zip(full_package['resources'], justice_dataset['distribution']):
            self.assertEqual('same-catalog-id_'+full_dataset_id+'_'+justice_distribution['identifier'],
                             resource['id'])

        for resource, full_distribution in zip(justice_package['resources'], full_dataset['distribution']):
            self.assertEqual('same-catalog-id_'+justice_dataset_id+'_'+full_distribution['identifier'],
                             resource['id'])

    def test_invalid_catalogs_are_rejected(self):
        invalid_sample = self.get_sample('missing_catalog_description.json')
        invalid_catalog = pydatajson.DataJson(invalid_sample)
        with self.assertRaises(ValueError):
            push_dataset_to_ckan(invalid_catalog, 'invalid', 'org-test', invalid_catalog.datasets[0]['identifier'],
                                 'http://localhost:8080', '153a648e-eed1-47a6-b53e-d3e30dc030b3')


if __name__ == '__main__':
    unittest.main()
