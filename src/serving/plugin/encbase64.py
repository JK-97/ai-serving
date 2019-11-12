import re
import base64
import logging
from io import BytesIO

from PIL import Image

def to_image(base64_str, path):
    try:
        base64_data = re.sub('^data:image/.+;base64,', '', base64_str)
        byte_data = base64.b64decode(base64_data)
        image_data = BytesIO(byte_data)
        img = Image.open(image_data).convert("RGB")
        if path is not None:
            img.save(path)
        return {'code': 0, 'msg': ""}
    except Exception as e:
        logging.exception(e)
        return {'code': 1, 'msg': "failed to decode images"}
