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

from interface import common_pb2 as c_pb2
from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc
from interface import model_pb2 as m_pb2
from interface import model_pb2_grpc as m_pb2_grpc
from interface import exchange_pb2 as e_pb2
from interface import exchange_pb2_grpc as e_pb2_grpc


def listStoredModel(m_stub):
    response = m_stub.ListStoredModel(c_pb2.PingRequest(client="test.client"))
    print("grpc.model.listStoredModel >>>", response.list)


def distroConfig(m_stub):
    response = m_stub.DistroConfig(m_pb2.DistroInfo(
        model=m_pb2.ModelInfo(
            model="tfpy_frozen_ver",
            version=["1"],
        ),
        threshold=[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        mapping=["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "n", "n", "n", "n", "n", "n", "n"],
    ))
    print("grpc.model.listStoredModel >>>", response.code, response.msg)


def run():
    channel = grpc.insecure_channel("localhost:50051")
    m_stub = m_pb2_grpc.ModelStub(channel)
    e_stub = e_pb2_grpc.ExchangeStub(channel)

    listStoredModel(m_stub)
    distroConfig(m_stub)


if __name__ == '__main__':
    run()

