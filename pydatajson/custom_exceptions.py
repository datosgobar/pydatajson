#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Excepciones personalizadas para validación y registro de errores"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


class BaseValidationError(object):
    """Estructura para errores de validación personalizados."""

    def __init__(self, validator, message, validator_value, path,
                 instance=None):
        super(BaseValidationError, self).__init__()

        # es el tipo de validación que se realiza
        self.validator = validator

        # es el mensaje de error que explica la validación que falla
        self.message = message

        # son los parámetros aplicados a ese tipo de validación
        self.validator_value = validator_value

        # es el camino que permite reconstruir el punto de falla en el JSON
        self.path = path

        self.instance = instance


class ThemeIdRepeated(BaseValidationError):

    def __init__(self, repeated_ids):

        # TODO: construcción del error
        validator = "repeatedValue"
        message = "Los ids {} estan repetidos en mas de un `theme`".format(
            repeated_ids)
        validator_value = "Chequea ids duplicados en themeTaxonomy"
        path = ["catalog", "themeTaxonomy"]

        super(ThemeIdRepeated, self).__init__(
            validator, message, validator_value, path)


class ThemeLabelRepeated(BaseValidationError):

    def __init__(self, repeated_labels):

        # TODO: construcción del error
        validator = "repeatedValue"
        message = "Etiquetas {} estan repetidas en mas de un `theme`".format(
            repeated_labels)
        validator_value = "Chequea labels duplicados en themeTaxonomy"
        path = ["catalog", "themeTaxonomy"]

        super(ThemeLabelRepeated, self).__init__(
            validator, message, validator_value, path)


class DownloadURLRepetitionError(BaseValidationError):

    def __init__(self, repeated_urls):

        # TODO: construcción del error
        validator = "repeatedValue"
        message = "DownloadURL's {} estan repetidas en mas de " \
                  "un `distribution`".format(repeated_urls)
        validator_value = "Chequea downloadURL's duplicados " \
                          "en las distribuciones"
        path = ["catalog", "dataset"]

        super(DownloadURLRepetitionError, self).__init__(
            validator, message, validator_value, path)


class ExtensionError(BaseValidationError):

    def __init__(self, dataset_idx, distribution_idx, distribution, attribute):

        validator = 'mismatchedValue'
        template = "distribution '{}' tiene distintas extensiones: " \
                   "format ('{}') y " + attribute + " ('{}')"
        extension = os.path.splitext(
            urlparse(distribution[attribute]).path)[-1].lower()
        message = template.format(
            distribution['identifier'], distribution['format'], extension)
        validator_value = 'Chequea format y la extension del ' + attribute
        path = ['dataset', dataset_idx, 'distribution', distribution_idx]

        super(ExtensionError, self).__init__(
            validator, message, validator_value, path)


class BaseUnexpectedValue(ValueError):

    """El id de una entidad está repetido en el catálogo."""

    def get_msg(self, entity_name, entity_id, value_type, value_found,
                value_expected):
        msg = "{} id '{}' figura con {} '{}' en lugar de '{}'".format(
            entity_name, entity_id, value_type, value_found, value_expected
        )
        return msg


class DatasetUnexpectedTitle(BaseUnexpectedValue):

    def __init__(self, dataset_id, title_found, title_expected):
        msg = self.get_msg(
            "dataset", dataset_id, "titulo", title_found, title_expected
        )
        super(DatasetUnexpectedTitle, self).__init__(msg)


class DistributionUnexpectedTitle(BaseUnexpectedValue):

    def __init__(self, distribution_id, title_found, title_expected):
        msg = self.get_msg("distribucion", distribution_id, "titulo",
                           title_found, title_expected)
        super(DistributionUnexpectedTitle, self).__init__(msg)


class NonParseableCatalog(ValueError):
    """No se puede leer un data.json a partir del parámetro pasado"""
    def __init__(self, catalog, error):
        msg = "Error parseando el datajson {}: {}".format(catalog, error)
        super(NonParseableCatalog, self).__init__(msg)


class BaseRepetitionError(ValueError):

    """El id de una entidad está repetido en el catálogo."""

    def get_msg(self, entity_name, entity_type, entity_id, repeated_entities,
                extra_msg=""):
        return "Hay mas de 1 {} con {} {}: {} {}".format(
            entity_name, entity_type, entity_id, repeated_entities, extra_msg)


class DistributionTitleRepetitionError(BaseRepetitionError):

    def __init__(self, distribution_title, repeated_distributions,
                 extra_msg=""):
        msg = self.get_msg("distribucion", "titulo", distribution_title,
                           repeated_distributions, extra_msg)
        super(DistributionTitleRepetitionError, self).__init__(msg)


class BaseNonExistentError(ValueError):

    """El id de una entidad no existe en el catálogo."""

    def get_msg(self, entity_name, entity_type, entity_id, extra_msg=""):
        return "No hay {} con {} {} {}".format(
            entity_name, entity_type, entity_id, extra_msg)


class DistributionTimeIndexNonExistentError(BaseNonExistentError):

    def __init__(self, distribution_title, dataset_id, extra_msg=""):
        msg = self.get_msg("distribucion", "titulo", distribution_title,
                           extra_msg)
        super(DistributionTimeIndexNonExistentError, self).__init__(msg)


class DistributionTitleNonExistentError(BaseNonExistentError):

    def __init__(self, distribution_title, dataset_id, extra_msg=""):
        msg = self.get_msg("distribucion", "titulo", distribution_title,
                           extra_msg)
        super(DistributionTitleNonExistentError, self).__init__(msg)


class FieldTitleTooLongError(ValueError):

    def __init__(self, field, field_len, max_field_len):
        msg = "'{}' tiene '{}' caracteres. Maximo: '{}'".format(
            field, field_len, max_field_len)
        super(FieldTitleTooLongError, self).__init__(msg)


class InvalidFieldTitleError(ValueError):

    def __init__(self, field, char, valid_field_chars):
        msg = "'{}' usa caracteres invalidos ('{}'). Validos: '{}'".format(
            field, char, valid_field_chars)
        super(InvalidFieldTitleError, self).__init__(msg)


class HeaderNotBlankOrIdError(ValueError):

    def __init__(self, worksheet, header_coord, header_value, ws_header_value):
        msg = "'{}' en hoja '{}' tiene '{}'. Debe ser vacio o '{}'".format(
            header_coord, worksheet, ws_header_value, header_value)
        super(HeaderNotBlankOrIdError, self).__init__(msg)


class TimeIndexFutureTimeValueError(ValueError):

    def __init__(self, iso_time_value, iso_now):
        msg = "{} es fecha futura respecto de {}".format(
            iso_time_value, iso_now)
        super(TimeIndexFutureTimeValueError, self).__init__(msg)


class FieldFewValuesError(ValueError):

    def __init__(self, field, positive_values, minimum_values):
        msg = "{} tiene {} valores, deberia tener {} o mas".format(
            field, positive_values, minimum_values)
        super(FieldFewValuesError, self).__init__(msg)


class FieldTooManyMissingsError(ValueError):

    def __init__(self, field, missing_values, positive_values):
        msg = "{} tiene mas missings ({}) que valores ({})".format(
            field, missing_values, positive_values)
        super(FieldTooManyMissingsError, self).__init__(msg)


class DatasetTemporalMetadataError(ValueError):

    def __init__(self, temporal):
        msg = "{} no es un formato de 'temporal' valido".format(temporal)
        super(DatasetTemporalMetadataError, self).__init__(msg)


class TimeValueBeforeTemporalError(ValueError):

    def __init__(self, iso_time_value, iso_ini_temporal):
        msg = "Serie comienza ({}) antes de 'temporal' ({}) ".format(
            iso_time_value, iso_ini_temporal)
        super(TimeValueBeforeTemporalError, self).__init__(msg)


class TimeIndexTooShortError(ValueError):

    def __init__(self, iso_end_index, iso_half_temporal, temporal):
        msg = "Serie termina ({}) antes de mitad de 'temporal' ({}) {}".format(
            iso_end_index, iso_half_temporal, temporal)
        super(TimeIndexTooShortError, self).__init__(msg)


class BaseRepetitionError(ValueError):

    """El id de una entidad está repetido en el catálogo."""

    def get_msg(self, entity_name, entity_type, entity_id=None,
                repeated_entities=None):
        if entity_id and repeated_entities is not None:
            return "Hay mas de 1 {} con {} {}: {}".format(
                entity_name, entity_type, entity_id, repeated_entities)
        elif repeated_entities is not None:
            return "Hay {} con {} repetido: {}".format(
                entity_name, entity_type, repeated_entities)
        else:
            raise NotImplementedError(
                "Hace falta por lo menos repeated_entities")


class FieldIdRepetitionError(BaseRepetitionError):

    def __init__(self, field_id=None, repeated_fields=None):
        msg = self.get_msg("field", "id", field_id, repeated_fields)
        super(FieldIdRepetitionError, self).__init__(msg)


class FieldTitleRepetitionError(BaseRepetitionError):

    """Hay un campo repetido en la distribución."""

    def __init__(self, field_title=None, repeated_fields=None):
        msg = self.get_msg("field", "title", field_title, repeated_fields)
        super(FieldTitleRepetitionError, self).__init__(msg)


class FieldDescriptionRepetitionError(BaseRepetitionError):

    """Hay un campo repetido en la distribución."""

    def __init__(self, field_desc=None, repeated_fields=None):
        msg = self.get_msg("field", "description", field_desc, repeated_fields)
        super(FieldDescriptionRepetitionError, self).__init__(msg)


class DistributionIdRepetitionError(BaseRepetitionError):

    def __init__(self, distribution_id=None, repeated_distributions=None):
        msg = self.get_msg("distribution", "id", distribution_id,
                           repeated_distributions)
        super(DistributionIdRepetitionError, self).__init__(msg)


class DatasetIdRepetitionError(BaseRepetitionError):

    def __init__(self, dataset_id=None, repeated_datasets=None):
        msg = self.get_msg("dataset", "id", dataset_id, repeated_datasets)
        super(DatasetIdRepetitionError, self).__init__(msg)


class BaseNonExistentError(ValueError):

    """El id de una entidad no existe en el catálogo."""

    def get_msg(self, entity_name, entity_type, entity_id):
        return "No hay ningun {} con {} {}".format(
            entity_name, entity_type, entity_id)


class FieldIdNonExistentError(BaseNonExistentError):

    def __init__(self, field_id):
        msg = self.get_msg("field", "id", field_id)
        super(FieldIdNonExistentError, self).__init__(msg)


class FieldTitleNonExistentError(BaseNonExistentError):

    def __init__(self, field_title):
        msg = self.get_msg("field", "title", field_title)
        super(FieldTitleNonExistentError, self).__init__(msg)


class DistributionIdNonExistentError(BaseNonExistentError):

    def __init__(self, distribution_id):
        msg = self.get_msg("distribution", "id", distribution_id)
        super(DistributionIdNonExistentError, self).__init__(msg)


class DatasetIdNonExistentError(BaseNonExistentError):

    def __init__(self, dataset_id):
        msg = self.get_msg("dataset", "id", dataset_id)
        super(DatasetIdNonExistentError, self).__init__(msg)


class ThemeTaxonomyNonExistentError(BaseNonExistentError):

    def __init__(self, dataset_id):
        msg = "Catalogo no tiene themeTaxonomy"
        super(ThemeTaxonomyNonExistentError, self).__init__(msg)


class ThemeNonExistentError(BaseNonExistentError):

    def __init__(self, theme):
        msg = "{} no existe en la themeTaxonomy como id ni como label."
        super(ThemeNonExistentError, self).__init__(msg)


class DownloadURLBrokenError(BaseNonExistentError):

    def __init__(self, distribution_id, distribution_downloadURL, status_code):
        msg = "Distribution ({}) con URL descarga ({}) inválida ({})"
        super(DownloadURLBrokenError, self).__init__(msg.format(
            distribution_id, distribution_downloadURL, status_code))


class FormatNameError(ValueError):
    pass


class NumericDistributionIdentifierError(ValueError):
    """La distribucion tiene un id puramente numerico"""
    pass
