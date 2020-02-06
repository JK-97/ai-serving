import logging

from google.protobuf.json_format import MessageToDict

from serving.core import inference, error_reply
from serving.core.error_code import InferenceDataError, RunTimeException
from ..interface import common_pb2 as c_pb2
from ..interface import inference_pb2_grpc as inf_pb2_grpc
from serving.utils import process

class Inference(inf_pb2_grpc.InferenceServicer):
    def InferenceLocal(self, request, context):
        try:
            inference.inferenceLocal(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except InferenceDataError as e:
            return c_pb2.ResultReply(
                code=InferenceDataError.code_local,
                msg=repr(e)
            )
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException,
                                         msg="failed to inference locally: {}".format(repr(e)))

    def InferenceRemote(self, request, context):
        try:
            inference.inferenceRemote(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except InferenceDataError as e:
            return c_pb2.ResultReply(
                code=InferenceDataError.code_remote,
                msg=repr(e)
            )
        except Exception as e:
            logging.exception(e)
            error_reply.error_msg(c_pb2, RunTimeException,
                                  msg="failed to inference remotely: {}".format(repr(e)))
