"""
  JXServing Tensorflow Python Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import logging
import tensorflow as tf
from enum import Enum, unique
from serving import utils
from serving.backend import abstract_backend as ab


@unique
class ModelType(Enum):
    Frozen   = 'frozen'
    Unfrozen = 'unfrozen'


def ModelTypeValidator(value):
    try:
        return ModelType(value), ""
    except ValueError as e:
        return None, "unsupported model type"


class TfPyBackend(ab.AbstractBackend):
    def __init__(self, collection, configurations = {}):
        super().__init__(collection, configurations)
        self.tensor_map = {}
        self.input_tensor_vec = []
        self.output_tensor_vec = []

    @utils.profiler_timer("TfPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
            # load classes info
            with open(os.path.join(self.current_model_path, 'class.txt')) as class_file:
                self.classes = eval(class_file.read().encode('utf-8'))
            # load graph configurations
            with open(os.path.join(self.current_model_path, 'tensor.json')) as tensor_file:
                self.tensor_map = self._loadsData(tensor_file.read())
            # load tensorflow session
            model_type = utils.getKey('mode', dicts=load_configs, v=ModelTypeValidator)
            if model_type == ModelType.Frozen:
                self._loadFrozenModel()
            if model_type == ModelType.Unfrozen:
                self._loadUnfrozenModel()
            # set input/output tensor
            self.output_tensor_vec = []
            for it in self.tensor_map['output']:
                self.output_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            self.input_tensor_vec = []
            for it in self.tensor_map['input']:
                self.input_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            return True
        except Exception as e:
            self.tensor_map = {}
            self.output_tensor_vec = []
            self.input_tensor_vec = []
            raise e

    @utils.profiler_timer("TfPyBackend::_loadFrozenModel")
    def _loadFrozenModel(self):
        with tf.Graph().as_default():
            graph_def = tf.GraphDef()
            path = os.path.join(self.current_model_path, "saved_model.pb")
            with open(path, "rb") as model_file:
                graph_def.ParseFromString(model_file.read())
                tf.import_graph_def(graph_def, name="")
            self.model_object = tf.Session()
            self.model_object.run(tf.global_variables_initializer())

    @utils.profiler_timer("TfPyBackend::_loadUnfrozenModel")
    def _loadUnfrozenModel(self):
        self.model_object = tf.Session(graph=tf.Graph())
        tf.saved_model.loader.load(
            self.model_object,
            [tf.saved_model.tag_constants.SERVING],
            self.current_model_path)

    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfPyBackend::_inferData")
    def _inferData(self, pre_p):
        feed_list = utils.getKey('feed_list', dicts=pre_p)
        feeding = {}
        for index, t in enumerate(self.input_tensor_vec):
            feeding[t] = feed_list[index]
        return self.model_object.run(self.output_tensor_vec, feed_dict=feeding)

