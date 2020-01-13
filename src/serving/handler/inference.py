import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import inference
from ..interface import common_pb2 as c_pb2
from ..interface import inference_pb2 as inf_pb2
from ..interface import inference_pb2_grpc as inf_pb2_grpc
from serving.utils import process

class Inference(inf_pb2_grpc.InferenceServicer):
    def InferenceLocal(self, request, context):
        try:
            inference.inferenceLocal(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to inference locally: {}".format(repr(e)))

    def InferenceRemote(self, request, context):
        try:
            inference.inferenceRemote(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to inference remotely: {}".format(repr(e)))

        inf_data = {
            'uuid':   request.uuid,
            'type':   request.type,
            'base64': request.base64,
        }
        ret = inference.inferenceRemote(inf_data, request.bid)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg'],
        )

