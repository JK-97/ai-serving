#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
import uuid
import time
import json
import redis
import base64

from PIL import Image
from io import BytesIO
from google.protobuf.json_format import ParseDict

from interface import common_pb2 as c_pb2
from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import model_pb2 as m_pb2
from interface import model_pb2_grpc as m_pb2_grpc
from interface import exchange_pb2 as e_pb2
from interface import exchange_pb2_grpc as e_pb2_grpc


def createModel(m_stub):
    example_model = {
        'name':   "tfpy_frozen_ver",
        'labels': [
            "class2", "class_2", "jyz_pl", "yw_gkxfw", "hxq_gjzc", "bj_bpmh", "jyz", "jsxs", "yw_nc", "hxq_yfzc", "bj_zc", "bj_bjps", "jyz_lw", "jyz_zc", "hxq_yfps", "hxq_gjbs",
        ],
        'head': "YOLO",
        'bone': "mobilenet",
        'impl': "tensorflow.frozen",
        "version": "1",
        "threshold": [
            "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25", "0.25"
        ],
        'mapping': [
            "class2", "class_2", "jyz_pl", "yw_gkxfw", "hxq_gjzc", "bj_bpmh", "jyz", "jsxs", "yw_nc", "hxq_yfzc", "bj_zc", "bj_bjps", "jyz_lw", "jyz_zc", "hxq_yfps", "hxq_gjbs",
        ],
        'modelext': "{\"tensors\": {\"input\": [\"input/input_data:0\", \"input/is_train:0\"], \"output\": [\"myoutput1:0\", \"myoutput2:0\", \"myoutput3:0\"]}}"
    }
    response = m_stub.CreateModel(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.createModel >>>", response.code, response.msg)

def run():
    channel = grpc.insecure_channel("localhost:50051")
    m_stub = m_pb2_grpc.ModelStub(channel)

    createModel(m_stub)


if __name__ == '__main__':
    run()
