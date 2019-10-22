"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import abc
import importlib
import logging
import os
import sys
from enum import Enum, unique
from multiprocessing import Value

import rapidjson as json
import redis

from settings import settings
from serving import utils
from serving.core import queue as q


@unique
class Type(Enum):
    TfPy = 'tensorflow'
    TfLite = 'tensorflow-lite'
    TfSrv = 'tensorflow-serving'
    Torch = 'pytorch'
    RknnPy = 'rknn'
    MxNet = 'mxNet'


@unique
class Status(Enum):
    Unloaded = 0
    Failed = 1
    Cleaning = 2
    Loading = 3
    Preheating = 4
    Running = 5


def BackendValidator(value):
    try:
        return Type(value), ""
    except ValueError as e:
        return None, "unsupported backend"


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, collection, configurations={}):
        self.model_object = None
        self.current_model_name = ""
        self.current_model_path = ""

        self.status = {}
        self.classes = []
        self.predp = None
        self.postdp = None

        self.collection_path = collection
        self.configurations = configurations

        self.multiple_mode = True
        self.infer_threads_num = 1

        rHost = utils.getKey('redis.host', self.configurations)
        rPort = utils.getKey('redis.port', self.configurations)
        self.rPipe = redis.Redis(host=rHost, port=rPort)

    def initBackend(self, switch_configs):
        try:
            decl_model_name = utils.getKey('mxNet', dicts=switch_configs)
            self.current_model_name = decl_model_name
            decl_model_path = os.path.join(self.collection_path, self.current_model_name)
            if not os.path.isdir(decl_model_path):
                raise RuntimeError("mxNet does not exist: {}".format(decl_model_path))
            self.current_model_path = decl_model_path

            if self.predp is None:
                sys.path.append(self.current_model_path)
                self.predp = importlib.import_module('pre_dataprocess')

            if self.postdp is None:
                sys.path.append(self.current_model_path)
                self.postdp = importlib.import_module('post_dataprocess')

            # start process
            self.preprocessor(q.input_queue, q.predp_queue, q.exit_flag)
            for i in range(0, self.infer_threads_num):
                self.status[i] = Value('B', Status.Unloaded.value)
                self.predictor(switch_configs, q.predp_queue, q.predict_queue, self.status[i], q.exit_flag)
            self.postprocessor(q.predict_queue, q.output_queue, q.exit_flag)
            self.exporter(q.output_queue, q.exit_flag)
        except Exception as e:
            logging.exception(e)

    def importer(self, infer_data):
        q.input_queue.put(infer_data)

    @utils.process
    def preprocessor(self, in_queue, out_queue, exit_flag):
        try:
            while True:
                if exit_flag.value == 10:
                    break
                """
                if in_queue.empty():
                    continue
                else:
                    package = in_queue.get()
                """
                package = in_queue.get()

                ret = {'id': package['uuid'],
                       'pre': self.predp.pre_dataprocess(package)}

                """
                if out_queue.full():
                    continue
                else:
                    out_queue.put(ret)
                """
                out_queue.put(ret)
        except Exception as e:
            logging.exception(e)

    @utils.process
    def predictor(self, switch_configs, in_queue, out_queue, load_status, exit_flag):
        try:
            # loading mxNet object
            load_status.value = Status.Loading.value
            is_loaded_param = self._loadModel(switch_configs)
            assert self.model_object is not None
            if not is_loaded_param:
                self._loadParameter(switch_configs)
            # preheat
            preheat = True
            backend_type = utils.getKey('backend', dicts=settings, env_key='JXSRV_BACKEND', v=BackendValidator)
            if preheat and backend_type != Type.MxNet:
                load_status.value = Status.Preheating.value
                filepath = self.configurations.get('preheat')
                self.importer({'uuid': "preheat", 'path': filepath})
            load_status.value = Status.Running.value
            self.predictor_core(in_queue, out_queue, exit_flag)
        except Exception as e:
            logging.exception(e)
            load_status.value = Status.Cleaning.value
            self.model_object = None
            load_status.value = Status.Failed.value

    def predictor_core(self, in_queue, out_queue, exit_flag):
        try:
            while True:
                if exit_flag.value == 10:
                    break
                """
                if in_queue.empty():
                    continue
                else:
                    package = in_queue.get()
                """
                package = in_queue.get()

                package['pred'] = self._inferData(package)
                package['class'] = self.classes
                ret = package
                if package.get('id') == "preheat":
                    logging.debug("skip preheat image")
                    continue

                """
                if out_queue.full():
                    continue
                else:
                    out_queue.put(ret)
                """
                out_queue.put(ret)
        except Exception as e:
            logging.exception(e)

    @utils.process
    def postprocessor(self, in_queue, out_queue, exit_flag):
        try:
            while True:

                print("exit_flag value::", exit_flag.value)

                if exit_flag.value == 10:
                    break
                """
                if in_queue.empty():
                    continue
                else:
                    package = in_queue.get()
                """
                package = in_queue.get()
                ret = {'id': package['id'], 'result': self.postdp.post_dataprocess(package['pred'])}
                """
                if out_queue.full():
                    continue
                else:
                    out_queue.put(ret)
                """
                out_queue.put(ret)
        except Exception as e:
            logging.exception(e)

    @utils.process
    def exporter(self, o_queue, exit_flag):
        try:
            while True:
                package = o_queue.get()
                self.rPipe.set(package.get('id'), self._dumpsData(package))
        except Exception as e:
            logging.exception(e)

    def reportStatus(self):
        status_vector = {}
        for i in range(0, self.infer_threads_num):
            status_vector[i] = self.status[i].value
        return {
            'mxNet': self.current_model_name,
            'status': status_vector,
            # 'error'  : "switch error: {}".format(self.switch_error),
        }

    # this function is expected a bool return value
    @abc.abstractmethod
    def _loadModel(self, load_configs):
        logging.critical("AbstractBackend::_loadModel called")
        exit(-1)

    @abc.abstractmethod
    def _loadParameter(self, load_configs):
        logging.critical("AbstractBackend::_loadParameter called")
        exit(-1)

    @abc.abstractmethod
    def _inferData(self, infer_data):
        logging.critical("AbstractBackend::_inference called")
        exit(-1)

    @utils.profiler_timer("AbstractBackend::_dumpsData")
    def _dumpsData(self, data):
        return json.dumps(data)

    @utils.profiler_timer("AbstractBackend::_loadsData")
    def _loadsData(self, data):
        return json.loads(data)
