pydatajson
===

[![Coverage Status](https://coveralls.io/repos/github/datosgobar/pydatajson/badge.svg?branch=master)](https://coveralls.io/github/datosgobar/pydatajson?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/pydatajson.svg?branch=master)](https://travis-ci.org/datosgobar/pydatajson)
[![PyPI](https://badge.fury.io/py/pydatajson.svg)](http://badge.fury.io/py/pydatajson)
[![Stories in Ready](https://badge.waffle.io/datosgobar/pydatajson.png?label=ready&title=Ready)](https://waffle.io/datosgobar/pydatajson)
[![Documentation Status](http://readthedocs.org/projects/pydatajson/badge/?version=latest)](http://pydatajson.readthedocs.io/en/latest/?badge=latest)

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

### Setup
La librería implementa un objeto, `DataJson`, con varios métodos para verificar la integridad de archivos `data.json` (locales o remotos) y manipular su contenido. Si se desea, se puede especificar un directorio absoluto (`schema_dir`) y un nombre de esquema de validacion (`schema_filename`) particular, pero *casi siempre*, sus valores por default serán adecuados, así que para empezar a trabajar, alcanza con:
```python
from pydatajson import DataJson

dj = DataJson()
```

### Posibles validaciones de catálogos

- Si se desea un **resultado sencillo (V o F)** sobre la validez de la estructura del catálogo, se utilizará **`is_valid_catalog(datajson_path_or_url)`**.
- Si se desea un **mensaje de error detallado**, se utilizará **`validate_catalog(datajson_path_or_url)`**.

### Ubicación del catálogo a validar

Ambos métodos mencionados de `DataJson()` son capaces de validar archivos `data.json` locales o remotos:
- para validar un **archivo local**, `datajson_path_or_url` deberá ser el **path absoluto** a él.
- para validar un archivo remoto, `datajson_path_or_url` deberá ser una **URL que comience con 'http' o 'https'**.

Por conveniencia, la carpeta [`tests/samples/`](tests/samples/) contiene varios ejemplos de `data.json`s bien y mal formados con distintos tipos de errores.


### Ejemplos

#### Archivo data.json local

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
        "catalog": {
            "status": "OK",
            "title": "Datos Argentina"
        },
        "dataset": [
            {
                "status": "OK",
                "title": "Sistema de contrataciones electrónicas"
            }

        ]
    }
}
```

#### Archivo data.json remoto

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
        "catalog": {
            "status": "ERROR",
            "title": "Título del portal"
        },
        "dataset": [
            {
                "status": "ERROR",
                "title": "Dataset ejemplo 04"
            },
            {
                "status": "ERROR",
                "title": "Dataset ejemplo 03"
            },
            {
                "status": "ERROR",
                "title": "Dataset ejemplo 02"
            },
            {
                "status": "ERROR",
                "title": "Dataset ejemplo 01"
            }
        ]
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

El validador de archivos `data.json` desarrollado es mayormente un envoltorio (*wrapper*) alrededor de la librería [`jsonschema`](https://github.com/Julian/jsonschema), que implementa el vocabulario definido por [JSONSchema.org](http://json-schema.org/) para anotar y validar archivos JSON.
