Manual de uso
=============

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
 

- [Contexto](#contexto)
- [Glosario](#glosario)
- [Funcionalidades](#funcionalidades)
  - [Métodos de validación de metadatos](#metodos-de-validacion-de-metadatos)
  - [Métodos de transformación de formatos de metadatos](#metodos-de-transformacion-de-formatos-de-metadatos)
  - [Métodos de generación de reportes](#metodos-de-generacion-de-reportes)
    - [Para federación de datasets](#para-federacion-de-datasets)
  - [Para presentación de catálogos y datasets](#para-presentacion-de-catalogos-y-datasets)
  - [Métodos para federación de datasets](#metodos-para-federacion-de-datasets)
- [Uso](#uso)
  - [Setup](#setup)
  - [Validación de catálogos](#validacion-de-catalogos)
  - [Transformación de `catalog.xlsx` a `data.json`](#transformacion-de-catalogxlsx-a-datajson)
  - [Generación de reportes](#generacion-de-reportes)
    - [Crear un archivo de configuración eligiendo manualmente los datasets a federar](#crear-un-archivo-de-configuracion-eligiendo-manualmente-los-datasets-a-federar)
    - [Crear un archivo de configuración que incluya únicamente los datasets con metadata válida](#crear-un-archivo-de-configuracion-que-incluya-unicamente-los-datasets-con-metadata-valida)
    - [Modificar catálogos para conservar únicamente los datasets válidos](#modificar-catalogos-para-conservar-unicamente-los-datasets-v%C3%A1lidos)
- [Anexo I: Estructura de respuestas](#anexo-i-estructura-de-respuestas)
  - [validate_catalog()](#validate_catalog)
  - [generate_datasets_report()](#generate_datasets_report)
  - [generate_harvester_config()](#generate_harvester_config)
  - [generate_datasets_summary()](#generate_datasets_summary)
  - [generate_catalog_readme()](#generate_catalog_readme)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Contexto

La política de Datos Abiertos de la República Argentina que nace con el Decreto 117/2016 (*"Plan de Apertura de Datos”*) se basa en un esquema descentralizado donde se conforma una red de nodos publicadores de datos y un nodo central o indexador.

El pilar fundamental de este esquema es el cumplimiento de un Perfil Nacional de Metadatos común a todos los nodos, en el que cada organismo de la APN que publique un archivo `data.json` o formato alternativo compatible.

Esto posibilita que todos los conjuntos de datos (*datasets*) publicados por organismos de la Administración Pública Nacional se puedan encontrar en el Portal Nacional de Datos: http://datos.gob.ar/.

## Glosario

Un *catálogo* de datos abiertos está compuesto por *datasets*, que a su vez son cada uno un conjunto de *distribuciones* (archivos descargables). Ver la  [Guía para el uso y la publicación de metadatos](http://paquete-apertura-datos.readthedocs.io/es/stable/guia_metadatos.html) para más información.

* **Catálogo de datos**: Directorio de conjuntos de datos que recopila y organiza metadatos descriptivos de los datos que produce una organización. Un portal de datos es una implementación posible de un catálogo. También lo es un archivo Excel, un JSON u otras.

* **Dataset**: También llamado conjunto de datos. Pieza principal en todo catálogo. Se trata de un activo de datos que agrupa recursos referidos a un mismo tema, que respetan una estructura de la información. Los recursos que lo componen pueden diferir en el formato en que se los presenta (por ejemplo: .csv, .json, .xls, etc.), la fecha a la que se refieren, el área geográfica cubierta o estar separados bajo algún otro criterio.

* **Distribución o recurso**: Es la unidad mínima de un catálogo de datos. Se trata de los activos de datos que se publican allí y que pueden ser descargados y re-utilizados por un usuario como archivos. Los recursos pueden tener diversos formatos (.csv, .shp, etc.). Están acompañados de información contextual asociada (“metadata”) que describe el tipo de información que se publica, el proceso por el cual se obtiene, la descripción de los campos del recurso y cualquier información extra que facilite su interpretación, procesamiento y lectura.

* **data.json y catalog.xlsx**: Son las dos _representaciones externas_ de los metadatos de un catálogo que `pydatajson` comprende. Para poder ser analizados programáticamente, los metadatos de un catálogo deben estar representados en un formato estandarizado: el PAD establece el archivo `data.json` para tal fin, y `pydatajson` permite leer una versión en XLSX equivalente.

* **diccionario de metadatos**: Es la _representación interna_ que la librería tiene de los metadatos de un catálogo. Todas las rutinas de la librería `pydatajson` que manipulan catálogos, toman como entrada una _representación externa_ (`data.json` o `catalog.xlsx`) del catálogo, y lo primero que hacen es "leerla" y generar una _representación interna_ de la información que la rutina sea capaz de manipular.

## Uso

.. autofunction:: pydatajson.backup.main

"ñalksdj"

### Setup

`DataJson` valida catálogos contra un esquema default que cumple con el perfil de metadatos recomendado en la [Guía para el uso y la publicación de metadatos](http://paquete-apertura-datos.readthedocs.io/es/stable/guia_metadatos.html) del [Paquete de Apertura de Datos](https://github.com/datosgobar/paquete-apertura-datos).

```python
from pydatajson import DataJson

catalog = DataJson("http://datos.gob.ar/data.json")
```

Si se desea utilizar un esquema alternativo, se debe especificar un **directorio absoluto** donde se almacenan los esquemas (`schema_dir`) y un nombre de esquema de validación (`schema_filename`), relativo al directorio  de los esquemas. Por ejemplo, si nuestro esquema alternativo se encuentra en `/home/datosgobar/metadatos-portal/esquema_de_validacion.json`, especificaremos:

```python
from pydatajson import DataJson

catalog = DataJson("http://datos.gob.ar/data.json",
                   schema_filename="esquema_de_validacion.json",
                   schema_dir="/home/datosgobar/metadatos-portal")
```

### Lectura

`pydatajson` puede leer un catálogo en JSON, XLSX, CKAN o `dict` de python:

```python
from pydatajson.ckan_reader import read_ckan_catalog
import requests

# data.json
catalog = DataJson("http://datos.gob.ar/data.json")
catalog = DataJson("local/path/data.json")

# catalog.xlsx
catalog = DataJson("http://datos.gob.ar/catalog.xlsx")
catalog = DataJson("local/path/catalog.xlsx")

# CKAN
catalog = DataJson(read_ckan_catalog("http://datos.gob.ar"))

# diccionario de python
catalog_dict = requests.get("http://datos.gob.ar/data.json").json()
catalog = DataJson(catalog_dict)
```

### Escritura

### Validación

Validar los metadatos de un catálogo y corregir errores.

```python
from pydatajson import DataJson

catalog = DataJson("tests/samples/full_data.json")

# es falso si existe por lo menos UN error / verdadero si no hay ningún error
validation_result = catalog.is_valid_catalog(catalog)

# objeto con los errores encontrados
validation_report = catalog.validate_catalog(catalog, only_errors=True)

# se puede tener el reporte en distintos formatos para transformar más fácilmente en un informe en CSV o Excel
validation_report = catalog.validate_catalog(catalog, only_errors=True, fmt="list")
```

También se puede correr desde la línea de comandos para ver un resultado rápido.

```
pydatajson validation "tests/samples/full_data.json"
pydatajson validation http://datos.gob.ar/data.json
```

Un ejemplo del resultado completo de `validate_catalog()` se puede consultar en el **Anexo I: Estructura de respuestas**.

### Federación y restauración

`pydatajson` permite federar o restaurar fácilmente un dataset de un catálogo hacia un Portal Andino (usa todo el perfil de metadatos) o CKAN (sólo usa campos de metadatos de CKAN), utilizando la API de CKAN.

Para esto hace falta un *apikey* que se puede sacar de la API de CKAN `/api/action/user_list` ingresando con un usuario administrador.

#### Federar un dataset

Incluye la transformación de algunos metadatos, para adaptar un dataset de un nodo original a cómo debe documentarse en un nodo indexador.

```python
catalog_origin = DataJson("https://datos.agroindustria.gob.ar/data.json")

catalog_origin.harvest_dataset_to_ckan(
    owner_org="ministerio-de-agroindustria",
    dataset_origin_identifier="8109e9e8-f8e9-41d1-978a-d20fcd2fe5f5",
    portal_url="http://datos.gob.ar",
    apikey="apikey",
    catalog_id="agroindustria"
)
```

La organización del nodo de destino debe estar previamente creada.

#### Restaurar un dataset

Los metadatos no sufren transformaciones: se escribe el dataset en el nodo de destino tal cual está en el nodo original.

```python
catalog_origin = DataJson("datosgobar/backup/2018-01-01/data.json")

catalog_origin.restore_dataset_to_ckan(
    owner_org="ministerio-de-agroindustria",
    dataset_origin_identifier="8109e9e8-f8e9-41d1-978a-d20fcd2fe5f5",
    portal_url="http://datos.gob.ar",
    apikey="apikey"
)
```

La organización del nodo de destino debe estar previamente creada. En este caso no hace falta `catalog_id` porque el `dataset_identifier` no sufre ninguna transformación.

### Transformación de `catalog.xlsx` a `data.json`

La lectura de un archivo de metadatos por parte de `pydatajson.readers.read_catalog` **no realiza ningún tipo de verificación sobre la validez de los metadatos leídos**. Por ende, si se quiere generar un archivo en formato JSON estándar únicamente en caso de que los metadatos de archivo XLSX sean válidos, se deberá realizar la validación por separado.

El siguiente código, por ejemplo, escribe a disco un catálogos de metadatos en formato JSONO sí y sólo sí los metadatos del XLSX leído son válidos:
```python
from pydatajson.readers import read_catalog
from pydatajson.writers import write_json
from pydatajson import DataJson

catalog = DataJson()
catalogo_xlsx = "tests/samples/catalogo_justicia.xlsx"

catalogo = read_catalog(catalogo_xlsx)
if catalog.is_valid_catalog(catalogo):
    write_json(obj=catalogo, path="tests/temp/catalogo_justicia.json")
else:
    print "Se encontraron metadatos inválidos. Operación de escritura cancelada."
```

Para más información y una versión más detallada de esta rutina en Jupyter Notebook, dirigirse [aquí](samples/caso-uso-1-pydatajson-xlsx-justicia-valido.ipynb) (metadatos válidos) y [aquí](samples/caso-uso-2-pydatajson-xlsx-justicia-no-valido.ipynb) (metadatos inválidos).

### Generación de reportes

El objetivo final de los métodos `generate_datasets_report`, `generate_harvester_config` y `generate_harvestable_catalogs`,  es proveer la configuración que Harvester necesita para cosechar datasets. Todos ellos devuelven una "tabla", que consiste en una lista de diccionarios que comparten las mismas claves (consultar ejemplos en el **Anexo I: Estructura de respuestas**). A continuación, se proveen algunos ejemplos de uso comunes:

#### Crear un archivo de configuración eligiendo manualmente los datasets a federar

```python
catalogs = ["tests/samples/full_data.json", "http://181.209.63.71/data.json"]
report_path = "path/to/report.xlsx"
catalog.generate_datasets_report(
    catalogs=catalogs,
    harvest='none', # El reporte generado tendrá `harvest==0` para todos los datasets
    export_path=report_path
)
# A continuación, se debe editar el archivo de Excel 'path/to/report.xlsx', cambiando a '1' el campo 'harvest' para aquellos datasets que se quieran cosechar.

config_path = 'path/to/config.csv'
catalog.generate_harvester_config(
    harvest='report',
    report=report_path,
    export_path=config_path
)
```
El archivo `config_path` puede ser provisto a Harvester para federar los datasets elegidos al editar el reporte intermedio `report_path`.

Alternativamente, el output de `generate_datasets_report()` se puede editar en un intérprete de python:
```python
# Asigno el resultado a una variable en lugar de exportarlo
datasets_report = catalog.generate_datasets_report(
    catalogs=catalogs,
    harvest='none', # El reporte generado tendrá `harvest==0` para todos los datasets
)
# Imaginemos que sólo se desea federar el primer dataset del reporte:
datasets_report[0]["harvest"] = 1

config_path = 'path/to/config.csv'
catalog.generate_harvester_config(
    harvest='report',
    report=datasets_report,
    export_path=config_path
)
```

#### Crear un archivo de configuración que incluya únicamente los datasets con metadata válida
Conservando las variables anteriores:
```python
catalog.generate_harvester_config(
    catalogs=catalogs,
    harvest='valid'
    export_path='path/to/config.csv'
)
```
Para fines ilustrativos, se incluye el siguiente bloque de código que produce los mismos resultados, pero genera el reporte intermedio sobre datasets:
```python
datasets_report = catalog.generate_datasets_report(
    catalogs=catalogs,
    harvest='valid'
)

# Como el reporte ya contiene la información necesaria sobre los datasets que se pretende cosechar, el argumento `catalogs` es innecesario.
catalog.generate_harvester_config(
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

catalog.generate_harvestable_catalogs(
    catalogs,
    harvest='valid',
    export_path=output_dir
)
```

## Funcionalidades

La librería cuenta con funciones para tres objetivos principales:
- **validación de metadatos de catálogos** y los datasets,
- **generación de reportes** sobre el contenido y la validez de los metadatos de catálogos y datasets,
- **transformación de archivos de metadatos** al formato estándar (JSON),
- **federación de datasets** a portales de destino.


Como se menciona en el Glosario estos métodos no tienen acceso *directo* a ningún catálogo, dataset ni distribución, sino únicamente a sus *representaciones externas*: archivos o partes de archivos en formato JSON que describen ciertas propiedades. Por conveniencia, en este documento se usan frases como "validar el dataset X", cuando una versión más precisa sería "validar la fracción del archivo `data.json` que consiste en una representación del dataset X en forma de diccionario". La diferencia es sutil, pero conviene mantenerla presente.

Todos los métodos públicos de la librería toman como primer parámetro `catalog`:
- o bien un diccionario de metadatos (una _representación interna_),
- o la ruta (local o remota) a un archivo de metadatos en formato legible (idealmente JSON, alternativamente XLSX).

Cuando el parámetro esperado es `catalogs`, en plural, se le puede pasar o un único catálogo, o una lista de ellos.

Todos los métodos comienzan por convertir `catalog(s)` en una **representación interna** unívoca: un diccionario cuyas claves son las definidas en el [Perfil de Metadatos](https://docs.google.com/spreadsheets/d/1PqlkhB1o0u2xKDYuex3UC-UIPubSjxKCSBxfG9QhQaA/edit?usp=sharing). La conversión se realiza a través de `pydatajson.readers.read_catalog(catalog)`: éste es la función que todos ellos invocan para obtener un diccionario de metadatos estándar.

### Métodos de validación de metadatos

* **pydatajson.DataJson.is_valid_catalog(catalog) -> bool**: Responde `True` únicamente si el catálogo no contiene ningún error.
* **pydatajson.DataJson.validate_catalog(catalog) -> dict**: Responde un diccionario con información detallada sobre la validez "global" de los metadatos, junto con detalles sobre la validez de los metadatos a nivel catálogo y cada uno de sus datasets. De haberlos, incluye una lista con información sobre los errores encontrados.

### Métodos de transformación de formatos de metadatos

Transformar un archivo de metadatos de un formato a otro implica un primer paso de lectura de un formato, y un segundo paso de escritura a un formato distinto. Para respetar las disposiciones del PAD, sólo se pueden escribir catálogos en formato JSON.

* **pydatajson.readers.read_catalog()**: Método que todas las funciones de DataJson llaman en primer lugar para interpretar cualquier tipo de representación externa de un catálogo.
* **pydatajson.writers.write_json_catalog()**: Fina capa de abstracción sobre `pydatajson.writers.write_json`, que simplemente vuelca un objeto de Python a un archivo en formato JSON.

### Métodos de generación de reportes

#### Para federación de datasets

Los siguientes métodos toman una o varias representaciones externas de catálogos, y las procesan para generar reportes específicos sobre su contenido:

- **pydatajson.DataJson.generate_datasets_report()**: Devuelve un reporte con información clave sobre cada dataset incluido en un catálogo, junto con variables indicando la validez de sus metadatos.
- **pydatajson.DataJson.generate_harvester_config()**: Devuelve un reporte con los campos mínimos que requiere el Harvester para federar un conjunto de datasets.
- **pydatajson.DataJson.generate_harvestable_catalogs()**: Devuelve la lista de catálogos ingresada, filtrada de forma que cada uno incluya únicamente los datasets que se pretende que el Harvester federe.

Los tres métodos toman los mismos cuatro parámetros, que se interpretan de manera muy similar:
- **catalogs**: Representación externa de un catálogo, o una lista compuesta por varias de ellas.
- **harvest**: Criterio de decisión utilizado para marcar los datasets a ser federados/cosechados. Acepta los siguientes valores:
  - `'all'`: Cosechar todos los datasets presentes en **catalogs**.
  - `'none'`: No cosechar ninguno de los datasets presentes en **catalogs**.
  - `'valid'`: Cosechar únicamente los datasets que no contengan errores, ni en su propia metadata ni en la metadata global del catálogo.
  - `'report'`: Cosechar únicamente los datasets indicados por el reporte provisto en `report`.
- **report**: En caso de que se pretenda cosechar un conjunto específico de catálogos, esta variable debe recibir la representación externa (path a un archivo) o interna (lista de diccionarios) de un reporte que identifique los datasets a cosechar.
- **export_path**: Esta variable controla el valor de retorno de los métodos de generación. Si es `None`, el método devolverá la representación interna del reporte generado. Si especifica el path a un archivo, el método devolverá `None`, pero escribirá a `export_path` la representación externa del reporte generado, en formato CSV o XLSX.

**generate_harvester_config()** puede tomar un parámetro extra, `frequency`, que permitirá indicarle a la rutina de cosecha de con qué frecuencia debe intentar actualizar su versión de cierto dataset. Por omisión, lo hará diariamente.

### Para presentación de catálogos y datasets

Existen dos métodos, cuyos reportes se incluyen diariamente entre los archivos que disponibiliza el repositorio [`libreria-catalogos`](https://github.com/datosgobar/libreria-catalogos/):

- **pydatajson.DataJson.generate_datasets_summary()**: Devuelve un informe tabular (en formato CSV o XLSX) sobre los datasets de un catálogo, detallando cuántas distribuciones tiene y el estado de sus propios metadatos.
- **pydatajson.DataJson.generate_catalog_readme()**: Genera un archivo de texto plano en formato Markdown para ser utilizado como "README", es decir, como texto introductorio al contenido del catálogo.

### Métodos para federación de datasets

- **pydatajson.DataJson.push_dataset_to_ckan()**: Copia la metadata de un dataset y la escribe en un portal de CKAN.
Toma los siguientes parámetros:
  - **owner_org**: La organización a la que pertence el dataset. Debe encontrarse en el portal de destino.
  - **dataset_origin_identifier**: Identificador del dataset en el catálogo de origen.
  - **portal_url**: URL del portal de CKAN de destino.
  - **apikey**: La apikey de un usuario del portal de destino con los permisos para crear el dataset bajo la
  organización pasada como parámetro.
  - **catalog_id** (opcional, default: None): El prefijo que va a preceder el id y name del dataset en el portal
  destino, separado por un guión.
  - **demote_superThemes** (opcional, default: True):Si está en true, los ids de los themes del dataset, se escriben
  como groups de CKAN.
  - **demote_themes** (opcional, default: True): Si está en true, los labels de los themes del dataset, se escriben como
  tags de CKAN; sino,se pasan como grupo.
  - **download_strategy** (opcional, default None): La referencia a una función que toma (catalog, distribution) de
  entrada y devuelve un booleano. Esta función se aplica sobre todas las distribuciones del dataset. Si devuelve `True`,
  se descarga el archivo indicado en el `downloadURL` de la distribución y se lo sube al portal de destino. Si es None,
  se omite esta operación.
  - **generate_new_access_url** (opcional, default None): Se pasan los ids de las distribuciones cuyo accessURL se regenerar en el portal de
      destino. Para el resto, el portal debe mantiene el valor pasado en el DataJson.
 


  Retorna el id en el nodo de destino del dataset federado.
  
  **Advertencia**: La función `push_dataset_to_ckan()` sólo garantiza consistencia con los estándares de CKAN. Para
  mantener una consistencia más estricta dentro del catálogo a federar, es necesario validar los datos antes de pasarlos
  a la función. 

- **pydatajson.federation.remove_dataset_from_ckan()**: Hace un borrado físico de un dataset en un portal de CKAN.
Toma los siguientes parámetros:
    - **portal_url**: La URL del portal CKAN. Debe implementar la funcionalidad de `/data.json`.
    - **apikey**: La apikey de un usuario con los permisos que le permitan borrar el dataset.
    - **filter_in**: Define el diccionario de filtro en el campo `dataset`. El filtro acepta los datasets cuyos campos
    coincidan con todos los del diccionario `filter_in['dataset']`.
    - **filter_out**: Define el diccionario de filtro en el campo `dataset`. El filtro acepta los datasets cuyos campos
    coincidan con alguno de los del diccionario `filter_out['dataset']`.
    - **only_time_series**: Borrar los datasets que tengan recursos con series de tiempo.
    - **organization**: Borrar los datasets que pertenezcan a cierta organizacion.
    
    En caso de pasar más de un parámetro opcional, la función `remove_dataset_from_ckan()` borra aquellos datasets que
    cumplan con todas las condiciones.

- **pydatajson.DataJson.push_theme_to_ckan()**: Crea un tema en el portal de destino
Toma los siguientes parámetros:
    - **portal_url**: La URL del portal CKAN.
    - **apikey**: La apikey de un usuario con los permisos que le permitan crear un grupo.
    - **identifier** (opcional, default: None): Id del `theme` que se quiere federar, en el catálogo de origen.
    - **label** (opcional, default: None): label del `theme` que se quiere federar, en el catálogo de origen.

    Debe pasarse por lo menos uno de los 2 parámetros opcionales. En caso de que se provean los 2, se prioriza el
    identifier sobre el label.

- **pydatajson.DataJson.push_new_themes()**: Toma los temas de la taxonomía de un DataJson y los crea en el catálogo de
    destino si no existen.
Toma los siguientes parámetros:
    - **portal_url**: La URL del portal CKAN adonde se escribiran los temas.
    - **apikey**: La apikey de un usuario con los permisos que le permitan crear los grupos.


Hay también funciones que facilitan el uso de `push_dataset_to_ckan()`:

- **pydatajson.DataJson.harvest_dataset_to_ckan()**: Federa la metadata de un dataset en un portal de CKAN.
Toma los siguientes parámetros:
  - **owner_org**: La organización a la que pertence el dataset. Debe encontrarse en el portal de destino.
  - **dataset_origin_identifier**: Identificador del dataset en el catálogo de origen.
  - **portal_url**: URL del portal de CKAN de destino.
  - **apikey**: La apikey de un usuario del portal de destino con los permisos para crear el dataset bajo la
  organización pasada como parámetro.
  - **catalog_id**: El prefijo que va a preceder el id y name del dataset en el portal
  destino, separado por un guión.
  - **download_strategy** (opcional, default None): La referencia a una función que toma (catalog, distribution) de
  entrada y devuelve un booleano. Esta función se aplica sobre todas las distribuciones del dataset. Si devuelve `True`,
  se descarga el archivo indicado en el `downloadURL` de la distribución y se lo sube al portal de destino. Si es None,
  se omite esta operación.


  Retorna el id en el nodo de destino del dataset federado.

- **pydatajson.DataJson.restore_dataset_to_ckan()**: Restaura la metadata de un dataset en un portal de CKAN.
Toma los siguientes parámetros:
  - **owner_org**: La organización a la que pertence el dataset. Debe encontrarse en el portal de destino.
  - **dataset_origin_identifier**: Identificador del dataset en el catálogo de origen.
  - **portal_url**: URL del portal de CKAN de destino.
  - **apikey**: La apikey de un usuario del portal de destino con los permisos para crear el dataset bajo la
  organización pasada como parámetro.
  - **download_strategy** (opcional, default None): La referencia a una función que toma (catalog, distribution) de
  entrada y devuelve un booleano. Esta función se aplica sobre todas las distribuciones del dataset. Si devuelve `True`,
  se descarga el archivo indicado en el `downloadURL` de la distribución y se lo sube al portal de destino. Si es None,
  se omite esta operación.
  - **generate_new_access_url** (opcional, default None): Se pasan los ids de las distribuciones cuyo accessURL se regenerar en el portal de
      destino. Para el resto, el portal debe mantiene el valor pasado en el DataJson.


  Retorna el id del dataset restaurado.

- **pydatajson.DataJson.harvest_catalog_to_ckan()**: Federa los datasets de un catálogo al portal pasado por parámetro.
Toma los siguientes parámetros:
  - **dataset_origin_identifier**: Identificador del dataset en el catálogo de origen.
  - **portal_url**: URL del portal de CKAN de destino.
  - **apikey**: La apikey de un usuario del portal de destino con los permisos para crear el dataset.
  - **catalog_id**: El prefijo que va a preceder el id y name del dataset en el portal
  destino, separado por un guión.
  - **dataset_list** (opcional, default: None): Lista de ids de los datasets a federar. Si no se pasa, se federan todos
  los datasets del catálogo.
  - **owner_org** (opcional, default: None): La organización a la que pertence el dataset. Debe encontrarse en el
  portal de destino. Si no se pasa, se toma como organización el catalog_id.
  - **download_strategy** (opcional, default None): La referencia a una función que toma (catalog, distribution) de
  entrada y devuelve un booleano. Esta función se aplica sobre todas las distribuciones del catálogo. Si devuelve
  `True`, se descarga el archivo indicado en el `downloadURL` de la distribución y se lo sube al portal de destino. Si
  es None, se omite esta operación.

  Retorna el id en el nodo de destino de los datasets federados.
  
- **pydatajson.DataJson.restore_organization_to_ckan()**: Restaura los datasets de una organización al portal pasado por
parámetro. Toma los siguientes parámetros:
    - **catalog**: El catálogo de origen que se restaura.
    - **portal_url**: La URL del portal CKAN de destino.
    - **apikey**: La apikey de un usuario con los permisos que le permitan crear o actualizar los dataset.
    - **dataset_list**: Los ids de los datasets a restaurar. Si no se pasa una lista, todos los datasests se restauran.
    - **owner_org**: La organización a la cual pertencen los datasets.
    - **download_strategy**: Una función (catálogo, distribución)->bool. Sobre las distribuciones que evalúa True,
        descarga el recurso en el downloadURL y lo sube al portal de destino. Por default no sube ninguna distribución.
    - **generate_new_access_url** (opcional, default None): Se pasan los ids de las distribuciones cuyo accessURL se regenerar en el portal de
        destino. Para el resto, el portal debe mantiene el valor pasado en el DataJson.
        
    Retorna la lista de ids de datasets subidos.

- **pydatajson.DataJson.restore_catalog_to_ckan()**: Restaura los datasets de un catálogo al portal pasado por parámetro.
Toma los siguientes parámetros:
  - **catalog**: El catálogo de origen que se restaura.
  - **origin_portal_url**: La URL del portal CKAN de origen.
  - **destination_portal_url**: La URL del portal CKAN de destino.
  - **apikey**: La apikey de un usuario con los permisos que le permitan crear o actualizar los dataset.
  - **download_strategy**: Una función (catálogo, distribución)-> bool. Sobre las distribuciones que evalúa True,
      descarga el recurso en el downloadURL y lo sube al portal de destino. Por default no sube ninguna distribución.
  - **generate_new_access_url** (opcional, default None): Se pasan los ids de las distribuciones cuyo accessURL se regenerar en el portal de
      destino. Para el resto, el portal debe mantiene el valor pasado en el DataJson.

  Retorna un diccionario con key organización y value la lista de ids de datasets subidos a esa organización

- **pydatajson.federation.resources_update()**: Sube archivos de recursos a las distribuciones indicadas y regenera los
accessURL en las distribuciones indicadas. Toma los siguientes parámetros:
  - **portal_url**: URL del portal de CKAN de destino.
  - **apikey**: La apikey de un usuario del portal de destino con los permisos para modificar la distribución.
  - **distributions**: Lista de distribuciones posibles para actualizar.
  - **resource_files** Diccionario con el id de las distribuciones y un path al recurso correspondiente a subir.
  - **generate_new_access_url** (opcional, default None): Lista de ids de distribuciones a las cuales se actualizará el
    accessURL con los valores generados por el portal de destino.
  - **catalog_id** (opcional, default None): prependea el id al id del recurso para encontrarlo antes de subirlo si es
    necesario.
      
  
  Retorna una lista con los ids de las distribuciones modificadas exitosamente.
  
  **Advertencia**: La función `resources_update()` cambia el `resource_type` de las distribuciones a `file.upload`.
  
### Métodos para manejo de organizaciones

- **pydatajson.federation.get_organizations_from_ckan()**: Devuelve el árbol de organizaciones del portal pasado por parámetro.
Toma los siguientes parámetros:
  - **portal_url**: URL del portal de CKAN. Debe implementar el endpoint `/group_tree`.
  
  Retorna una lista de diccionarios con la información de las organizaciones. Recursivamente, dentro del campo `children`,
  se encuentran las organizaciones dependientes en la jerarquía. 

- **pydatajson.federation.get_organization_from_ckan()**: Devuelve un diccionario con la información de una 
organización en base a un id y un portal pasados por parámetro.
Toma los siguientes parámetros:
  - **portal_url**: URL del portal de CKAN. Debe implementar el endpoint `/organization_show`.
  - **org_id**: Identificador o name de la organización a buscar.
  
  Retorna un diccionario con la información de la organización correspondiente al identificador obtenido. 
  _No_ incluye su jerarquía, por lo cual ésta deberá ser conseguida mediante el uso de la función 
  `get_organizations_from_ckan`.

- **pydatajson.federation.push_organization_tree_to_ckan()**: Tomando un árbol de organizaciones como el creado por
`get_organizations_from_ckan()` crea en el portal de destino las organizaciones dentro de su jerarquía. Toma los siguientes
parámetros:
  - **portal_url**: La URL del portal CKAN de destino.
  - **apikey**: La apikey de un usuario con los permisos que le permitan crear las organizaciones.
  - **org_tree**: lista de diccionarios con la data de organizaciones a crear.
  - **parent** (opcional, default: None): Si se pasa, el árbol de organizaciones pasado en `org_tree` se
  crea bajo la organización con `name` pasado en `parent`. Si no se pasa un parámetro, las organizaciones son creadas
  como primer nivel.
  
  Retorna el árbol de organizaciones creadas. Cada nodo tiene un campo `success` que indica si fue creado exitosamente o
  no. En caso de que `success` sea False, los hijos de esa organización no son creados.

- **pydatajson.federation.push_organization_to_ckan()**: Tomando en un diccionario la data de una organización; la crea
en el portal de destino. Toma los siguientes parámetros:
  - **portal_url**: La URL del portal CKAN de destino.
  - **apikey**: La apikey de un usuario con los permisos que le permitan crear las organizaciones.
  - **organization**: Diccionario con la información a crear, el único campo obligatorio es `name`. Para más
  información sobre los campos posibles, ver la [documentación de CKAN](https://docs.ckan.org/en/latest/api/#ckan.logic.action.create.organization_create)
  - **parent** (opcional, default: None): Si se define, la organización pasada en `organization` se crea bajo la
  organización con `name` pasado en `parent`. Si no se pasa un parámetro, las organizaciones son creadas como primer
  nivel.
  
  Retorna el diccionario de la organización creada. El resultado tiene un campo `success` que indica si fue creado
  exitosamente o no.

- **pydatajson.federation.remove_organization_from_ckan()**: Tomando el id o name de una organización; la borra en el
portal de destino. Toma los siguientes parámetros:
  - **portal_url**: La URL del portal CKAN de destino.
  - **apikey**: La apikey de un usuario con los permisos que le permitan borrar la organización.
  - **organization_id**: Id o name de la organización a borrar.
    
  Retorna None.
  
  **Advertencia**: En caso de que la organización tenga hijos en la jerarquía, estos pasan a ser de primer nivel.


- **pydatajson.federation.remove_organizations_from_ckan()**: Tomando una lista de ids o names de organizaciones,
las borra en el portal de destino. Toma los siguientes parámetros:
  - **portal_url**: La URL del portal CKAN de destino.
  - **apikey**: La apikey de un usuario con los permisos que le permitan borrar organizaciones.
  - **organization_list**: Lista de id o names de las organizaciones a borrar.
    
  Retorna None.

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

### generate_datasets_summary()

Se genera a partir de un único catálogo, y contiene, para cada uno de dus datasets:

* **Índice**: El índice, identificador posicional del dataset dentro de la lista `catalog["dataset"]`.
* **Título**: dataset["title"], si lo tiene (es un campo obligatorio).
* **Identificador**: dataset["identifier"], si lo tiene (es un campo recomendado).
* **Cantidad de Errores**: Cuántos errores de validación contiene el dataset, según figure en el detalle de `validate_catalog`
* **Cantidad de Distribuiones**: El largo de la lista `dataset["distribution"]`

A continuación, un fragmento del resultado de este método al aplicarlo sobre el Catálogo del Ministerio de Justicia:
```
[OrderedDict([(u'indice', 0),
              (u'titulo', u'Base de datos legislativos Infoleg'),
              (u'identificador', u'd9a963ea-8b1d-4ca3-9dd9-07a4773e8c23'),
              (u'estado_metadatos', u'OK'),
              (u'cant_errores', 0),
              (u'cant_distribuciones', 3)]),
 OrderedDict([(u'indice', 1),
              (u'titulo', u'Centros de Acceso a la Justicia -CAJ-'),
              (u'identificador', u'9775fcdf-99b9-47f6-87ae-6d46cfd15b40'),
              (u'estado_metadatos', u'OK'),
              (u'cant_errores', 0),
              (u'cant_distribuciones', 1)]),
 OrderedDict([(u'indice', 2),
              (u'titulo',
               u'Sistema de Consulta Nacional de Rebeld\xedas y Capturas - Co.Na.R.C.'),
              (u'identificador', u'e042c362-ff39-476f-9328-056a9de753f0'),
              (u'estado_metadatos', u'OK'),
              (u'cant_errores', 0),
              (u'cant_distribuciones', 1)]),

( ... 13 datasets más ...)

 OrderedDict([(u'indice', 15),
              (u'titulo',
               u'Registro, Sistematizaci\xf3n y Seguimiento de Hechos de Violencia Institucional'),
              (u'identificador', u'c64b3899-65df-4024-afe8-bdf971f30dd8'),
              (u'estado_metadatos', u'OK'),
              (u'cant_errores', 0),
              (u'cant_distribuciones', 1)])]
```

### generate_catalog_readme()

Este reporte en texto plano se pretende como primera introducción somera al contenido de un catálogo, como figurarán en la [Librería de Catálogos](https://github.com/datosgobar/libreria-catalogos/). Incluye datos clave sobre el editor responsable del catálogo, junto con:
- estado de los metadatos a nivel catálogo,
- estado global de los metadatos, y
- cantidad de datasets y distribuciones incluidas.

A continuación, el resultado de este método al aplicarlo sobre el Catálogo del Ministerio de Justicia:
```
# Catálogo: Datos Justicia Argentina

## Información General

- **Autor**: Ministerio de Justicia y Derechos Humanos
- **Correo Electrónico**: justiciaabierta@jus.gov.ar
- **Nombre del catálogo**: Datos Justicia Argentina
- **Descripción**:

> Portal de Datos de Justicia de la República Argentina. El Portal publica datos del sistema de justicia de modo que pueda ser reutilizada para efectuar visualizaciones o desarrollo de aplicaciones. Esta herramienta se propone como un punto de encuentro entre las organizaciones de justicia y la ciudadanía.

## Estado de los metadatos y cantidad de recursos

Estado metadatos globales | Estado metadatos catálogo | # de Datasets | # de Distribuciones
----------------|---------------------------|---------------|--------------------
OK | OK | 16 | 56

## Datasets incluidos

Por favor, consulte el informe [`datasets.csv`](datasets.csv).
```

## Anexo II: Restaurar un catálogo

El primer paso es replicar la estructura de organizaciones del catálogo original al catálogo destino. Asumiendo que
los nombres e ids de las organizaciones del original no se utilizan en el portal donde se replican:

```python
from pydatajson.federation import get_organizations_from_ckan, push_organization_tree_to_ckan
arbol_original = get_organizations_from_ckan('url_portal_original')
arbol_replicado = push_organization_tree_to_ckan('url_portal_destino', 'apikey', arbol_original)
``` 

Para cada organización en `arbol_replicado`, el campo `success` tiene un booleano que marca si fue subida exitosamente.
Con las organizaciones replicadas podemos restaurar la data y metadata del catálogo orginal:

```python
from pydatajson.core import DataJson
from pydatajson.helpers import is_local_andino_resource

original = DataJson('portal-original/data.json')
pushed_datasets =original.restore_catalog_to_ckan('portal-original-url', 'portal-destino-url', 'apikey',
    download_strategy=is_local_andino_resource)
``` 

Si pasamos `download_strategy=None`, tan solo se restaura la metadata. `is_local_andino_resource` es una función
auxiliar que toma una distribución y un catálogo y realiza las siguientes validaciones:

 -1: Chequea que el campo `type` sea `file.upload`
 
 -2: Si la distribución no tiene campo `type`, chequea que el `downloadURL` comience con el `homepage` del catálogo
 
Si se cumple alguna de las condiciones, descarga el recurso y lo sube al portal de destino. Tambien es posible definir
una función propia como estrategia para carga y descarga de archivos. Esta función debe tomar una distribución, un
catálogo y devolver un booleano.
