#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo pydatajson."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os.path
import unittest
import nose
from .context import pydatajson
from pydatajson.documentation import field_to_markdown
from pydatajson.documentation import distribution_to_markdown
from pydatajson.documentation import dataset_to_markdown


class DocumentationTestCase(unittest.TestCase):

    SAMPLES_DIR = os.path.join("tests", "samples")
    RESULTS_DIR = os.path.join("tests", "results")

    def test_field_to_markdown(self):
        field = {
            "title": "procedimiento_id",
            "type": "integer",
            "description": "Identificador único del procedimiento"
        }

        result = field_to_markdown(field)
        expected = "**procedimiento_id** (integer): " \
                   "Identificador único del procedimiento"
        self.assertEqual(result, expected)

        # elimino campo de type
        field.pop("type")
        result = field_to_markdown(field)
        expected = "**procedimiento_id**: " \
                   "Identificador único del procedimiento"
        self.assertEqual(result, expected)

        # elimino campo de description
        field.pop("description")
        result = field_to_markdown(field)
        expected = "**procedimiento_id**"
        self.assertEqual(result, expected)

    def test_distribution_to_markdown(self):
        distribution = {"title": "Convocatorias abiertas durante el año 2015",
                        "description": "Listado de las convocatorias abiertas "
                                       "durante el año 2015 en el sistema de "
                                       "contrataciones electrónicas",
                        "field": [{"title": "procedimiento_id",
                                   "type": "integer",
                                   "description": "Identificador único del "
                                                  "procedimiento"},
                                  {"title": "unidad_operativa_"
                                            "contrataciones_id",
                                   "type": "integer",
                                   "description": "Identificador único de la "
                                                  "unidad operativa de "
                                                  "contrataciones"}]}

        result = distribution_to_markdown(distribution)
        expected = '\n### Convocatorias abiertas durante el año 2015\n\n' \
                   'Listado de las convocatorias abiertas durante el año ' \
                   '2015 en el sistema de contrataciones electrónicas\n\n' \
                   '#### Campos del recurso\n\n' \
                   '- **procedimiento_id** (integer): Identificador único ' \
                   'del procedimiento\n' \
                   '- **unidad_operativa_contrataciones_id** (integer): ' \
                   'Identificador único de la unidad operativa de' \
                   ' contrataciones\n'
        self.assertEqual(result, expected)

        # elimino campos no obligatiorios
        distribution.pop("field")
        distribution.pop("description")
        result = distribution_to_markdown(distribution)
        expected = '\n### Convocatorias abiertas durante el año 2015\n\n' \
                   '\n\n#### Campos del recurso'
        print(result)
        self.assertEqual(result.strip(), expected.strip())

    def test_dataset_to_markdown(self):
        dataset = {"title": "Sistema de contrataciones electrónicas",
                   "description":
                       "Datos correspondientes al Sistema de "
                       "Contrataciones Electrónicas (Argentina Compra)",
                   "distribution": [{"title": "Convocatorias abiertas durante "
                                              "el año 2015",
                                     "description":
                                         "Listado de las convocatorias "
                                         "abiertas durante el año 2015 en el "
                                         "sistema de contrataciones "
                                         "electrónicas",
                                     "field": [{"title": "procedimiento_id",
                                                "type": "integer",
                                                "description":
                                                    "Identificador único del "
                                                    "procedimiento"},
                                               {"title":
                                                    "unidad_operativa_"
                                                    "contrataciones_id",
                                                "type": "integer",
                                                "description":
                                                    "Identificador único de la"
                                                    " unidad operativa de "
                                                    "contrataciones"}]},
                                    {"title":
                                         "Convocatorias abiertas durante el "
                                         "año 2016",
                                     "description":
                                         "Listado de las convocatorias "
                                         "abiertas durante el año 2016 en el "
                                         "sistema de contrataciones "
                                         "electrónicas",
                                     }]}

        result = dataset_to_markdown(dataset)
        expected = '\n# Sistema de contrataciones electrónicas\n\n'\
                   'Datos correspondientes al Sistema de Contrataciones ' \
                   'Electrónicas (Argentina Compra)\n\n'\
                   '## Recursos del dataset\n\n\n'\
                   '### Convocatorias abiertas durante el año 2015\n\n'\
                   'Listado de las convocatorias abiertas durante el año ' \
                   '2015 en el sistema de contrataciones electrónicas\n\n'\
                   '#### Campos del recurso\n\n'\
                   '- **procedimiento_id** (integer): Identificador ' \
                   'único del procedimiento\n'\
                   '- **unidad_operativa_contrataciones_id** (integer): ' \
                   'Identificador único de la unidad operativa de ' \
                   'contrataciones\n\n'\
                   '### Convocatorias abiertas durante el año 2016\n\n'\
                   'Listado de las convocatorias abiertas durante el año ' \
                   '2016 en el sistema de contrataciones electrónicas\n\n'\
                   '#### Campos del recurso'

        self.assertEqual.__self__.maxDiff = None
        self.assertEqual(result.strip(), expected.strip())


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
