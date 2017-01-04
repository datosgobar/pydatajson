
Manual de uso del módulo `pydatajson`
=====================================

## Contexto

En el marco de la política de Datos Abiertos, y el Decreto 117/2016, *"Plan de Apertura de Datos”*, pretendemos que todos los conjuntos de datos (*datasets*) publicados por organismos de la Administración Pública Nacional sean descubribles desde el Portal Nacional de Datos, http://datos.gob.ar/. A tal fin, se decidió que todo portal de datos de la APN cuente en su raíz con un archivo `data.json`, que especifica sus propiedades y los contenidos disponibles.

Para facilitar y automatizar la validación, manipulación y transformación de archivos `data.json`, se creó el módulo `pydatajson`

## Glosario

Un Portal de datos consiste en un *catálogo*, compuesto por *datasets*, que a su vez son cada uno un conjunto de *distribuciones*. De la "Guía para el uso y la publicación de metadatos".

* **Catálogo de datos**: Es un directorio de conjuntos de datos, que recopila y organiza metadatos descriptivos, de los datos que produce una organización. Un portal de datos es un catálogo.

* **Dataset**: También llamado conjunto de datos, es la pieza principal en todo catálogo. Se trata de un activo de datos que agrupa recursos referidos a un mismo tema, que respetan una estructura de la información. Los recursos que lo componen pueden diferir en el formato en que se los presenta (por ejemplo: .csv, .json, .xls, etc.), la fecha a la que se refieren, el área geográfica cubierta o estar separados bajo algún otro criterio. 

* **Distribución o recurso**: Es la unidad mínima de un catálogo de datos. Se trata de los activos de datos que se publican allí y que pueden ser descargados y re-utilizados por un usuario como archivos. Los recursos pueden tener diversos formatos (.csv, .shp, etc.). Están acompañados de información contextual asociada (“metadata”) que describe el tipo de información que se publica, el proceso por el cual se obtiene, la descripción de los campos del recurso y cualquier información extra que facilite su interpretación, procesamiento y lectura.

## Métodos

El módulo cuenta actualmente con dos categorías principales de métodos:

- **validación de metadata de catálogos** enteros, y
- **generación de reportes sobre datasets** pertenecientes a cierto(s) catálogo(s).

Estos métodos no tienen acceso *directo* a ningún catálogo, dataset ni distribución, sino únicamente a sus *representaciones*: archivos o partes de archivos en formato JSON que describen ciertas propiedades. Por conveniencia, en este documento se usan frases como "validar el dataset X", cuando una versión más precisa sería "validar la fracción del archivo `data.json` que consiste en una representación del dataset X en forma de diccionario". La diferencia es sutil, pero conviene mantenerla presente.

### Métodos de validación de metadatos

Los siguientes métodos toman una **representación externa de un catálogo**, que puede ser:
- una `string` con el path a un archivo local o la URL de un archivo externo en formato JSON que contiene la metadata de un catálogo, o
- un objeto `dict` que contiene la metadata de un catálogo.

* **is_valid_catalog(catalog) -> bool**: Responde `True` únicamente si el catálogo no contiene ningún error.
* **validate_catalog(catalog) -> dict**: Responde un diccionario con información detallada sobre la validez "global" de la metadata, junto con detalles sobre la validez de la metadata a nivel catálogo y cada uno de sus datasets. De haberlos, incluye una lista con información sobre los errores encontrados.

Tanto estos dos métodos, como cualquier otro que reciba un argumento `catalog(s)`, comienzan por convertir la representación externa de un catálogo a una **representación interna** unívoca: un diccionario cuyas claves son las definidas en el [Perfil de Metadatos](https://docs.google.com/spreadsheets/d/1PqlkhB1o0u2xKDYuex3UC-UIPubSjxKCSBxfG9QhQaA/edit?usp=sharing).

### Métodos de generación de reportes

Los siguientes métodos toman una o varias representaciones externas de catálogos, y las procesan para generar reportes específicos sobre su contenido:

- **generate_datasets_report()**: Devuelve un reporte con información clave sobre cada dataset incluido en un catálogo, junto con variables indicando la validez de sus metadatos.
- **generate_harvester_config()**: Devuelve un reporte con los campos mínimos que requiere el Harvester para federar un conjunto de datasets.
- **generate_harvestable_catalogs()**: Devuelve la lista de catálogos ingresada, filtrada de forma que cada uno incluya únicamente los datasets que se pretende que el Harvester federe.

Los tres métodos toman los mismos cuatro parámetros, que se interpretan de manera muy similar:
- **catalogs**: Representación externa de un catálogo, o una lista compuesta por varias de ellas.
- **harvest**: Criterio de decisión utilizado para marcar los datasets a ser federados/cosechados. Acepta los siguientes valores:
  - `'all'`: Cosechar todos los datasets presentes en **catalogs**.
  - `'none'`: No cosechar ninguno de los datasets presentes en **catalogs**.
  - `'valid'`: Cosechar únicamente los datasets que no contengan errores, ni en su propia metadata ni en la metadata global del catálogo.
  - `'report'`: Cosechar únicamente los datasets indicados por el reporte provisto en `report`.
- **report**: En caso de que se pretenda cosechar un conjunto específico de catálogos, esta variable debe recibir la representación externa (path a un archivo) o interna (lista de diccionarios) de un reporte que identifique los datasets a cosechar.
- **export_path**: Esta variable controla el valor de retorno de los métodos de generación. Si es `None`, el método devolverá la representación interna del reporte generado. Si especifica el path a un archivo, el método devolverá `None`, pero escribirá a `export_path` la representación externa del reporte generado, en formato CSV o XLSX.

## Uso

### Setup

`DataJson` valida catálogos contra un esquema default que cumple con el perfil de metadatos recomendado en la [Guía para el uso y la publicación de metadatos (v0.1)](https://github.com/datosgobar/paquete-apertura-datos/raw/master/docs/Gu%C3%ADa%20para%20el%20uso%20y%20la%20publicaci%C3%B3n%20de%20metadatos%20(v0.1).pdf) del [Paquete de Apertura de Datos](https://github.com/datosgobar/paquete-apertura-datos). El setup por default cubre la enorme mayoría de los casos:

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

### Validación de catálogos

Los métodos de validación de catálogos procesan un catálogo por llamada. En el siguiente ejemplo, `catalogs` contiene las tres representaciones de un catálogo que DataJson entiende:
```python
from pydatajson import DataJson

dj = DataJson()
catalogs = [
    "tests/samples/full_data.json", # path local
    "http://181.209.63.71/data.json", # URL remota
    # El siguiente catálogo está incompleto 
    {
        "title": "Catálogo del Portal Nacional",
        "dataset": []
    } # diccionario de Python
]

for catalog in catalogs:
    validation_result = dj.is_valid_catalog(catalog)
    validation_report = dj.validate_catalog(catalog)
    print """
Catálogo: {}
¿Es válida su metadata?: {}
Validación completa: {}
""".format(catalog, validation_result, validation_report)
```
Un ejemplo del resultado completo de `validate_catalog()` se puede consultar en el **Anexo I: Estructura de respuestas**.

### Generación de reportes

El objetivo final de los métodos `generate_X()` es proveer la configuración que Harvester necesita para cosechar datasets. Todos ellos devuelven una "tabla", que consiste en una lista de diccionarios que comparten las mismas claves (consultar ejemplos en el **Anexo I: Estructura de respuestas**). A continuación, se proveen algunos ejemplos de uso comunes:

#### Crear un archivo de configuración eligiendo manualmente los datasets a federar

```python
catalogs = ["tests/samples/full_data.json", "http://181.209.63.71/data.json"]
report_path = "path/to/report.xlsx"
dj.generate_datasets_report(
    catalogs=catalogs,
    harvest='none', # El reporte generado tendrá `harvest==0` para todos los datasets
    export_path=report_path
)
# A continuación, se debe editar el archivo de Excel 'path/to/report.xlsx', cambiando a '1' el campo 'harvest' para aquellos datasets que se quieran cosechar.

config_path = 'path/to/config.csv'
dj.generate_harvester_config(
    harvest='report',
    report=report_path,
    export_path=config_path
)
```
El archivo `config_path` puede ser provisto a Harvester para federar los datasets elegidos al editar el reporte intermedio `report_path`.

Alternativamente, el output de `generate_datasets_report()` se puede editar en un intérprete de python:
```python
# Asigno el resultado a una variable en lugar de exportarlo
datasets_report = dj.generate_datasets_report(
    catalogs=catalogs,
    harvest='none', # El reporte generado tendrá `harvest==0` para todos los datasets
)
# Imaginemos que sólo se desea federar el primer dataset del reporte:
datasets_report[0]["harvest"] = 1

config_path = 'path/to/config.csv'
dj.generate_harvester_config(
    harvest='report',
    report=datasets_report,
    export_path=config_path
)
```

#### Crear un archivo de configuración que incluya únicamente los datasets con metadata válida
Conservando las variables anteriores:
```python
dj.generate_harvester_config(
    catalogs=catalogs,
    harvest='valid'
    export_path='path/to/config.csv'
)
```
Para fines ilustrativos, se incluye el siguiente bloque de código que produce los mismos resultados, pero genera el reporte intermedio sobre datasets:
```python
datasets_report = dj.generate_datasets_report(
    catalogs=catalogs,
    harvest='valid'
)

# Como el reporte ya contiene la información necesaria sobre los datasets que se pretende cosechar, el argumento `catalogs` es innecesario.
dj.generate_harvester_config(
    harvest='report'
    report=datasets_report
    export_path='path/to/config.csv'
)
```

#### Modificar catálogos para conservar únicamente los datasets válidos

```python
# Creamos un directorio donde guardar los catálogos
output_dir = "catalogos_limpios"
import os; os.mkdir(output_dir)

dj.generate_harvestable_catalogs(
    catalogs,
    harvest='valid',
    export_path=output_dir
)
```

**NOTA:** El criterio `'harvest='valid'` considera válido un dataset sí y sólo sí:
- su propia metadata es válida, y
- la metadata "global" del catálogo al que pertenece es válida (título, descripción, datos del organismo editor, etcétera)

Por lo tanto, **si un catálogo tiene un error en su título, ninguno de sus datasets será cosechado bajo el criterio harvest='valid'**, y la clave "dataset" será `[]`.


## Anexo I: Estructura de respuestas

### validate_catalog()

El resultado de la validación completa de un catálogo, es un diccionario con la siguiente estructura:

```
{
    "status": "OK",  # resultado de la validación global
    "error": {
	"catalog": {
            # validez de la metadata propia del catálogo, ignorando los
            # datasets particulares
	    "status": "OK",
 	    "errors": []
	    "title": "Título Catalog"},
	"dataset": [
	    {
		# Validez de la metadata propia de cada dataset
                "status": "OK",
		"errors": [],
		"title": "Titulo Dataset 1"
	    },
	    {
		"status": "ERROR",
		"errors": [
                    {
                        "error_code": 2,
                        "instance": "",
                        "message": "'' is not a 'email'",
                        "path": ["publisher", "mbox"],
                        "validator": "format",
                        "validator_value": "email"
                   },
                   {
                        "error_code": 2,
                        "instance": "",
                        "message": """ is too short",
                        "path": ["publisher", "name"],
                        "validator": "minLength",
                        "validator_value": 1
                   }
               ],
               "title": "Titulo Dataset 2"
	    }
	]
    }
}
```

Si `validate_catalog()` encuentra algún error, éste se reportará en la lista `errors` del nivel correspondiente, a través de un diccionario con las siguientes claves:
- **path**: Posición en el diccionario de metadata del catálogo donde se encontró el error.
- **instance**: Valor concreto que no pasó la validación. Es el valor de la clave `path` en la metadata del catálogo.
- **message**: Descripción humanamente legible explicando el error.
- **validator**: Nombre del validador violado, ("type" para errores de tipo, "minLength" para errores de cadenas vacías, et cétera).
- **validator_value**: Valor esperado por el validador `validator`, que no fue respetado.
- **error_code**: Código describiendo genéricamente el error. Puede ser:
  - **1**: Valor obligatorio faltante: Un campo obligatorio no se encuentra presente.
  - **2**: Error de tipo y formato: se esperaba un `array` y se encontró un `dict`, se esperaba un `string` en formato `email` y se encontró una `string` que no cumple con el formato, et cétera.

### generate_datasets_report()
El reporte resultante tendrá tantas filas como datasets contenga el conjunto de catálogos ingresado, y contará con los siguientes campos, casi todos autodescriptivos:
- **catalog_metadata_url**: En caso de que se haya provisto una representación externa de un catálogo, la string de su ubicación; sino `None`.
- **catalog_title**
- **catalog_description**
- **valid_catalog_metadata**: Validez de la metadata "global" del catálogo, es decir, ignorando la metadata de datasets particulares.
- **dataset_title**
- **dataset_description**
- **dataset_index**: Posición (comenzando desde cero) en la que aparece el dataset en cuestión en lista del campo `catalog["dataset"]`.
- **valid_dataset_metadata**: Validez de la metadata *específica a este dataset* que figura en el catálogo (`catalog["dataset"][dataset_index]`).
- **harvest**: '0' o '1', según se desee excluir o incluir, respectivamente, un dataset de cierto proceso de cosecha. El default es '0', pero se puede controlar a través del parámetro 'harvest'.
- **dataset_accrualPeriodicity**
- **dataset_publisher_name**
- **dataset_superTheme**: Lista los valores que aparecen en el campo dataset["superTheme"], separados por comas.
- **dataset_theme**: Lista los valores que aparecen en el campo dataset["theme"], separados por comas.
- **dataset_landingPage**
- **distributions_list**: Lista los títulos y direcciones de descarga de todas las distribuciones incluidas en un dataset, separadas por "newline".

La *representación interna* de este reporte es una lista compuesta en su totalidad de diccionarios con las claves mencionadas. La *representación externa* de este reporte, es un archivo con información tabular, en formato CSV o XLSX. A continuación, un ejemplo de la _lista de diccionarios_ que devuelve `generate_datasets_report()`:
```python
[
    {
        "catalog_metadata_url": "http://181.209.63.71/data.json",
        "catalog_title": "Andino",
        "catalog_description": "Portal Andino Demo",
        "valid_catalog_metadata": 0,
        "dataset_title": "Dataset Demo",
        "dataset_description": "Este es un dataset de ejemplo, se incluye como material DEMO y no contiene ningun valor estadistico.",
        "dataset_index": 0,
        "valid_dataset_metadata": 1,
        "harvest": 0,
        "dataset_accrualPeriodicity": "eventual",
        "dataset_publisher_name": "Andino",
        "dataset_superThem"": "TECH",
        "dataset_theme": "Tema.demo",
        "dataset_landingPage": "https://github.com/datosgobar/portal-andino",
        "distributions_list": ""Recurso de Ejemplo": http://181.209.63.71/dataset/6897d435-8084-4685-b8ce-304b190755e4/resource/6145bf1c-a2fb-4bb5-b090-bb25f8419198/download/estructura-organica-3.csv"
    },
    {
        "catalog_metadata_url": "http://datos.gob.ar/data.json",
        "catalog_title": "Portal Nacional de Datos Abiertos",
        ( ... )
    }
]
```

### generate_harvester_config()
Este reporte se puede generar a partir de un conjunto de catálogos, o a partir del resultado de `generate_datasets_report()`, pues no es más que un subconjunto del mismo. Incluye únicamente las claves necesarias para que el Harvester pueda federar un dataset, si `'harvest'==1`:
- **catalog_metadata_url**
- **dataset_title**
- **dataset_accrualPeriodicity**

La *representación interna* de este reporte es una lista compuesta en su totalidad de diccionarios con las claves mencionadas. La *representación externa* de este reporte, es un archivo con información tabular, en formato CSV o XLSX. A continuación, un ejemplo con la _lista de diccionarios_ que devuelve `generate_harvester_config()`:
```python
[
    {
        "catalog_metadata_url": "tests/samples/full_data.json",
        "dataset_title": "Sistema de contrataciones electrónicas",
        "dataset_accrualPeriodicity": "R/P1Y"
    },
    {
        "catalog_metadata_url": "tests/samples/several_datasets_for_harvest.json",
        "dataset_title": "Sistema de Alumbrado Público CABA",
        "dataset_accrualPeriodicity": "R/P1Y"
    },
    {
        "catalog_metadata_url": "tests/samples/several_datasets_for_harvest.json",
        "dataset_title": "Listado de Presidentes Argentinos",
        "dataset_accrualPeriodicity": "R/P1Y"
    }
]
```
