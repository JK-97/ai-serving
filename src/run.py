#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Basic run script"""

import os
# force protobuf to use cpp-implementation
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'cpp'

from serving.urls import url_patterns
import tornado.ioloop
import tornado.options
from tornado.options import options
import tornado.web
import tornado.autoreload
import logging
from settings import settings
from serving import utils
from serving.core import runtime
from serving.backend import abstract_backend as ab

enable_better_exceptions = os.getenv("BETTER_EXCEPTIONS")


class TornadoApplication(tornado.web.Application):

    def __init__(self):
        tornado.web.Application.__init__(self, url_patterns, **settings)


def newBackendWithCollection(collection):
    backend = utils.getKey('backend', dicts=settings,
                          env_key='JXSRV_BACKEND', v=ab.BackendValidator)

    if backend == ab.Type.TfPy:
        from serving.backend import tensorflow_python as tfpy
        return tfpy.TfPyBackend(collection, {
            'preheat': utils.getKey('be.tfpy.preheat', dicts=settings)
        })
    if backend == ab.Type.TfSrv:
        from serving.backend import tensorflow_serving as tfsrv
        return tfsrv.TfSrvBackend(collection, {
            'host': utils.getKey('be.tfsrv.host', dicts=settings),
            'port': utils.getKey('be.tfsrv.rest_port', dicts=settings),
        })
    if backend == ab.Type.Torch:
        from serving.backend import torch_python as trpy
        return trpy.TorchPyBackend(collection, {
            'preheat': utils.getKey('be.trpy.preheat', dicts=settings),
            'mixed_mode': utils.getKey('be.trpy.mixed_mode', dicts=settings),
        })

def main():
    tornado.options.parse_command_line()
    if enable_better_exceptions == "1":
        import better_exceptions
        better_exceptions.hook()

    if options.debug:
        logging.getLogger('').setLevel(logging.DEBUG)
    else:
        logging.getLogger('').setLevel(logging.INFO)

    if options.profile:
        from google.protobuf.internal import api_implementation
        logging.warning("Using protobuf implementation: {}".format(api_implementation.Type()))

    runtime.BACKEND = newBackendWithCollection(
            utils.getKey('collection_path', dicts=settings, env_key='JXSRV_COLLECTION_PATH'))
    assert(runtime.BACKEND != None)
    logging.debug("Loaded backend: {}".format(runtime.BACKEND))

    app = TornadoApplication()
    app.listen(options.port)
    logging.info("start service at: {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
