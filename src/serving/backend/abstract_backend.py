"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import sys
import logging
import importlib
import rapidjson as json
from enum import Enum, unique
from serving import utils


@unique
class Type(Enum):
    TfPy    = 'tensorflow'
    TfSrv   = 'tensorflow-serving'
    Torch   = 'pytorch'
    RknnPy  = 'rknn'


@unique
class Status(Enum):
    Unloaded   = 'unloaded'
    Cleaning   = 'cleaning'
    Loading    = 'loading'
    Preheating = 'preheating'
    Loaded     = 'loaded'
    Failed     = 'failed'


def BackendValidator(value):
    try:
        return Type(value), ""
    except ValueError as e:
        return None, "unsupported backend"


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, collection, configurations = {}):
        self.model_object = None
        self.current_model_name = ""
        self.current_model_path = ""
        self.switch_status = Status.Unloaded
        self.switch_error = None

        self.classes = []
        self.predp = None
        self.postdp = None

        self.collection_path = collection
        self.configurations = configurations

    @utils.threads
    def loadModel(self, switch_configs):
        try:
            declared_model_name = utils.getKey('model', dicts=switch_configs)
            if (declared_model_name == self.current_model_name
              and self.switch_status == Status.Loaded):
                return None
            # cleaning
            if self.model_object != None:
                self.switch_status = Status.Cleaning
                self.model_object = None
            # loading
            self.switch_status = Status.Loading
            self.current_model_name = declared_model_name
            self.switch_error = None
            declared_model_path = os.path.join(self.collection_path, declared_model_name)
            if not os.path.isdir(declared_model_path):
                raise RuntimeError("model does not exist: {}".format(declared_model_path))
            self.current_model_path = declared_model_path
            # loading model object
            is_loaded_param = self._loadModel(switch_configs)
            assert self.model_object is not None
            if not is_loaded_param:
                self._loadParameter(switch_configs)
            # preheat
            preheat = True
            logging.warning("force to preheat")
            if preheat == True:
                self.switch_status = Status.Preheating
                filepath = utils.getKey('preheat', dicts=self.configurations)
                if self.inferData({'path':filepath})['status'] == "failed":
                    logging.warning("preheat failed")
            # set status
            self.switch_status = Status.Loaded
        except Exception as e:
            self.switch_status = Status.Cleaning
            self.model_object = None
            logging.exception(e)
            self.switch_status = Status.Failed
            self.switch_error = e

    def inferData(self, infer_data):
        inference = {
            'status': "failed",
            'result': None,
            'message': "",
        }
        try:
            if (self.switch_status != Status.Loaded
              and self.switch_status != Status.Preheating):
                raise RuntimeError("model status is unhealthy")
            pre_p = self._preDataProcessing(infer_data)
            predict = self._inferData(pre_p)
            post_p = self._postDataProcessing(pre_p, predict, self.classes)
            inference['result'] = post_p
            inference['status'] = "success"
            return inference
        except Exception as e:
            logging.exception(e)
            inference['status'] = "failed"
            inference['message'] = "infer error: {}".format(e)
            return inference

    def reportStatus(self):
        return {
            'model'  : self.current_model_name,
            'status' : self.switch_status.value,
            'error'  : "switch error: {}".format(self.switch_error),
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
   
    @utils.profiler_timer("AbstractBackend::preDataProcessing")
    def _preDataProcessing(self, infer_data):
        try:
            if self.predp:
                return self.predp.pre_dataprocess(infer_data)
            else:
               sys.path.append(self.current_model_path)
               self.predp = importlib.import_module('pre_dataprocess')
               return self.predp.pre_dataprocess(infer_data)
        except Exception as e:
            logging.exception(e)
            raise e

    @utils.profiler_timer("AbstractBackend::postDataProcessing")
    def _postDataProcessing(self, pre_p, predict, classes):
        try:
            if self.postdp:
                return self.postdp.post_dataprocess(pre_p, predict, classes)
            else:
               sys.path.append(self.current_model_path)
               self.postdp = importlib.import_module('post_dataprocess')
               return self.postdp.post_dataprocess(pre_p, predict, classes)
        except Exception as e:
            logging.exception(e)
            raise e
 
    @utils.profiler_timer("AbstractBackend::_dumpsData")
    def _dumpsData(self, data):
        return json.dumps(data)

    @utils.profiler_timer("AbstractBackend::_loadsData")
    def _loadsData(self, data):
        return json.loads(data)

