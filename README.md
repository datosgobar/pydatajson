pydatajson
===

[![Coverage Status](https://coveralls.io/repos/github/datosgobar/pydatajson/badge.svg?branch=master)](https://coveralls.io/github/datosgobar/pydatajson?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/pydatajson.svg?branch=master)](https://travis-ci.org/datosgobar/pydatajson)
[![PyPI](https://badge.fury.io/py/pydatajson.svg)](http://badge.fury.io/py/pydatajson)
[![Stories in Ready](https://badge.waffle.io/datosgobar/pydatajson.png?label=ready&title=Ready)](https://waffle.io/datosgobar/pydatajson)
[![Documentation Status](http://readthedocs.org/projects/pydatajson/badge/?version=latest)](http://data-cleaner.readthedocs.org/en/latest/?badge=latest)

Paquete en python con herramientas para manipular y validar metadatos de catálogos de datos en formato data.json.


* Licencia: MIT license
* Documentación: https://pydatajson.readthedocs.io.


## Instalación

Instalar la librería debería ser tan sencillo como un `pip install`:

* **Producción:** Desde cualquier parte

```
pip install pydatajson
```

* **Desarrollo:** Clonar este repositorio, y desde su raíz, ejecutar:
```
pip install -e .
```

## Uso

### Validar la estructura de un data.json contra el esquema por default que incluye la librería

```python
from pydatajson import DataJson

dj = DataJson()
validation_result = dj.is_valid_catalog("path/to/data.json")

print validation_result
True
```

### Con ejemplos del repositorio

```python
validation_result = dj.is_valid_catalog("tests/samples/full_data.json")
print validation_result
True

validation_result = dj.is_valid_catalog(
    "tests/samples/missing_catalog_title_data.json")
print validation_result
False
```

## Tests

Los tests de la librería se desarrollaron con `nose`. Para correrlos, desde la raíz del repositorio:
```
pip install nose # Sólo la primera vez
nosetests
```

## Créditos

El validador de archivos `data.json` desarrollado no es más que un conveniente envoltorio alrededor de la librería `jsonschema`, que implementa el estándar definido por [JSONSchema.org](http://json-schema.org/).
*AYUDA: ¿Usás código de otra persona/organización? ¿Alguien o algo fue una fuente de inspiración/asesoramiento/ayuda para este repositorio? ¿Es esto un fork?*
