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

def bin_request(bin_list):
    for b in bin_list:
        yield b


def bin_response(bin_list):
    for i in range(len(bin_list)):
        yield e_pb2.BinData(
            pack=e_pb2.Block(
                index=i,
                block=bin_list[i],
            ))


def listStoredModel(m_stub):
    response = m_stub.ListStoredModel(c_pb2.PingRequest(client="test.client"))
    print("grpc.model.listStoredModel >>>", response.list)


def exportModelImage(m_stub, e_stub):
    response = m_stub.ExportModelImage(m_pb2.ModelInfo(model="tfpy_frozen_ver", version=["1"]))
    print("grpc.model.exportModelImage >>>", response.code, response.msg)
    ret_uuid = json.loads(response.msg)['1']
    responses = e_stub.DownloadBin(bin_request([e_pb2.BinData(uuid=ret_uuid)]))
    bin_blob = []
    for r in responses:
        print("grpc.exchange.downloadBin >>>", r.pack.index)
        bin_blob.append(r.pack.block)
    with open(ret_uuid+".tar.gz", "ab") as dump:
        for bb in bin_blob:
            dump.write(bb)


def importModelDistro(m_stub, e_stub):
    bin_name = None
    bin_blob = []
    chunk_size = 2*1024*1024
    with open("test.tar.gz", "rb") as f:
        blob = f.read(chunk_size)
        while blob != b"":
            bin_blob.append(blob)
            blob = f.read(chunk_size)
    print(len(bin_blob))
    responses = e_stub.UploadBin(bin_response(bin_blob))
    for r in responses:
        print("grpc.exchange.uploadBin >>>", r.uuid)
        bin_name = r.uuid
    response = m_stub.ImportModelDistro(m_pb2.DistroInfo(
        model=m_pb2.ModelInfo(model="tfpy_frozen_ver", version=["1"]),
        threshold = "[0.1, 0.2, 0.3]",
        mapping = "[lbl1, lbl1, lbl2]",
        uuid = bin_name,
    ))
    print("grpc.model.importModelDistro >>>", response.code, response.msg)


def deleteModel(m_stub):
    response = m_stub.DeleteModel(m_pb2.ModelInfo(model="tfpy_frozen_ver", version=["1"]))
    print("grpc.model.deleteModel >>>", response.code, response.msg)


def run():
    channel = grpc.insecure_channel("localhost:50051")
    m_stub = m_pb2_grpc.ModelStub(channel)
    e_stub = e_pb2_grpc.ExchangeStub(channel)

    listStoredModel(m_stub)
    exportModelImage(m_stub, e_stub)
    deleteModel(m_stub)
    importModelDistro(m_stub, e_stub)
    listStoredModel(m_stub)


if __name__ == '__main__':
    run()

