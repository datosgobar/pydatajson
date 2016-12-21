pydatajson
===

[![Coverage Status](https://coveralls.io/repos/github/datosgobar/pydatajson/badge.svg?branch=master)](https://coveralls.io/github/datosgobar/pydatajson?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/pydatajson.svg?branch=master)](https://travis-ci.org/datosgobar/pydatajson)
[![PyPI](https://badge.fury.io/py/pydatajson.svg)](http://badge.fury.io/py/pydatajson)
[![Stories in Ready](https://badge.waffle.io/datosgobar/pydatajson.png?label=ready&title=Ready)](https://waffle.io/datosgobar/pydatajson)
[![Documentation Status](http://readthedocs.org/projects/pydatajson/badge/?version=latest)](http://pydatajson.readthedocs.io/en/latest/?badge=latest)

Paquete en python con herramientas para manipular y validar metadatos de catálogos de datos en formato data.json.

* Licencia: MIT license
* Documentación: [https://pydatajson.readthedocs.io](https://pydatajson.readthedocs.io)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

## Indice

- [Instalación](#instalaci%C3%B3n)
- [Uso](#uso)
  - [Setup](#setup)
  - [Posibles validaciones de catálogos](#posibles-validaciones-de-cat%C3%A1logos)
  - [Ubicación del catálogo a validar](#ubicaci%C3%B3n-del-cat%C3%A1logo-a-validar)
  - [Ejemplos](#ejemplos)
    - [Archivo data.json local](#archivo-datajson-local)
    - [Archivo data.json remoto](#archivo-datajson-remoto)
    - [Diccionario (data.json deserializado)](#diccionario-datajson-deserializado)
- [Tests](#tests)
- [Créditos](#cr%C3%A9ditos)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Instalación

* **Producción:** Desde cualquier parte

```bash
$ pip install pydatajson
```

* **Desarrollo:** Clonar este repositorio, y desde su raíz, ejecutar:
```bash
$ pip install -e .
```

## Uso

La librería implementa el objeto `DataJson` con varios métodos para verificar la integridad de archivos de metadatos `data.json` (locales o remotos) y manipular su contenido.

### Setup

`DataJson` utiliza un esquema default que cumple con el perfil de metadatos recomendado en la [Guía para el uso y la publicación de metadatos (v0.1)](https://github.com/datosgobar/paquete-apertura-datos/raw/master/docs/Gu%C3%ADa%20para%20el%20uso%20y%20la%20publicaci%C3%B3n%20de%20metadatos%20(v0.1).pdf) del [Paquete de Apertura de Datos](https://github.com/datosgobar/paquete-apertura-datos).

```python
from pydatajson import DataJson

dj = DataJson()
```

Si se desea utilizar un esquema alternativo, se debe especificar un **directorio absoluto** donde se almacenan los esquemas (`schema_dir`) y un nombre de esquema de validación (`schema_filename`), relativo al directorio  de los esquemas. Por ejemplo, si nuestro esquema alternativo se encuentra en `/home/datosgobar/metadatos-portal/esquema_de_validacion.json`, especificaremos:

```python
from pydatajson import DataJson

dj = DataJson(schema_filename="esquema_de_validacion.json",
              schema_dir="/home/datosgobar/metadatos-portal")
```

### Posibles validaciones de catálogos

- Si se desea un **resultado sencillo (V o F)** sobre la validez de la estructura del catálogo, se utilizará **`is_valid_catalog(datajson_path_or_url)`**.
- Si se desea un **mensaje de error detallado**, se utilizará **`validate_catalog(datajson_path_or_url)`**.

### Ubicación del catálogo a validar

Ambos métodos mencionados de `DataJson()` son capaces de validar archivos `data.json` locales o remotos:

- Para validar un **archivo local**, `datajson_path_or_url` deberá ser el **path absoluto** a él.
- Para validar un **archivo remoto**, `datajson_path_or_url` deberá ser una **URL que comience con 'http' o 'https'**.

Alternativamente, también se pueden validar **diccionarios**, es decir, el resultado de deserializar un archivo `data.json` en una variable.

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
            "errors": [],
            "title": "Datos Argentina"
        },
        "dataset": [
            {
                "status": "OK",
                "errors": [],
                "title": "Sistema de contrataciones electrónicas"
            }
        ]
    }
}
```

#### Archivo data.json remoto

```python
datajson_url = "http://181.209.63.71/data.json"
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
            "errors": [
                {
                    "instance": "",
                    "validator": "format",
                    "path": [
                        "publisher",
                        "mbox"
                    ],
                    "message": "u'' is not a u'email'",
                    "error_code": 2,
                    "validator_value": "email"
                },
                {
                    "instance": "",
                    "validator": "minLength",
                    "path": [
                        "publisher",
                        "name"
                    ],
                    "message": "u'' is too short",
                    "error_code": 2,
                    "validator_value": 1
                }
            ],
            "title": "Andino"
        },
        "dataset": [
            {
                "status": "OK",
                "errors": [],
                "title": "Dataset Demo"
            }
        ]
    }
}
```

#### Diccionario (data.json deserializado)

El siguiente fragmento de código tendrá resultados idénticos al primero:
```python
import json
datajson_path = "tests/samples/full_data.json"

datajson = json.load(datajson_path)

validation_result = dj.is_valid_catalog(datajson)
validation_report = dj.validate_catalog(datajson)
(...)

```

## Tests

Los tests se corren con `nose`. Desde la raíz del repositorio:
**Configuración inicial:**
```bash
$ pip install nose
$ mkdir tests/temp
```
**Correr la suite de tests:**
```bash
$ nosetests
```

## Créditos

El validador de archivos `data.json` desarrollado es mayormente un envoltorio (*wrapper*) alrededor de la librería [`jsonschema`](https://github.com/Julian/jsonschema), que implementa el vocabulario definido por [JSONSchema.org](http://json-schema.org/) para anotar y validar archivos JSON.
