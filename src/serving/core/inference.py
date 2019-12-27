import os
import logging

from serving import utils
from serving.core import runtime

@utils.gate(runtime.FGs['use_native_stat'], runtime.Ps['native_stat'])
def inferenceLocal(data):
    backend_instance = runtime.BEs.get(data.get('bid'))
    if backend_instance is None:
        raise RuntimeError("failed to find backend")
    print(data)
    data_id = data.get('uuid')
    data_src = data.get('path')
    if data_id is None or data_src is None:
        raise ValueError("lack of data")
    backend_instance.enqueueData({'uuid': data_id, 'path': data_src})


@utils.gate(runtime.FGs['use_native_stat'], runtime.Ps['native_stat'])
def inferenceRemote(data):
    backend_instance = runtime.BEs.get(data.get('bid'))
    if backend_instance is None:
        raise RuntimeError("failed to find backend")
    data_id = data.get('uuid')
    data_src = data.get('base64')
    data_type = data.get('type')
    if data_id is None or data_src is None or data_type is None:
        raise ValueError("lack of data")

    # TODO(): directly transfer base64 data to memory
    tmp_file = os.path.join('/tmp', data_id+'.'+data_type)
    ret = runtime.Ps['encbase64'].to_image(data_src, tmp_file)
    if ret['code'] != 0:
        raise RuntimeError("failed to dump remote data")
    backend_instance.enqueueData({'uuid': data_id, 'path': tmp_file})
    