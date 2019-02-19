Versiones
=========
0.4.35 (2019-02-19)
-------------------
* Actualiza la validación para aceptar el string vacío como valor válido
* Marca los identificadores de distribuciones y datasets como campos requeridos


0.4.34 (2019-02-01)
-------------------
* Implementa método para tomar frecuencia de una serie de tiempo


0.4.33 (2019-01-10)
-------------------
* Cambia el kwarg dj_format por catalog_format
* Pequeño fix para los catalogos remotos json incorrectamente leídos como xlsx


0.4.32 (2019-01-08)
-------------------
* Fix al dj_format para las lecturas


0.4.31 (2019-01-08)
-------------------
* Se aceptan catálogos sin formato para la lectura del DataJson
* Nuevo parámetro para forzar la lectura de un catálogo en cierto formato
* Actualización de pyyaml  


0.4.30 (2018-12-28)
-------------------
* No se validan URLs repetidas para datasets, hay casos válidos donde ocurren 


0.4.29 (2018-12-21)
-------------------
* Método `remove_organizations_from_ckan()`.
* Cambia la estrategia de lectura para json sin extensión. 


0.4.28 (2018-12-11)
-------------------
* Parametro opcional a `push_dataset_to_ckan()` para regenerar `accessURL` de recursos.
* Permite el cálculo de indicadores con catálogo central opcional. 


0.4.27 (2018-11-23)
-------------------
* Las funcionalidades que estaban en `restore_catalog_to_ckan()` pasan a ser de `restore_organization`. `restore_catalog` se compone de varias llamadas a `restore_organization`.
* Documentación de `restore_catalog_to_ckan`.

0.4.26 (2018-11-05)
-------------------
* Agrega métodos de manejo de organizaciones para bajar la información o subir a un portal CKAN.
* Fix en indicador 'datasets_con_datos_pct' al calcular el porcentaje.
* Cambio en los tests para que usen archivos temporales en lugar de crearlos en la carpeta results.


0.4.25 (2018-10-22)
-------------------
* Agrega indicador 'datasets_con_datos_cant' para identificar la cantidad de datasets que tienen alguna distribución potencialmente con datos y los que no.
* Expande la función `backup.make_catalogs_backup()` con argumentos opcionales para facilitar la generación de backups descargando las distribuciones.


0.4.24 (2018-10-16)
-------------------
* Cambia el valor default en el indicador `datasets_frecuencias_cant`.


0.4.23 (2018-10-2)
-------------------
* Se agregan HTML, PHP y RAR como formatos de datos posibles.
* Bugfix relacionado a los valores default en el cálculo de indicadores.


0.4.22 (2018-09-05)
-------------------
* Agrega espacios a los caracteres permitidos en keyword.


0.4.21 (2018-08-21)
-------------------
* Tests y pequeños bugfixes a ckan_reader.
* Adecua el codigo a pycodestyle.
* Fija piso de 80% de coverage para CI.


0.4.20 (2018-08-09)
-------------------

* Agrega tildes y ñ a los caracteres permitidos en keyword.
* Cuenta los campos faltantes como `None` en los indicadores.


0.4.19 (2018-08-07)
-------------------

* Validación de caracteres permitidos en los keywords.
* Bugfix a la lectura de listas en xlsx con comas extras.
* Bugfix en el cual se repetían los errores de validación si se pedía formato lista.


0.4.18 (2018-07-30)
-------------------

* Agrega interfaz por línea de comandos para validar rápidamente un catálogo: `pydatajson validation http://datos.gob.ar/data.json`.
* Validación de keywords, themes, y lenguajes vacíos.
* Bugfix en `distribution_has_time_index` para capturar excepciones en field inválidos.


0.4.17 (2018-07-10)
-------------------

* Agregados 3 indicadores `distribuciones_federadas`, `datasets_licencias_cant` y `distribuciones_tipos_cant`.
* `harvest_catalog_to_ckan` devuelve el mensaje en lugar de las representaciones de las excepciones.


0.4.16 (2018-06-19)
-------------------

* Bugfix en la escritura y lectura de catálogos xlsx.
* Federar campo `type` en distribuciones.
* Refactor del logging del módulo. Todos los eventos se escriben en el logger `pydatajson`.
* Reestructuración de la respuesta de `harvest_catalog_to_ckan()`, devuelve adicionalmente los datasets con errores de federación.


0.4.15 (2018-05-15)
-------------------

* Cambios en los requerimientos y `setup.py` para definir los environment markers de manera que soporte setuptools.


0.4.14 (2018-05-11)
-------------------

* `harvest_catalog_to_ckan()` atrapa todas las excepciones de un dataset y no detiene la ejecución.


0.4.13 (2018-05-06)
-------------------

* Agrega una primer interfaz sencilla por línea de comandos. Cualquier módulo puede ser usado como `pydatajson module_name arg1 arg2 arg3` siempre que defina un método `main()` a nivel del módulo que procese los parámetros.

0.4.12 (2018-05-04)
-------------------

* Agrega función `get_distribution_time_index()` que devuelve el `title` del `field` marcado como time_index en una distribución de series de tiempo, si este lo tiene.

0.4.11 (2018-04-25)
-------------------

* Corrige bug de `harvest_catalog_ot_ckan` para manejar excepciones de validación de los datasets


0.4.10 (2018-04-24)
-------------------

* Mejora manejo de errores de las funciones para federar catálogos completos.

0.4.9 (2018-04-24)
-------------------

* Agrego función para generar ids de distribuciones en catálogos que nos los tienen (compatibilidad con perfil 1.0)
* Agrega función para eliminar todos los datastets federados de un catálogo que se encuentren en un CKAN
* Implemento fallback que busca un theme por identifier primero o por label después (si falla)
* Agrego excepciones a los chequeos de formato vs. extensión
* Agrego paramétros a la función title_to_name() para establecer una longitud máxima del resultado de la transformación en caracteres

0.4.8 (2018-04-18)
-------------------

* Mejoro manejo de errores de los métodos optimizados de búsqueda

0.4.7 (2018-04-17)
-------------------

* Flexibiliza métodos de búsqueda optimizados para aceptar data.json's versión 1.0
* Mejora la performance de los métodos de búsqueda optimizados

0.4.6 (2018-04-17)
-------------------

* Re-estructura el archivo de configuración para federación (nueva versión simplificada)
* Agrega módulo para hacer backups de datos y metadatos de un catálogo
* Mejora la performance de guardar catálogos en Excel

0.4.4 (2018-04-09)
-------------------

* Agrega wrappers para `push_dataset_to_ckan()`

0.4.3 (2018-03-20)
-------------------

* Mejora el manejo de themes para recrear un catálogo

0.4.2 (2018-03-13)
-------------------

* Agrega funciones auxiliares para la administración de un CKAN vía API para facilitar la administración de la federación de datasets
    - `remove_dataset_to_ckan()`
* Incorpora nuevas validaciones (formatos y fileNames)
* Agrega flags opcionales para que `push_dataset_to_ckan()` sea un método que transforma opcionalmente la metadata de un dataset

0.4.1 (2018-02-16)
-------------------

* `datasets_equal()` permite especificar los campos a tener en cuenta para la comparación, como un parámetro.

0.4.0 (2018-02-08)
-------------------

* Incorpora métodos para federar un dataset de un catálogo a un CKAN o un Andino: `push_dataset_to_ckan()`.
* Actualiza validaciones y esquema de metadatos al Perfil Nacional de Metadatos versión 1.1.

0.3.21 (2017-12-22)
-------------------

* Agrega soporte para Python 3.6

0.3.20 (2017-11-16)
-------------------

* Agrego método `get_theme()` para devolver un tema de la taxonomía específica del catálogo según su `id` o `label`.

0.3.19 (2017-10-31)
-------------------

* Agrego métodos de búsqueda de series de tiempo en un catálogo (`get_time_series()`) y un parámetro `only_time_series=True or False` para filtrar datasets y distribuciones en sus métodos de búsqueda (`get_datasets(only_time_series=True)` devuelve sólo aquellos datasets que tengan alguna serie de tiempo).

0.3.18 (2017-10-19)
-------------------

* Agrego posibilidad de pasar un logger desde afuera a la función de lectura de catálogos en Excel.

0.3.15 (2017-10-09)
-------------------

* Agrega filtro por series de tiempo en `get_datasets()` y `get_distributions()`. Tienen un parámetro `only_time_series` que devuelve sólo aquellos que tengan o sean distribuciones con series de tiempo.

0.3.12 (2017-09-21)
-------------------

* Agrega función para escribir un catálogo en Excel.
* Agrega funciones para remover datasets o distribuciones de un catálogo.

0.3.11 (2017-09-13)
-------------------

* Incorpora parámetro para excluir campos de metadatos en la devolución de la búsqueda de datasets y distribuciones.

0.3.10 (2017-09-11)
-------------------

* Agregar referencia interna a los ids de las entidades padre de otras (distribuciones y fields.)

0.3.9 (2017-09-05)
-------------------

* Flexibiliza lectura de extras en ckan to datajson.
* Flexibiliza longitud mínima de campos para recomendar su federación o no.
* Agrega método para devolver los metadatos a nivel de catálogo.
* Resuelve la escritura de objetos python como texto en excel.

0.3.8 (2017-08-25)
-------------------

* Agrega stop words a `helpers.title_to_name()`

0.3.4 (2017-08-21)
-------------------

* Agrega método para buscar la localización de un `field` en un catálogo.

0.3.3 (2017-08-20)
-------------------

* Agrega método para convertir el título de un dataset o distribución en un nombre normalizado para la creación de URLs.

0.3.2 (2017-08-16)
-------------------

* Amplía reporte de federación en markdown.

0.3.0 (2017-08-14)
-------------------

* Agrega métodos para navegar un catálogo desde el objeto DataJson.

0.2.27 (2017-08-11)
-------------------

* Agrega validacion de que el campo `superTheme` sólo contenga ids en mayúsculas o minúsculas de alguno de los 13 temas de la taxonomía temática de datos.gob.ar.
* Agrega validación limitando a 60 caracteres los nombres de los campos `field_title`.
* Mejoras al reporte de asistencia a la federación.

0.2.26 (2017-08-04)
-------------------

* Agrega validación de que no haya ids repetidos en la lista de temas de `themeTaxonomy`.
* Agrega traducción de ckan del campo extra `Cobertura temporal` a `temporal`.

0.2.24 (2017-08-03)
-------------------
* Mejoras en los reportes de errores y análisis de datasets para federación
* Métodos `DataJson.validate_catalog()` y `DataJson.generate_datasets_report()` tienen nuevas opciones para mejorar los reportes, especialmente en excel.

0.2.23 (2017-08-02)
-------------------

* Bug fixes

0.2.22 (2017-08-02)
-------------------

* Agrega estilo y formato al reporte de datasets
* Agrega nuevos campos al reporte de datasets
* Agrega un campo identificador del catálogo en el archivo de configuración de federación

0.2.21 (2017-08-02)
-------------------

* Tolera el caso de intentar escribir un reporte de datasets sobre un catálogo que no tiene datasets. Loggea un warning en lugar de levantar una excepción.

0.2.20 (2017-08-01)
-------------------

* Elimina la verificación de SSL en las requests de ckan_reader.

0.2.19 (2017-08-01)
-------------------

* Elimina la verificación de SSL en las requests.

0.2.18 (2017-07-25)
-------------------

* Mejora la validación del campo `temporal`
* Agrega formas de reporte de errores para el método `DataJson.validate_catalog()`:
    - Devuelve sólo errores con  `only_errors=True`
    - Devuelve una lista de errores lista para ser convertida en tabla con `fmt="list"`

0.2.17 (2017-07-18)
-------------------

* Agrega un método para convertir un intervalo repetido (Ej.: R/P1Y) en su representación en prosa ("Anualmente").
* Agrego método que estima los datasets federados que fueron borrados de un catálogo específico. Se consideran datasets federados y borrados de un catálogo específico aquellos cuyo publisher.name existe dentro de algún otro dataset todavía presente en el catálogo específico.

0.2.16 (2017-07-13)
-------------------

* Bug fix: convierte a unicode antes de escribir un objeto a JSON.

0.2.15 (2017-07-11)
-------------------

* Modifica la definición de dataset actualizado usando el campo "modified" del perfil de metadatos. Si este campo no está presente en la metadata de un dataset, se lo considera desactualizado.

0.2.14 (2017-07-10)
-------------------

* Modifica la definición de dataset usada para comparar limitándola a la comparación por "title" y "publisher_name".

0.2.13 (2017-06-22)
-------------------

* Agrega método para verificar si un dataset individual está actualizado

0.2.12 (2017-06-22)
-------------------

* Se modifica el template de CATALOG README
* Se agrega el indicador "datasets_no_federados" a generate_catalogs_indicators

0.2.11 (2017-05-23)
-------------------

* Se agrega en `core` el método `DataJson.generate_catalogs_indicators`, que genera indicadores de monitoreo de catálogos, recopilando información sobre, entre otras cosas, su validez, actualidad y formato de sus contenidos.

0.2.10 (2017-05-11)
-------------------

* Correción ortográfica del listado de frecuencias de actualización admisibles (`pydatajson/schemas/accrualPeriodicity.json`).

0.2.9 (2017-05-04)
------------------

* Hotfixes para que `pydatajson` sea deployable en nuevos entornos donde el `setup.py` estaba fallando.

0.2.5 (2017-02-16)
------------------

* Se agrega una nueva función a `readers`, `read_ckan_catalog`, que traduce los metadatos que disponibiliza la Action API v3 de CKAN al estándar `data.json`. Esta función _no_ está integrada a `read_catalog`.

* Se modifican todos los esquemas de validación, de modo que los campos opcionales de cualquier tipo y nivel acepten strings vacías.

0.2.0 (2017-01-31)
------------------

* Se reestructura la librería en 4 módulos: `core`, `readers`, `writers` y `helpers`. Toda la funcionalidad se mantiene intacta, pero algunas funciones muy utilizadas cambian de módulo. En particular, `pydatajson.pydatajson.read_catalog` es ahora `pydatajson.readers.read_catalog`, y `pydatajson.xlsx_to_json.write_json_catalog` es ahora `pydatajson.writers.write_json_catalog` (o `pydatajson.writers.write_json`).

* Se agrega el parámetro `frequency` a `pydatajson.DataJson.generate_harvester_config`, que controla la frecuencia de cosecha que se pretende de los datasets a incluir en el archivo de configuración. Por omisión, se usa `'R/P1D'` (diariamente) para todos los datasets.

* Se agrega la carpeta `samples/`, con dos rutinas de transformación y reporte sobre catálogos de metadatos en formato XLSX.

0.1.7 (2017-01-10)
------------------

* Se agrega el módulo `xlsx_to_json`, con dos métodos para lectura de archivos locales o remotos, sean JSON genéricos (`xlsx_to_json.read_json()`) o metadatos de catálogos en formato XLSX (`read_local_xlsx_catalog()`).
* Se agrega el método `pydatajson.read_catalog()` que interpreta todos las representaciones externas o internas de catálogos conocidas, y devuelve un diccionario con sus metadatos.

0.1.6 (2017-01-04)
------------------

* Se incorpora el método `DataJson.generate_harvestable_catalogs()`, que filtra los datasets no deseados de un conjunto de catálogos.
* Se agrega el parámetro `harvest` a los métodos `DataJson.generate_harvestable_catalogs()`, `DataJson.generate_datasets_report()` y `DataJson.generate_harvester_config()`, para controlar el criterio de elección de los datasets a cosechar.
* Se agrega el parámetro `export_path` a los métodos `DataJson.generate_harvestable_catalogs()`, `DataJson.generate_datasets_report()` y `DataJson.generate_harvester_config()`, para controlar la exportación de sus resultados.

0.1.4 (2016-12-23)
------------------

* Se incorpora el método `DataJson.generate_datasets_report()`, que reporta sobre los datasets y la calidad de calidad de metadatos de un conjunto de catálogos.
* Se incorpora el método `DataJson.generate_harvester_config()`, que crea archivos de configuración para el Harvester a partir de los reportes de `generate_datasets_report()`.

0.1.3 (2016-12-19)
------------------

* Al resultado de `DataJson.validate_catalog()` se le incorpora una lista (`"errors"`) con información de los errores encontrados durante la validación en cada nivel de jerarquía ("catalog" y cada elemento de "dataset")

0.1.2 (2016-12-14)
------------------

* Se incorpora validación de tipo y formato de campo
* Los métodos `DataJson.is_valid_catalog()` y `DataJson.validate_catalog()` ahora aceptan un `dict` además de un `path/to/data.json` o una url a un data.json.

0.1.0 (2016-12-01)
------------------

Primera versión para uso productivo del paquete.

* La instalación via `pip install` debería reconocer correctamente la ubicación de los validadores por default.
* El manejo de data.json's ubicados remotamente se hace en función del resultado de `urlparse.urlparse`
* El formato de respuesta de `validate_catalog` se adecúa a la última especificación (ver [`samples/validate_catalog_returns.json`](samples/validate_catalog_returns.json).

0.0.13 (2016-11-25)
-------------------

* Intentar que la instalación del paquete sepa donde están instalados los schemas por default

0.0.12 (2016-11-25)
-------------------

* Primera versión propuesta para v0.1.0
