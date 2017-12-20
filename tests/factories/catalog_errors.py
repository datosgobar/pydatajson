# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .utils import jsonschema_str


def catalog_error_response(options=None):
    default_options = {
        'title': "Datos Argentina",
        'message': None,
        "validator": "required",
        "path": [],
        "instance": None,
        'dataset': [
            {
                "status": "OK",
                "identifier": "99db6631-d1c9-470b-a73e-c62daa32c420",
                "list_index": 0,
                "errors": [],
                "title": "Sistema de contrataciones electrónicas"
            }
        ],
        "error_code": 1,
        "validator_value": [
            "dataset",
            "title",
            "description",
            "publisher",
            "superThemeTaxonomy"
        ]
    }

    if options is not None:
        default_options.update(options)
    options = default_options
    return {
        "status": "ERROR",
        "error": {
            "catalog": {
                "status": "ERROR",
                "errors": [
                    {
                        "instance": options['instance'],
                        "validator": options['validator'],
                        "path": options['path'],
                        "message": options['message'],
                        "error_code": options["error_code"],
                        "validator_value": options['validator_value'],
                    }
                ],
                "title": options['title'],
            },
            "dataset": options['dataset'],
        }
    }


def missing_catalog_dataset():
    return catalog_error_response({
        'message': "%s is a required property" % jsonschema_str('dataset'),
        'dataset': None,
    })


def missing_catalog_title():
    return catalog_error_response({
        'message': "%s is a required property" % jsonschema_str('title'),
        'title': None,
    })


def missing_catalog_description():
    return catalog_error_response({
        'message': "%s is a required property" % jsonschema_str('description'),
    })


def invalid_catalog_publisher_type():
    return catalog_error_response({
        'instance': [
            "Ministerio de Modernización",
            "datos@modernizacion.gob.ar"
        ],
        "validator": "type",
        "path": ["publisher"],

        "message": "[%s, %s] is not of type %s" % (
            jsonschema_str('Ministerio de Modernización'),
            jsonschema_str('datos@modernizacion.gob.ar'),
            jsonschema_str('object'),
        ),
        "error_code": 2,
        "validator_value": "object"
    })


def invalid_publisher_mbox_format():
    return catalog_error_response({
        "error_code": 2,
        "message": "%s is not a %s" % (
        jsonschema_str('datosATmodernizacion.gob.ar'), jsonschema_str('email')),
        "validator": "format",
        "validator_value": "email",
        "path": [
            "publisher",
            "mbox"
        ],
        "instance": "datosATmodernizacion.gob.ar"
    })