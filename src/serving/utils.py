"""
  AI-Serving Utils

  Contact: 1179160244@qq.com
"""

import os
import time
import logging
from multiprocessing import Process
from enum import Enum, unique  # auto is available after python 3.7
from serving.core import error_code


@unique
class Access(Enum):
    Essential = 'essential'
    Optional = 'optional'


profile = False


def profiler_timer(prompt):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if profile:
                ts = time.time()
                ret = func(*args, **kwargs)
                te = time.time()
                #logging.debug("{} elapse {} secs".format(prompt, te-ts))
                print("{} elapse {} secs".format(prompt, te-ts))
                return ret
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def gate(gate_option, feature_func):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if gate_option:
                feature_func()
                return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def limit(gate_option, feature_func):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if gate_option:
                isExist = feature_func(*args, **kwargs)
                if isExist:
                    raise error_code.ExistBackendError()
                return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def process(func):
    def wrapper(*args, **kwargs):
        return Process(target=func, args=args, kwargs=kwargs).start()
    return wrapper


def getKey(key, dicts, env_key='', v=None, level=Access.Essential):
    value = None
    # get Key
    if key in dicts:
        value = dicts[key]
        if isinstance(value, str):
            logging.debug("Get <{}> from dicts: {}".format(key, value))
        else:
            logging.debug("Get <{}> from dicts".format(key))
    if env_key in os.environ:
        value = os.environ[env_key]
        logging.debug("Overwrite <{}> from environment: {}".format(key, value))
    if isinstance(value, str) and value == '':
        value = None
    # access level
    if value is None:
        if level == Access.Essential:
            message = "Failed to get <{}> from dicts or environ".format(key)
            logging.debug(message)
            raise RuntimeError(message)
        if level == Access.Optional:
            logging.debug("Return None for <{}>".format(key))
    # validator
    if hasattr(v, '__call__'):
        ret, err = v(value)
        if ret is not None:
            logging.debug("Pass <{}> on {}: {}".format(key, v, ret))
            value = ret
        else:
            raise RuntimeError("Validate <{}> failed: {}".format(key, err))
    else:
        if v is not None and value != v:
            raise RuntimeError("Expected {}, but get {}".format(v, value))
    # return
    return value
