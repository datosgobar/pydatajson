from pydatajson import threading_helper
from pydatajson import constants
from pydatajson.helpers import is_working_url
from pydatajson.readers import read_catalog
from pydatajson.reporting import generate_datasets_summary


class StatusIndicatorsGenerator(object):

    def __init__(self, catalog, validator=None):
        self.download_url_ok = None
        self.catalog = read_catalog(catalog)
        self.summary = generate_datasets_summary(self.catalog,
                                                 validator=validator)

    def datasets_cant(self):
        return len(self.summary)

    def distribuciones_cant(self):
        return sum(ds['cant_distribuciones'] for ds in self.summary)

    def datasets_meta_ok_cant(self):
        return sum(ds['estado_metadatos'] == 'OK' for ds in self.summary)

    def datasets_meta_error_cant(self):
        return sum(ds['estado_metadatos'] == 'ERROR' for ds in self.summary)

    def datasets_meta_ok_pct(self):
        return self._get_dataset_percentage(self.datasets_meta_ok_cant)

    def datasets_con_datos_cant(self):
        return sum(ds['tiene_datos'] == 'SI' for ds in self.summary)

    def datasets_sin_datos_cant(self):
        return sum(ds['tiene_datos'] == 'NO' for ds in self.summary)

    def datasets_con_datos_pct(self):
        return self._get_dataset_percentage(self.datasets_con_datos_cant)

    def distribuciones_download_url_ok_cant(self):
        return self.download_url_ok or self._validate_download_urls()

    def distribuciones_download_url_error_cant(self):
        return self.distribuciones_cant() - \
               self.distribuciones_download_url_ok_cant()

    def distribuciones_download_url_ok_pct(self):
        total = self.distribuciones_cant()
        if not total:
            return None
        return \
            round(float(self.distribuciones_download_url_ok_cant()) / total, 4)

    def _validate_download_urls(self):
        async_results = []
        for dataset in self.catalog.get('dataset', []):
            distribution_urls = \
                [distribution.get('downloadURL', '')
                 for distribution in dataset.get('distribution', [])]
            async_results += threading_helper\
                .apply_threading(distribution_urls,
                                 is_working_url,
                                 constants.CANT_THREADS_BROKEN_URL_VALIDATOR)

        result = 0
        for res, _ in async_results:
            result += res

        # Guardo el resultado una vez calculado
        self.download_url_ok = result
        return result

    def _get_dataset_percentage(self, indicator):
        total = self.datasets_cant()
        if not total:
            return None
        return round(float(indicator()) / total, 4)
