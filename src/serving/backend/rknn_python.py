"""
  AIServing RKNN Backend

  Contact: 1179160244@qq.com
"""

import os
import json
from rknn.api import RKNN
from serving import utils
from serving.backend import abstract_backend as ab


class RKNNPyBackend(ab.AbstractBackend):
    def __del__(self):
        if self.model_object is not None:
            self.model_object.release()

    @utils.profiler_timer("RKNNPyBackend::_loadModel")
    def _loadModel(self, load_configs):
        self.model_object = RKNN()
        path = os.path.join(self.model_path, self.model_filename)
        self.model_object.load_rknn(path)
        ret = self.model_object.init_runtime()
        if ret != 0:
            raise RuntimeError(
                "Failed to initialize RKNN runtime enrvironment")
        return True

    @utils.profiler_timer("RKNNPyBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("RKNNPyBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize != 1:
            raise Exception("batchsize unequal one")
        id_lists, feed_lists, passby_lists = self.__buildBatch(
            input_queue, batchsize)
        if feed_lists is None:
            return id_lists, [None] * batchsize
        infer_lists = self.__inferBatch(feed_lists)
        result_lists = self.__processBatch(
            passby_lists, infer_lists, batchsize)
        return id_lists, result_lists

    @utils.profiler_timer("RKNNPyBackend::__buildBatch")
    def __buildBatch(self, in_queue, batchsize):
        predp_data = [None] * batchsize
        id_lists = [None] * batchsize
        feed_lists = [None] * batchsize
        passby_lists = [None] * batchsize
        index = batchsize - 1
        package = self.configs['queue.in'].blpop(in_queue)
        if package is not None:
            predp_frame = json.loads(package[-1].decode("utf-8"))
            id_lists[index] = predp_frame['uuid']
            predp_data[index] = self.predp.pre_dataprocess(predp_frame)
            if predp_data[index] is not None:
                feed_lists[index] = predp_data[index]['feed_list']
                passby_lists[index] = predp_data[index]['passby']
        return id_lists, feed_lists[index], passby_lists[index]

    @utils.profiler_timer("RKNNPyBackend::__inferBatch")
    def __inferBatch(self, feed_lists):
        return self.model_object.inference(feed_lists)

    @utils.profiler_timer("RKNNPyBackend::__processBatch")
    def __processBatch(self, passby_lists, infer_lists, batchsize):
        labels = self.model_configs.get('labels')
        threshold = [float(i) for i in self.model_configs.get('threshold')]
        mapping = self.model_configs.get('mapping')
        result_lists = [None] * batchsize
        post_frame = {
            'infers': infer_lists,
            'labels': labels,
            'passby': passby_lists,
            'threshold': threshold,
            'mapping': mapping,
        }
        result_lists[0] = self.postdp.post_dataprocess(post_frame)
        return result_lists
