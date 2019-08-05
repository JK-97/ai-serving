import json
import logging, sys
from serving.handler.base import V1BaseHandler
from serving.core import runtime
from serving.core import serving

class DetectHandler(V1BaseHandler):

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        """
        POST:
          "path"     : string, specify which image is sending to tensorflow model

        Response:
          "result"   : dict, model prediction result
        """

        json_response = None
        try:
            data = str(self.request.body, encoding="utf-8")

            image_path = json.loads(data)["path"]
            json_response = serving.runSingleSession(image_path)

            self.finish({"result": json_response})
        except KeyError as e:
            logging.exception(e)
            self.send_error_response(status_code=400, message="missing key {}".format(e))
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")


class SwitchModelHandler(V1BaseHandler):

    def get(self, *args, **kwargs):
        """
        Response:
          "model"   : string, current serving model
          "status"  : string <"cleaning", "loading", "preheating", "loaded", "failed">, indicate current status of model switching 
          "error"   : string, error message when failed to load a model
        """
        try:
            self.finish({
                "model":  runtime.MODEL_NAME,
                "status": runtime.SWITCH_STATUS,
                "error":  runtime.SWITCH_ERROR})
        except KeyError as e:
            logging.exception(e)
            self.send_error_response(status_code=400, message="missing key {}".format(e))
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")

    def post(self, *args, **kwargs):
        """
        POST:
          "model"   : string, specify the model that want to switch or load
          "mode"    : string <"frozen", "unfrozen">, specify the model is a frozen model or unfrozen model
          "preheat" : bool, specify whether to preheat the session

        Response:
          "status"  : string <"succ", "fail">, indicate whether a model is found correctly and 
        """

        json_response = None
        try:
            data = str(self.request.body, encoding="utf-8")
            data = json.loads(data)
            
            preheat = bool(data['preheat'])
            logging.warning("Force to PRE-HEAT while calling serving.switchModel")
            ret = serving.switchModel(data['model'], data['mode'])
            if ret:
                json_response = "succ"
            else:
                json_response = "fail"
            logging.debug(json_response)

            self.finish({"status": json_response})
        except KeyError as e:
            logging.exception(e)
            self.send_error_response(status_code=400, message="missing key {}".format(e))
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")


