# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pydatajson.response_formatters.list_formatter import ListFormatter
from pydatajson.response_formatters.tables_formatter import TablesFormatter


def format_response(validation, export_path, fmt):
    if export_path:
        return TablesFormatter(validation, export_path).format()
    elif fmt == "dict":
        return validation
    elif fmt == "list":
        return ListFormatter(validation).format()
    else:
        raise Exception("No se reconoce el formato {}".format(fmt))
