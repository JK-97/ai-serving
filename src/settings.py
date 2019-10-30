# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os

from tornado.options import define


define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)


settings = {
    'storage': "/home/ubuntu/ar_example_model",
    'preheat': "/home/ubuntu/ar_example_model/preheat.jpeg",
    'redis.host': "localhost",
    'redis.port': "6379",
    'security': "0",

    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",

    'be.trpy.mixed_mode': "1",

    'be.rknnpy.target': "rk3399pro",
}

