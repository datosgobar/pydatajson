
# coding: utf-8

# In[3]:

import openpyxl as pyxl
import json
import io


# In[4]:

dataxlsx = "tests/catalogo_justicia.xlsx"


# In[5]:

workbook = pyxl.load_workbook(dataxlsx)


# In[6]:

def sheet_to_table(worksheet):
    headers = [cell.value for cell in worksheet.rows[0]]
    value_rows = [
        [cell.value for cell in row] for row in worksheet.rows[1:] 
        # Únicamente considero filas con al menos un campo de valor no-nulo (None)
        if any([cell.value for cell in row])]
    
    table = [
        # Ignoro los campos con valores nulos (None)
        {k: v for (k, v) in zip(headers, row) if v} 
        for row in value_rows
    ]
    return table

def string_to_list(s):
    return [value.strip() for value in s.split(",")]

def make_publisher(catalog_or_dataset):
    level = catalog_or_dataset
    keys = [k for k in ["publisher_name", "publisher_mbox"] if k in level]
    if fields:
        level["publisher"] = {
            key.replace("publisher_",""): level.pop(key) for key in keys
        }
    return level

assert(string_to_list(" pan , vino,gorriones ,23")==["pan", "vino", "gorriones", "23"])

def make_contactPoint(dataset):
    keys = [k for k in ["contactPoint_fn", "contactPoint_hasEmail"] if k in dataset]
    if fields:
        dataset["contactPoint"] = {
            key.replace("contactPoint_",""): dataset.pop(key) for key in keys
        }
    return dataset

def get_dataset_index(dataset_identifier):
    """Devuelve el índice de un dataset en el catálogo en función de su identificador"""
    matching_datasets = [idx for idx, dataset in enumerate(catalog["catalog_dataset"]) if dataset["dataset_identifier"]==dataset_identifier]
    assert len(matching_datasets)!=0, "No hay ningún dataset con el identifier {}".format(dataset_identifier)
    assert len(matching_datasets)<2, "Hay más de un dataset con el identifier {}: {}".format(dataset_identifier, matching_datasets)
    dataset_index = matching_datasets[0]
    
    return dataset_index

def get_distribution_indexes(dataset_identifier, distribution_title):
    """Devuelve el índice de una distribución en su dataset en función de su título, junto con el índice de su dataset padre en el catálogo, en función de su identificador"""
    dataset_index = get_dataset_index(dataset_identifier)
    dataset = catalog["catalog_dataset"][dataset_index]
    
    matching_distributions = [idx for idx, distribution in enumerate(dataset["dataset_distribution"]) if distribution["distribution_title"]==distribution_title]
    assert len(matching_distributions)!=0, "No hay ninguna distribución con el título {} en el dataset con identificador {}".format(distribution_title, dataset_identifier)
    assert len(matching_distributions)<2, "Hay más de una distribución con el título {} en el dataset con identificador {}: {}".format(distribution_title, dataset_identifier, matching_distributions)
    distribution_index = matching_distributions[0]
    
    return dataset_index, distribution_index


# In[7]:

catalogs = sheet_to_table(workbook["Catalog"])
datasets = sheet_to_table(workbook["Dataset"])
distributions = sheet_to_table(workbook["Distribution"])
themes = sheet_to_table(workbook["Theme"])
fields = sheet_to_table(workbook["Field"])


# In[8]:

# Genero el catálogo base
assert (len(catalogs)==1), "Hay más de un catálogo en la hoja 'Catalog'"
catalog = catalogs[0]


# In[9]:

# Agrego themes y datasets al catálogo
catalog["catalog_themeTaxonomy"] = themes
catalog["catalog_dataset"] = datasets


# In[10]:

# Agrego lista de distribuciones vacía a cada datasets
for dataset in catalog["catalog_dataset"]:
    dataset["dataset_distribution"] = []


# In[11]:

# Agrego distribuciones a los datasets
for distribution in distributions:
    dataset_index = get_dataset_index(distribution["dataset_identifier"])
    catalog["catalog_dataset"][dataset_index]["dataset_distribution"].append(distribution)


# In[12]:

# Agrego fields a las distribuciones
for field in fields:
    dataset_index, distribution_index = get_distribution_indexes(field["dataset_identifier"], field["distribution_title"])
    distribution = catalog["catalog_dataset"][dataset_index]["dataset_distribution"][distribution_index]
    if "distribution_field" in distribution:
        distribution["distribution_field"].append(field)
    else:
        distribution["distribution_field"] = [field]


# In[13]:

# Transformo campos de texto separado por comas en listas/arrays
if "catalog_language" in catalog:
    catalog["catalog_language"] = string_to_list(catalog["catalog_language"])

for dataset in catalog["catalog_dataset"]:
    array_fields = ["dataset_superTheme", "dataset_theme", "dataset_tags", "dataset_keyword", "dataset_language"]
    for field in array_fields:
        if field in dataset:
            dataset[field] = string_to_list(dataset[field])


# In[14]:

# Elimino los prefijos de los campos a nivel catálogo
for key in catalog.keys():
    if key.startswith("catalog_"):
        catalog[key.replace("catalog_", "")] = catalog.pop(key)
    else:
        catalog.pop(key)


# In[15]:

# Elimino los prefijos de los campos a nivel tema
for theme in catalog["themeTaxonomy"]:
    for key in theme.keys():
        if key.startswith("theme_"):
            theme[key.replace("theme_", "")] = theme.pop(key)
        else:
            theme.pop(key)


# In[16]:

# Elimino los prefijos de los campos a nivel dataset
for dataset in catalog["dataset"]:
    for key in dataset.keys():
        if key.startswith("dataset_"):
            dataset[key.replace("dataset_", "")] = dataset.pop(key)
        else:
            dataset.pop(key)
    


# In[17]:

# Elimino los campos auxiliares y los prefijos de los campos a nivel distribución
for dataset in catalog["dataset"]:
    for distribution in dataset["distribution"]:
        for key in distribution.keys():
            if key.startswith("distribution_"):
                    distribution[key.replace("distribution_", "")] = distribution.pop(key)
            else:
                distribution.pop(key)


# In[18]:

# Elimino los campos auxiliares y los prefijos de los campos a nivel "campo"
for dataset in catalog["dataset"]:
    for distribution in dataset["distribution"]:
        if "field" in distribution:
            for field in distribution["field"]:
                for key in field.keys():
                    if key.startswith("field_"):
                        field[key.replace("field_", "")] = field.pop(key)
                    else:
                        field.pop(key)


# In[19]:

# Agrupo las claves de "publisher" y "contactPoint" en un diccionario
catalog = make_publisher(catalog)
for dataset in catalog["dataset"]:
    dataset = make_publisher(dataset)
    dataset = make_contactPoint(dataset)


# In[20]:

# Exporto el resultado
target_file = "tests/catalogo_justicia.json"

catalog_str = json.dumps(catalog, indent=4, separators=(",", ": "), encoding="utf-8", ensure_ascii=False)
with io.open(target_file, "w", encoding='utf-8') as target:
    target.write(catalog_str)


# ## Validación del resultado

# In[21]:

import pydatajson

dj = pydatajson.DataJson()
dj.generate_harvester_config(target_file, harvest='valid', export_path="catalogo_jus_harvest.csv")
dj.generate_datasets_report(target_file, harvest='valid', export_path="catalogo_jus_report.csv")

