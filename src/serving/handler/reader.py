import logging

from google.protobuf.json_format import MessageToDict

from ..interface import common_pb2 as c_pb2
from ..interface import reader_pb2_grpc as re_pb2_grpc
from serving.core import runtime
from serving.core import runtime
from multiprocessing import Process


class Reader(re_pb2_grpc.ReaderServicer):
    def GetReader(self, request, context):
        data = MessageToDict(request)
        try:
            p1 = Process(target=runtime.Ps['reader'].reader, args=(data,))
            p2 = Process(target=runtime.Ps['trigger'].trigger, args=(data,))
            p1.start()
            p2.start()
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to get reader: {}".format(repr(e)))



