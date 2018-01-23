import unittest
import os
import re
from dateutil import parser, tz
from ckanapi import RemoteCKAN
from .context import pydatajson

SAMPLES_DIR = os.path.join("tests", "samples")


class FederationTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    @classmethod
    def setUpClass(cls):
        catalog = pydatajson.DataJson(cls.get_sample('minimum_data.json'))
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
        plain_replicated_attributes = [('title', 'title'),
                                       ('notes', 'description'),
                                       ('license_id', 'license'),
                                       ('url', 'landingPage')]
        for fst, snd in plain_replicated_attributes:
            self.assertEqual(self.dataset.get(snd), self.package.get(fst))

    def test_dataset_nested_replicated_attributes_stay_the_same(self):
        contact_point_nested = [('maintainer', 'fn'),
                                ('maintainer_email', 'hasEmail')]
        for fst, snd in contact_point_nested:
            self.assertEqual(self.dataset.get('contactPoint', {}).get(snd), self.package.get(fst))

        publisher_nested = [('author', 'name'),
                            ('author_email', 'mbox')]
        for fst, snd in publisher_nested:
            self.assertEqual(self.dataset.get('publisher').get(snd), self.package.get(fst))

    def test_dataset_array_attributes_are_correct(self):
        groups = [group['name'] for group in self.package.get('groups', [])]
        super_themes = [re.sub(r'(\W+|-)', '', s_theme).lower() for s_theme in self.dataset.get('superTheme')]
        self.assertItemsEqual(super_themes, groups)

        tags = [tag['name'] for tag in self.package['tags']]
        themes_and_keywords = self.dataset.get('theme', []) + self.dataset.get('keyword', [])
        themes_and_keywords = list(set(themes_and_keywords))
        self.assertItemsEqual(themes_and_keywords, tags)

    def test_resources_replicated_attributes_stay_the_same(self):
        for resource in self.package['resources']:
            distribution = next(x for x in self.dataset['distribution'] if x['identifier'] == resource['id'])
            replicated_attributes = [('name', 'title'),
                                     ('url', 'downloadURL'),
                                     ('mimetype', 'mediaType')]
            for fst, snd in replicated_attributes:
                if distribution.get(snd):
                    self.assertEqual(distribution.get(snd), resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))

    def test_resources_transformed_attributes_are_correct(self):
        for resource in self.package['resources']:
            distribution = next(x for x in self.dataset['distribution'] if x['identifier'] == resource['id'])
            if distribution.get('byteSize'):
                self.assertEqual(unicode(distribution.get('byteSize')), resource.get('size'))
            else:
                self.assertIsNone(resource.get('size'))

            description_attributes = [('description', 'description'), ('format', 'format')]
            for fst, snd in description_attributes:
                if distribution.get('snd'):
                    self.assertEqual(distribution.get(snd), resource.get(fst))
                else:
                    self.assertEqual(u'', resource.get(fst))

            time_attributes = [('created', 'issued'), ('last_modified', 'modified')]
            for fst, snd in time_attributes:
                if distribution.get(snd):
                    dist_time = parser.parse(distribution.get(snd)).astimezone(tz.tzutc())
                    dist_time = dist_time.replace(tzinfo=None).isoformat()
                    self.assertEqual(unicode(dist_time), resource.get(fst))
                else:
                    self.assertIsNone(resource.get(fst))


if __name__ == '__main__':
    unittest.main()
