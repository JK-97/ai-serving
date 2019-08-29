"""
  JXServing Utils

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
import time
import logging
import threading
from enum import Enum, unique # auto is available after python 3.7
from tornado.options import options


@unique
class Access(Enum):
    Essential = 'essential'
    Optional  = 'optional'


def profiler_timer(prompt):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if options.profile:
                ts = time.time()
                ret = func(*args, **kwargs)
                te = time.time()
                logging.debug("{} elapse {} secs".format(prompt, te-ts))
                return ret
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def threads(func):
    def wrapper(*args, **kwargs):
        return threading.Thread(target=func, args=args, kwargs=kwargs).start()
    return wrapper


def getKey(key, dicts, env_key='', v=None, level=Access.Essential):
    value = None

    if (key in dicts) and (dicts[key] != ''):
        value = dicts[key]
        logging.debug("Get <{}> from dicts: {}".format(key, value))
    if (env_key in os.environ) and (os.environ[env_key] != ''):
        value = os.environ[env_key]
        logging.debug("Overwrite <{}> from environment: {}".format(key, value))

    if value == None:
        if level == Access.Essential:
            message = "Failed to get <{}> from dicts or environ".format(key)
            logging.debug(message)
            raise RuntimeError(message)
        if level == Access.Optional:
            logging.debug("Return None for <{}>".format(key))

    if v:
        ret, err = v(value)
        if ret != None: 
            logging.debug("Pass <{}> on {}: {}".format(key, v, ret))
            value = ret
        else:
            raise RuntimeError("Validation <{}> failed: {}".format(key, err))
            value = None

    return value
