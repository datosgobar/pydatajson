pydatajson
==========

[![Coverage Status](https://coveralls.io/repos/github/datosgobar/pydatajson/badge.svg?branch=master)](https://coveralls.io/github/datosgobar/pydatajson?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/pydatajson.svg?branch=master)](https://travis-ci.org/datosgobar/pydatajson)
[![PyPI](https://badge.fury.io/py/pydatajson.svg)](http://badge.fury.io/py/pydatajson)
[![Stories in Ready](https://badge.waffle.io/datosgobar/pydatajson.png?label=ready&title=Ready)](https://waffle.io/datosgobar/pydatajson)
[![Documentation Status](http://readthedocs.org/projects/pydatajson/badge/?version=stable)](http://pydatajson.readthedocs.io/es/stable/?badge=stable)

Paquete en python con herramientas para manipular y validar metadatos de catálogos de datos.

* Versión python: 2 y 3
* Licencia: MIT license
* Documentación: [https://pydatajson.readthedocs.io/es/stable](https://pydatajson.readthedocs.io/es/stable)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
 

- [Instalación](#instalacion)
- [Usos](#usos)
  - [Setup](#setup)
  - [Validación de metadatos de catálogos](#validacion-de-metadatos-de-catalogos)
    - [Archivo data.json local](#archivo-datajson-local)
    - [Otros formatos](#otros-formatos)
  - [Generación de reportes y configuraciones del Harvester](#generacion-de-reportes-y-configuraciones-del-harvester)
    - [Crear un archivo de configuración eligiendo manualmente los datasets a federar](#crear-un-archivo-de-configuracion-eligiendo-manualmente-los-datasets-a-federar)
    - [Crear un archivo de configuración que incluya únicamente los datasets con metadata válida](#crear-un-archivo-de-configuracion-que-incluya-unicamente-los-datasets-con-metadata-valida)
  - [Transformación de un archivo de metados XLSX al estándar JSON](#transformacion-de-un-archivo-de-metados-xlsx-al-estandar-json)
  - [Generación de indicadores de monitoreo de catálogos](#generacion-de-indicadores-de-monitoreo-de-catalogos)
- [Tests](#tests)
- [Recursos de interés](#recursos-de-interes)
- [Créditos](#creditos)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Este README cubre los casos de uso más comunes para la librería, junto con ejemplos de código, pero sin mayores explicaciones. Para una versión más detallada de los comportamientos, revise la [documentación oficial](http://pydatajson.readthedocs.io) o el [Manual de Uso](docs/MANUAL.md) de la librería.

## Instalación

* **Producción:** Desde cualquier parte

```bash
$ pip install pydatajson
```

* **Desarrollo:** Clonar este repositorio, y desde su raíz, ejecutar:
```bash
$ pip install -e .
```

A partir de la versión 0.2.x (Febrero 2017), la funcionalidad del paquete se mantendrá fundamentalmente estable hasta futuro aviso. De todas maneras, si piensa utilizar esta librería en producción, le sugerimos fijar la versión que emplea en un archivo `requirements.txt`.

## Usos

La librería cuenta con funciones para cuatro objetivos principales:
- **validación de metadatos de catálogos** y los _datasets_,
- **generación de reportes** sobre el contenido y la validez de los metadatos de catálogos y _datasets_,
- **transformación de archivos de metadatos** al formato estándar (JSON), y
- **generación de indicadores de monitoreo de catálogos** y sus _datasets_.

A continuación se proveen ejemplos de cada uno de estas acciones. Si desea analizar un flujo de trabajo más completo, refiérase a los Jupyter Notebook de [`samples/`](samples/)

### Setup

`DataJson` utiliza un esquema default que cumple con el perfil de metadatos recomendado en la [Guía para el uso y la publicación de metadatos (v0.1)](https://github.com/datosgobar/paquete-apertura-datos/raw/master/docs/Guia%20para%20el%20uso%20y%20la%20publicacion%20de%20metadatos%20(v0.1).pdf) del [Paquete de Apertura de Datos](https://github.com/datosgobar/paquete-apertura-datos).

```python
from pydatajson import DataJson

dj = DataJson()
```

Si se desea utilizar un esquema alternativo, por favor, consulte la sección "Uso > Setup" del [manual oficial](docs/MANUAL.md), o la documentación oficial.

### Validación de metadatos de catálogos

- Si se desea un **resultado sencillo (V o F)** sobre la validez de la estructura del catálogo, se utilizará **`is_valid_catalog(catalog)`**.
- Si se desea un **mensaje de error detallado**, se utilizará **`validate_catalog(catalog)`**.

Por conveniencia, la carpeta [`tests/samples/`](tests/samples/) contiene varios ejemplos de `data.json` bien y mal formados con distintos tipos de errores.

#### Archivo data.json local

```python
from pydatajson import DataJson

dj = DataJson()
catalog = "tests/samples/full_data.json"
validation_result = dj.is_valid_catalog(catalog)
validation_report = dj.validate_catalog(catalog)

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

#### Otros formatos

`pydatajson` puede interpretar catálogos tanto en formato JSON como en formato XLSX (siempre y cuando se hayan creado utilizando la [plantilla](samples/plantilla_data.xlsx), estén estos almacenados localmente o remotamente a través de URLs de descarga directa. También es capaz de interpretar diccionarios de Python con metadatos de catálogos.

```python
from pydatajson import DataJson

dj = DataJson()
catalogs = [
    "tests/samples/full_data.json", # archivo JSON local
    "http://181.209.63.71/data.json", # archivo JSON remoto
    "tests/samples/catalogo_justicia.xlsx", # archivo XLSX local
    "https://raw.githubusercontent.com/datosgobar/pydatajson/master/tests/samples/catalogo_justicia.xlsx", # archivo XLSX remoto
    {
        "title": "Catálogo del Portal Nacional",
	"description" "Datasets abiertos para el ciudadano."
        "dataset": [...],
	(...)
    } # diccionario de Python
]

for catalog in catalogs:
    validation_result = dj.is_valid_catalog(catalog)
    validation_report = dj.validate_catalog(catalog)
```

### Generación de reportes y configuraciones del Harvester

Si ya se sabe que se desean cosechar todos los _datasets_ [válidos] de uno o varios catálogos, se pueden utilizar directamente el método `generate_harvester_config()`, proveyendo `harvest='all'` o `harvest='valid'` respectivamente. Si se desea revisar manualmente la lista de _datasets_ contenidos, se puede invocar primero `generate_datasets_report()`, editar el reporte generado y luego proveérselo a `generate_harvester_config()`, junto con la opción `harvest='report'`.

#### Crear un archivo de configuración eligiendo manualmente los datasets a federar

```python
catalogs = ["tests/samples/full_data.json", "http://181.209.63.71/data.json"]
report_path = "path/to/report.xlsx"
dj.generate_datasets_report(
    catalogs=catalogs,
    harvest='none', # El reporte tendrá `harvest==0` para todos los datasets
    export_path=report_path
)

# A continuación, se debe editar el archivo de Excel 'path/to/report.xlsx',
# cambiando a '1' el campo 'harvest' en los datasets que se quieran cosechar.

config_path = 'path/to/config.csv'
dj.generate_harvester_config(
    harvest='report',
    report=report_path,
    export_path=config_path
)
```
El archivo `config_path` puede ser provisto a Harvester para federar los _datasets_ elegidos al editar el reporte intermedio `report_path`.

Por omisión, en la salida de `generate_harvester_config` la frecuencia de actualización deseada para cada _dataset_ será "R/P1D", para intentar cosecharlos diariamente. De preferir otra frecuencia (siempre y cuando sea válida según ISO 8601), se la puede especificar a través del parámetro opcional `frequency`. Si especifica expĺicitamente `frequency=None`, se conservarán las frecuencias de actualización indicadas en el campo `accrualPeriodicity` de cada _dataset_.

#### Crear un archivo de configuración que incluya únicamente los datasets con metadata válida

Conservando las variables anteriores:

```python
dj.generate_harvester_config(
    catalogs=catalogs,
    harvest='valid'
    export_path='path/to/config.csv'
)
```

### Transformación de un archivo de metados XLSX al estándar JSON

```python
from pydatajson.readers import read_catalog
from pydatajson.writers import write_json
from pydatajson import DataJson

dj = DataJson()
catalogo_xlsx = "tests/samples/catalogo_justicia.xlsx"

catalogo = read_catalog(catalogo_xlsx)
write_json(obj=catalogo, path="tests/temp/catalogo_justicia.json")
```

### Generación de indicadores de monitoreo de catálogos

`pydatajson` puede calcular indicadores sobre uno o más catálogos. Estos indicadores recopilan información de interés sobre los _datasets_ de cada uno, tales como:
- el estado de validez de los catálogos;
- el número de días desde su última actualización;
- el formato de sus distribuciones;
- frecuencia de actualización de los _datasets_;
- estado de federación de los _datasets_, comparándolo con el catálogo central

La función usada es `generate_catalogs_indicators`, que acepta los catálogos como parámetros. Devuelve dos valores:
- una lista con tantos valores como catálogos, con cada elemento siendo un diccionario con los indicadores del catálogo respectivo;
- un diccionario con los indicadores de la red entera (una suma de los individuales)

```python
catalogs = ["tests/samples/full_data.json", "http://181.209.63.71/data.json"]
indicators, network_indicators = dj.generate_catalogs_indicators(catalogs)

# Opcionalmente podemos pasar como segundo argumento un catálogo central,
# para poder calcular indicadores sobre la federación de los datasets en 'catalogs'

central_catalog = "http://datos.gob.ar/data.json"
indicators, network_indicators = dj.generate_catalogs_indicators(catalogs, central_catalog)
```

## Tests

Los tests se corren con `nose`. Desde la raíz del repositorio:

**Configuración inicial:**

```bash
$ pip install -r requirements_dev.txt
$ mkdir tests/temp
```

**Correr la suite de tests:**

```bash
$ nosetests
```

## Recursos de interés

* [Estándar ISO 8601 - Wikipedia](https://es.wikipedia.org/wiki/ISO_8601)
* [JSON SChema - Sitio oficial del estándar](http://json-schema.org/)
* [Documentación completa de `pydatajson` - Read the Docs](http://pydatajson.readthedocs.io)
* [Guía para el uso y la publicación de metafatos](https://docs.google.com/document/d/1Z7XhpzOinvITN_9wqUbOYpceDzic3KTOHLtHcGCPAwo/edit)

## Créditos

El validador de archivos `data.json` desarrollado es mayormente un envoltorio (*wrapper*) alrededor de la librería [`jsonschema`](https://github.com/Julian/jsonschema), que implementa el vocabulario definido por [JSONSchema.org](http://json-schema.org/) para anotar y validar archivos JSON.
