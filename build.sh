#! /bin/bash

PROJECT=${1}
VERSION=${2}
BASE_REPO=${3}

if [ "x${PROJECT}" == "x" ]; then
    echo "bad project name"
    exit 1
fi

if [ "x${VERSION}" == "x" ]; then
    VERSION="0.0.0"
fi

if [ x"${BASE_REPO}" == "x" ]; then
    BASE_REPO="registry.jiangxingai.com:5000"
fi

BUILDFILE="Dockerfile"
ARCH=`uname -i`

if [ "${ARCH}" == "x86_64" ]; then
    BUILDFILE="Dockerfile"
    ARCH="x86"
elif [ "${ARCH}" == "aarch64" ]; then
    BUILDFILE="Dockerfile"
    ARCH="arm64v8"
else
    echo "unkown cpu arch"
    exit 1
fi

echo "version is: ${VERSION}"

repo="${BASE_REPO}/${PROJECT}:${ARCH}_${VERSION}"
latest_repo="${BASE_REPO}/${PROJECT}:${ARCH}_latest"

sudo docker build . -t ${repo} -f ${BUILDFILE}
sudo docker tag ${repo} ${latest_repo}
sudo docker push ${repo}
sudo docker push ${latest_repo}

