import os
import json
import uuid
import shutil
import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving import utils
from serving.core import model
from ..interface import common_pb2 as c_pb2
from ..interface import model_pb2 as m_pb2
from ..interface import model_pb2_grpc as m_pb2_grpc
from settings import settings

class Model(m_pb2_grpc.ModelServicer):
    def CreateModel(self, request, context):
        try:
            model.createModel(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to create model: {}".format(repr(e)))

    def ListModels(self, request, context):
        try:
            return ParseDict(model.listModels(), m_pb2.ModelList())
        except Exception as e:
            logging.exception(e)
            return m_pb2.ModelList(models=[])

    def DistroConfig(self, request, context):
        try:
            model.updateModel(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to update model info: {}".format(repr(e)))

    def DeleteModel(self, request, context):
        try:
            model.deleteModel(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to delete model: {}".format(repr(e)))

    def ExportModelImage(self, request, context):
        try:
            model.buildImageBundleFromDistroBundle(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to export model image: {}".format(repr(e)))

    def ImportModelDistro(self, request, context):
        try:
            model.unpackImageBundleAndImportWithDistro(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to import model distribution: {}".format(repr(e)))
