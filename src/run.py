#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

import tornado.ioloop
import tornado.web
from tornado.options import options

from serving.urls import url_patterns
from settings import settings

# force protobuf to use cpp-implementation
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'


class TornadoApplication(tornado.web.Application):

    def __init__(self):
        tornado.web.Application.__init__(self, url_patterns, **settings)


def main():
    tornado.options.parse_command_line()

    if options.debug:
        logging.getLogger('').setLevel(logging.DEBUG)
    else:
        logging.getLogger('').setLevel(logging.INFO)

    if options.profile:
        from google.protobuf.internal import api_implementation
        logging.warning("Using protobuf implementation: {}".format(api_implementation.Type()))

    app = TornadoApplication()
    app.listen(options.port)
    logging.info("start service at: {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
