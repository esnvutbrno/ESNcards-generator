import cv2 as cv
import numpy as np
import logging
import matplotlib.pyplot as plt

from config import EqualizeHistMode, PhotoSize, Config
from tools import retrieve_name

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
        # Mask only negative values and make them positive
        negCoords = np.negative(rects[:,:2] * (rects[:,:2] < 0))
        # Add negative part to the oposite coordinates
        rects[:, 2:] += negCoords
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

        # Make sure the rectangle is not larger than the image
        h,w = img.shape
        rects[rects[..., 2] > w, 2] = w
        rects[rects[..., 3] > h, 3] = h
            
        return rects

    @staticmethod
    def draw_rects(img, rects, color):
        i = 0
        for (x1, y1, x2, y2) in rects:
            cv.rectangle(img, (x1, y1), (x2, y2), color, 2)

            if np.shape(rects)[0] > 1:
                fontSize = (x2-x1)>>6
                cv.putText(img, str(i), (x1, y2), cv.FONT_HERSHEY_SIMPLEX, fontSize, color, fontSize)
                i += 1

    @staticmethod
    def crop(img, x1, y1, x2, y2):
        return img[y1:y2, x1:x2]

    @staticmethod
    def hist_eq_other(img_in):
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
    def hist_eq_clahe(img):
        img_yuv = cv.cvtColor(img, cv.COLOR_BGR2YUV)
        clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(2,2))
        img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
        img_out = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)
        return img_out

    @staticmethod
    def hist_eq_heq_yuv(img):
        img_yuv = cv.cvtColor(img, cv.COLOR_BGR2YUV)
        # Histogram equalisation on the Y-channel
        img_yuv[:, :, 0] = cv.equalizeHist(img_yuv[:, :, 0])
        img_out = cv.cvtColor(img_yuv, cv.COLOR_YUV2BGR)
        return img_out

    @staticmethod
    def hist_eq_heq_hsv(img):
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        # Histogram equalisation on the V-channel
        img_hsv[:, :, 2] = cv.equalizeHist(img_hsv[:, :, 2])
        img_out = cv.cvtColor(img_hsv, cv.COLOR_HSV2BGR)
        return img_out

    @staticmethod
    def run(imgpath, cascpath):
        # Prepare vars
        img = cv.imread(imgpath)
        faceCascade = cv.CascadeClassifier(cascpath)

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        gray = cv.equalizeHist(gray)

        # Run facial recognition
        rects = FaceDetector.detect(gray, faceCascade)

        # Process found faces
        logger.debug(f"Found {len(rects)} faces!")

        if len(rects) == 0:
            return img
        elif len(rects) > 1:
            # # We found more faces...choose one
            # vis_faces = img.copy()
            # FaceDetector.draw_rects(vis_faces, rects, (0, 255, 0))
            # cv.imshow("Several faces found!", vis_faces)
            # i = input("Enter one number [0]: ")
            #
            # if i.isnumeric() and int(i) < np.shape(rects)[0]:
            #     rects = rects[[int(i)], :]
            # else:
            #     logger.warning(f"'{i}' is not valid! Choosing the 0th one.")
            #     rects = rects[[0], :]
            #
            # cv.destroyAllWindows()
            rects = rects[[0], :]

        vis = img.copy()

        if Config.interactive:
            # In interactive mode, do not care about other settings,
            # just compute all variants and show them.

            # Original version with rectangles printed
            vis_rects = vis.copy()
            FaceDetector.draw_rects(vis_rects, rects, (0, 255, 0))

            # Crop around face
            vis_cropped = FaceDetector.crop(vis, rects[0,0], rects[0,1], rects[0,2], rects[0,3])
            
            # Different histogram equalization methods
            vis_eq_clahe = FaceDetector.hist_eq_clahe(vis_cropped)
            vis_eq_heq_yuv = FaceDetector.hist_eq_heq_yuv(vis_cropped)
            vis_eq_heq_hsv = FaceDetector.hist_eq_heq_hsv(vis_cropped)
            vis_eq_other = FaceDetector.hist_eq_other(vis_cropped)

            vislist = [vis, vis_cropped, vis_eq_clahe, vis_eq_heq_yuv, vis_eq_heq_hsv, vis_eq_other]

            f, ax = plt.subplots(3,2)
            i = 0
            for axi in ax.ravel(): 
                axi.set_axis_off()
                axi.set_title(str(i) + ":" + retrieve_name(vislist[i]))
                i += 1
            
            ax[0,0].imshow(cv.cvtColor(vis_rects, cv.COLOR_BGR2RGB))
            ax[0,1].imshow(cv.cvtColor(vislist[1], cv.COLOR_BGR2RGB))
            ax[1,0].imshow(cv.cvtColor(vislist[2], cv.COLOR_BGR2RGB))
            ax[1,1].imshow(cv.cvtColor(vislist[3], cv.COLOR_BGR2RGB))
            ax[2,0].imshow(cv.cvtColor(vislist[4], cv.COLOR_BGR2RGB))
            ax[2,1].imshow(cv.cvtColor(vislist[5], cv.COLOR_BGR2RGB))
            f.tight_layout()

            print(f"Which image should be used? ({len(vislist)}) to skip this person.")
            i = input("Enter one number [1]: ")

            plt.close(f)

            if i.isnumeric() and int(i) <= len(vislist):
                i = int(i)
            else:
                logger.warning(f"'{i}' is not valid! Choosing the cropped image.")
                i = 1
            
            if i == 6:
                raise Exception("Skipping person...")

            return vislist[i]

        # Not interactive mode, continue in your stuff
        if Config.crop:
            vis = FaceDetector.crop(vis, rects[0,0], rects[0,1], rects[0,2], rects[0,3])

        if Config.equalizehist:
            # TODO https://docs.opencv.org/3.1.0/d5/daf/tutorial_py_histogram_equalization.html

            if Config.equalizehist == EqualizeHistMode.CLAHE:
                vis = FaceDetector.hist_eq_clahe(vis)

            elif Config.equalizehist == EqualizeHistMode.HEQ_YUV:
                vis = FaceDetector.hist_eq_heq_yuv(vis)

            elif Config.equalizehist == EqualizeHistMode.HEQ_HSV:
                vis = FaceDetector.hist_eq_heq_hsv(vis)

            elif Config.equalizehist == EqualizeHistMode.OTHER:
                vis = FaceDetector.hist_eq_other(vis)
            
        return vis
