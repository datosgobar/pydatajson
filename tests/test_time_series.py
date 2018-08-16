from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
from pydatajson.core import DataJson
from pydatajson.time_series import get_distribution_time_index,\
    distribution_has_time_index, dataset_has_time_series
from pydatajson.custom_exceptions import DistributionTimeIndexNonExistentError

SAMPLES_DIR = os.path.join("tests", "samples")


class TimeSeriesTestCase(unittest.TestCase):

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(SAMPLES_DIR, sample_filename)

    def setUp(self):
        ts_catalog = DataJson(self.get_sample('time_series_data.json'))
        full_catalog = DataJson(self.get_sample('full_data.json'))
        self.ts_dataset = ts_catalog.datasets[0]
        self.non_ts_datasets = full_catalog.datasets[0]
        self.ts_distribution = ts_catalog.distributions[1]
        self.non_ts_distribution = full_catalog.distributions[0]

    def test_get_distribution_time_index(self):
        self.assertEqual(
            'indice_tiempo',
            get_distribution_time_index(
                self.ts_distribution))
        with self.assertRaises(DistributionTimeIndexNonExistentError):
            get_distribution_time_index(self.non_ts_distribution)

    def test_distribution_has_time_index(self):
        self.assertTrue(distribution_has_time_index(self.ts_distribution))
        self.assertFalse(distribution_has_time_index(self.non_ts_distribution))
        self.ts_distribution['field'] = ['p', 'r', 'o', 'b', 'l', 'e', 'm']
        self.assertFalse(distribution_has_time_index(self.ts_distribution))

    def test_dataset_has_time_series(self):
        self.assertTrue(dataset_has_time_series(self.ts_dataset))
        self.assertFalse(dataset_has_time_series(self.non_ts_datasets))
