import logging

from django.conf import settings
from django.core.cache import cache
from functools import wraps

CACHE_FILTER_TIMEOUT = None
PREFIX_CACHE_KEY = 'cache_filter'

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def cache_filter(param_list=None):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            try:
                if request.GET:
                    _save_filter_to_cache(request, param_list)
                _restore_filter_from_cache(request, param_list)
            except Exception:
                logger.exception('An error occured with cache system')
            return func(request, *args, **kwargs)
        return inner
    return decorator


def _save_filter_to_cache(request, param_list):
    param_to_cache = {key: value for key, value in request.GET.items() if key in param_list} if param_list \
                     else request.GET
    key = _get_filter_key(request)
    cache.set(key, param_to_cache, timeout=CACHE_FILTER_TIMEOUT)


def _restore_filter_from_cache(request, param_list):
    cached_value = _get_from_cache(request)
    if cached_value:
        request.GET = {key: value for key, value in cached_value.items() if key in param_list} if param_list \
                      else cached_value


def _get_from_cache(request):
    key = _get_filter_key(request)
    return cache.get(key)


def _get_filter_key(request):
    user = request.user
    path = request.path
    return "_".join([PREFIX_CACHE_KEY, str(user.id), path])
