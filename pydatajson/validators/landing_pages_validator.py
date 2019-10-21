#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pydatajson.custom_exceptions as ce
from pydatajson import threading_helper, constants
from pydatajson.validators.url_validator import UrlValidator


class LandingPagesValidator(UrlValidator):

    def validate(self):
        datasets = self.catalog.get('dataset')
        datasets = filter(lambda x: x.get('landingPage'), datasets)

        metadata = []
        urls = []

        for dataset_idx, dataset in enumerate(datasets):
            metadata.append({
                "dataset_idx": dataset_idx,
                "dataset_title": dataset.get('title'),
                "landing_page": dataset.get('landingPage'),
            })
            urls.append(dataset.get('landingPage'))

        sync_res = threading_helper \
            .apply_threading(urls,
                             self.is_working_url,
                             constants.CANT_THREADS_BROKEN_URL_VALIDATOR)

        for i in range(len(sync_res)):
            valid, status_code = sync_res[i]
            act_metadata = metadata[i]
            dataset_idx = act_metadata["dataset_idx"]
            dataset_title = act_metadata["dataset_title"]
            landing_page = act_metadata["landing_page"]

            if not valid:
                yield ce.BrokenLandingPageError(dataset_idx, dataset_title,
                                                landing_page, status_code)
