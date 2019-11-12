from ..core import runtime
from ..core import backend
from ..interface import common_pb2 as c_pb2
from ..interface import backend_pb2 as be_pb2
from ..interface import backend_pb2_grpc as be_pb2_grpc

class Backend(be_pb2_grpc.BackendServicer):

    def ListSupportedType(self, request, context):
        return be_pb2.SupportedReply(
            support="Not implemented"
        )

    def ListRunningBackends(self, request, context):
        be_list = []
        for key, _ in runtime.BEs.items():
            ret = backend.listBackend(key)
            be_list.append(be_pb2.RunningReply.Status(
                bid=key,
                model=ret['model'],
                status=ret['status'],
                msg=ret['msg'],
            ))
        return be_pb2.RunningReply(status=be_list)

    def InitializeBackend(self, request, context):
        ret = backend.createBackend({'btype': request.btype})
        return c_pb2.ResultReply(
            code=0,
            msg=str(ret),
        )

    def ListBackend(self, request, context):
        ret = backend.listBackend(request.bid)
        return be_pb2.RunningReply.Status(
            bid=request.bid,
            model=ret['model'],
            status=ret['status'],
            msg=ret['msg'],
        )

    def TerminateBackend(self, request, context):
        ret = backend.terminateBackend(request.bid)
        return c_pb2.ResultReply(
            code=ret['code'],
            msg=ret['msg']
        )

