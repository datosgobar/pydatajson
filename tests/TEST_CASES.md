# Estrategia de testeo para `pydatajson`

## Tests de `is_valid_catalog` y `validate_catalog` locales

Estas dos funciones son las principales herramientas de validación de archivos `data.json` (de ahroa en más, "datajsons"). Para testearlas, se utilizan datajsons de prueba guardados en [`samples/`](samples/).

El archivo de prueba fundamental se llama [full_data.json`](samples/full_data.json), que contiene todas las claves (requeridos y opcionales) descritos en el [Perfil de Metadatos](https://docs.google.com/spreadsheets/d/1PqlkhB1o0u2xKDYuex3UC-UIPubSjxKCSBxfG9QhQaA/edit#gid=1493891225), con valores de ejemplo de tipo y formato correcto. Este archivo *siempre* debe pasar la validación sin errores.

A partir de este archivo base, se crearon otros 26 datajsons, cada uno con una o (rara vez) unas pocas modificaciones que cubren distintas funcionaliades del validador. Por ejemplo, el archivo [`missing_dataset_title.json`](samples/missing_dataset_title.json) es idéntico a `full_data.json`, salvo que la clave `catalog["dataset"]["title"]` fue eliminada.

Cada uno de ellos se utiliza en una función de testeo cuyo nombre tiene el formato `test_validity_of_[DATAJSON_FILENAME]` en el archivo[`test_pydatajson.json`](test_pydtajson.json). En caso de que el nombre del datajson no sea lo suficientemente esclarecedor respecto a su intención, la función de testeo tendrá un docstring brevísimo explicándola en cierto detalle.

### Casos de testeo **válidos**:

- `full_data.json`: Ejemplo completo según las especificaciones de `paquete-apertura-datos`.
- `minimum_data.json`: Idéntico a `full_data.json`, pero incluye únicamente con los campos obligatorios.
- `null_dataset_theme.json`, `null_field_description.json`: Idénticos a `full_data.json`, con un campo opcional faltante.

## Casos de testeo **inválidos**:

Todos los demás datajsons (23) son casos de testeo inválidos, y los errores que contienen caen en una de tres categorías:
- una clave requerida está ausente del catálogo,
- una clave requerida u opcional está presente, pero el tipo del valor que toma no es el esperado, o
- una clave requerida u opcional está presente y su valor es del tipo esperado, pero el formato no es el correcto.

## Tests de `is_valid_catalog` y `validate_catalog` remotos

Como ambas funciones tienen la capacidad de validar un datajson en una ubicación remota en caso de que se les pase una URL bien formada, la función `test_correctness_of_accrualPeriodicity_regex`.
