FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev
RUN apt-get install -y python3-pip
RUN pip3 install -U pip
RUN pip3 install -U setuptools
RUN pip3 install -U h5py
RUN pip3 install -U numpy grpcio absl-py py-cpuinfo psutil portpicker six mock requests gast astor termcolor protobuf keras-applications keras-preprocessing wrapt google-pasta
RUN pip3 install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v42 tensorflow-gpu==$TF_VERSION+nv$NV_VERSION
