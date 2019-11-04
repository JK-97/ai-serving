#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc

from interface import common_pb2 as c_pb2
from interface import backend_pb2 as be_pb2
from interface import backend_pb2_grpc as be_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = be_pb2_grpc.BackendStub(channel)

    response = stub.ListSupportedType(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listSupportedType >>>", response.support)

    response = stub.ListRunningBackends(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listRunningBackends >>>", response.status)

    response = stub.InitializeBackend(be_pb2.BackendRequest(
        bid="",
        btype="tensorflow"
    ))
    print("grpc.backend.initializeBackend >>>", response.code, response.msg)
    return_bid = response.msg

    response = stub.ListBackend(be_pb2.BackendRequest(bid=return_bid, btype=""))
    print("grpc.backend.listBackend >>>",
        response.bid,
        response.model,
        response.status,
        response.msg)

    response = stub.ListRunningBackends(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listRunningBackends >>>", response.status)

    response = stub.TerminateBackend(be_pb2.BackendRequest(bid=return_bid, btype=""))
    print("grpc.backend.terminateBackend >>>", response.code, response.msg)

    response = stub.ListRunningBackends(c_pb2.PingRequest(client="test.client"))
    print("grpc.backend.listRunningBackends >>>", response.status)

if __name__ == '__main__':
    run()

