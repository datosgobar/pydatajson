# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from openpyxl.styles import Alignment, Font

from pydatajson import writers
from pydatajson.response_formatters.list_formatter import ListFormatter
from pydatajson.response_formatters.validation_response_formatter import\
    ValidationResponseFormatter


class TablesFormatter(ValidationResponseFormatter):

    def __init__(self, response, export_path):
        super(TablesFormatter, self).__init__(response)
        self.export_path = export_path

    def format(self):
        validation_lists = ListFormatter(self.response).format()

        column_styles = {
            "catalog": {
                "catalog_status": {"width": 20},
                "catalog_error_location": {"width": 40},
                "catalog_error_message": {"width": 40},
                "catalog_title": {"width": 20},
            },
            "dataset": {
                "dataset_error_location": {"width": 20},
                "dataset_identifier": {"width": 40},
                "dataset_status": {"width": 20},
                "dataset_title": {"width": 40},
                "dataset_list_index": {"width": 20},
                "dataset_error_message": {"width": 40},
            }
        }
        cell_styles = {
            "catalog": [
                {"alignment": Alignment(vertical="center")},
                {"row": 1, "font": Font(bold=True)},
            ],
            "dataset": [
                {"alignment": Alignment(vertical="center")},
                {"row": 1, "font": Font(bold=True)},
            ]
        }

        # crea tablas en un sólo excel o varios CSVs
        writers.write_tables(
            tables=validation_lists, path=self.export_path,
            column_styles=column_styles, cell_styles=cell_styles
        )
