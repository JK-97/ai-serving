# -*- coding: utf-8 -*-

"""Global settings for the project"""

import os

from tornado.options import define


define("debug", default=False, help="debug mode")
define("profile", default=False, help="profile mode")

define("port", default=8080, help="run on the given port", type=int)


settings = {
    'model_path': "/home/tx1-node1/ai-demo/ai-service/src/model", 
    'preheat_image_path': "/home/tx1-node1/ai-demo/ai-service/src/preheat/preheat.jpeg"
}


