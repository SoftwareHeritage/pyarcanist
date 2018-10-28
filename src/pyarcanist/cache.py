import os
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': os.path.expanduser('~/.cache/pyarcanist/data'),
    'cache.lock_dir': os.path.expanduser('~/.cache/pyarcanist/lock')
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

__all__ = (cache, )
