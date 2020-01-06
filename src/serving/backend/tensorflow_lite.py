import os
import json
import tensorflow as tf
from serving import utils
from serving.backend import abstract_backend as ab

class TfLiteBackend(ab.AbstractBackend):
    def __init__(self, configurations = {}):
        super().__init__(configurations)

    @utils.profiler_timer("TfLiteBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
            # load model pb
            self.model_object = tf.lite.Interpreter(model_path=os.path.join(self.model_path, self.model_filename))
            self.model_object.allocate_tensors()
            self.input_details = self.model_object.get_input_details()
            self.output_details = self.model_object.get_output_details()
            return True
        except Exception as e:
            raise e

    @utils.profiler_timer("TfLiteBackend::_loadParameter")
    def _loadParameter(self, load_configs):
        pass

    @utils.profiler_timer("TfLiteBackend::_inferData")
    def _inferData(self, input_queue, batchsize):
        if batchsize != 1:
            raise Exception("batchsize unequal one")
        id_lists, passby_lists = self.__buildBatch(input_queue, batchsize)
        infer_lists = self.__inferBatch(passby_lists)
        result_lists = self.__processBatch(passby_lists, infer_lists, batchsize)
        return id_lists, result_lists

    @utils.profiler_timer("TfLiteBackend::__buildBatch")
    def __buildBatch(self, in_queue, batchsize):
        predp_data = [None] * batchsize
        id_lists = [None] * batchsize
        passby_lists = [None] * batchsize
        index = batchsize - 1
        package = self.configs['queue.in'].blpop(in_queue)
        predp_frame = json.loads(package[-1].decode("utf-8"))
        if package is not None:
            id_lists[index] = predp_frame['uuid']
            predp_data[index] = self.predp.pre_dataprocess(predp_frame)
            passby_lists[index] = predp_data[index]['passby']
        return id_lists, passby_lists[index]

    @utils.profiler_timer("TfLiteBackend::__inferBatch")
    def __inferBatch(self, passby_lists):
        ori = utils.getKey('shape', dicts=passby_lists)
        self.model_object.set_tensor(self.input_details[0]['index'], ori)
        self.model_object.invoke()
        infer_lists = []
        for i in range(0, len(self.output_details)):
            infer_lists.append(self.model_object.get_tensor(self.output_details[i]['index']).squeeze())
        return infer_lists

    @utils.profiler_timer("TfLiteBackend::__processBatch")
    def __processBatch(self, passby_lists, infer_lists, batchsize):
        result_lists = [None] * batchsize
        index = batchsize - 1
        post_frame = {
            'passby': passby_lists,
            'infers': infer_lists,
        }
        result_lists[index] = self.postdp.post_dataprocess(post_frame)
        return result_lists
