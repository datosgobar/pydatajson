# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, with_statement

import json
import os.path
import re

import vcr
from nose.tools import assert_true, assert_false, assert_dict_equal,\
    assert_regexp_matches
from six import iteritems, text_type

from tests.support.factories.core_files import TEST_FILE_RESPONSES
from .support.constants import BAD_DATAJSON_URL, BAD_DATAJSON_URL2
from .support.utils import jsonschema_str

try:
    import mock
except ImportError:
    from unittest import mock
import io
from .context import pydatajson
from .support.decorators import RESULTS_DIR

my_vcr = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
                 cassette_library_dir=os.path.join("tests", "cassetes"),
                 record_mode='once')


class TestDataJsonTestCase(object):
    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = RESULTS_DIR
    TEMP_DIR = os.path.join("tests", "temp")

    @classmethod
    def get_sample(cls, sample_filename):
        return os.path.join(cls.SAMPLES_DIR, sample_filename)

    @classmethod
    def setUp(cls):
        cls.dj = pydatajson.DataJson(cls.get_sample("full_data.json"))
        cls.catalog = pydatajson.readers.read_catalog(
            cls.get_sample("full_data.json"))
        cls.maxDiff = None
        cls.longMessage = True

    @classmethod
    def tearDown(cls):
        del cls.dj

    def run_case(self, case_filename, expected_dict=None):

        sample_path = os.path.join(self.SAMPLES_DIR, case_filename + ".json")
        result_path = os.path.join(self.RESULTS_DIR, case_filename + ".json")

        if expected_dict is None:
            with io.open(result_path, encoding='utf8') as result_file:
                expected_dict = json.load(result_file)

        response_bool = self.dj.is_valid_catalog(sample_path)
        response_dict = self.dj.validate_catalog(sample_path)

        print(text_type(json.dumps(
            response_dict, indent=4, separators=(",", ": "),
            ensure_ascii=False
        )))

        if expected_dict["status"] == "OK":
            assert_true(response_bool)
        elif expected_dict["status"] == "ERROR":
            assert_false(response_bool)
        else:
            raise Exception("LA RESPUESTA {} TIENE UN status INVALIDO".format(
                case_filename))
        assert_dict_equal.__self__.maxDiff = None
        assert_dict_equal(expected_dict, response_dict)

    # Tests de CAMPOS REQUERIDOS

    # Tests de inputs válidos
    def test_validity(self):
        for filename, value_or_none in iteritems(TEST_FILE_RESPONSES):
            yield self.run_case, filename, value_or_none

    def test_validity_of_invalid_dataset_type(self):
        """
        Validación ante un campo 'dataset' inválido en un catalogo
        :return:
        """
        case_filename = "invalid_dataset_type"
        expected_valid = False
        path = ['error', 'catalog', 'errors', 0, 'message']
        regex = '\{.*\} is not of type %s' % jsonschema_str('array')

        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_invalid_dataset_theme_type(self):
        case_filename = "invalid_dataset_theme_type"
        expected_valid = False
        path = ['error', 'dataset', 0, 'errors', 0, 'message']
        regex = "%s is not valid under any of the given schemas"\
                % jsonschema_str('contrataciones')
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_invalid_empty_super_theme_list(self):
        case_filename = "empty_super_theme_list"
        expected_valid = False
        path = ['error', 'dataset', 0, 'errors', 0, 'message']
        regex = "\[\] is too short"
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_invalid_keywords(self):
        case_filename = "invalid_keywords"
        expected_valid = False
        path = ['error', 'dataset', 1, 'errors', 0, 'message']
        regex = "\[%s, %s, %s\] is not valid under any of the given schemas"\
                % (jsonschema_str(';;bienes;;'), jsonschema_str('::compras::'),
                   jsonschema_str('//contrataciones//'))
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_invalid_whitespace_emails(self):
        case_filename = "invalid_whitespace_emails"
        expected_valid = False
        path = ['error', 'dataset', 0, 'errors', 0, 'message']
        regex = "%s is not valid under any of the given schemas" \
                % (jsonschema_str(' whitespace@mail.com'), )
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)
        path = ['error', 'dataset', 1, 'errors', 0, 'message']
        regex = "%s is not valid under any of the given schemas" \
                % (jsonschema_str('trailspace@mail.com '),)
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_invalid_multiple_emails(self):
        case_filename = "invalid_multiple_emails"
        expected_valid = False
        path = ['error', 'dataset', 0, 'errors', 0, 'message']
        regex = "%s is not valid under any of the given schemas" \
                % (jsonschema_str('first@mail.com; second@mail.com'), )
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)
        path = ['error', 'dataset', 1, 'errors', 0, 'message']
        regex = "%s is not valid under any of the given schemas" \
                % (jsonschema_str('one@mail.com;two@mail.com;three@mail.com'),)
        self.validate_message_with_file(
            case_filename, expected_valid, path, regex)

    def test_several_assorted_errors(self):
        case_filename = "several_assorted_errors"
        expected_errors = [
            (
                ['error', 'catalog', 'errors', ],
                "%s is a required property" % jsonschema_str('title')
            ),
            (
                ['error', 'catalog', 'errors', ],
                "789 is not valid under any of the given schemas"
            ),
            (
                ['error', 'catalog', 'errors', ], "%s is not a %s"
                % (jsonschema_str('datosmodernizacion.gob.ar'),
                   jsonschema_str('email'))
            ),
            (
                ['error', 'catalog', 'errors', ],
                "%s is not valid under any of the given schemas"
                % jsonschema_str('datos.gob.ar')
            ),
            (
                ['error', 'catalog', 'errors', ],
                "\[%s, %s\] is not valid under any of the given schemas"
                % (jsonschema_str('spa'), jsonschema_str(''))
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "%s is too long" % jsonschema_str('title' * 25)
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "123 is not valid under any of the given schemas"
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "%s is not valid under any of the given schemas"
                % jsonschema_str('convocatoriasabiertasduranteela.*o.csv')
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "\[.*\] is not of type %s" % jsonschema_str('object')
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "\[%s\] is not valid under any of the given schemas"
                % jsonschema_str('string')
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "\[%s, %s\] is not valid under any of the given schemas"
                % (jsonschema_str('spa'), jsonschema_str(''))
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "\[%s, %s, %s, %s] is not valid under any of the given schemas"
                % tuple(map(jsonschema_str,
                            ('bienes', 'compras', 'contrataciones', '')
                            ))
            ),
            (
                ['error', 'dataset', 0, 'errors', ],
                "\[%s, %s, %s, %s] is not valid under any of the given schemas"
                % tuple(map(jsonschema_str,
                            ('contrataciones', 'compras', 'convocatorias', '')
                            ))
            ),
        ]
        for path, regex in expected_errors:
            yield self.validate_contains_message_with_file,\
                  case_filename, path, regex

    def validate_message_with_file(
            self,
            case_filename,
            expected_valid,
            path,
            regex):
        sample_path = os.path.join(self.SAMPLES_DIR, case_filename + ".json")

        self.validate_string_in(sample_path, path, regex)
        self.validate_valid(sample_path, expected_valid)

    def validate_string_in(self, datajson, path, regex):
        response_dict = self.dj.validate_catalog(datajson)
        p = re.compile(regex)
        response = response_dict.copy()
        for key in path:
            response = response[key]
        assert_regexp_matches(response, p)

    def validate_valid(self, datajson, expected_valid):
        response_bool = self.dj.is_valid_catalog(datajson)
        if expected_valid:
            assert_true(response_bool)
        else:
            assert_false(response_bool)

    def validate_contains_message_with_file(self, case_filename, path, regex):
        sample_path = os.path.join(self.SAMPLES_DIR, case_filename + ".json")
        self.validate_contains_message(sample_path, path, regex)

    def validate_contains_message(self, datajson, path, regex):
        response_bool = self.dj.is_valid_catalog(datajson)
        response_dict = self.dj.validate_catalog(datajson)

        assert_false(response_bool)

        response = response_dict.copy()
        for key in path:
            response = response[key]

        p = re.compile(regex)
        matches = [p.match(error['message']) for error in response]
        assert_true(any(matches))

    @my_vcr.use_cassette('test_validate_bad_remote_datajson')
    def test_validate_invalid_remote_datajson_is_invalid(self):
        """ Testea `is_valid_catalog` contra un data.json remoto invalido."""

        res = self.dj.is_valid_catalog(BAD_DATAJSON_URL)
        assert_false(res)

    def test_validate_invalid_remote_datajson_has_errors(self):
        """ Testea `validate_catalog` contra un data.json remoto invalido."""

        errors = [(
                    ['error', 'catalog', 'errors', ],
                    "%s is too short" % jsonschema_str('')
                   ),
                  (
                    ['error', 'catalog', 'errors', ],
                    "%s is not a %s" % (jsonschema_str(''),
                                        jsonschema_str('email'))
                  )]
        for path, regex in errors:
            with my_vcr.use_cassette('test_validate_bad_remote_datajson'):
                yield self.validate_contains_message, BAD_DATAJSON_URL,\
                      path, regex

    # Tests contra una URL REMOTA
    @my_vcr.use_cassette('test_validate_bad_remote_datajson2')
    def test_validate_invalid_remote_datajson_is_invalid2(self):
        """ Testea `is_valid_catalog` contra un data.json remoto invalido."""

        res = self.dj.is_valid_catalog(BAD_DATAJSON_URL2)
        assert_false(res)

    def test_validate_invalid_remote_datajson_has_errors2(self):
        """ Testea `validate_catalog` contra un data.json remoto invalido."""
        errors = [
            ([
                'error', 'catalog', 'errors', ], "%s is not a %s" %
                (jsonschema_str(''), jsonschema_str('email'))), ([
                    'error', 'catalog', 'errors', ], "%s is too short" %
                jsonschema_str('')), ]
        for path, regex in errors:
            with my_vcr.use_cassette('test_validate_bad_remote_datajson2'):
                yield self.validate_contains_message, BAD_DATAJSON_URL2,\
                      path, regex

    def test_correctness_of_accrualPeriodicity_regex(self):
        """Prueba que la regex de validación de
        dataset["accrualPeriodicity"] sea correcta."""

        datajson_path = "tests/samples/full_data.json"
        datajson = json.load(open(datajson_path))

        valid_values = ['R/P10Y', 'R/P4Y', 'R/P3Y', 'R/P2Y', 'R/P1Y',
                        'R/P6M', 'R/P4M', 'R/P3M', 'R/P2M', 'R/P1M',
                        'R/P0.5M', 'R/P0.33M', 'R/P1W', 'R/P0.5W',
                        'R/P0.33W', 'R/P1D', 'R/PT1H', 'R/PT1S',
                        'eventual']

        for value in valid_values:
            datajson["dataset"][0]["accrualPeriodicity"] = value
            res = self.dj.is_valid_catalog(datajson)
            assert_true(res, msg=value)

        invalid_values = ['RP10Y', 'R/PY', 'R/P3', 'RR/P2Y', 'R/PnY',
                          'R/P6MT', 'R/PT', 'R/T1M', 'R/P0.M', '/P0.33M',
                          'R/P1Week', 'R/P.5W', 'R/P', 'R/T', 'R/PT1H3M',
                          'eventual ', '']

        for value in invalid_values:
            datajson["dataset"][0]["accrualPeriodicity"] = value
            res = self.dj.is_valid_catalog(datajson)
            assert_false(res, msg=value)

    def test_valid_catalog_list_format(self):
        report_list = self.dj.validate_catalog(fmt='list')
        assert_true(len(report_list['catalog']) == 1)
        assert_true(report_list['catalog'][0]['catalog_status'] == 'OK')
        assert_true(len(report_list['dataset']) == 2)
        for report in report_list['dataset']:
            assert_true(report['dataset_status'] == 'OK')

    def test_invalid_catalog_list_format(self):
        catalog = pydatajson.DataJson(
            self.get_sample("several_assorted_errors.json"))
        report_list = catalog.validate_catalog(fmt='list')
        report_dict = catalog.validate_catalog()

        for error in report_dict['error']['catalog']['errors']:
            assert_true(
                error['message'] in [
                    reported['catalog_error_message'] for reported
                    in report_list['catalog']])

        for error in report_dict['error']['dataset'][0]['errors']:
            assert_true(
                error['message'] in [
                    reported['dataset_error_message'] for reported
                    in report_list['dataset']])
