#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
# force protobuf to use cpp-implementation
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import time
import logging
from concurrent import futures

import grpc

from settings import settings
from serving import router
from serving.core import runtime

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
debug = True
profile = False

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    router.register_response(server)
    server.add_insecure_port('[::]:50051')

    runtime.loadPlugins()

    server.start()
    logging.info("start service at: {}".format("[::]:50051"))
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    if debug:
        logging.getLogger('').setLevel(logging.DEBUG)
    else:
        logging.getLogger('').setLevel(logging.INFO)

    if profile:
        from google.protobuf.internal import api_implementation
        logging.warning("Using protobuf implementation: {}".format(api_implementation.Type()))

    serve()
