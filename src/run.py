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

    try:
        model_path = os.environ['JXSRV_MODEL_PATH']
        settings['model_path'] = model_path
        logging.debug("Overwrite model_path from ENV: {}".format(settings['model_path']))
    except KeyError as e:
        pass
    if settings['model_path'] == "":
        logging.error("Unset model_path in settings or ENV")
        exit(-1)
    logging.debug("Set model_path from settings: {}".format(settings['model_path']))

    try:
        preheat_image_path = os.environ['JXSRV_PREHEAT_IMAGE_PATH']
        settings['preheat_image_path'] = preheat_image_path
        logging.debug("Overwrite preheat_image_path from ENV: {}".format(settings['preheat_image_path']))
    except KeyError as e:
        pass
    if settings['preheat_image_path'] == "":
        logging.error("Unset preheat_image_path in settings or ENV")
        exit(-1)
    logging.debug("Set preheat_image_path from settings: {}".format(settings['preheat_image_path']))

    app = TornadoApplication()
    app.listen(options.port)
    logging.info("start service at: {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
