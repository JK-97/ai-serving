# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os

from tornado.options import define


define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)


settings = {
    'backend': "rknn",
    'collection_path': "/home/toybrick/ar_example_model",
    'redis.host': "localhost",
    'redis.port': "6379",
    'security': "0",

    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",
    'be.tfsrv.preheat': "/home/jiangxing/ar_example_model/preheat.jpeg",

    'be.tfpy.preheat': "/home/jiangxing/ar_example_model/preheat.jpeg",

    'be.trpy.preheat': "/home/jiangxing/ar_example_model/ar_pose/data/preview.jpg",
    'be.trpy.mixed_mode': "1",

    'be.rknnpy.preheat': "/home/toybrick/jxserving/src/test/daoxian30.jpg",
    'be.rknnpy.target': "rk3399pro",
}

    #'be.tfpy.preheat': "/home/jiangxing/ar_example_model/ar_pose/data/preview.jpg",
