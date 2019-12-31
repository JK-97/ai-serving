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

import os
import sys
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from interface import common_pb2 as c_pb2
from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import model_pb2 as m_pb2
from interface import model_pb2_grpc as m_pb2_grpc
from interface import exchange_pb2 as e_pb2
from interface import exchange_pb2_grpc as e_pb2_grpc


def createModel(m_stub):
    ext = {
        "tensors": {
            'input_type': ["1", "0"],
            'input':      ["Placeholder:0", "Placeholder_1:0"],
            'output':     [
                "resnet_v1_101_5/cls_score/BiasAdd:0",
                "resnet_v1_101_5/cls_prob:0",
                "add:0",
                "resnet_v1_101_3/rois/concat:0"
            ]
        }
    }
    example_model = {
        "name": "iot_bdz_frcnn_frozen_new",
        "labels": ["lbl1", "lbl2", "lbl3"],
        "head": "rcnn",
        "bone": "resnet",
        "impl": "tensorflow.frozen",
        "version": "1",
        "threshold":["0.25", "0.25", "0.25"],
        "mapping": ["map1", "map2", "map3"],
        "modelext": json.dumps(ext),
    }
    response = m_stub.CreateModel(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.createModel >>>", response.code, response.msg)

def run():
    channel = grpc.insecure_channel("localhost:50051")
    m_stub = m_pb2_grpc.ModelStub(channel)

    createModel(m_stub)


if __name__ == '__main__':
    run()
