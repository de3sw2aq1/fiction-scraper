import pkgutil

from .spider import Spider
from . import sites


# A slightly hacky plugin system

# Spider subclasses are defined in a sites submodule. During import this module
# imports all modules in the sites submodule. This module makes available a
# dict mapping domains to spiders.

# A quirk of this importing is that the import heirachy is broken a bit. That
# is, spiders must use:
#     from . import Spider
# instead of:
#     from .. import Spider

# Manually load all modules inside sites submodule
for _loader, _name, _ in pkgutil.iter_modules(sites.__path__, prefix=__name__+'.'):
    _loader.find_module(_name).load_module(_name)

# Spider subclasses exist now that the modules have been loaded
spiders = {s.domain: s for s in Spider.__subclasses__()}
