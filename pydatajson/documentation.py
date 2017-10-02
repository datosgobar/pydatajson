#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'documentation' de Pydatajson

Contiene métodos para generar documentación en markdown de distintos
componentes de un catálogo.
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from functools import partial
from collections import OrderedDict
import json

from validation import validate_catalog
import custom_exceptions as ce
from . import readers
from . import helpers


def distribution_to_markdown(distribution):
    """Genera texto en markdown a partir de los metadatos de un `field`.

    Args:
        catalog (dict): Diccionario con metadatos de un `field`.

    Returns:
        str: Texto que describe un `field`.
    """
    text_template = """
    ### {title}

    #### Campos del recurso

    {fields}
    """

    # TODO: generar texto de fields
    # fields =

    return text_template(title=distribution["title"], fields=fields)


def field_to_markdown(field):
    """Genera texto en markdown a partir de los metadatos de un `field`.

    Args:
        catalog (dict): Diccionario con metadatos de un `field`.

    Returns:
        str: Texto que describe un `field`.
    """
    if "title" in field:
        field_title = "**{}**".format(field["title"])
    else:
        raise Exception("Es necesario un `title` para describir un campo.")

    field_type = " ({})".format(field["type"]) if "type" in field else ""
    field_desc = ": {}".format(
        field["description"]) if "description" in field else ""

    text = "{title}{type}{description}".format(
        title=field_title,
        type=field_type,
        description=field_desc
    )

    return text
