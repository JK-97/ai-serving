from .interface import backend_pb2_grpc as backend
from .interface import connectivity_pb2_grpc as connectivity
from .interface import exchange_pb2_grpc as exchange
from .interface import inference_pb2_grpc as inference
#import interfaces.dataset_pb2_grpc as dataset
from .interface import model_pb2_grpc as model

from .handler import backend as hbe
from .handler import connectivity as hconn
from .handler import exchange as hexc
from .handler import inference as hinf
from .handler import model as hm

def register_response(server):
    backend.add_BackendServicer_to_server(hbe.Backend(), server)
    connectivity.add_ConnectivityServicer_to_server(hconn.Connectivity(), server)
    exchange.add_ExchangeServicer_to_server(hexc.Exchange(), server)
    inference.add_InferenceServicer_to_server(hinf.Inference(), server)
    model.add_ModelServicer_to_server(hm.Model(), server)
