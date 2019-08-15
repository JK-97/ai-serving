"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import abc
import logging
import rapidjson as json
from enum import Enum, unique
from serving import utils


@unique
class Type(Enum):
    TfPy    = 'tensorflow'
    TfSrv   = 'tensorflow-serving'


@unique
class Status(Enum):
    Unloaded   = 'unloaded'
    Cleaning   = 'cleaning'
    Loading    = 'loading'
    Preheating = 'preheating'
    Loaded     = 'loaded'
    Failed     = 'failed'


def validBackend(value):
    try:
        return Type(value), ""
    except ValueError as e:
        return None, "unsupported backend"


class AbstractBackend(metaclass=abc.ABCMeta):
    def __init__(self, collection, settings = {}):
        self.current_model_name = ""
        self.current_model_path = ""
        self.switch_status = Status.Unloaded
        self.switch_error_message = ""

        self.classes = []
        self.predp = None
        self.postdp = None

        self.collection_path = collection
        logging.warning("Didn't check collection is valid")
        self.settings = settings

    @abc.abstractmethod
    def switchModel(self, switch_data):
        logging.critical("AbstractBackend::switchModel called")
        exit(-1)

    @abc.abstractmethod
    def runSingleSession(self, filepath):
        logging.critical("AbstractBackend::runSingleSession called")
        exit(-1)

    @utils.profiler_timer("AbstractBackend::_dumpsData")
    def _dumpsData(self, data):
        return json.dumps(data)

    @utils.profiler_timer("AbstractBackend::_loadsData")
    def _loadsData(self, data):
        return json.loads(data)

    @utils.profiler_timer("AbstractBackend::preDataProcessing")
    def preDataProcessing(self, path):
        if self.predp:
            return self.predp.pre_dataprocess(path)
        else:
            try:
               sys.path.append(self.current_model_path)
               self.predp = importlib.import_module('pre_dataprocess')
               return self.predp.pre_dataprocess(path)
            except Exception as e:
               logging.critical(e)
               logging.exception(e)
               raise e

    @utils.profiler_timer("AbstractBackend::postDataProcessing")
    def postDataProcessing(self, original_image, prediction_dict, classes):
        if self.postdp:
            return self.postdp.pre_dataprocess(original_image,
                                               prediction_dict,
                                               classes)
        else:
            try:
               sys.path.append(self.current_model_path)
               self.postdp = importlib.import_module('post_dataprocess')
               return self.postdp.pre_dataprocess(original_image,
                                                  prediction_dict,
                                                  classes)
            except Exception as e:
               logging.critical(e)
               logging.exception(e)
               raise e

    def reportStatus(self):
        return {
            'model'  : self.current_model_name,
            'status' : self.switch_status.value,
            'error'  : self.switch_error_message,
        }

