import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving import utils
from serving.core import runtime
from ..core import backend

from serving.backend import supported_backend as sb
from settings import settings
from ..interface import common_pb2 as c_pb2
from serving.interface import model_pb2 as m_pb2
from ..interface import backend_pb2 as be_pb2
from ..interface import backend_pb2_grpc as be_pb2_grpc

class Backend(be_pb2_grpc.BackendServicer):
    def ListSupportedType(self, request, context):
        return be_pb2.SupportedReply(support="not implemented")

    def ListRunningBackends(self, request, context):
        try:
            ret = backend.listAllBackends()
            return ParseDict(ret, be_pb2.BackendList())
        except Exception as e:
            logging.exception(e)
            return be_pb2.BackendList()

    def InitializeBackend(self, request, context):
        try:
            ret = backend.initializeBackend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to initialize backend: {}".format(repr(e)))

    def ListBackend(self, request, context):
        try:
            ret = backend.listOneBackend(MessageToDict(request))
            return ParseDict(ret, be_pb2.BackendStatus())
        except Exception as e:
            logging.exception(e)
            return be_pb2.BackendStatus()

    def ReloadModelOnBackend(self, request, context):
        try:
            ret = backend.reloadModelOnBackend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to (re)load model on backend: {}".format(repr(e)))

    def TerminateBackend(self, request, context):
        try:
            backend.terminateBackend(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to terminate backend: {}".format(repr(e)))

    def CreateAndLoadModel(self, request, context):
        try:
            ret = backend.createAndLoadModel(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            return c_pb2.ResultReply(
                code=1,
                msg="failed to create and load model on backend: {}".format(repr(e)))
