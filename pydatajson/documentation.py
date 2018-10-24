#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Módulo 'documentation' de Pydatajson

Contiene métodos para generar documentación en markdown de distintos
componentes de un catálogo.
"""

from __future__ import print_function, unicode_literals, with_statement

from six.moves import map


def dataset_to_markdown(dataset):
    """Genera texto en markdown a partir de los metadatos de una `dataset`.

    Args:
        dataset (dict): Diccionario con metadatos de una `dataset`.

    Returns:
        str: Texto que describe una `dataset`.
    """
    text_template = """
# {title}

{description}

## Recursos del dataset

{distributions}
"""

    if "distribution" in dataset:
        distributions = "".join(
            map(distribution_to_markdown, dataset["distribution"]))
    else:
        distributions = ""

    text = text_template.format(
        title=dataset["title"],
        description=dataset.get("description", ""),
        distributions=distributions
    )

    return text


def distribution_to_markdown(distribution):
    """Genera texto en markdown a partir de los metadatos de una
    `distribution`.

    Args:
        distribution (dict): Diccionario con metadatos de una
        `distribution`.

    Returns:
        str: Texto que describe una `distribution`.
    """
    text_template = """
### {title}

{description}

#### Campos del recurso

{fields}
"""

    if "field" in distribution:
        fields = "- " + \
            "\n- ".join(map(field_to_markdown, distribution["field"]))
    else:
        fields = ""

    text = text_template.format(
        title=distribution["title"],
        description=distribution.get("description", ""),
        fields=fields
    )

    return text


def field_to_markdown(field):
    """Genera texto en markdown a partir de los metadatos de un `field`.

    Args:
        field (dict): Diccionario con metadatos de un `field`.

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

    text_template = "{title}{type}{description}"
    text = text_template.format(title=field_title, type=field_type,
                                description=field_desc)

    return text
