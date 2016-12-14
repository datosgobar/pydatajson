# Tests de `is_valid_catalog`

## Casos de testeo **válidos**:

- `full_data.json`: Ejemplo completo segun `paquete-apertura-datos`.
- `minimum_data.json`: Idéntico a `full_data.json`, pero únicamente con los campos obligatorios.
- `empty_minimum_data.json`: Idéntico a `minimum_data.json`, pero con todos los valores de campos vacíos.

## Casos de testeo **inválidos**:

Están creados en base a `full_data.json`, quitando el campo `title` en los tres niveles de la jerarquía de metadatos: Catálogo, Dataset, Recurso:

- `missing_catalog_title_data.json`
- `missing_dataset_title_data.json`
- `missing_resource_title_data.json`
