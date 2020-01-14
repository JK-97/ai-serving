#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
from google.protobuf.json_format import ParseDict

from serving.interface import common_pb2 as c_pb2
from serving.interface import exchange_pb2 as e_pb2
from serving.interface import exchange_pb2_grpc as e_pb2_grpc
from serving.interface import model_pb2 as m_pb2
from serving.interface import model_pb2_grpc as m_pb2_grpc


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


def listModels(m_stub):
    response = m_stub.ListModels(c_pb2.PingRequest(client="test.client"))
    print("grpc.model.listModels >>>", response.models)


def createModel(m_stub):
    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        "version": "1",
    }
    response = m_stub.CreateModel(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.createModel >>>", response.code, response.msg)


def updateConfig(m_stub):
    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        "version": "1",
        "implhash": "da6c749c0738ba54fb10861c5b4f6de9",
        "threshold": ["0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2"],
        "mapping": ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        "modelext": "{\"tensors\": {\"input\": [\"input/input_data:0\", \"input/is_train:0\"], \"output\": [\"myoutput1:0\", \"myoutput2:0\", \"myoutput3:0\"]}}"
    }
    response = m_stub.DistroConfig(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.distroConfig >>>", response.code, response.msg)


def deleteModel(m_stub):
    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        "version": "1",
    }
    response = m_stub.DeleteModel(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.deleteModel >>>", response.code, response.msg)


def exportModelImage(m_stub, e_stub):
    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        "version": "1",
    }
    response = m_stub.ExportModelImage(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.exportModelImage >>>", response.code, response.msg)

    implhash = "da6c749c0738ba54fb10861c5b4f6de9"
    responses = e_stub.DownloadBin(bin_request([e_pb2.BinData(uuid=implhash)]))
    bin_blob = []
    for r in responses:
        print("grpc.exchange.downloadBin >>>", r.pack.index)
        bin_blob.append(r.pack.block)
    with open(implhash + ".tar.gz", "ab") as dump:
        for bb in bin_blob:
            dump.write(bb)


def importModelDistro(m_stub, e_stub):
    bin_name = None
    bin_blob = []
    chunk_size = 2 * 1024 * 1024
    with open("da6c749c0738ba54fb10861c5b4f6de9.tar.gz", "rb") as f:
        blob = f.read(chunk_size)
        while blob != b"":
            bin_blob.append(blob)
            blob = f.read(chunk_size)
    print(len(bin_blob))
    responses = e_stub.UploadBin(bin_response(bin_blob))
    for r in responses:
        print("grpc.exchange.uploadBin >>>", r.uuid)
        bin_name = r.uuid

    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'bundle': bin_name,
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        'version': "1",
        'implhash': "da6c749c0738ba54fb10861c5b4f6de9",
        "threshold": ["0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2",
                      "0.2", "0.2"],
        "mapping": ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "dA", "dB", "dC", "dD", "dE", "dF"],
    }
    response = m_stub.ImportModelDistro(ParseDict(example_model, m_pb2.ModelInfo()))
    print("grpc.model.importModelDistro >>>", response.code, response.msg)


def importModelDistroV2(m_stub, e_stub):
    bin_name = None
    bin_blob = []
    chunk_size = 2 * 1024 * 1024
    with open("da6c749c0738ba54fb10861c5b4f6de9.tar.gz", "rb") as f:
        blob = f.read(chunk_size)
        while blob != b"":
            bin_blob.append(blob)
            blob = f.read(chunk_size)
    print(len(bin_blob))
    responses = e_stub.UploadBin(bin_response(bin_blob))
    for r in responses:
        print("grpc.exchange.uploadBin >>>", r.uuid)
        bin_name = r.uuid

    example_model = {
        'name': "biandianzhan",
        'labels': ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cA", "cB", "cC", "cD", "cE", "cF"],
        'bundle': bin_name,
        'head': "YOLOv3",
        'bone': "darknet",
        'impl': "tensorflow.frozen",
        'fullhash': "226a7354795692913f24bee21b0cd387-1",
        "threshold": ["0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2", "0.2",
                      "0.2", "0.2"],
        "mapping": ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "dA", "dB", "dC", "dD", "dE", "dF"],
    }
    response = m_stub.ImportModelDistroV2(ParseDict(example_model, m_pb2.ModelInfoBrief()))
    print("grpc.model.importModelDistroV2 >>>", response.code, response.msg)


def run():
    channel = grpc.insecure_channel("localhost:50051")
    m_stub = m_pb2_grpc.ModelStub(channel)
    e_stub = e_pb2_grpc.ExchangeStub(channel)

    listModels(m_stub)
    createModel(m_stub)
    listModels(m_stub)
    createModel(m_stub)
    updateConfig(m_stub)
    exportModelImage(m_stub, e_stub)
    deleteModel(m_stub)
    importModelDistro(m_stub, e_stub)
    listModels(m_stub)
    deleteModel(m_stub)


if __name__ == '__main__':
    run()
