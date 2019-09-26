# -*- coding: utf-8 -*-


from __future__ import unicode_literals

from tests.support.utils import jsonschema_str


def dataset_error(options=None):
    default_options = {
        "dataset_title": "Sistema de contrataciones electrónicas",
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
            },
            {
                "pattern": "^EVENTUAL$",
                "type": "string"
            },
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
                    "title": options['dataset_title']
                }
            ]
        }
    }


def missing_dataset_title():
    return dataset_error({
        "instance": None,
        "validator": "required",
        "path": [
            "dataset",
            0
        ],
        "message": "%s is a required property" % jsonschema_str('title'),
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
        ],
        "dataset_title": None,
    })


def missing_dataset_description():
    return dataset_error({
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
        ],
        "dataset_title": 'Sistema de contrataciones electrónicas',
    })


def malformed_accrualperiodicity():
    return dataset_error({
        'message': "%s is not valid under any of the given schemas"
                   % jsonschema_str('RP1Y'),
    })


def malformed_temporal():
    return dataset_error({
        "instance": "2015-01-1/2015-12-31",
        "validator": "anyOf",
        "path": [
            "dataset",
            0,
            "temporal"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('2015-01-1/2015-12-31'),
        "error_code": 2,
        "validator_value": [
            {
                "pattern":
                    "^(\\d{4}-\\d\\d-\\d\\d(T\\d\\d:\\d\\d:\\d\\d(\\.\\d+)?)"
                    "?(([+-]\\d\\d:\\d\\d)|Z)?)\\/(\\d{4}-\\d\\d-\\d\\"
                    "d(T\\d\\d:\\d\\d:\\d\\d(\\.\\d+)?)"
                    "?(([+-]\\d\\d:\\d\\d)|Z)?)$",
                "type": "string"
            },
            {
                "type": "null"
            },
            {
                "type": "string",
                "maxLength": 0
            }
        ]
    })


def malformed_temporal2():
    return dataset_error({
        "instance": "2015-01-10/31-12-2015",
        "validator": "anyOf",
        "path": [
            "dataset",
            0,
            "temporal"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('2015-01-10/31-12-2015'),
        "error_code": 2,
        "validator_value": [
            {
                "pattern": "^(\\d{4}-\\d\\d-\\d\\d"
                           "(T\\d\\d:\\d\\d:\\d\\d(\\.\\d+)?)"
                           "?(([+-]\\d\\d:\\d\\d)|Z)?)\\/"
                           "(\\d{4}-\\d\\d-\\d\\d(T\\d\\d:\\d\\d:\\d"
                           "\\d(\\.\\d+)?)?(([+-]\\d\\d:\\d\\d)|Z)?)$",
                "type": "string"
            },
            {
                "type": "null"
            },
            {
                "type": "string",
                "maxLength": 0
            }
        ]
    })


def too_long_field_title():
    return dataset_error({
        "instance": "organismo_unidad_operativa_contrataciones_desc_"
                    "organismo_unidad_operativa_contrataciones_desc",
        "validator": "anyOf",
        "path": [
            "dataset",
            0,
            "distribution",
            0,
            "field",
            3,
            "title"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('organismo_unidad_operativa_contrataciones'
                                    '_desc_organismo_unidad_operativa_'
                                    'contrataciones_desc'),
        "error_code": 2,
        "validator_value": [
            {
                "type": "string",
                "maxLength": 60
            },
            {
                "type": "null"
            }
        ]
    })
