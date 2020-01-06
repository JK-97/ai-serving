import os
import sys
import uuid

from ..interface import exchange_pb2 as ex_pb2
from ..interface import exchange_pb2_grpc as ex_pb2_grpc

chunk_size = 2 * 1024 * 1024
block_limit = 500


class Exchange(ex_pb2_grpc.ExchangeServicer):

    def DownloadBin(self, request_iterator, context):
        for req in request_iterator:
            bin_path = os.path.join("/tmp", req.uuid + ".tar.gz")
            bin_size = sys.getsizeof(bin_path)
            bin_blob = []
            with open(bin_path, "rb") as f:
                blob = f.read(chunk_size)
                while blob != b"":
                    bin_blob.append(blob)
                    blob = f.read(chunk_size)
                for i in range(len(bin_blob)):
                    yield ex_pb2.BinData(
                        uuid=req.uuid,
                        size=bin_size,
                        pack=ex_pb2.Block(
                            index=i,
                            block=bin_blob[i]
                        ))
                yield ex_pb2.BinData(
                    uuid=req.uuid,
                    size=0,
                    pack=ex_pb2.Block(
                        index=0,
                        block=b""
                    ))

    def UploadBin(self, request_iterator, context):
        tmp = str(uuid.uuid4())
        bin_path = os.path.join("/tmp", tmp + ".tar.gz")
        response_list = []
        with open(bin_path, "ab") as dump:
            for req in request_iterator:
                if req.pack.index > block_limit:
                    yield ex_pb2.BinData(uuid="-1")
                    break
                dump.write(req.pack.block)
                yield ex_pb2.BinData(uuid=tmp)
