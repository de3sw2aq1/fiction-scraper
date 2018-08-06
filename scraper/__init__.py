import pkgutil

from .spider import Spider
from . import sites


# A slightly hacky plugin system

# Spider subclasses are defined in a sites submodule. During import this module
# imports all modules in the sites submodule. This module makes available a
# dict mapping domains to spiders.

# Within a spider, ensure a subclass is defined:
#
#     from .. import Spider
#     class MySpider(Spider):
#         domain = 'example.com'
#         def parse(self, url): pass


# Manually load all modules inside sites submodule
for _loader, _name, _ in pkgutil.iter_modules(sites.__path__, prefix=sites.__name__+'.'):
    _loader.find_module(_name).load_module(_name)

# Spider subclasses exist now that the modules have been loaded
spiders = {s.domain: s for s in Spider.__subclasses__()}
