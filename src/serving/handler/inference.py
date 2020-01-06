import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import inference, error_code, error_reply
from ..interface import common_pb2 as c_pb2
from ..interface import inference_pb2 as inf_pb2
from ..interface import inference_pb2_grpc as inf_pb2_grpc


class Inference(inf_pb2_grpc.InferenceServicer):
    def InferenceLocal(self, request, context):
        try:
            inference.inferenceLocal(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.InferenceDataError):
                return c_pb2.ResultReply(
                    code=error_code.InferenceDataError.code_local,
                    msg=repr(e)
                )
            return error_reply.error_msg(c_pb2, error_code.RunTimeException,
                                         msg="failed to inference locally: {}".format(repr(e)))

    def InferenceRemote(self, request, context):
        try:
            inference.inferenceRemote(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.InferenceDataError):
                return c_pb2.ResultReply(
                    code=error_code.InferenceDataError.code_remote,
                    msg=repr(e)
                )
            error_reply.error_msg(c_pb2, error_code.RunTimeException,
                                  msg="failed to inference remotely: {}".format(repr(e)))
