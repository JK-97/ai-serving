"""
  JXServing Model

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
from serving.core import runtime as grt
from settings import settings


"""
  This function connects to external pre-process function defined in pre_dataprocess.py

  Input:
      path:             the path of image
  Output:
      original_image:   original image
      feed_list:        tensorflow feed_dict struct, indexed by given tensor.json
"""
def preDataProcessing(path):
    if grt.PREDP:
        return grt.PREDP.pre_dataprocess(path)
    else:
        try: 
            sys.path.append(grt.MODEL_PATH)
            grt.PREDP = importlib.import_module('pre_dataprocess')
            return grt.PREDP.pre_dataprocess(path)
        except Exception as e:
            logging.critical(e)
            logging.exception(e)
            raise e

"""
  This function connects to external pre-process function defined in post_dataprocess.py

  Input:
      original_image:   original image
      prediction_dict:  return value of tensorflow sess.run
      classes:          classes of tensorflow model prediction
  Output:
      result:           processed result, or filtered result
"""
def postDataProcessing(original_image, prediction_dict, classes):
    if grt.POSTDP:
        return grt.POSTDP.post_dataprocess(original_image, prediction_dict, classes)
    else:
        try: 
            sys.path.append(grt.MODEL_PATH)
            grt.POSTDP = importlib.import_module('post_dataprocess')
            return grt.POSTDP.post_dataprocess(original_image, prediction_dict, classes)
        except Exception as e:
            logging.critical(e)
            logging.exception(e)
            raise e

"""
  This function create tensorflow session with frozen pb file

  Input:
      model  :          which model is going to serve
      mode   :          which mode is going to serve
      pb_name:          read specific pb file, by default = "model.pb" 
      preheat:          preheat session, skip tensorflow's lazy load, by default = True
  Output:
      no output, global variable grt.SESS stores this created session 
"""
def switchModel(model, mode, pb_name = "model.pb", preheat = True):
    supported_modes = {
        "frozen":   switchSessionWithFrozenModel,
        "unfrozen": switchSessionWithUnfrozenModel,
    }

    if mode not in supported_modes:
        grt.SWITCH_STATUS = "falied"
        grt.SWITCH_ERROR = "unspported mode"
        return False
    else:
        th_load = threading.Thread(
                target=switchSessionWithModel, 
                args=(model, supported_modes[mode], pb_name, preheat))
        th_load.start()
        return True


def timer(prompt):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if options.profile:
                ts = time.time()
                func(*args, **kwargs)
                te = time.time()
                logging.debug("{} elapse {} secs".format(prompt, te-ts))
            else:
                func(*args, **kwargs)
        return wrapper
    return decorator


@timer(prompt="switchSessionWithModel")
def switchSessionWithModel(model, loader, pb_name, preheat):
    try:
        if model == grt.MODEL_NAME:
            return True

        # cleaning
        if grt.SESS != None:
            grt.SWITCH_STATUS = "cleaning"
            grt.SESS = None

        grt.MODEL_NAME = model
        grt.SWITCH_ERROR = ""

        # validating
        tmp_path = os.path.join(settings['model_path'], model)
        if not os.path.isdir(tmp_path):
            raise RuntimeError("model does not exist: {}".format(tmp_path))

        # loading
        grt.MODEL_PATH = tmp_path
        grt.SWITCH_STATUS = "loading"

        # load model classes
        with open(os.path.join(grt.MODEL_PATH, 'class.txt')) as class_file: 
            grt.CLASSES_VEC = eval(class_file.read().encode('utf-8'))

        # load graph configurations
        with open(os.path.join(grt.MODEL_PATH, 'tensor.json')) as tensor_file:
            grt.TENSOR_MAP = json.loads(tensor_file.read())

        # load graph
        loader(model, pb_name)
        if grt.SESS == None:
            raise RuntimeError("unknown error, tensorflow session == none")

        # set input/output tensor
        grt.OUTPUT_TENSOR_VEC = []
        for it in grt.TENSOR_MAP['output']:
            grt.OUTPUT_TENSOR_VEC.append(grt.SESS.graph.get_tensor_by_name(it))
        grt.INPUT_TENSOR_DICT = []
        for it in grt.TENSOR_MAP['input']:
            grt.INPUT_TENSOR_DICT.append(grt.SESS.graph.get_tensor_by_name(it))

        # preheat neural network
        if preheat == True:
            grt.SWITCH_STATUS = "preheating"
            _, feed_list = preDataProcessing(settings['preheat_image_path'])
            feeding = {}
            for index, t in enumerate(grt.INPUT_TENSOR_DICT):
                feeding[t] = feed_list[index]
            grt.SESS.run(grt.OUTPUT_TENSOR_VEC, feed_dict=feeding)

        grt.SWITCH_STATUS = "loaded"
        return True

    except Exception as e:
        logging.error(e)
        logging.exception(e)
        grt.SESS = None
        grt.SWITCH_STATUS = "failed"
        grt.SWITCH_ERROR = "switch error: {}".format(e)
        grt.OUTPUT_TENSOR_VEC = []
        grt.INPUT_TENSOR_DICT = []
        grt.TENSOR_MAP = {}
        return False


@timer(prompt="switchFrozenModel")
def switchSessionWithFrozenModel(model, pb_name):
    with tf.Graph().as_default():
        graph_def = tf.GraphDef()

        path = os.path.join(grt.MODEL_PATH, pb_name)
        with open(path, "rb") as model_file:
            graph_def.ParseFromString(model_file.read())
            tf.import_graph_def(graph_def, name="")

        grt.SESS = tf.Session()
        grt.SESS.run(tf.global_variables_initializer())


@timer(prompt="switchUnfrozenModel")
def switchSessionWithUnfrozenModel(model, pb_name):
    # saved_model.loader only takes model path as input
    pb_name = None

    grt.SESS = tf.Session(graph=tf.Graph())
    tf.saved_model.loader.load(
            grt.SESS, 
            [tf.saved_model.tag_constants.SERVING],
            grt.MODEL_PATH)


"""
  This function run tensorflow session with the given image

  Input:
      filename:         image's location (an absolute path is safer than a relevant path)
  Output:
      result:           prediction result
"""
def runSingleSession(filepath):
    try:
        original_image, feed_list = preDataProcessing(filepath)
        feeding = {}
        for index, t in enumerate(grt.INPUT_TENSOR_DICT):
            feeding[t] = feed_list[index]
        #print(feeding)
        predict = grt.SESS.run(grt.OUTPUT_TENSOR_VEC, feed_dict=feeding)
        return postDataProcessing(original_image, predict, grt.CLASSES_VEC)
    except Exception as e:
        logging.exception(e)
        logging.error("failed to run session: {}".format(e))
        return None

