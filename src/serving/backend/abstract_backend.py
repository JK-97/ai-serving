"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import sys
import logging
import importlib
import threading
import rapidjson as json
from enum import Enum, unique
from serving import utils


@unique
class Type(Enum):
    TfPy    = 'tensorflow'
    TfSrv   = 'tensorflow-serving'
    Torch   = 'pytorch'


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
        self.switch_error_message = ""

        self.classes = []
        self.predp = None
        self.postdp = None

        self.collection_path = collection
        self.configurations = configurations

    def switchModel(self, switch_data):
        th_switch = threading.Thread(target=self._switchModel, args=switch_data)
        th_switch.start()

    def inference(self, infer_data):
        result = {
            'status': "failed"
            'result': None
            'message': ""
        }
        try:
           pre_p = self._preDataProcessing(infer_data)
           predict = self._inference(pre_p)
           post_p = self.postDataProcessing(pre_p, predict, self.classes)
           result['result'] = post_p
           result['status'] = "success"
           return result
        except Exception as e:
            logging.error(e)
            logging.exception(e)
            result['status'] = "failed"
            result['message'] = "infer error: {}".format(e)
            return result

    def reportStatus(self):
       return {
           'model'  : self.current_model_name,
           'status' : self.switch_status.value,
           'error'  : self.switch_error_message,
       }

    def _switchModel(self, switch_data):
        try:
            declared_model_name = utils.getKey('model', dicts=switch_data)
            if declared_model_name == self.current_model_name:
                return True
            # cleaning
            if self.model_object != None:
                self.switch_status = Status.Cleaning
                self.model_object = None
            # loading
            self.switch_status = Status.Loading
            self.current_model_name = declared_model_name
            self.switch_error_message = ""
            declared_model_path = os.path.join(self.collection_path, declared_model_name)
            if not os.path.isdir(declared_model_path):
                raise RuntimeError("model does not exist: {}".format(declared_model_path))
            self.current_model_path = declared_model_path
            # loading classes info
            with open(os.path.join(self.current_model_path, 'class.txt')) as class_file:
                self.classes = eval(class_file.read().encode('utf-8'))
            # loading model object
            loaded_param = self._loadModel(switch_data)
            assert(self.model_object != None)
            if not loaded_param:
                self._loadParameter(switch_data)
            # preheat
            preheat = True
            logging.warning("force to preheat")
            if preheat == True:
                self.switch_status = Status.Preheating
                self.runSingleSession(utils.getKey('preheat', dicts=self.configurations))
            # set status
            self.switch_status = Status.Loaded
            return True
        except Exception as e:
            logging.error(e)
            logging.exception(e)
            self.switch_status = Status.Failed
            self.switch_error_messasge = "switch error: {}".format(e)
            return False

    # this function is expected a bool return value
    @abc.abstractmethod
    def _loadModel(self, load_data):
        logging.critical("AbstractBackend::_loadModel called")
        exit(-1)
        #return False

    @abc.abstractmethod
    def _loadParameter(self, load_data):
        logging.critical("AbstractBackend::_loadParameter called")
        exit(-1)

    @abc.abstractmethod
    def _inference(self, infer_data):
        logging.critical("AbstractBackend::_inference called")
        exit(-1)
   
    @utils.profiler_timer("AbstractBackend::preDataProcessing")
    def _preDataProcessing(self, path):
        try:
            if self.predp:
                return self.predp.pre_dataprocess(path)
            else:
               sys.path.append(self.current_model_path)
               self.predp = importlib.import_module('pre_dataprocess')
               return self.predp.pre_dataprocess(path)
        except Exception as e:
            logging.critical(e)
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
            logging.critical(e)
            logging.exception(e)
            raise e
 
    @utils.profiler_timer("AbstractBackend::_dumpsData")
    def _dumpsData(self, data):
        return json.dumps(data)

    @utils.profiler_timer("AbstractBackend::_loadsData")
    def _loadsData(self, data):
        return json.loads(data)

