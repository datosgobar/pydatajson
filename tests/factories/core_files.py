# -*- coding: utf-8 -*-


from __future__ import unicode_literals

FULL_DATA_RESPONSE = {
    "status": "OK",
    "error": {
        "catalog": {
            "status": "OK",
            "errors": [],
            "title": "Datos Argentina"
        },
        "dataset": [
            {
                "status": "OK",
                "identifier": "99db6631-d1c9-470b-a73e-c62daa32c777",
                "list_index": 0,
                "errors": [],
                "title": "Sistema de contrataciones electrónicas"
            },
            {
                "status": "OK",
                "identifier": "99db6631-d1c9-470b-a73e-c62daa32c420",
                "list_index": 1,
                "errors": [],
                "title": "Sistema de contrataciones electrónicas (sin datos)"
            }
        ]
    }
}

TEST_FILE_RESPONSES = {
    # Tests de CAMPOS REQUERIDOS
    # Tests de inputs válidos
    'full_data': FULL_DATA_RESPONSE,
    # Un datajson con valores correctos únicamente para las claves requeridas
    'minimum_data': None,
    # Tests de inputs inválidos
    # 'missing_catalog_title': None,
    # 'missing_catalog_description': None,
    # 'missing_catalog_dataset': None,
    # 'missing_dataset_title': None,
    # 'missing_dataset_description': None,
    # 'missing_distribution_title': None,
    'multiple_missing_descriptions': None,

    # Tests de TIPOS DE CAMPOS
    # Tests de inputs válidos
    'null_dataset_theme': None,
    'null_field_description': None,
    # Tests de inputs inválidos
    'invalid_catalog_publisher_type': None,
    'invalid_publisher_mbox_format': None,
    # Catalog_publisher y distribution_bytesize fallan
    'invalid_multiple_fields_type': None,
    'invalid_dataset_theme_type': None,
    'invalid_field_description_type': None,
    'null_catalog_publisher': None,
    # La clave requerida catalog["description"] NO puede ser str vacía
    'empty_mandatory_string': None,
    'empty_optional_string': None,
    # dataset["accrualPeriodicity"] no cumple con el patrón esperado
    'malformed_accrualperiodicity': None,
    # catalog["issued"] no es una fecha ISO 8601 válida
    'malformed_date': None,
    # catalog["issued"] no es una fecha y hora ISO 8601 válida
    'malformed_datetime': None,
    # catalog["issued"] no es una fecha y hora ISO 8601 válida
    'malformed_datetime2': None,
    # dataset["temporal"] no es un rango de fechas ISO 8601 válido
    'malformed_temporal': None,
    # dataset["temporal"] no es un rango de fechas ISO 8601 válido
    'malformed_temporal2': None,
    # catalog["publisher"]["mbox"] no es un email válido
    'malformed_email': None,
    # catalog["superThemeTaxonomy"] no es una URI válida
    'malformed_uri': None,
    'invalid_dataset_type': None,
    'invalid_themeTaxonomy': None,
    'missing_dataset': None,
    'too_long_field_title': None,
    # Prueba que las listas con info de errores se generen correctamente
    #   en presencia de 7 errores de distinto tipo y jerarquía
    'several_assorted_errors': None,

}


def jsonschema_str(string):
    return repr(string)


DEFAULT_OPTIONS = {
    'title': "Datos Argentina",
    'message': None,
    'dataset': [
        {
            "status": "OK",
            "identifier": "99db6631-d1c9-470b-a73e-c62daa32c420",
            "list_index": 0,
            "errors": [],
            "title": "Sistema de contrataciones electrónicas"
        }
    ]
}


def error_response(options=None):
    default_options = DEFAULT_OPTIONS.copy()
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
                        "instance": None,
                        "validator": "required",
                        "path": [],
                        "message": options['message'],
                        "error_code": 1,
                        "validator_value": [
                            "dataset",
                            "title",
                            "description",
                            "publisher",
                            "superThemeTaxonomy"
                        ]
                    }
                ],
                "title": options['title'],
            },
            "dataset": options['dataset'],
        }
    }


def missing_catalog_dataset():
    return error_response({
        'message': "%s is a required property" % jsonschema_str('dataset'),
        'dataset': None,
    })


def missing_catalog_title():
    return error_response({
        'message': "%s is a required property" % jsonschema_str('title'),
        'title': None,
    })


def missing_catalog_description():
    return error_response({
        'message': "%s is a required property" % jsonschema_str('description'),
    })


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
                            "message": "%s is a required property" % jsonschema_str('title'),
                            "error_code": 1,
                            "validator_value": [
                                "accessURL",
                                "downloadURL",
                                "title",
                                "issued"
                            ]
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


def missing_distribution_title():
    return distribution_error()


DATAJSON_RESULTS = {
    'missing_catalog_title': missing_catalog_title(),
    'missing_catalog_description': missing_catalog_description(),
    'missing_catalog_dataset': missing_catalog_dataset(),

    'missing_dataset_title': missing_dataset_title(),
    'missing_dataset_description': missing_dataset_description(),

    'missing_distribution_title': missing_distribution_title()
}

TEST_FILE_RESPONSES.update(DATAJSON_RESULTS)
