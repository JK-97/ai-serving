import logging
import cv2
import os
import uuid
import wget
import zipfile
import tarfile

from serving.core import runtime
from serving import utils

def handlerStream(data):
    try:
        if data.get('source') == "video":
            tar = tarfile.open(data.get('path'))
            names = tar.getnames()
            video_path = ""
            for name in names:
                tar.extract(name, "/tmp/")
                video_path = "/tmp/" + name
            tar.close()
            cap = cv2.VideoCapture(video_path)
        else:
            video_path = data.get('path')
            cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                cap = cv2.VideoCapture(video_path)
                continue
            #cv2.imshow('capture', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            else:
                runtime.Images_pool["stream"] = frame
        cap.release()
        #cv2.destroyAllWindows()
    except Exception as e:
        logging.exception(e)
        raise RuntimeError("failed to handler stream")

def handlerImageSets(data):
    try:
        imageSets_url =data.get("path")
        filename = wget.detect_filename(imageSets_url)
        imageSets_name = "/tmp/" + filename
        logging.debug(imageSets_name)
        if os.path.exists(imageSets_name):
            os.remove(imageSets_name)
        wget.download(imageSets_url, out="/tmp")
        if not os.path.exists(imageSets_name):
            logging.error("imageSets wget error:", imageSets_url)
        zFile = zipfile.ZipFile(imageSets_name)
        for zFile_name in zFile.namelist():
            zFile.extract(zFile_name, "/tmp/")
        zFile.close()

        image_dir = imageSets_name.split(".")[0] + "/JPEGImages/"
        for image_name in os.listdir(image_dir):
            image_id = str(uuid.uuid4())
            runtime.Images_pool[image_id] = utils.imread_image(image_dir + image_name)
            runtime.ImageSets_info.append(image_id)
    except Exception as e:
        logging.exception(e)
        raise RuntimeError("failed to handler ImageSets")

def reader(data):
    if data.get("source") == "imageSets":
        handlerImageSets(data)

    if data.get("source") == "stream" or data.get("source") == "video":
        handlerStream(data)










