import cv2 as cv
import logging

logger = logging.getLogger(__name__)

class FaceDetector:
    @classmethod
    def detect(cls, img, cascade):
        rects = cascade.detectMultiScale(
            img,
            scaleFactor=1.3,
            minNeighbors=6,
            minSize=(60, 60),
            flags = cv.CASCADE_SCALE_IMAGE
        )

        if len(rects) == 0:
            return []
        rects[:,2:] += rects[:,:2]
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