import unittest
import os
import vcr
from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from pydatajson.helpers import title_to_name
from pydatajson.federation import push_dataset_to_ckan,\
    remove_datasets_from_ckan
from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")


class PushTestCase(unittest.TestCase):
    CKAN_VCR = vcr.VCR(
        path_transformer=vcr.VCR.ensure_suffix('.yaml'),
        cassette_library_dir=os.path.join(
            "tests",
            "cassetes",
            "ckan_integration",
            "push_dataset"),
        filter_headers=[
            'Authorization',
            'X-CKAN-API-Key'],
        record_mode='once')

    portal_url = 'http://localhost:8080'
    apikey = "<apikey>"

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @CKAN_VCR.use_cassette()
    def setUp(self):
        self.portal = RemoteCKAN(self.portal_url, apikey=self.apikey)
        self.full_catalog = pydatajson.DataJson(
            self.get_sample('full_data.json'))
        self.justice_catalog = pydatajson.DataJson(
            self.get_sample('catalogo_justicia.json'))

    @CKAN_VCR.use_cassette()
    def tearDown(self):
        full_dataset = self.full_catalog.datasets[0]
        full_name = title_to_name(full_dataset['title'])
        justice_dataset = self.justice_catalog.datasets[0]
        justice_name = title_to_name(justice_dataset['title'])
        try:
            self.portal.call_action(
                'dataset_purge', data_dict={'id': full_name})
        except NotFound:
            pass
        try:
            self.portal.call_action(
                'dataset_purge', data_dict={'id': justice_name})
        except NotFound:
            pass

        self.portal.close()

    @CKAN_VCR.use_cassette()
    def test_dataset_is_created_correctly(self):
        catalog = self.full_catalog
        catalog_id = title_to_name(catalog['title'])
        dataset = catalog.datasets[0]
        dataset_id = dataset['identifier']
        return_id = push_dataset_to_ckan(
            catalog,
            "oficina-de-muestra",
            dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )
        self.assertEqual(return_id, catalog_id + '_' + dataset_id)

    @CKAN_VCR.use_cassette()
    def test_dataset_is_updated_correctly(self):
        catalog = self.full_catalog
        catalog_id = title_to_name(catalog['title'])
        dataset_id = catalog.datasets[0]['identifier']
        push_dataset_to_ckan(
            catalog,
            "oficina-de-muestra",
            dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )

        catalog.datasets[0]['description'] = 'updated description'
        return_id = push_dataset_to_ckan(
            catalog,
            "oficina-de-muestra",
            dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )

        data_dict = {'id': catalog_id + '_' + dataset_id}
        package = self.portal.call_action('package_show', data_dict=data_dict)
        self.assertEqual(return_id, catalog_id + '_' + dataset_id)
        self.assertEqual('updated description', package['notes'])

    @CKAN_VCR.use_cassette()
    def test_resources_swapped_correctly(self):
        catalog_id = 'same-catalog-id'
        full_dataset = self.full_catalog.datasets[0]
        full_dataset_id = full_dataset['identifier']
        push_dataset_to_ckan(
            self.full_catalog,
            'oficina-de-muestra',
            full_dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )

        justice_dataset = self.justice_catalog.datasets[0]
        justice_dataset_id = justice_dataset['identifier']
        push_dataset_to_ckan(
            self.justice_catalog,
            'oficina-de-muestra',
            justice_dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )
        # Switch them and update
        full_dataset['distribution'], justice_dataset['distribution'] = \
            justice_dataset['distribution'], full_dataset['distribution']

        full_package_id = push_dataset_to_ckan(
            self.full_catalog,
            'oficina-de-muestra',
            full_dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )
        justice_package_id = push_dataset_to_ckan(
            self.justice_catalog,
            'oficina-de-muestra',
            justice_dataset_id,
            self.portal_url,
            self.apikey,
            catalog_id=catalog_id,
        )
        # Switch them back
        full_dataset['distribution'], justice_dataset['distribution'] = \
            justice_dataset['distribution'], full_dataset['distribution']

        data_dict = {'id': full_package_id}
        full_package = self.portal.call_action(
            'package_show', data_dict=data_dict)
        data_dict = {'id': justice_package_id}
        justice_package = self.portal.call_action(
            'package_show', data_dict=data_dict)

        self.assertEqual(len(full_package['resources']), len(
            justice_dataset['distribution']))
        self.assertEqual(len(justice_package['resources']), len(
            full_dataset['distribution']))

        for resource, justice_distribution in zip(
                full_package['resources'], justice_dataset['distribution']):
            self.assertEqual(
                'same-catalog-id_' +
                justice_distribution['identifier'],
                resource['id'])

        for resource, full_distribution in zip(
                justice_package['resources'], full_dataset['distribution']):
            self.assertEqual('same-catalog-id_' +
                             full_distribution['identifier'], resource['id'])


class RemoveTestCase(unittest.TestCase):
    CKAN_VCR = vcr.VCR(
        path_transformer=vcr.VCR.ensure_suffix('.yaml'),
        cassette_library_dir=os.path.join(
            "tests",
            "cassetes",
            "ckan_integration",
            "remove_dataset"),
        filter_headers=[
            'Authorization',
            'X-CKAN-API-Key'],
        record_mode='once')

    test_datasets = [{'id': '1.1',
                      'owner_org': 'org-1',
                      'author': 'author_a',
                      'name': 'data1_1'},
                     {'id': '2.1',
                      'owner_org': 'org-2',
                      'author': 'author_a',
                      'name': 'data2_1'},
                     {'id': '2.2',
                      'owner_org': 'org-2',
                      'author': 'author_b',
                      'name': 'data2_2'},
                     {'id': '3.1',
                      'owner_org': 'org-3',
                      'author': 'author_a',
                      'name': 'data3_1'},
                     {'id': '3.2',
                      'owner_org': 'org-3',
                      'author': 'author_b',
                      'name': 'data3_2'},
                     {'id': '3.3',
                      'owner_org': 'org-3',
                      'author': 'author_c',
                      'name': 'data3_3'}]

    portal_url = 'http://localhost:8080'
    apikey = "<apikey>"

    @CKAN_VCR.use_cassette()
    def setUp(self):
        self.ckan_portal = RemoteCKAN(self.portal_url, apikey=self.apikey)
        for dataset in self.test_datasets:
            try:
                self.ckan_portal.call_action(
                    'dataset_purge', data_dict={'id': dataset['id']})
            except NotFound:
                continue
        for dataset in self.test_datasets:
            self.ckan_portal.call_action('package_create', data_dict=dataset)

    @CKAN_VCR.use_cassette()
    def tearDown(self):
        for dataset in self.test_datasets:
            try:
                self.ckan_portal.call_action(
                    'dataset_purge', data_dict={'id': dataset['id']})
            except NotFound:
                continue

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_id(self):
        filter_in = {'dataset': {'identifier': '1.1'}}
        remove_datasets_from_ckan(
            self.portal_url, self.apikey, filter_in=filter_in)
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data1_1' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_title(self):
        filter_in = {'dataset': {'title': 'data3_3'}}
        remove_datasets_from_ckan(
            self.portal_url, self.apikey, filter_in=filter_in)
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data3_3' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_organization(self):
        remove_datasets_from_ckan(
            self.portal_url, self.apikey, organization='org-2')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data2_1' not in package_list)
        self.assertTrue('data2_2' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_publisher_and_organization(self):
        filter_in = {'dataset': {'publisher': {
            'name': 'author_b', 'mbox': None}}}
        remove_datasets_from_ckan(
            self.portal_url,
            self.apikey,
            filter_in=filter_in,
            organization='org-3')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data3_2' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_filter_out(self):
        filter_out = {'dataset': {'publisher': {
            'name': 'author_b', 'mbox': None}}}
        remove_datasets_from_ckan(
            self.portal_url, self.apikey, filter_out=filter_out)
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data2_2' in package_list)
        self.assertTrue('data3_2' in package_list)
        self.assertTrue('data2_1' not in package_list)
        self.assertTrue('data3_3' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_remove_dataset_by_filter_out_and_organization(self):
        filter_out = {'dataset': {'publisher': {
            'name': 'author_b', 'mbox': None}}}
        remove_datasets_from_ckan(
            self.portal_url,
            self.apikey,
            filter_out=filter_out,
            organization='org-3')
        package_list = self.ckan_portal.call_action('package_list')
        self.assertTrue('data3_1' not in package_list)
        self.assertTrue('data3_3' not in package_list)

    @CKAN_VCR.use_cassette()
    def test_empty_query_result(self):
        filter_in = {'dataset': {'identifier': '4.4'}}
        package_list_pre = self.ckan_portal.call_action('package_list')
        remove_datasets_from_ckan(
            self.portal_url,
            self.apikey,
            filter_in=filter_in,
            organization='org-4')
        package_list_post = self.ckan_portal.call_action('package_list')
        self.assertEqual(len(package_list_pre), len(package_list_post))

    @CKAN_VCR.use_cassette()
    def test_with_no_parametres(self):
        package_list_pre = self.ckan_portal.call_action('package_list')

        remove_datasets_from_ckan(self.portal_url, self.apikey)

        package_list_post = self.ckan_portal.call_action('package_list')
        self.assertEqual(len(package_list_pre), len(package_list_post))
