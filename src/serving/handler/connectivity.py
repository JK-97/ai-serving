import psutil

from ..interface import connectivity_pb2 as conn_pb2
from ..interface import connectivity_pb2_grpc as conn_pb2_grpc

class Connectivity(conn_pb2_grpc.ConnectivityServicer):

    def Ping(self, request, context):
        return conn_pb2.PingReply(
            version="1.0"\
        )

    def ListNodeResources(self, request, context):
        gpu_mem = ""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_mem = meminfo.used
        except Exception:
            gpu_mem = "N/A"

        return conn_pb2.ResourcesReply(
            cpu=str(psutil.cpu_percent(interval=1)),
            mem=str(psutil.virtual_memory().percent),
            gpu=str(gpu_mem),
            dsk=str(psutil.disk_usage('/')[3]),
        )

