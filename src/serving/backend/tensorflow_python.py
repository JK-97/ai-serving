"""
  JXServing Tensorflow Python Backend

  Contact: songdanyang@jiangxing.ai
"""

import os
import json
import logging
import tensorflow as tf
from enum import Enum, unique
from serving import utils
from serving.backend import abstract_backend as ab
import numpy as np


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
    def __init__(self, configurations = {}):
        super().__init__(configurations)
        self.input_tensor_vec = []
        self.output_tensor_vec = []

    @utils.profiler_timer("TfPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
            # load tensorflow session
            model_type = utils.getKey(
                'm',
                {'m': str.split(self.model_configs['impl'], ".")[1]},
                v=ModelTypeValidator)
            # model_type = utils.getKey('mode', dicts=load_configs, v=ModelTypeValidator)
            if model_type == ModelType.Frozen:
                self.__loadFrozenModel()
            if model_type == ModelType.Unfrozen:
                self.__loadUnfrozenModel()
            # set input/output tensor
            tensor_map = json.loads(self.model_configs['modelext']).get('tensors')
            self.input_tensor_vec = []
            for it in tensor_map['input']:
                self.input_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            self.output_tensor_vec = []
            for it in tensor_map['output']:
                self.output_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))

            return True
        except Exception as e:
            self.output_tensor_vec = []
            self.input_tensor_vec = []
            raise e

    @utils.profiler_timer("TfPyBackend::__loadFrozenModel")
    def __loadFrozenModel(self):
        with tf.Graph().as_default():
            graph_def = tf.GraphDef()
            path = os.path.join(self.model_path, self.model_filename)
            with open(path, "rb") as model_file:
                graph_def.ParseFromString(model_file.read())
                tf.import_graph_def(graph_def, name="")
            config = tf.ConfigProto()
            # TODO(arth): FGs -> GPU config
            # config.gpu_options.allow_growth=True
            # config.gpu_options.per_process_gpu_memory_fraction = (1 - 0.01) / self.configs['inferproc_num']
            self.model_object = tf.Session(config=config)
            self.model_object.run(tf.global_variables_initializer())

    @utils.profiler_timer("TfPyBackend::__loadUnfrozenModel")
    def __loadUnfrozenModel(self):
        os.rename(os.path.join(self.model_path, self.model_filename),
                  os.path.join(self.model_path, "saved_model.pb"))
        config = tf.ConfigProto()
        # TODO(arth): FGs -> GPU config
        # config.gpu_options.allow_growth=True
        # config.gpu_options.per_process_gpu_memory_fraction = (1 - 0.01) / self.configs['inferproc_num']
        self.model_object = tf.Session(graph=tf.Graph(),config=config)
        tf.saved_model.loader.load(
            self.model_object,
            [tf.saved_model.tag_constants.SERVING],
            self.configs['model_path'])
        os.rename(os.path.join(self.model_path, "saved_model.pb"),
                  os.path.join(self.model_path, self.model_filename))

    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfPyBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize < 1:
            raise Exception("batchsize smaller than one")
        id_lists, feed_lists, passby_lists = self.__buildBatch(input_queue, batchsize)
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(infer_lists, passby_lists, batchsize)
        return id_lists, result_lists

    @utils.profiler_timer("TfPyBackend::__buildBatch")
    def __buildBatch(self, in_queue, batchsize):
        predp_data = [None] * batchsize
        id_lists = [None] * batchsize
        feed_lists =np.array([[None] * batchsize] * len(self.input_tensor_vec))
        passby_lists = [None] * batchsize
        input_type = json.loads(self.model_configs['modelext']).get('tensors')['input_type']


        for i in range(batchsize):
            package = self.configs['queue.in'].blpop(in_queue)
            if package is not None:
                # blopop returns: (b'key', b'{...}')
                predp_frame = json.loads(package[-1].decode("utf-8"))
                id_lists[i] = predp_frame['uuid']
                predp_data[i] = self.predp.pre_dataprocess(predp_frame)
                passby_lists[i] = predp_data[i]['passby']

                for j in range(len(self.input_tensor_vec)):
                    feed_lists[j][i] = np.squeeze(predp_data[i]['feed_list'][j])

        feed_lists_return = []
        for i in range(len(self.input_tensor_vec)):
            if int(input_type[i]) == 1:
                feed_lists_return.append(np.array(feed_lists[i].tolist()))
            if int(input_type[i]) == 0:
                feed_lists_return.append(feed_lists[i][0])

        return id_lists, feed_lists_return, passby_lists

    @utils.profiler_timer("TfPyBackend::__inferBatch")
    def __inferBatch(self, feed_list):
        feeding = {}
        for index, t in enumerate(self.input_tensor_vec):
            feeding[t] = feed_list[index]
        return self.model_object.run(self.output_tensor_vec, feed_dict=feeding)


    @utils.profiler_timer("TfPyBackend::__processBatch")
    def __processBatch(self, infer_lists, passby_lists, batchsize):
        labels = self.model_configs.get('labels')
        threshold = [float(i) for i in self.model_configs.get('threshold')]
        mapping = self.model_configs.get('mapping')
        result_lists = [None] * batchsize

        for i in range(batchsize):
            post_frame = {
                'infers': [infer_lists[k][i] for k in range(len(infer_lists))],
                'labels': labels,
                'threshold': threshold,
                'mapping': mapping,
                'passby': passby_lists[i]
            }
            result_lists[i] = self.postdp.post_dataprocess(post_frame)

        return result_lists

