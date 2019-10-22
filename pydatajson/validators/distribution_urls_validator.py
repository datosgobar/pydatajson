#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pydatajson.custom_exceptions as ce
from pydatajson import threading_helper, constants
from pydatajson.validators.url_validator import UrlValidator


class DistributionUrlsValidator(UrlValidator):

    def validate(self):
        datasets = self.catalog.get('dataset')

        metadata = []
        urls = []
        for dataset_idx, dataset in enumerate(datasets):
            distributions = dataset.get('distribution')

            for distribution_idx, distribution in enumerate(distributions):
                distribution_title = distribution.get('title')
                access_url = distribution.get('accessURL')
                download_url = distribution.get('downloadURL')

                metadata.append({
                    "dataset_idx": dataset_idx,
                    "dist_idx": distribution_idx,
                    "dist_title": distribution_title
                })
                urls += [access_url, download_url]

        sync_res = threading_helper \
            .apply_threading(urls,
                             self.is_working_url,
                             constants.CANT_THREADS_BROKEN_URL_VALIDATOR)

        for i in range(len(metadata)):
            actual_metadata = metadata[i]
            dataset_idx = actual_metadata["dataset_idx"]
            distribution_idx = actual_metadata["dist_idx"]
            distribution_title = actual_metadata["dist_title"]

            k = i * 2
            access_url = urls[k]
            download_url = urls[k + 1]

            access_url_is_valid, access_url_status_code = sync_res[k]
            download_url_is_valid, download_url_status_code = sync_res[k + 1]

            if not access_url_is_valid:
                yield ce.BrokenAccessUrlError(dataset_idx,
                                              distribution_idx,
                                              distribution_title,
                                              access_url,
                                              access_url_status_code)
            if not download_url_is_valid:
                yield ce.BrokenDownloadUrlError(dataset_idx,
                                                distribution_idx,
                                                distribution_title,
                                                download_url,
                                                download_url_status_code)
