from serving.core import runtime

def ConstrainBackendInfo(info):
    if info['batchsize'] > 1000:
        raise ValueError("batchsize exceed limitation")
    if info['inferprocnum'] > 2:
        raise ValueError("inference process number exceed limitation")

def LimitBackendInstance():
    if len(runtime.BEs)+1 > 2:
        raise RuntimeError("backend instance exceed limitaion")