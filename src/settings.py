# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os

from tornado.options import define


define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)


settings = {
    'backend': "pytorch",
    'collection_path': "",
    'security': "0",

    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",

    'be.tfpy.preheat': "",

    'be.trpy.preheat': "",
    'be.trpy.mixed_mode': "1",
}

