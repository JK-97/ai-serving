import os
import sys, platform

major_ver = "api_v1"
minor_ver = "alpha"

micro_arch = platform.machine()
py_major = str(sys.version_info[0])
py_minor = str(sys.version_info[1])

# Cleaning
print(">> Cleaning...")
if os.path.exists(os.path.join(os.getcwd(), 'build')):
    os.system("rm -r build")
if os.path.exists(os.path.join(os.getcwd(), 'release-pack')):
    os.system("rm -r release-pack")

# Building
print(">> Building", major_ver, "/", minor_ver, "...")
source_files = [
    "serving/core/serving.py",
    "serving/core/runtime.py",
    "serving/urls.py",
    "serving/handler/base.py",
    "serving/handler/"+major_ver+"/"+minor_ver+"/handler.py",
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
os.system("cp -r src release-pack")
for s in source_files:
    rm_cmd = "rm release-pack/" + s.replace(".py", ".*")
    os.system(rm_cmd)
    so_name = (s.split('/')[-1]).split('.')[0]
    cp_cmd = "cp build/lib.linux-"+micro_arch+"-"+py_major+"."+py_minor+"/"+so_name+".cpython-"+py_major+py_minor+"m-"+micro_arch+"-linux-gnu.so release-pack/"+s.replace(".py", ".so")
    os.system(cp_cmd)
#if os.path.exists(os.path.join(os.getcwd(), 'build')):
#    os.system("rm -r build")

print("Done")

