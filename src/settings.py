# -*- coding: utf-8 -*-

"""Global settings for the project"""

from tornado.options import define

define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)

settings = {
    # 'storage': "/Users/zhouyou/Documents/jx.github.com/jxserving-framework/src/mxNet",
    'storage': "/Users/zhouyou/Documents/jx.github.com/jxserving-framework/src",
    'preheat': "/Users/zhouyou/Desktop/pose.jpg",
    'redis.host': "localhost",
    'redis.port': "6379",
    'security': "0",

    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",

    'be.trpy.mixed_mode': "1",

    'be.rknnpy.target': "rk3399pro",

    'be.mxpy.preheat': "/Users/zhouyou/Documents/jx.github.com/jxserving-framework/src/mxNet/model1/jx_all.jpg",
    'mxnet_json_path': '/refer_files/refer_json.json',
    'arch': 1,  # 0:GPU /  1:CPU
    'face_image_size': (112, 112),
    "mxnet_identifier_suffix": "/Users/zhouyou/Documents/jx.github.com/jxserving-framework/src/mxNet/model4/identify/insightface/model,0",

}
