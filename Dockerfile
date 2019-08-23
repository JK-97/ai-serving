FROM arm64v8/ubuntu:18.04 as builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends libhdf5-serial-dev \ 
    hdf5-tools \
    libhdf5-dev \
    zlib1g-dev \ 
    libjpeg8-dev \
    python3-pip \
    python3-h5py \
    build-essential \
    wget \
    cmake \
    git \
    libgtk2.0-dev \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    python3-dev \
    libtbb2 \
    libtbb-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libdc1394-22-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN pip3 install -U --no-cache-dir setuptools  

RUN pip3 install -U --no-cache-dir numpy==1.16.0 \
    requests==2.20.0 \
    tornado==4.5.2 \
    grpcio \
    absl-py \
    py-cpuinfo \
    psutil \
    portpicker \
    six \
    mock \
    gast \
    astor \
    termcolor \
    protobuf \
    wrapt \ 
    google-pasta \
    keras-preprocessing \ 
    && wget https://developer.download.nvidia.com/compute/redist/jp/v42/tensorflow-gpu/tensorflow_gpu-1.13.1+nv19.3-cp36-cp36m-linux_aarch64.whl \
    && pip3 install tensorflow_gpu-1.13.1+nv19.3-cp36-cp36m-linux_aarch64.whl \
    && rm -rf tensorflow_gpu-1.13.1+nv19.3-cp36-cp36m-linux_aarch64.whl


COPY ./cuda-10.0 /usr/local/cuda-10.0

COPY ./ld.conf  /etc/ld.so.conf.d/

WORKDIR /home/tx1-node2/ai-service/src

ENV PY_NAME "python3.6"

RUN  git clone https://github.com/opencv/opencv.git \
    && cd opencv/ \
    && git checkout 4.1.0 \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_BUILD_TYPE=RELEASE \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DPYTHON2_EXECUTABLE=$(which python3) \
    -DPYTHON_INCLUDE_DIR=/usr/include/$PY_NAME \
    -DPYTHON_INCLUDE_DIR2=/usr/include/aarch64-linux-gnu/$PY_NAME \
    -DPYTHON_LIBRARY=/usr/lib/aarch64-linux-gnu/lib$PY_NAME.so \
    -DPYTHON2_NUMPY_INCLUDE_DIRS=/usr/lib/$PY_NAME/dist-packages/numpy/core/include/ \
    -DBUILD_DOCS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PERF_TESTS=OFF \
    .. \
    && make -j$(nproc --all) \
    && make install \
    && ldconfig -v \
    && rm -rf /home/tx1-node2/ai-service/src/opencv

COPY ./src /home/tx1-node2/ai-service/src

RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.9.1/protobuf-python-3.9.1.tar.gz \
    && tar -zxvf protobuf-python-3.9.1.tar.gz -C . \
    && cd protobuf-3.9.1 \
    && ./configure --prefix=/usr/local/protobuf \
    && make \
    && make install \
    && cd python \
    && python3 setup.py install --cpp_implementation \
    && cd .. \
    && cd .. \
    && rm -rf protobuf-python-3.9.1.tar.gz \
    && rm -rf protobuf-3.9.1 \
    && ln -s /usr/local/protobuf/lib/libprotobuf.so.20.0.1 /usr/lib/aarch64-linux-gnu/libprotobuf.so.20 \
    && ln -s /usr/local/protobuf/lib/libprotoc.so.20.0.1 /usr/lib/aarch64-linux-gnu/libprotoc.so.20


ENTRYPOINT ["python3","run.py"]

