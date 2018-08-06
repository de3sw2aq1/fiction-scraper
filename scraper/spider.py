from abc import ABC, abstractmethod
import os
import sys
import tempfile
from pathlib import Path
import logging

from lxml.html import document_fromstring, tostring, builder as E
import requests

from . import filters


class Spider(ABC):
    def __init__(self, *args):
        super().__init__()
        self._session = requests.session()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.metadata = {}

    filters = filters.DEFAULT_FILTERS

    @property
    @abstractmethod
    def domain(self):
        pass

    @abstractmethod
    def parse(self, url):
        pass

    def fetch(self, url):
        """Fetch a URL and return it as an lxml document.

        Follows HTTP redirects. The `base_url` is set on the returned
        document. All links in the document are converted to absolute links.
        """
        r = self._session.get(url)
        doc = document_fromstring(r.content, base_url=r.url)
        doc.make_links_absolute()
        return doc

    def crawl(self, url):
        # Clear metadata in case story is being re-crawled
        self.metadata = {}

        self.info('beginning parse')
        body = E.BODY(*self.parse(url))

        self.info('applying filters')
        for f in self.filters:
            f(body)

        # parse() must be called before metadata is accessed, or it may not be
        # populated yet. 
        head = E.HEAD(*self._generate_meadata_elements())

        doc = E.HTML(head, body)

        self.info('tostring on document')
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
