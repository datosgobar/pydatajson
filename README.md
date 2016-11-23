pydatajson
===

[![Coverage Status](https://coveralls.io/repos/datosgobar/pydatajson/badge.svg?branch=master)](https://coveralls.io/r/datosgobar/pydatajson?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/pydatajson.svg?branch=master)](https://travis-ci.org/datosgobar/pydatajson)
[![PyPI](https://badge.fury.io/py/pydatajson.svg)](http://badge.fury.io/py/pydatajson)
[![Stories in Ready](https://badge.waffle.io/datosgobar/pydatajson.png?label=ready&title=Ready)](https://waffle.io/datosgobar/pydatajson)
[![Documentation Status](http://readthedocs.org/projects/pydatajson/badge/?version=latest)](http://data-cleaner.readthedocs.org/en/latest/?badge=latest)

Paquete en python con herramientas para generar y validar metadatos de catálogos de datos en formato data.json.


* Licencia: MIT license
* Documentación: https://pydatajson.readthedocs.io.


## Instalación

*AYUDA: ¿Qué dependencias del sistema son necesarias? ¿Tests/pruebas post instalación? Usar screenshots/gifs (si cabe).*

## Uso
*AYUDA: Ejemplo rápido. Usar screenshots/gifs (si cabe).*

### Para validar la estructura de un data.json

```python
from pydatajson import DataJson

dj = DataJson()
validation_result = dj.is_valid_catalog("path/to/data.json")

print validation_result
True
```

Con ejemplos del repositorio

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

*AYUDA: ¿Cómo correr los tests? ¿Cómo me instalo dependencias para los tests?*

## Créditos

*AYUDA: ¿Usás código de otra persona/organización? ¿Alguien o algo fue una fuente de inspiración/asesoramiento/ayuda para este repositorio? ¿Es esto un fork?*
