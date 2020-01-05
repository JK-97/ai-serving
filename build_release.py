import os
import sys, platform


micro_arch = platform.machine()
py_major = str(sys.version_info[0])
py_minor = str(sys.version_info[1])


def clean_pycache(filepath):
    files = os.listdir(filepath)
    for fd in files:
        cur_path = os.path.join(filepath, fd)
        if os.path.isdir(cur_path):
            if fd == "__pycache__":
                print("rm %s -rf" % cur_path)
                os.system("rm %s -rf" % cur_path)
            else:
                clean_pycache(cur_path)

# Cleaning
print(">> Cleaning...")
if os.path.exists(os.path.join(os.getcwd(), 'build')):
    os.system("rm -r build")
if os.path.exists(os.path.join(os.getcwd(), 'release-pack')):
    os.system("rm -r release-pack")

# Insert Device Info
# TODO(): overwrite device serial number

# Building
version = None
with open("VERSION", 'r') as ver_file:
    version = ver_file.read()
if version is None:
    raise RuntimeError("failed to read version")
print(">> Building", version, "...")
os.system("make protoc")
os.system("make message-linux-amd64")
source_files = [
    "serving/backend/abstract_backend.py",
    "serving/backend/rknn_python.py",
    "serving/backend/supported_backend.py",
    # "serving/backend/tensorflow_lite.py",
    "serving/backend/tensorflow_python.py",
    "serving/backend/tensorflow_serving.py",
    # "serving/backend/torch_python.py",

    "serving/core/backend.py",
    "serving/core/inference.py",
    "serving/core/model.py",
    "serving/core/regulator.py",
    "serving/core/runtime.py",
    "serving/core/sandbox_helper.py",
    "serving/core/sandbox.py",

    #"serving/handler/backend.py",
    #"serving/handler/connectivity.py",
    #"serving/handler/exchange.py",
    #"serving/handler/inference.py",
    #"serving/handler/model.py",

    "serving/interface/backend_pb2_grpc.py",
    "serving/interface/backend_pb2.py",
    "serving/interface/common_pb2_grpc.py",
    "serving/interface/common_pb2.py",
    "serving/interface/connectivity_pb2_grpc.py",
    "serving/interface/connectivity_pb2.py",
    "serving/interface/exchange_pb2_grpc.py",
    "serving/interface/exchange_pb2.py",
    "serving/interface/inference_pb2_grpc.py",
    "serving/interface/inference_pb2.py",
    "serving/interface/model_pb2_grpc.py",
    "serving/interface/model_pb2.py",

    "serving/plugin/encbase64.py",

    "serving/router.py",
    "serving/utils.py",
]

srcs = []
for s in source_files:
    srcs.append("src/" + s)
with open("srcs.txt", "w") as f:
    f.write(str(srcs))
os.system("python3 setup.py build_ext")
os.system("rm srcs.txt")

# Constructing
print(">> Constructing...")
os.system("mkdir release-pack")
os.system("cp src/run.py release-pack")
os.system("cp -r src/serving release-pack/")
os.system("cp src/requirements.txt release-pack/")
os.system("cp settings_tmpl.py release-pack/settings.py")
for s in source_files:
    rm_cmd = "rm release-pack/" + s.replace(".py", ".*")
    os.system(rm_cmd)
    so_name = (s.split('/')[-1]).split('.')[0]
    cp_cmd = "cp build/lib.linux-"+micro_arch+"-"+py_major+"."+py_minor+"/"+so_name+".cpython-"+py_major+py_minor+"m-"+micro_arch+"-linux-gnu.so release-pack/"+s.replace(".py", ".so")
    os.system(cp_cmd)
clean_pycache("release-pack")

if os.path.exists(os.path.join(os.getcwd(), 'build')):
   os.system("rm -r build")

print("Done")
