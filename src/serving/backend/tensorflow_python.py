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
            model_type = utils.getKey('mode', dicts=load_configs, v=ModelTypeValidator)
            if model_type == ModelType.Frozen:
                self._loadFrozenModel()
            if model_type == ModelType.Unfrozen:
                self._loadUnfrozenModel()

            # set input/output tensor
            tensor_map = self.configs['model_configs'].get('tensors')
            self.input_tensor_vec = []
            for it in tensor_map['input']:
                self.input_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))
            self.output_tensor_vec = []
            for it in tensor_map['output']:
                self.output_tensor_vec.append(self.model_object.graph.get_tensor_by_name(it))

            return True
        except Exception as e:
            #self.tensor_map = {}
            self.output_tensor_vec = []
            self.input_tensor_vec = []
            raise e

    @utils.profiler_timer("TfPyBackend::_loadFrozenModel")
    def _loadFrozenModel(self):
        with tf.Graph().as_default():
            graph_def = tf.GraphDef()
            path = os.path.join(self.configs['model_path'], "saved_model.pb")
            with open(path, "rb") as model_file:
                graph_def.ParseFromString(model_file.read())
                tf.import_graph_def(graph_def, name="")
            config = tf.ConfigProto()
            config.gpu_options.allow_growth=True
            config.gpu_options.per_process_gpu_memory_fraction = (1 - 0.01) / self.configs['inferproc_num']
            self.model_object = tf.Session(config=config)
            self.model_object.run(tf.global_variables_initializer())

    @utils.profiler_timer("TfPyBackend::_loadUnfrozenModel")
    def _loadUnfrozenModel(self):
        config = tf.ConfigProto()
        config.gpu_options.allow_growth=True
        config.gpu_options.per_process_gpu_memory_fraction = (1 - 0.01) / self.configs['inferproc_num']
        self.model_object = tf.Session(graph=tf.Graph(),config=config)
        tf.saved_model.loader.load(
            self.model_object,
            [tf.saved_model.tag_constants.SERVING],
            self.configs['model_path'])

    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfPyBackend::_inferData")
    def _inferData(self, pre_p):
        feed_list = utils.getKey('feed_list', dicts=pre_p)
        feeding = {}
        for index, t in enumerate(self.input_tensor_vec):
            feeding[t] = feed_list[index]
        return self.model_object.run(self.output_tensor_vec, feed_dict=feeding)

    @utils.profiler_timer("TfPyBackend::_inferBatch")
    def _createBatch(self, in_queue):
        ids_for_batch = []
        pres_for_batch = []

        for i in range(self.configs['batchsize']):

            package_for_raw_data = self.rPipe_for_raw_data.blpop(in_queue)

            if package_for_raw_data != None:
                package_for_predp = self.loadData(package_for_raw_data[-1])
                data_for_infer = {'id': package_for_predp['uuid'],
                                  'pre': self.predp.pre_dataprocess(package_for_predp)}

            ids_for_batch.append(data_for_infer['id'])
            pres_for_batch.append(data_for_infer['pre'])

        shapes_for_batch = []
        feed_lists = []
        for i in range(len(pres_for_batch)):
            shapes_for_batch.append(pres_for_batch[i]['shape'])
            feed_lists.append(np.squeeze(pres_for_batch[i]['feed_list'][0]))
        feed_lists = np.array(feed_lists)
        feed_lists = [feed_lists, False]

        dic_for_inferData = {}
        dic_for_inferData['shape'] = shapes_for_batch
        dic_for_inferData['feed_list'] = feed_lists

        return dic_for_inferData, ids_for_batch, pres_for_batch

    @utils.profiler_timer("TfPyBackend::_postPreocessBatch")
    def _postProcessBatch(self, ids_for_batch, pres_for_batch, result_for_inferDate):
        ids_for_postdp = []
        result_for_postdp = []
        labels = self.configs['model_configs'].get('labels')

        for i in range(self.configs['batchsize']):
            temp_package = {}
            temp_package['id'] = ids_for_batch[i]
            temp_package['pre'] = pres_for_batch[i]
            temp_package['pred'] = [result_for_inferDate[0][i],
                                    result_for_inferDate[1][i],
                                    result_for_inferDate[2][i]]
            temp_package['class'] = labels

            ids_for_postdp.append(temp_package['id'])
            result_for_postdp.append(self.postdp.post_dataprocess(temp_package))

        dic_for_postdp = {}
        dic_for_postdp = {'id': ids_for_postdp, 'result': result_for_postdp}

        return dic_for_postdp
