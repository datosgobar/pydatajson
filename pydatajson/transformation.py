#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Funciones auxiliares para realizar transformaciones de metadatos"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import os


def generate_distribution_ids(catalog):
    """Genera identificadores para las distribuciones que no los tienen.

    Los identificadores de distribuciones se generan concatenando el id del
    dataset al que pertenecen con el índice posicional de la distribución en el
    dataset: distribution_identifier = "{dataset_identifier}_{index}".
    """

    for dataset in catalog.get("dataset", []):
        for distribution_index, distribution in enumerate(
                dataset.get("distribution", [])):
            if "identifier" not in distribution:
                distribution["identifier"] = "{}_{}".format(
                    dataset["identifier"], distribution_index)
