from abc import ABC, abstractmethod
import os
import sys
import tempfile
from pathlib import Path
import logging

from lxml.html import document_fromstring, tostring, builder as E
import requests


class Spider(ABC):
    def __init__(self, *args):
        super().__init__()
        self._session = requests.session()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.metadata = {}

    @property
    @abstractmethod
    def domain(self):
        pass

    @abstractmethod
    def parse(self, url):
        pass

    def fetch(self, url):
        r = self._session.get(url)
        doc = document_fromstring(r.content)
        doc.make_links_absolute(r.url)
        return doc

    def crawl(self, url):
        # Clear metadata in case story is being re-crawled
        self.metadata = {}

        self.info('beginning parse')
        body = E.BODY(*self.parse(url))

        # parse() must be called before metadata is accessed, or it may not be
        # populated yet. 
        head = E.HEAD(*self._generate_meadata_elements())

        doc = E.HTML(head, body)
        
        return tostring(doc, encoding='unicode', pretty_print=True, doctype='<!doctype html>')
    
    def debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self._logger.info(*args, **kwargs)
    
    def warning(self, *args, **kwargs):
        self._logger.warning(*args, **kwargs)
    
    def critical(self, *args, **kwargs):
        self._logger.critical(*args, **kwargs)

    def log(self, *args, **kwargs):
        self._logger.log(*args, **kwargs)

    def _generate_meadata_elements(self):
        yield E.META(charset="UTF-8")

        for name, content in self.metadata.items():
            if name == 'title':
                yield E.TITLE(content)
            else:
                yield E.META(name=name, content=content)
