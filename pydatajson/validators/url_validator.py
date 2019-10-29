#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

import requests
from requests import RequestException, Timeout

from pydatajson.constants import EXCEPTION_STATUS_CODES, \
    INVALID_STATUS_CODES_REGEX
from pydatajson.validators.simple_validator import SimpleValidator


class UrlValidator(SimpleValidator):

    def __init__(self, catalog, verify_ssl, url_check_timeout):
        super(UrlValidator, self).__init__(catalog)
        self.verify_ssl = verify_ssl
        self.url_check_timeout = url_check_timeout

    def validate(self):
        raise NotImplementedError

    def is_working_url(self, url):
        try:
            response = requests.head(url,
                                     timeout=self.url_check_timeout,
                                     verify=self.verify_ssl)
            matches = []
            if response.status_code not in EXCEPTION_STATUS_CODES:
                matches = \
                    [re.match(pattern, str(response.status_code)) is not None
                     for pattern in INVALID_STATUS_CODES_REGEX]
            return True not in matches, response.status_code
        except Timeout:
            return False, 408
        except (RequestException, Exception):
            return False, None
