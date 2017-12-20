# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from tests.factories.utils import jsonschema_str


def gen_dataset_error(options=None):
    default_options = {
        "instance": "RP1Y",
        "validator": "anyOf",
        "path": [
            "dataset",
            0,
            "accrualPeriodicity"
        ],
        "message": "u'RP1Y' is not valid under any of the given schemas",
        "error_code": 2,
        "validator_value": [
            {
                "pattern": "^R/P\\d+(\\.\\d+)?[Y|M|W|D]$",
                "type": "string"
            },
            {
                "pattern": "^R/PT\\d+(\\.\\d+)?[H|M|S]$",
                "type": "string"
            },
            {
                "pattern": "^eventual$",
                "type": "string"
            }
        ]
    }
    if options is not None:
        default_options.update(options)
    options = default_options
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
                            "instance": options['instance'],
                            "validator": options['validator'],
                            "path": options['path'],
                            "message": options['message'],
                            "error_code": options['error_code'],
                            "validator_value": options['validator_value'],
                        }
                    ],
                    "title": "Sistema de contrataciones electrónicas"
                }
            ]
        }
    }


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


def malformed_accrualperiodicity():
    return gen_dataset_error({
        'message': "%s is not valid under any of the given schemas" % jsonschema_str('RP1Y'),
    })
