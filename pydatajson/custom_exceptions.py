#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Excepciones personalizadas para validación y registro de errores"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os


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


class DistributionTitleNonExistentError(BaseNonExistentError):

    def __init__(self, distribution_title, dataset_id, extra_msg=""):
        msg = self.get_msg("distribucion", "titulo", distribution_title,
                           extra_msg)
        super(DistributionTitleNonExistentError, self).__init__(msg)
