import unittest
import os

from ckanapi import RemoteCKAN
from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")


class FederationTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        catalog = pydatajson.DataJson(cls.get_sample('full_data.json'))
        cls.dataset = catalog.datasets[0]
        cls.portal = RemoteCKAN('http://localhost:8080', apikey='fe3c3610-6f7a-4e97-8f47-30c891cf1456')
        cls.dataset_id = catalog.push_dataset_to_ckan(cls.dataset['identifier'], "http://localhost:8080", 'org-test',
                                                      "fe3c3610-6f7a-4e97-8f47-30c891cf1456")

    def setUp(self):
        data_dict = {'id': self.dataset_id}
        self.package = self.portal.call_action('package_show', data_dict=data_dict)

    @classmethod
    def tearDownClass(cls):
        data_dict = {'id': cls.dataset_id}
        cls.portal.call_action('dataset_purge', data_dict=data_dict)

    def test_dataset_plain_replicated_attributes_stay_the_same(self):
        plain_replicated_attributes = {'title': 'title',
                                       'notes': 'description',
                                       'license_id': 'license',
                                       'url': 'landingPage'
                                       }
        for k, v in plain_replicated_attributes.items():
            self.assertEqual(self.dataset.get(v), self.package.get(k))

    def test_dataset_nested_replicated_attributes_stay_the_same(self):
        contact_point_nested = {'maintainer': 'fn',
                                'maintainer_email': 'hasEmail'}
        for k, v in contact_point_nested.items():
            self.assertEqual(self.dataset.get('contactPoint').get(v), self.package.get(k))

        publisher_nested = {'author': 'name',
                            'author_email': 'mbox'}
        for k, v in publisher_nested.items():
            self.assertEqual(self.dataset.get('publisher').get(v), self.package.get(k))

    def test_dataset_array_attributes_are_correct(self):
        groups = [group['name'] for group in self.package.get('groups',[])]
        self.assertItemsEqual(self.dataset.get('superTheme'), groups)

        tags = [tag['name'] for tag in self.package['tags']]
        themes_and_keywords = self.dataset.get('theme', []) + self.dataset.get('keyword', [])
        self.assertItemsEqual(themes_and_keywords, tags)

    def test_resources_replicated_attributes_stay_the_same(self):
        pass

    def test_resources_transformed_attributes_are_correct(self):
        pass


if __name__ == '__main__':
    unittest.main()
