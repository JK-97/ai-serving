"""
  JXServing Tensorflow Python Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import sys
import rapidjson as json
import time
import logging
import importlib
import threading
import tensorflow as tf
from tornado.options import options
from enum import Enum, unique
from serving import utils
from serving.backend import abstract_backend as ab
from settings import settings


@unique
class ModelType(Enum):
    Frozen   = 'frozen'
    Unfrozen = 'unfrozen'


def validModel(value):
    try:
        return ModelType(value), ""
    except ValueError as e:
        return None, "unsupported model type"


class TfPyBackend(ab.AbstractBackend):
    def __init__(self, collection, settings = {}):
        super().__init__(collection, settings)
        self.session = None
        self.tensor_map = {}
        self.input_tensor_vec = []
        self.output_tensor_vec = []

    @utils.profiler_timer("TfPyBackend::switchModel")
    def switchModel(switch_data):
        try:
            host = utils.getKeyFromDicts('model', dicts=switch_data)
            model_ty = utils.getKeyFromDicts('mode',
                                             dicts=switch_data,
                                             validator=validModel)
            preheat = True
            logging.warning("Force to PRE_HEAT on TfPyBackend::switchModel")

            actualSwitcher = None
            if model_ty == ModelType.Frozen:
                actualSwitcher = self._switchWithFrozenModel
            if model_ty == ModelType.Unfrozen:
                actualSwitcher = self._switchWithUnfrozenModel
            assert(actualModelSwitcher != None)

            th_load = threading.Thread(target=self.switchSessionWithModel,
                                       args=(model, actualModelSwitcher, preheat))
            th_load.start()
            return True
        except Exception as e:
            logging.error(e)
            logging.exception(e)
            self.switch_status = ab.Status.Failed
            self.switch_error_message = "switch error: {}".format(e)
            return False

    @utils.profiler_timer("TfPyBackend::_switchSessionWithModel")
    def _switchSessionWithModel(model, loader, preheat):
        try:
            if model == self.current_model_name:
                return True
            # cleaning, [attention] this is not thread safe
            if self.session != None:
                self.switch_status = ab.Status.Cleaning
                self.session = None

            self.current_model_name = model
            self.switch_error_message = ""
            # validating
            tmp_path = os.path.join(self.collection_path, model)
            if not os.path.isdir(tmp_path):
                raise RuntimeError("model does not exist: {}".format(tmp_path))
            # loading
            self.switch_status = ab.Status.Loading
            self.current_model_path = tmp_path
            # load model classes
            with open(os.path.join(self.current_model_path, 'class.txt')) as class_file: 
                self.classes = eval(class_file.read().encode('utf-8'))
            # load graph configurations
            with open(os.path.join(self.current_model_path, 'tensor.json')) as tensor_file:
                self.tensor_map = json.loads(tensor_file.read())
            # load graph
            loader(model)
            if self.session == None:
                raise RuntimeError("unknown error, tensorflow session == none")
            # set input/output tensor
            self.output_tenosr_vec = []
            for it in self.tensor_map['output']:
                self.output_tensor_vec.append(self.session.graph.get_tensor_by_name(it))
            self.input_tensor_vec = []
            for it in self.tensor_map['input']:
                self.input_tensor_vec.append(self.session.graph.get_tensor_by_name(it))
            # preheat neural network
            if preheat == True:
                self.switch_status = ab.Status.Preheating
                _, feed_list = preDataProcessing(self.settings['preheat_image_path'])
                feeding = {}
                for index, t in enumerate(self.input_tensor_vec):
                    feeding[t] = feed_list[index]
                self.session.run(self.output_tensor_vec, feed_dict=feeding)
            self.switch_status = ab.Status.Loaded
            return True
        except Exception as e:
            logging.error(e)
            logging.exception(e)
            self.session = None
            self.switch_status = ab.Status.Failed
            self.switch_error_message = "switch error: {}".format(e)
            self.tensor_map = {}
            self.output_tensor_vec = []
            self.input_tensor_vec = []
            return False

    @utils.profiler_timer("TfPyBackend::_switchSessionWithModel")
    def _switchWithFrozenModel(self, model):
        with tf.Graph().as_default():
            graph_def = tf.GraphDef()
            path = os.path.join(self.current_model_path, "saved_model.pb")
            with open(path, "rb") as model_file:
                graph_def.ParseFromString(model_file.read())
                tf.import_graph_def(graph_def, name="")

            self.session = tf.Session()
            self.session.run(tf.global_variables_initializer())

    @utils.profiler_timer("TfPyBackend::_switchSessionWithModel")
    def _switchWithUnfrozenModel(self, model):
        self.session = tf.Session(graph=tf.Graph())
        tf.saved_model.loader.load(
            self.session,
            [tf.saved_model.tag_constants.SERVING],
            self.current_model_path)


    @utils.profiler_timer("TfPyBackend::runSingleSession")
    def runSingleSession(self, filepath):
        try:
            original_image, feed_list = preDataProcessing(filepath)
            feeding = {}
            for index, t in enumerate(self.input_tensor_vec):
                feeding[t] = feed_list[index]
            #print(feeding)
            predict = self.session.run(grt.OUTPUT_TENSOR_VEC, feed_dict=feeding)
            return postDataProcessing(original_image, predict, grt.CLASSES_VEC)
        except Exception as e:
            logging.exception(e)
            logging.error("failed to run session: {}".format(e))
            return None



