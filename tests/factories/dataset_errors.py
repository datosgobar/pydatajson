# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from tests.factories.utils import jsonschema_str


def dataset_error(string, dataset_title=None):
    return {
        "status": "ERROR",
        "error": {
            "catalog": {
                "status": "OK",
                "errors": [],
                "title": "Datos Argentina"
            },
            "dataset": [
                {
                    "status": "ERROR",
                    "identifier": "99db6631-d1c9-470b-a73e-c62daa32c420",
                    "list_index": 0,
                    "errors": [
                        {
                            "instance": None,
                            "validator": "required",
                            "path": [
                                "dataset",
                                0
                            ],
                            "message": "%s is a required property" % jsonschema_str(string),
                            "error_code": 1,
                            "validator_value": [
                                "title",
                                "description",
                                "publisher",
                                "superTheme",
                                "distribution",
                                "accrualPeriodicity",
                                "issued"
                            ]
                        }
                    ],
                    "title": dataset_title
                }
            ]
        }
    }


def missing_dataset_title():
    return dataset_error('title')


def missing_dataset_description():
    return dataset_error('description', dataset_title='Sistema de contrataciones electrónicas')
