#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydatajson import threading_helper
from pydatajson.validators.url_validator import UrlValidator


class DistributionDownloadUrlsValidator(UrlValidator):

    def validate(self):
        async_results = []
        for dataset in self.catalog.get('dataset', []):
            distribution_urls = \
                [distribution.get('downloadURL', '')
                 for distribution in dataset.get('distribution', [])]
            async_results += threading_helper \
                .apply_threading(distribution_urls,
                                 self.is_working_url,
                                 self.threads_count)

        result = 0
        for res, _ in async_results:
            result += res

        return result
