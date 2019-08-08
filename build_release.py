import os

# Cleaning
print(">> Cleaning...")
if os.path.exists(os.path.join(os.getcwd(), 'build')):
    os.system("rm -r build")
if os.path.exists(os.path.join(os.getcwd(), 'release-pack')):
    os.system("rm -r release-pack")

# Building
major_ver = "api_v1"
minor_ver = "alpha"

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
    cp_cmd = "cp build/lib.linux-aarch64-3.6/" + so_name + ".cpython-36m-aarch64-linux-gnu.so release-pack/" + s.replace(".py", ".so")
    os.system(cp_cmd)
if os.path.exists(os.path.join(os.getcwd(), 'build')):
    os.system("rm -r build")

print("Done")

