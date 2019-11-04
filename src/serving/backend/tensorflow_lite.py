import os

import tensorflow as tf

from serving import utils
from serving.backend import abstract_backend as ab


class TfLiteBackend(ab.AbstractBackend):
    def __init__(self, configurations={}):
        super().__init__(configurations)

    @utils.profiler_timer("TfLiteBackend::_loadModel")
    def _loadModel(self, load_configs):
        try:
            # load model pb
            self.model_object = tf.lite.Interpreter(model_path=os.path.join(self.configs['model_path'], "model.tflite"))
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
    def _inferData(self, in_queue, batchsize):

        data = [None] * batchsize
        id_lists = [None] * batchsize

        for i in range(batchsize):
            package = self.rPipe_for_raw_data.blpop(in_queue)
            if package is not None:
                predp_frame = self.loadData(package[-1])
                id_lists[i] = predp_frame['uuid']
                pre_p = self.predp.pre_dataprocess(predp_frame)
                self.model_object.set_tensor(self.input_details[0]['index'], pre_p[0])
                self.model_object.invoke()
                output_res = []
                for j in range(0, len(self.output_details)):
                    output_res.append(self.model_object.get_tensor(self.output_details[j]['index']).squeeze())
                output_res.append(pre_p)
                out_img = self.postdp.post_dataprocess(output_res)
                data[i] = {'data': out_img}
        return id_lists, data
