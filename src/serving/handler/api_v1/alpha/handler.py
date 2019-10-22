import logging, sys
import rapidjson as json
from serving.handler.base import BaseHandler, AsyncHandler
from serving.core import runtime

class DetectHandler(AsyncHandler):

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        """
        POST:
          "path"     : string, specify which image is sending to tensorflow mxNet

        Response:
          "result"   : dict, mxNet prediction result
        """

        json_response = None
        try:
            data = str(self.request.body, encoding="utf-8")

            #json_response = runtime.BACKEND.inferData(json.loads(data))
            #self.finish(json_response)
            # json_response = runtime.BACKEND.inferData(json.loads(data))
            self.finish(runtime.inputData(json.loads(data)))
        except KeyError as e:
            logging.exception(e)
            self.finish({"err":400, "msg":"missing key {}".format(e)})
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")


class SwitchModelHandler(BaseHandler):

    def get(self, *args, **kwargs):
        """
        Response:
          "mxNet"   : string, current serving mxNet
          "status"  : string <"cleaning", "loading", "preheating", "loaded", "failed">, indicate current status of mxNet switching
          "error"   : string, error message when failed to load a mxNet
        """
        try:
            self.finish(runtime.reporter())
        except KeyError as e:
            logging.exception(e)
            self.finish({"err":400, "msg":"missing key {}".format(e)})
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")

    def post(self, *args, **kwargs):
        """
        POST:
          "mxNet"   : string, specify the mxNet that want to switch or load
          "mode"    : string <"frozen", "unfrozen">, specify the mxNet is a frozen mxNet or unfrozen mxNet
          "device"  : string, specify which device to run the session
          "preheat" : bool, specify whether to preheat the session

        Response:
          "status"  : string <"succ", "fail">, indicate whether a mxNet is found correctly and
        """

        try:
            data = str(self.request.body, encoding="utf-8")
            runtime.loadBackends(json.loads(data), 0)
            self.finish({"status": "succ"})
        except KeyError as e:
            logging.exception(e)
            self.send_error_response(status_code=400, message="missing key {}".format(e))
        except UnboundLocalError as e:
            logging.info("UnboundLocalError: request too fast")

