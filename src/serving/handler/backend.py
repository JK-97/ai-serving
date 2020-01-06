import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core import error_code, error_reply
from ..core import backend
from ..interface import backend_pb2 as be_pb2
from ..interface import backend_pb2_grpc as be_pb2_grpc
from ..interface import common_pb2 as c_pb2


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
            ret = backend.initializeBackend(MessageToDict(request), passby_model=None)
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.CreateAndLoadModelError):
                return error_reply.error_msg(c_pb2, error_code.CreateAndLoadModelError, exception=e)
            return error_reply.error_msg(c_pb2, error_code.RunTimeException,
                                         msg="failed to initialize backend: {}".format(repr(e)))

    def ListBackend(self, request, context):
        try:
            ret = backend.listOneBackend(MessageToDict(request))
            return ParseDict(ret, be_pb2.BackendStatus())
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.ListOneBackendError):
                return error_reply.error_msg(c_pb2, error_code.ListOneBackendError, exception=e)
            return be_pb2.BackendStatus()

    def ReloadModelOnBackend(self, request, context):
        try:
            ret = backend.reloadModelOnBackend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.ReloadModelOnBackendError):
                return error_reply.error_msg(c_pb2, error_code.ReloadModelOnBackendError, exception=e)
            return error_reply.error_msg(c_pb2, error_code.RunTimeException,
                                         msg="failed to (re)load model on backend: {}".format(repr(e)))

    def TerminateBackend(self, request, context):
        try:
            backend.terminateBackend(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.TerminateBackendError):
                return error_reply.error_msg(c_pb2, error_code.TerminateBackendError, exception=e)
            return error_reply.error_msg(c_pb2, error_code.RunTimeException,
                                         msg="failed to terminate backend: {}".format(repr(e)))

    def CreateAndLoadModel(self, request, context):
        try:
            ret = backend.createAndLoadModel(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.ExistBackendError):
                return error_reply.error_msg(c_pb2, error_code.ExistBackendError, exception=e)
            return error_reply.error_msg(c_pb2, error_code.RunTimeException, msg=repr(e))

    def CreateAndLoadModelV2(self, request, context):
        try:
            ret = backend.createAndLoadModelV2(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except Exception as e:
            logging.exception(e)
            if isinstance(e, error_code.ExistBackendError):
                return error_reply.error_msg(c_pb2, error_code.ExistBackendError, exception=e)
            return error_reply.error_msg(c_pb2, error_code.RunTimeException, msg=repr(e))
