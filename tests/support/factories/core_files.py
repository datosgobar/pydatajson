# -*- coding: utf-8 -*-


from __future__ import unicode_literals, absolute_import

from .catalog_errors import missing_catalog_title, \
    missing_catalog_description, \
    missing_catalog_dataset, invalid_catalog_publisher_type,\
    invalid_publisher_mbox_format, null_catalog_publisher,\
    empty_mandatory_string, malformed_date, malformed_datetime, \
    malformed_datetime2, malformed_email, malformed_uri,\
    invalid_theme_taxonomy, missing_dataset, repeated_downloadURL
from .dataset_errors import missing_dataset_title, \
    missing_dataset_description, \
    malformed_accrualperiodicity, malformed_temporal,\
    malformed_temporal2, too_long_field_title
from .distribution_errors import missing_distribution_title
from .other_errors import multiple_missing_descriptions, \
    invalid_multiple_fields_type

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

TEST_FROM_RESULT_FILE = {
    # Tests de CAMPOS REQUERIDOS
    # Tests de inputs válidos
    'full_data': FULL_DATA_RESPONSE,
    # Un datajson con valores correctos únicamente para las claves requeridas
    'minimum_data': None,

    # Tests de TIPOS DE CAMPOS
    # Tests de inputs válidos
    'null_dataset_theme': None,
    'null_field_description': None,
    # Tests de inputs inválidos
    'invalid_catalog_publisher_type': None,
    'invalid_publisher_mbox_format': None,
    # Catalog_publisher y distribution_bytesize fallan
    'invalid_field_description_type': None,
    # La clave requerida catalog["description"] NO puede ser str vacía
    'empty_optional_string': None,
    # El format y extension de fileName de las distribuciones deben
    # coincidir si estan los campos presentes
    'mismatched_fileName_and_format': None,
    # El format y extension de downloadURL de las distribuciones deben
    # coincidir si estan los campos presentes
    'mismatched_downloadURL_and_format': None,
}

TEST_FROM_GENERATED_RESULT = {

    'multiple_missing_descriptions': multiple_missing_descriptions(),
    'invalid_multiple_fields_type': invalid_multiple_fields_type(),

    'missing_catalog_title': missing_catalog_title(),
    'missing_catalog_description': missing_catalog_description(),
    'missing_catalog_dataset': missing_catalog_dataset(),
    'null_catalog_publisher': null_catalog_publisher(),
    'empty_mandatory_string': empty_mandatory_string(),
    'malformed_datetime': malformed_datetime(),
    'malformed_datetime2': malformed_datetime2(),
    'malformed_email': malformed_email(),
    'malformed_uri': malformed_uri(),
    'invalid_themeTaxonomy': invalid_theme_taxonomy(),
    'missing_dataset': missing_dataset(),

    'missing_dataset_title': missing_dataset_title(),
    'missing_dataset_description': missing_dataset_description(),
    'malformed_accrualperiodicity': malformed_accrualperiodicity(),
    'malformed_date': malformed_date(),
    'malformed_temporal': malformed_temporal(),
    'malformed_temporal2': malformed_temporal2(),
    'too_long_field_title': too_long_field_title(),

    'missing_distribution_title': missing_distribution_title(),

    'invalid_catalog_publisher_type': invalid_catalog_publisher_type(),
    'invalid_publisher_mbox_format': invalid_publisher_mbox_format(),

    # 'repeated_downloadURL': repeated_downloadURL(),
}

TEST_FILE_RESPONSES = {}
TEST_FILE_RESPONSES.update(TEST_FROM_RESULT_FILE)
TEST_FILE_RESPONSES.update(TEST_FROM_GENERATED_RESULT)
