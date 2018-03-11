import os
import subprocess
import sys
import tempfile
import yaml

META_LUA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    'filters',
    'meta.lua')

class Pandoc:
    def __init__(self, *args, format='html'):
        # There isn't a good way to specify yaml metadata for all writers
        # By using a filter we can manually specify a path to a yaml file
        # https://groups.google.com/d/msg/pandoc-discuss/6KLbZk7NVWk/0XMWewhLCQAJ
        # http://pandoc.org/lua-filters.html#default-metadata-file

        self.metadata = {'title': 'foo'}
        self._metadata_file = tempfile.NamedTemporaryFile('w', suffix='.markdown', delete=False)
        self._pandoc = subprocess.Popen(
            [
                'pandoc',
                *args,
                '--from', format,
                '--lua-filter', META_LUA_PATH, '--metadata=metadata_file:'+self._metadata_file.name
            ],
            stdin=subprocess.PIPE)
    
    def write(self, *args, **kwargs):
        self._pandoc.stdin.write(*args, **kwargs)
    
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
