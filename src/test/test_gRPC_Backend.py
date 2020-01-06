#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
from google.protobuf.json_format import ParseDict

from serving.interface import backend_pb2 as be_pb2
from serving.interface import backend_pb2_grpc as be_pb2_grpc
from serving.interface import common_pb2 as c_pb2


def listSupport(stub):
    response = stub.ListSupportedType(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listSupportedType >>>", response.support)


def listAll(stub):
    response = stub.ListRunningBackends(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listRunningBackends >>>", response.backends)


def initialize(stub):
    backend_info = {'impl': "tensorflow.frozen"}
    response = stub.InitializeBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
    print("grpc.backend.initializeBackend >>>", response.code, response.msg)
    return response.msg


def listOne(stub, return_bid):
    backend_info = {'bid': return_bid}
    response = stub.ListBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
    print("grpc.backend.listBackend >>>",
          response.info,
          response.status,
          response.msg)


def loadModel(stub, return_bid):
    load_info = {
        'bid': return_bid,
        'model': {
            'implhash': "226a7354795692913f24bee21b0cd387",
            'version': "1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.ReloadModelOnBackend(ParseDict(load_info, be_pb2.LoadRequest()))
    print("grpc.backend.reloadModelOnBackend >>>", response.code, response.msg)


def createAndLoadModel(stub):
    load_info = {
        'backend': {'impl': "tensorflow.frozen"},
        'model': {
            'implhash': "226a7354795692913f24bee21b0cd387",
            'version': "1",
        },
        'encrypted': 0,
        'a64key': "",
        'pvtkey': "",
    }
    response = stub.CreateAndLoadModel(ParseDict(load_info, be_pb2.FullLoadRequest()))
    print("grpc.backend.createAndLoadModel >>>", response.code, response.msg)


def terminate(stub, return_bid):
    backend_info = {'bid': return_bid}
    response = stub.TerminateBackend(ParseDict(backend_info, be_pb2.BackendInfo()))
    print("grpc.backend.terminateBackend >>>", response.code, response.msg)


def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = be_pb2_grpc.BackendStub(channel)

    listSupport(stub)
    listAll(stub)
    ret = initialize(stub)
    listOne(stub, ret)
    # listAll(stub)
    # loadModel(stub, ret)
    # terminate(stub, ret)
    # listAll(stub)
    # createAndLoadModel(stub)
    # createAndLoadModel(stub)
    # createAndLoadModel(stub)  # expected failed, test creation limitation


if __name__ == '__main__':
    run()
