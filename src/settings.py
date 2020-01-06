# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os


settings = {
    'port': "[::]:50051",
    'storage': "/home/zhouyou/jxserving_storage",
    'preheat': "/home/zhouyou/jxserving_storage/preheat.jpeg",
    'redis.host': "localhost",
    'redis.port': "6379",

    'be.tfsrv.host': "127.0.0.1",
    'be.tfsrv.adapter': "restful",
    'be.tfsrv.grpc_port': "8500",
    'be.tfsrv.rest_port': "8501",

    'be.trpy.mixed_mode': "1",

    'be.rknnpy.target': "rk3399pro",
}

