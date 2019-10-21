#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import Counter

import pydatajson.custom_exceptions as ce
from pydatajson.validators.simple_validator import SimpleValidator


class ThemeIdsNotRepeatedValidator(SimpleValidator):

    def validate(self):
        if "themeTaxonomy" in self.catalog:
            theme_ids = [theme["id"]
                         for theme in self.catalog["themeTaxonomy"]]
            dups = self._find_dups(theme_ids)
            if len(dups) > 0:
                yield ce.ThemeIdRepeated(dups)

    @staticmethod
    def _find_dups(elements):
        return [item for item, count in Counter(elements).items()
                if count > 1]
