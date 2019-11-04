"""
  JXServing Abstract Backend

  Contact: songdanyang@jiangxing.ai
"""

from enum import Enum, unique


@unique
class Type(Enum):
    TfPy = 'tensorflow'
    TfSrv = 'tensorflow-serving'
    Torch = 'pytorch'
    TfLite = 'tensorflow-lite'
    RknnPy = 'rknn'
    MxNet = 'mxNet'


def Validator(value):
    try:
        return Type(value), ""
    except ValueError as e:
        return None, "unsupported backend"
