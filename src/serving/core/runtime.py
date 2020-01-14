import os
import redis
import logging
import importlib
import multiprocessing
from serving import utils
from serving.core import sandbox
from settings import settings

dev_serial = None
dev_debug = True

FGs = {
  'enable_sandbox': True,
  'enable_device_validation': False,
  'enable_regulator': True,
  'use_native_stat': True
}
Ps = {
  'native_stat': lambda: print("IOI")
}

BEs = {}
Images_pool = multiprocessing.Manager().dict()
Task_Info = multiprocessing.Manager().list()
Conns = {
  'redis.pool': redis.ConnectionPool(
                     host=utils.getKey('redis.host', dicts=settings),
                     port=utils.getKey('redis.port', dicts=settings),
                     db=5),
}


def default_dev_validator():
    global dev_serial
    dsn = sandbox.default_device_serial()
    logging.debug(dsn)
    if dev_serial != sandbox.sha256_digest(dsn):
        os._exit(-1)

@utils.gate(FGs['enable_device_validation'], default_dev_validator)
def loadPlugins(customized_plugins={}):
    Ps['encbase64'] = importlib.import_module('serving.plugin.encbase64')
    Ps['reader'] = importlib.import_module('serving.plugin.reader')
    Ps['trigger'] = importlib.import_module('serving.plugin.trigger')
    for k, v in customized_plugins:
        Ps[k] = v
    logging.debug("Loaded plugins: {}".format(Ps))
