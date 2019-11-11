from ..core import backend
from ..interface import common_pb2 as c_pb2
from ..interface import inference_pb2 as inf_pb2
from ..interface import inference_pb2_grpc as inf_pb2_grpc

class Inference(inf_pb2_grpc.InferenceServicer):

    def CreateAndLoadModel(self, request, context):
        calm_data = {
            'bid':   request.bid,
            'btype': request.btype,
            'model': request.model,
            'version': request.version,
            'mode':  request.mode,
            'encrypted': request.encrypted,
            'a64key': request.a64key,
            'pvtpth': request.pvtpth,
            'extra': request.extra,
        }
        ret = backend.createAndLoadModel(calm_data)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg'],
        )

    def ReloadModel(self, request, context):
        calm_data = {
            'bid':   request.bid,
            'btype': request.btype,
            'model': request.model,
            'version': request.version,
            'mode':  request.mode,
            'encrypted': request.encrypted,
            'a64key': request.a64key,
            'pvtpth': request.pvtpth,
            'extra': request.extra,
        }
        ret = backend.loadModel(calm_data, request.bid)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg'],
        )

    def InferenceLocal(self, request, context):
        inf_data = {
            'uuid': request.uuid,
            'path': request.path,
        }
        ret = backend.inferenceLocal(inf_data, request.bid)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg'],
        )

    def InferenceRemote(self, request, context):
        inf_data = {
            'uuid':   request.uuid,
            'type':   request.type,
            'base64': request.base64,
        }
        ret = backend.inferenceRemote(inf_data, request.bid)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg'],
        )

