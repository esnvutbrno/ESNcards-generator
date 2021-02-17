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

        # FIXME hack for 'more' faces in a photo
        #rects = np.array([rects[0,:]])

        # Add x and y coordinates to the width and height of the squere to get second coordinates
        rects[:,2:] += rects[:,:2]

        #logger.debug(f"Rectangles original: {rects}")

        # Get correct rectangle ratio and expand it into the correct directions
        # After the expansion, eyes would be in the middle of the photo,
        # so the rectangle is expanded more to the bottom and less to the top.
        # FIXME we count with height being biger than width here...
        hOffsets = (PhotoSize.h / PhotoSize.w) / 100
        rects[:,1] -= (rects[:,1] * (hOffsets * 40)).astype(int) # by 40% of the offset to the top
        rects[:,3] += (rects[:,1] * (hOffsets * 60)).astype(int) # by 60% of the offset to the bottom

        # Now espand the whole rectangle by some relative size to make space for the rest of the head
        rects[:,:2] -= (rects[:,2:] >> 3) # 12.5% of the bigger coordinate (not a typo)
        rects[:,2:] += (rects[:,2:] >> 3) # 12.5% of the bigger coordinate

        #logger.debug(f"Rectangles expanded: {rects}")
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