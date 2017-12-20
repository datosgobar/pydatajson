#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from collections import OrderedDict

import six


def to_native_dict(ordered_dict):
    return json.loads(json.dumps(ordered_dict))


def to_dict(table_list):
    ordered_dict = OrderedDict(table_list)
    if six.PY3:
        return to_native_dict(ordered_dict)
    else:
        return ordered_dict


CSV_TABLE = [
    to_dict([(u'Plato', u'Milanesa'),
             (u'Precio', u'Bajo'),
             (u'Sabor', u'666')]),
    to_dict([(u'Plato', u'Thoné, Vitel'),
             (u'Precio', u'Alto'),
             (u'Sabor', u'8000')]),
    to_dict([(u'Plato', u'Aceitunas'),
             (u'Precio', u''),
             (u'Sabor', u'15')])
]

WRITE_XLSX_TABLE = [
    to_dict([(u'Plato', u'Milanesa'),
             (u'Precio', u'Bajo'),
             (u'Sabor', 666)]),
    to_dict([(u'Plato', u'Thoné, Vitel'),
             (u'Precio', u'Alto'),
             (u'Sabor', 8000)]),
    to_dict([(u'Plato', u'Aceitunas'),
             (u'Precio', None),
             (u'Sabor', 15)])
]

READ_XLSX_TABLE = [
    to_dict([(u'Plato', u'Milanesa'),
             (u'Precio', u'Bajo'),
             (u'Sabor', 666)]),
    to_dict([(u'Plato', u'Thoné, Vitel'),
             (u'Precio', u'Alto'),
             (u'Sabor', 8000)]),
    to_dict([(u'Plato', u'Aceitunas'),
             (u'Sabor', 15)])
]
