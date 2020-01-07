import logging

from google.protobuf.json_format import MessageToDict, ParseDict

from serving.core.error_code import ExistBackendError, RunTimeException, CreateAndLoadModelError, ListOneBackendError, \
    ReloadModelOnBackendError, TerminateBackendError
from serving.core import   error_reply
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
        except CreateAndLoadModelError as e:
            return error_reply.error_msg(c_pb2, CreateAndLoadModelError, exception=e)
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException,
                                         msg="failed to initialize backend: {}".format(repr(e)))

    def ListBackend(self, request, context):
        try:
            ret = backend.listOneBackend(MessageToDict(request))
            return ParseDict(ret, be_pb2.BackendStatus())
        except ListOneBackendError as e:
            return error_reply.error_msg(c_pb2, ListOneBackendError, exception=e)
        except Exception as e:
            logging.exception(e)
            return be_pb2.BackendStatus()

    def ReloadModelOnBackend(self, request, context):
        try:
            ret = backend.reloadModelOnBackend(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except ReloadModelOnBackendError as e:
            return error_reply.error_msg(c_pb2, ReloadModelOnBackendError, exception=e)
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException,
                                         msg="failed to (re)load model on backend: {}".format(repr(e)))

    def TerminateBackend(self, request, context):
        try:
            backend.terminateBackend(MessageToDict(request))
            return c_pb2.ResultReply(code=0, msg="")
        except TerminateBackendError as e:
            return error_reply.error_msg(c_pb2, TerminateBackendError, exception=e)
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException,
                                         msg="failed to terminate backend: {}".format(repr(e)))

    def CreateAndLoadModel(self, request, context):
        try:
            ret = backend.createAndLoadModel(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except ExistBackendError as e:
            return error_reply.error_msg(c_pb2, ExistBackendError, exception=e)
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException, msg=repr(e))

    def CreateAndLoadModelV2(self, request, context):
        try:
            ret = backend.createAndLoadModelV2(MessageToDict(request))
            return ParseDict(ret, c_pb2.ResultReply())
        except ExistBackendError as e:
            return error_reply.error_msg(c_pb2, ExistBackendError, exception=e)
        except Exception as e:
            logging.exception(e)
            return error_reply.error_msg(c_pb2, RunTimeException, msg=repr(e))
