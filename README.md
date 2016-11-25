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

```bash
$ pip install pydatajson
```

* **Desarrollo:** Clonar este repositorio, y desde su raíz, ejecutar:
```bash
$ pip install -e .
```

## Uso

La librería implementa un objeto, `DataJson`, con varios métodos para verificar la integridad de los archivos `data.json` y manipular su contenido. De particular interés son `is_valid_catalog` y `validate_catalog`.

### Validar la estructura de un data.json contra el esquema por default que incluye la librería

#### Archivo data.json local

DataJson es capaz de validar archivos locales en cualquier directorio (accesible) siempre y cuando se provea el path absoluto a él.
Por conveniencia, la carpeta [`tests/samples/`](tests/samples/) contiene varios ejemplos de `data.json`s bien y mal formados con distintos tipos de errores.

```python
from pydatajson import DataJson

dj = DataJson()
datajson_path = "tests/samples/full_data.json"
validation_result = dj.is_valid_catalog(datajson_path)
validation_report = dj.validate_catalog(datajson_path)

print validation_result
True

print validation_report
{ 
    "status": "OK", 
    "error": { 
        "catalog": [], 
        "dataset": [] 
    }   
}   
```

#### Archivo data.json remoto

También es posible proveer una URL remota al archivo `data.json` de un portal productivo. Internamente, DataJson entiende que si el path del archivo a validar comienza con "http", se trata de una URL remota.

```python
datajson_url = "http://104.131.35.253/data.json"
validation_result = dj.is_valid_catalog(datajson_url)
validation_report = dj.validate_catalog(datajson_url)

print validation_result
False

print validation_report
{
    "status": "ERROR",
    "error": {
        "catalog": ["Título del portal"],
        "dataset": ["Dataset ejemplo 04", "Dataset ejemplo 03",
                    "Dataset ejemplo 02", "Dataset ejemplo 01"]
    }   
}   
```

## Tests

Los tests de la librería se desarrollaron con `nose`. Para correrlos, desde la raíz del repositorio:
```
$ pip install nose # Sólo la primera vez
$ nosetests
```

## Créditos

El validador de archivos `data.json` desarrollado no es más que un conveniente envoltorio alrededor de la librería `jsonschema`, que implementa el estándar definido por [JSONSchema.org](http://json-schema.org/).
