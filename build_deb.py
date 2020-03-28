import os
import sys
import platform


micro_arch = platform.machine()
py_major = str(sys.version_info[0])
py_minor = str(sys.version_info[1])


# Cleaning
print(">> Cleaning...")
if os.path.exists(os.path.join(os.getcwd(), 'deb')):
    os.system("rm -r deb")

# Insert Device Info
# TODO(): overwrite device serial number

# Building
version = None
with open("VERSION", 'r') as ver_file:
    version = ver_file.read()
if version is None:
    raise RuntimeError("failed to read version")

arch = None
print("Detected build env:", micro_arch)
if micro_arch == "x86_64":
    arch = "amd64"
if micro_arch == "aarch64":
    arch = "arm64"
if arch is None:
    raise RuntimeError("failed to determine architecture")
print(">> Building", version, "in:", arch, "...")

# Constructing
print(">> Constructing...")
os.system("mkdir deb")
os.system("cp -r DEBIAN deb/")
os.system("cp -r release-pack deb/aiserving")
os.system("cp VERSION deb/aiserving/")
os.system("cp CHANGELOG deb/aiserving/")
ctrl_content = None
with open("deb/DEBIAN/control", 'r') as ctrl_file:
    ctrl_content = ctrl_file.read()
ctrl_content = ctrl_content.replace("REPLACE_VERSION", version.strip())
ctrl_content = ctrl_content.replace("REPLACE_ARCH", arch)
with open("deb/DEBIAN/control", 'w') as ctrl_file:
    ctrl_file.write(ctrl_content)
    ctrl_file.flush()
print(ctrl_content)
print("Done")
os.system("dpkg-deb -b deb trueno-board-linux-"+arch+".deb")
