#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc

from interface import common_pb2 as c_pb2
from interface import connectivity_pb2 as conn_pb2
from interface import connectivity_pb2_grpc as conn_pb2_grpc

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = conn_pb2_grpc.ConnectivityStub(channel)

    response = stub.Ping(c_pb2.PingRequest(client="test.client"))
    print("grpc.connectivity.ping >>>", response.version)

    response = stub.ListNodeResources(c_pb2.PingRequest(client="test.client"))
    print("grpc.connectivity.listNodeResources >>> cpu:", response.cpu, "mem:", response.mem, "gpu:", response.gpu, "dsk:", response.dsk)

if __name__ == '__main__':
    run()

