#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mimetypes
import os

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import pydatajson.custom_exceptions as ce
from pydatajson.validators.simple_validator import SimpleValidator

EXTENSIONS_EXCEPTIONS = ["zip", "php", "asp", "aspx"]


class ConsistentDistributionFieldsValidator(SimpleValidator):

    def validate(self):
        for dataset_idx, dataset in enumerate(self.catalog["dataset"]):
            for distribution_idx, distribution in enumerate(
                    dataset["distribution"]):
                for attribute in ['downloadURL', 'fileName']:
                    if not self._format_matches_extension(distribution,
                                                          attribute):
                        yield ce.ExtensionError(dataset_idx, distribution_idx,
                                                distribution, attribute)

    @staticmethod
    def _format_matches_extension(distribution, attribute):
        """Chequea si una extensión podría corresponder a un formato dado."""

        if attribute in distribution and "format" in distribution:
            if "/" in distribution['format']:
                possible_format_extensions = mimetypes.guess_all_extensions(
                    distribution['format'])
            else:
                possible_format_extensions = [
                    '.' + distribution['format'].lower()
                ]

            file_name = urlparse(distribution[attribute]).path
            extension = os.path.splitext(file_name)[-1].lower()

            if attribute == 'downloadURL' and not extension:
                return True

            # hay extensiones exceptuadas porque enmascaran otros formatos
            if extension.lower().replace(".", "") in EXTENSIONS_EXCEPTIONS:
                return True

            if extension not in possible_format_extensions:
                return False

        return True
