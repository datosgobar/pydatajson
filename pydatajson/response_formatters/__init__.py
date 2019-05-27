# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pydatajson import custom_exceptions

from pydatajson.response_formatters.dict_formatter import DictFormatter
from pydatajson.response_formatters.list_formatter import ListFormatter
from pydatajson.response_formatters.tables_formatter import TablesFormatter


def format_response(validation, export_path, response_format):
    formats = {
        'table': TablesFormatter(validation, export_path),
        'dict': DictFormatter(validation),
        'list': ListFormatter(validation),
    }
    try:
        return formats[response_format].format()
    except KeyError:
        msg = "No se reconoce el formato {}".format(response_format)
        raise custom_exceptions.FormatNameError(msg)
