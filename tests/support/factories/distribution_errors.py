# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from tests.support.utils import jsonschema_str


def distribution_error():
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
                                0,
                                "distribution",
                                0
                            ],
                            "message": "%s is a required property"
                                       % jsonschema_str('title'),
                            "error_code": 1,
                            "validator_value": [
                                "accessURL",
                                "downloadURL",
                                "title",
                                "issued",
                                "identifier"
                            ]
                        }
                    ],
                    "title": "Sistema de contrataciones electrónicas"
                }
            ]
        }
    }


def missing_distribution_title():
    return distribution_error()
