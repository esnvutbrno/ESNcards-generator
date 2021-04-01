import cv2 as cv
import numpy as np
import logging

from config import EqualizeHistMode, PhotoSize, Config

logger = logging.getLogger(__name__)

class FaceDetector:
    @staticmethod
    def expand_rects(rects):
        # Expand the square around a face by some relative size to make space for the rest of the head
        rects[:,:2] -= (rects[:,2:] >> 2) # move x0 and y0 by 12.5% of the height and width
        rects[:,2:] += (rects[:,2:] >> 1).astype(int) # expand the square size by 50%

        # Expand the square into a rectangle to fit the face with body.
        # Use aspect ratio computed from photo size.
        # TODO we count with height being biger than width here...
        ratio = (PhotoSize.h / PhotoSize.w)

        # After the expansion, eyes would be in the middle of the photo,
        # so the rectangle is moved more to the bottom than to the top.
        rects[:,3] = (rects[:,3] * ratio).astype(int)
        rects[:,1] -= rects[:,3] >> 3 # by 12.5% of the offset to the top



        # Fix negative coordinates
        negCoords = rects[rects < 0]
        # TODO add negCoords to oposite coordintes
        rects[rects < 0] = 0

        return rects

    @staticmethod
    def detect(img, cascade, expand = True):
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

        if expand:
            #logger.debug(f"Rectangles original: \n{rects}")
            rects = FaceDetector.expand_rects(rects)
            #logger.debug(f"Rectangles expanded: \n{rects}")

        # Add x and y coordinates to the width and height of the square to get second coordinates
        rects[:,2:] += rects[:,:2]

        return rects

    @staticmethod
    def draw_rects(img, rects, color):
        for (x1, y1, x2, y2) in rects:
            cv.rectangle(img, (x1, y1), (x2, y2), color, 2)

    @staticmethod
    def crop(img, x1, y1, x2, y2):
        return img[y1:y2, x1:x2]

    @staticmethod
    def histogram_equalization(img_in):
        #https://stackoverflow.com/a/62980480

        # segregate color streams
        b, g, r = cv.split(img_in)
        h_b, bin_b = np.histogram(b.flatten(), 256, [0, 256])
        h_g, bin_g = np.histogram(g.flatten(), 256, [0, 256])
        h_r, bin_r = np.histogram(r.flatten(), 256, [0, 256])
        # calculate cdf
        cdf_b = np.cumsum(h_b)
        cdf_g = np.cumsum(h_g)
        cdf_r = np.cumsum(h_r)

        # mask all pixels with value=0 and replace it with mean of the pixel values
        cdf_m_b = np.ma.masked_equal(cdf_b, 0)
        cdf_m_b = (cdf_m_b - cdf_m_b.min()) * 255 / (cdf_m_b.max() - cdf_m_b.min())
        cdf_final_b = np.ma.filled(cdf_m_b, 0).astype('uint8')

        cdf_m_g = np.ma.masked_equal(cdf_g, 0)
        cdf_m_g = (cdf_m_g - cdf_m_g.min()) * 255 / (cdf_m_g.max() - cdf_m_g.min())
        cdf_final_g = np.ma.filled(cdf_m_g, 0).astype('uint8')


        cdf_m_r = np.ma.masked_equal(cdf_r, 0)
        cdf_m_r = (cdf_m_r - cdf_m_r.min()) * 255 / (cdf_m_r.max() - cdf_m_r.min())
        cdf_final_r = np.ma.filled(cdf_m_r, 0).astype('uint8')
        # merge the images in the three channels
        img_b = cdf_final_b[b]
        img_g = cdf_final_g[g]
        img_r = cdf_final_r[r]

        img_out = cv.merge((img_b, img_g, img_r))
        # validation
        equ_b = cv.equalizeHist(b)
        equ_g = cv.equalizeHist(g)
        equ_r = cv.equalizeHist(r)
        equ = cv.merge((equ_b, equ_g, equ_r))
        # print(equ)
        # cv2.imwrite('output_name.png', equ)
        return img_out

    @staticmethod
    def run(imgpath, cascpath):
        img = cv.imread(imgpath)
        faceCascade = cv.CascadeClassifier(cascpath)

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        gray = cv.equalizeHist(gray)

        rects = FaceDetector.detect(gray, faceCascade)

        logger.debug(f"Found {len(rects)} faces!")

        if len(rects) == 0:
            return img
        elif len(rects) > 1:
            pass # TODO handle more faces and false positives

        vis = img.copy()

        if Config.facedetect:
            FaceDetector.draw_rects(vis, rects, (0, 255, 0))

            if Config.debug:
                cv.imshow("Faces found", vis)
                cv.waitKey(0)

        if Config.crop:
            vis = FaceDetector.crop(vis, rects[0,0], rects[0,1], rects[0,2], rects[0,3])

        if Config.equalizehist:
            # TODO https://docs.opencv.org/3.1.0/d5/daf/tutorial_py_histogram_equalization.html

            if Config.equalizehist == EqualizeHistMode.CLACHE:
                img_yuv = cv.cvtColor(vis, cv.COLOR_BGR2YUV)
                clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(2,2))
                img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
                vis = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)

            elif Config.equalizehist == EqualizeHistMode.HEQ_YUV:
                img_yuv = cv.cvtColor(vis, cv.COLOR_BGR2YUV)
                # Histogram equalisation on the Y-channel
                img_yuv[:, :, 0] = cv.equalizeHist(img_yuv[:, :, 0])
                vis = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)

            elif Config.equalizehist == EqualizeHistMode.HEQ_HSV:
                img_hsv = cv.cvtColor(vis, cv.COLOR_BGR2HSV)
                # Histogram equalisation on the V-channel
                img_hsv[:, :, 2] = cv.equalizeHist(img_hsv[:, :, 2])
                vis = cv.cvtColor(img_hsv, cv.COLOR_HSV2BGR)

            elif Config.equalizehist == EqualizeHistMode.OTHER:
                vis = FaceDetector.histogram_equalization(vis)

        return vis
