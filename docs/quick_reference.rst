Referencia rápida
=================

Lectura
-------
.. autoclass:: pydatajson.core.DataJson
   :members: __init__

Escritura
---------
.. autoclass:: pydatajson.core.DataJson
   :members: to_json, to_xlsx

Validación
----------
.. autoclass:: pydatajson.core.DataJson
   :members: is_valid_catalog, validate_catalog

Búsqueda
--------
.. autoclass:: pydatajson.core.DataJson
   :members: get_datasets, get_dataset, get_fields, get_field

Indicadores
-----------
.. autoclass:: pydatajson.core.DataJson
   :members: generate_indicators

Reportes
--------
.. autoclass:: pydatajson.core.DataJson
   :members: generate_datasets_summary, generate_catalog_readme

Federación
----------
.. autoclass:: pydatajson.core.DataJson
   :members: harvest_dataset_to_ckan, restore_dataset_to_ckan, harvest_catalog_to_ckan, restore_catalog_to_ckan, push_theme_to_ckan, push_new_themes

.. autofunction:: pydatajson.federation.remove_dataset_from_ckan
