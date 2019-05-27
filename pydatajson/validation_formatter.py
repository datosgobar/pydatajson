import abc

from openpyxl.styles import Alignment, Font

from pydatajson import writers


class ValidationResponseFormatter(abc.ABC):

    def __init__(self, response):
        self.response = response

    @abc.abstractmethod
    def format(self):
        raise NotImplementedError


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


class TablesFormatter(ValidationResponseFormatter):

    def __init__(self, response, export_path):
        super().__init__(response)
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
