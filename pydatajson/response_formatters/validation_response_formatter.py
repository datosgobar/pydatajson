# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import abc


class ValidationResponseFormatter(object):

    def __init__(self, response):
        self.response = response

    @abc.abstractmethod
    def format(self):
        raise NotImplementedError
