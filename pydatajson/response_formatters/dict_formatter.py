# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pydatajson.response_formatters.validation_response_formatter import \
    ValidationResponseFormatter


class DictFormatter(ValidationResponseFormatter):

    def format(self):
        return self.response
