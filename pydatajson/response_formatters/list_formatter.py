# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pydatajson.response_formatters.validation_response_formatter import \
    ValidationResponseFormatter


class ListFormatter(ValidationResponseFormatter):

    def format(self):
        rows_catalog = []
        validation_result = {
            "catalog_title": self.response["error"]["catalog"]["title"],
            "catalog_status": self.response["error"]["catalog"]["status"],
        }
        for error in self.response["error"]["catalog"]["errors"]:
            catalog_result = dict(validation_result)
            catalog_result.update({
                "catalog_error_message": error["message"],
                "catalog_error_location": ", ".join(error["path"]),
            })
            rows_catalog.append(catalog_result)

        if len(self.response["error"]["catalog"]["errors"]) == 0:
            catalog_result = dict(validation_result)
            catalog_result.update({
                "catalog_error_message": None,
                "catalog_error_location": None
            })
            rows_catalog.append(catalog_result)

        # crea una lista de dicts para volcarse en una tabla (dataset)
        rows_dataset = []
        for dataset in self.response["error"]["dataset"]:
            validation_result = {
                "dataset_title": dataset["title"],
                "dataset_identifier": dataset["identifier"],
                "dataset_list_index": dataset["list_index"],
                "dataset_status": dataset["status"]
            }
            for error in dataset["errors"]:
                dataset_result = dict(validation_result)
                dataset_result.update({
                    "dataset_error_message": error["message"],
                    "dataset_error_location": error["path"][-1]
                })
                rows_dataset.append(dataset_result)

            if len(dataset["errors"]) == 0:
                dataset_result = dict(validation_result)
                dataset_result.update({
                    "dataset_error_message": None,
                    "dataset_error_location": None
                })
                rows_dataset.append(dataset_result)

        return {"catalog": rows_catalog, "dataset": rows_dataset}
