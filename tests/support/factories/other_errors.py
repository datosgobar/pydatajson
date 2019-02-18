# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from tests.support.utils import jsonschema_str


def gen_error(catalog_error, dataset_error):
    return {
        "status": "ERROR",
        "error": {
            "catalog": {
                "status": "ERROR",
                "errors": [
                    catalog_error
                ],
                "title": "Datos Argentina"
            },
            "dataset": [
                {
                    "status": "ERROR",
                    "identifier": "99db6631-d1c9-470b-a73e-c62daa32c420",
                    "list_index": 0,
                    "errors": [
                        dataset_error,
                    ],
                    "title": "Sistema de contrataciones electrónicas"
                }
            ]
        }
    }


def multiple_missing_descriptions():
    return gen_error({
        "instance": None,
        "validator": "required",
        "path": [],
        "message": "%s is a required property" % jsonschema_str('description'),
        "error_code": 1,
        "validator_value": [
            "dataset",
            "title",
            "description",
            "publisher",
            "superThemeTaxonomy"
        ]
    }, {
        "instance": None,
        "validator": "required",
        "path": [
            "dataset",
            0
        ],
        "message": "%s is a required property" % jsonschema_str('description'),
        "error_code": 1,
        "validator_value": [
            "title",
            "description",
            "publisher",
            "superTheme",
            "distribution",
            "accrualPeriodicity",
            "issued",
            "identifier"
        ]
    })


def invalid_multiple_fields_type():
    return gen_error({
        "instance": [
            "Ministerio de Modernización",
            "datos@modernizacion.gob.ar"
        ],
        "validator": "type",
        "path": [
            "publisher"
        ],
        "message": "[%s, %s] is not of type %s" % (
            jsonschema_str('Ministerio de Modernización'),
            jsonschema_str('datos@modernizacion.gob.ar'),
            jsonschema_str('object'),
        ),
        "error_code": 2,
        "validator_value": "object"
    }, {
        "instance": "5120",
        "validator": "anyOf",
        "path": [
            "dataset",
            0,
            "distribution",
            0,
            "byteSize"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('5120'),
        "error_code": 2,
        "validator_value": [
            {
                "type": "integer"
            },
            {
                '$ref': 'mixed-types.json#emptyValue'
            }
        ]
    })
