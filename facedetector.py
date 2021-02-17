from common import PhotoSize
import cv2 as cv
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaceDetector:
    @classmethod
    def detect(cls, img, cascade):
        rects = cascade.detectMultiScale(
            img,
            scaleFactor=1.01,
            minNeighbors=50,
            minSize=(100, 100),
            flags = cv.CASCADE_SCALE_IMAGE
        )

        if len(rects) == 0:
            return []

        # Compute offsets to expand square to fit desired dimensions of a photo
        wOffsets = int(np.array([(PhotoSize.w - rects[:, 2]) / 2]).T)
        hOffsets = int(np.array([(PhotoSize.h - rects[:, 3]) / 2]).T)

        # Add x and y coordinates to the width and height of the squere to get second coordinates
        rects[:,2:] += rects[:,:2]

        # Expand the squre
        rects[:,0] -=  wOffsets
        rects[:,1] -=  hOffsets
        rects[:,2] +=  wOffsets
        rects[:,3] +=  hOffsets

        logger.debug(f"Rectangles: {rects}")
        return rects

    @classmethod
    def draw_rects(cls, img, rects, color):
        for (x1, y1, x2, y2) in rects:
            cv.rectangle(img, (x1, y1), (x2, y2), color, 2)

    @classmethod
    def run(cls, imgpath, cascpath):
        img = cv.imread(imgpath)
        faceCascade = cv.CascadeClassifier(cascpath)

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        gray = cv.equalizeHist(gray)

        rects = cls.detect(gray, faceCascade)
        vis = img.copy()
        cls.draw_rects(vis, rects, (0, 255, 0))

        # TODO handle more faces (?scaleFactor?)
        logger.debug(f"Found {len(rects)} faces!")

        cv.imshow("Faces found", vis)
        cv.waitKey(0)

        return vis