import os
import uuid
import shutil
import logging
import rapidjson as json

from serving import utils
from serving.core import model
from ..interface import common_pb2 as c_pb2
from ..interface import model_pb2 as m_pb2
from ..interface import model_pb2_grpc as m_pb2_grpc
from settings import settings

class Model(m_pb2_grpc.ModelServicer):

    def ListStoredModel(self, request, context):
        models = []
        storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
        for m in os.listdir(os.path.join(storage, "models")):
            ver_list = os.listdir(os.path.join(storage, "models", m))
            models.append(m_pb2.ModelInfo(
                model=m,
                version=ver_list))
        return m_pb2.ListReply(list=models)

    def ExportModelImage(self, request, context):
        packList = {}
        for ver in request.version:
            ret = model.packBundle(request.model, ver)
            logging.debug("pack model {}({}): ".format(request.model, ver, ret))
            if ret is not None:
                packList[ver] = ret
        return c_pb2.ResultReply(code=0, msg=json.dumps(packList))

    def DistroConfig(self, request, context):
        ret = model.updateDistro(
                  request.model.model,
                  request.model.version[0],
                  request.threshold, request.mapping, request.md5)
        return c_pb2.ResultReply(code=ret['code'], msg=ret['msg'])

    def ImportModelDistro(self, request, context):
        ret = model.unpackBundle(request.uuid, {
            'md5':       request.md5,
            'model':     request.model.model,
            'version':   request.model.version[0],
            'mapping':   request.mapping,
            'threshold': request.threshold,
        })
        return c_pb2.ResultReply(code=ret['code'], msg=ret['msg'])

    def DeleteModel(self, request, context):
        storage = utils.getKey('storage', dicts=settings, env_key='JXSRV_STORAGE')
        print(type(request.version))
        version_list = request.version
        model_path = os.path.join(storage, "models", request.model)
        for ver in version_list:
            try:
                shutil.rmtree(os.path.join(model_path, ver))
            except Exception:
                continue
        if len(os.listdir(model_path)) == 0:
            shutil.rmtree(model_path)
        return c_pb2.ResultReply(code=0, msg="deleted")

