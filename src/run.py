#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Basic run script"""

import os
from serving.urls import url_patterns
from settings import settings
import tornado.ioloop
import tornado.options
from tornado.options import options
import tornado.web
import tornado.autoreload
import logging

enable_better_exceptions = os.getenv("BETTER_EXCEPTIONS")


class TornadoApplication(tornado.web.Application):

    def __init__(self):
        tornado.web.Application.__init__(self, url_patterns, **settings)


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
        logging.warning("Detect protobuf implementation: {}".format(api_implementation.Type()))

    app = TornadoApplication()
    app.listen(options.port)
    logging.info("start service at: {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
