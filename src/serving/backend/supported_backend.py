"""
  AIServing Abstract Backend

  Contact: 1179160244@qq.com
"""

from enum import Enum, unique


@unique
class Type(Enum):
    TfPy = 'tensorflow'
    TfSrv = 'tensorflow-serving'
    TfLite = 'tensorflow-lite'
    Torch = 'pytorch'
    RknnPy = 'rknn'


def Validator(value):
    try:
        return Type(value), ""
    except ValueError as e:
        return None, "unsupported backend"
