# -*- coding: utf-8 -*-

from pydatajson.readers import read_catalog
from pydatajson.reporting import generate_datasets_summary
from pydatajson.validators\
    .distribution_download_urls_validator \
    import DistributionDownloadUrlsValidator


class StatusIndicatorsGenerator(object):

    def __init__(self, catalog, validator=None, verify_ssl=True,
                 url_check_timeout=1):
        self.download_url_ok = None
        self.catalog = read_catalog(catalog)
        self.summary = generate_datasets_summary(self.catalog,
                                                 validator=validator,
                                                 verify_ssl=verify_ssl)
        self.verify_url = verify_ssl
        self.url_check_timeout = url_check_timeout

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
        if self.download_url_ok:
            return self.download_url_ok
        validator = DistributionDownloadUrlsValidator(
            self.catalog, self.verify_url, self.url_check_timeout)
        self.download_url_ok = validator.validate()
        return self.download_url_ok

    def distribuciones_download_url_error_cant(self):
        return self.distribuciones_cant() - \
               self.distribuciones_download_url_ok_cant()

    def distribuciones_download_url_ok_pct(self):
        total = self.distribuciones_cant()
        if not total:
            return None
        return \
            round(float(self.distribuciones_download_url_ok_cant()) / total, 4)

    def _get_dataset_percentage(self, indicator):
        total = self.datasets_cant()
        if not total:
            return None
        return round(float(indicator()) / total, 4)
