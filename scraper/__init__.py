import pkgutil

from .spider import Spider
from . import sites

# Manually load all modules inside sites
for _loader, _name, _ in pkgutil.iter_modules(sites.__path__, prefix=__name__+'.'):
    _loader.find_module(_name).load_module(_name)

# Spider subclasses exist now that the modules have been loaded
spiders = {s.domain: s for s in Spider.__subclasses__()}
