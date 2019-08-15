# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os

from tornado.options import define


define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)


settings = {
    'backend': "tensorflow-serving",
    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",

    'collection_path': "/home/admin/to_sd_tf_serving/tf_serving/TF_serving1",
    'preheat_image': "/home/admin/to_sd_tf_serving/try/daoxian30.jpg"
}

