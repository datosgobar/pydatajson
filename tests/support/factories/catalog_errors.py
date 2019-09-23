# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tests.support.factories.dataset_errors import update_dataset_error, BROKEN_LINK_ERROR
from tests.support.utils import jsonschema_str


def catalog_error(options=None):
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
    return catalog_error({
        'message': "%s is a required property" % jsonschema_str('dataset'),
        'dataset': None,
    })


def missing_catalog_title():
    error_report = catalog_error({
        'message': "%s is a required property" % jsonschema_str('title'),
        'title': None,
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def missing_catalog_description():
    error_report = catalog_error({
        'message': "%s is a required property" % jsonschema_str('description'),
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def invalid_catalog_publisher_type():
    return catalog_error({
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
    return catalog_error({
        "error_code": 2,
        "message": "%s is not a %s" %
                   (jsonschema_str('datosATmodernizacion.gob.ar'),
                    jsonschema_str('email')),
        "validator": "format",
        "validator_value": "email",
        "path": ["publisher", "mbox"],
        "instance": "datosATmodernizacion.gob.ar"
    })


def null_catalog_publisher():
    error_report = catalog_error({
        "error_code": 2,
        "message": "None is not of type %s" % jsonschema_str('object'),
        "path": ['publisher'],
        "validator": 'type',
        "validator_value": 'object',
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def empty_mandatory_string():
    error_report = catalog_error({
        "error_code": 2,
        "message": "%s is too short" % jsonschema_str(''),
        "path": ['description'],
        "validator": 'minLength',
        "validator_value": 1,
        "instance": "",
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def malformed_date():
    error_report = catalog_error({
        "instance": "2016/04/14",
        "validator": "anyOf",
        "path": [
            "issued"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('2016/04/14'),
        "error_code": 2,
        "validator_value": [
            {
                "type": "string",
                "format": "date"
            },
            {
                "type": "string",
                "format": "date-time"
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

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def malformed_datetime():
    error_report = catalog_error({
        "instance": "2016-04-1419:48:05.433640-03:00",
        "validator": "anyOf",
        "path": [
            "issued"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('2016-04-1419:48:05.433640-03:00'),
        "error_code": 2,
        "validator_value": [
            {
                "type": "string",
                "format": "date"
            },
            {
                "type": "string",
                "format": "date-time"
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

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def malformed_datetime2():
    error_report =  catalog_error({
        "instance": "2016-04-54T19:48:05.433640-03:00",
        "validator": "anyOf",
        "path": [
            "issued"
        ],
        "message": "%s is not valid under any of the given schemas"
                   % jsonschema_str('2016-04-54T19:48:05.433640-03:00'),
        "error_code": 2,
        "validator_value": [
            {
                "type": "string",
                "format": "date"
            },
            {
                "type": "string",
                "format": "date-time"
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

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def malformed_email():
    error_report = catalog_error({
        "instance": "datosATmodernizacion.gob.ar",
        "validator": "format",
        "path": [
            "publisher",
            "mbox"
        ],
        "message": "%s is not a %s"
                   % (jsonschema_str('datosATmodernizacion.gob.ar'),
                      jsonschema_str('email')),
        "error_code": 2,
        "validator_value": "email"
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def malformed_uri():
    error_report =  catalog_error({
        "instance": "datos.gob.ar/superThemeTaxonomy.json",
        "validator": "format",
        "path": [
            "superThemeTaxonomy"
        ],
        "message": "%s is not a %s"
                   % (jsonschema_str('datos.gob.ar/superThemeTaxonomy.json'),
                      jsonschema_str('uri')),
        "error_code": 2,
        "validator_value": "uri"
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def invalid_theme_taxonomy():
    error_report = catalog_error({
        "instance": None,
        "validator": "repeatedValue",
        "path": [
            "catalog",
            "themeTaxonomy"
        ],
        "message": "Los ids [%s] estan repetidos en mas de un `theme`"
                   % jsonschema_str('convocatorias'),
        "error_code": 2,
        "validator_value": "Chequea ids duplicados en themeTaxonomy"
    })

    return update_dataset_error(error_report, BROKEN_LINK_ERROR)


def missing_dataset():
    return catalog_error({
        "instance": None,
        "validator": "required",
        "path": [],
        "message": "%s is a required property"
                   % jsonschema_str('dataset'),
        "error_code": 1,
        "validator_value": [
            "dataset",
            "title",
            "description",
            "publisher",
            "superThemeTaxonomy"
        ],
        "dataset": None,
    })


def repeated_downloadURL():
    return catalog_error({
        "instance": None,
        "validator": "repeatedValue",
        "path": [
            "catalog",
            "dataset"
        ],
        "message": "DownloadURL's [%s] estan repetidas en mas de "
                   "un `distribution`"
                   % jsonschema_str('http://186.33.211.253/dataset/'
                                    '99db6631-d1c9-470b-a73e-c62daa32c420/'
                                    'resource/'
                                    '4b7447cb-31ff-4352-96c3-589d212e1cc9/'
                                    'download/'
                                    'convocatorias-abiertas-anio-2015.csv'),
        "error_code": 2,
        "validator_value": "Chequea downloadURL's duplicados "
                           "en las distribuciones"
    })
