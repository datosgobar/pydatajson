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
- **export_path**: Esta variable controla el valor de retorno de los métodos de generación. Si es `None`, el método devolverá la representación interna del reporte generado. Si especifica el path a un archivo, el método devolverá `None`, pero escribirá a `export_path` la representación externa del reporte generado.

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

### Generación de reportes

El objetivo final de los métodos `generate_X` es proveer la configuración que Harvester necesita para cosechar datasets.




