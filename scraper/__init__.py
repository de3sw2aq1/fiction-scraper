import os
import subprocess
import sys
import tempfile
from pathlib import Path

from lxml.html import document_fromstring, tostring, clean
import requests

import yaml

META_LUA_PATH = Path(__file__).parent.parent / 'pandoc' / 'filters' / 'meta.lua'

class Document:
    def __init__(self, *args):
        # There isn't a good way to specify yaml metadata for all writers
        # By using a filter we can manually specify a path to a yaml file
        # https://groups.google.com/d/msg/pandoc-discuss/6KLbZk7NVWk/0XMWewhLCQAJ
        # http://pandoc.org/lua-filters.html#default-metadata-file

        self.metadata = {}
        self._metadata_file = tempfile.NamedTemporaryFile('w', suffix='.markdown', delete=False)
        self._pandoc = subprocess.Popen(
            [
                'pandoc',
                *args,
                '--from', 'html',
                '--lua-filter', META_LUA_PATH, '--metadata=metadata_file:'+self._metadata_file.name
            ],
            stdin=subprocess.PIPE)

        self._session = requests.session()

    def fetch_doc(self, url):
        doc = document_fromstring(self._session.get(url).content)
        doc.make_links_absolute(url)
        return doc

    def _write(self, *args, **kwargs):
        self._pandoc.stdin.write(*args, **kwargs)

    def write(self, *elements):
        for e in elements:
            self._write(tostring(e))

    def close(self):
        try:
            # Write metadata
            yaml.safe_dump(
                self.metadata,
                self._metadata_file,
                explicit_start=True,
                explicit_end=True,
                default_flow_style=False)
        finally:
            # Close stdin to pandoc
            self._pandoc.stdin.close()

            # Wait for pandoc and clean up
            self._pandoc.wait()
            os.unlink(self._metadata_file.name)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
