#!/usr/bin/env python3

import argparse
import csv
import cv2
import logging
import os
import re
import sys
import tempfile

from datetime import date

from config import PrintMode, PrintDirection, EqualizeHistMode, CardSpacing, Config
from facedetector import FaceDetector
from pdfprinter import PDFPrinter

logging.basicConfig(filename='/dev/stdout/',
                    format='[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PersonInfo:
    name = ""
    nationality = ""
    birthday = None
    faculty = "VUT Brno"
    section = "ESN VUT Brno"
    validity = None
    before_arrival = ""

    def __init__(self, row):
        self.parse(row)

    def parse(self, row):
        self.name = row["name"]
        self.nationality = row["country"]
        self.birthday = date(int("20" + row["Y0"] + row["Y1"]), int(row["M0"] + row["M1"]), int(row["D0"] + row["D1"]))       # FIXME fix the dirty year hack (20xx) - download_images.py does not export first two numbers of the year
        self.validity = date(int("20" + row["TY0"] + row["TY1"]), int(row["TM0"] + row["TM1"]), int(row["TD0"] + row["TD1"])) # FIXME fix the dirty year hack (20xx) - download_images.py does not export first two numbers of the year
        self.before_arrival = row["before_arrival"]


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--imgpath', default=Config.imgpath, help=f'Folder with images to be processed.')
    parser.add_argument('-p', '--peoplecsv', default=Config.peoplecsv, help=f'CSV file with students and their details.')
    parser.add_argument('-o', '--output', default=argparse.SUPPRESS, help=f'Output file. (default: {Config.output})')
    parser.add_argument('-m', '--mode', type=PrintMode, choices=list(PrintMode), default=Config.mode, help=f'Printing mode.')
    parser.add_argument('-d', '--direction', type=PrintDirection, choices=list(PrintDirection), default=Config.direction, help=f'Printing direction: {PrintDirection.NORMAL} - TOP -> BOTTOM, {PrintDirection.REVERSED} - BOTTOM -> TOP')
    parser.add_argument('-e', '--equalizehist', type=EqualizeHistMode, choices=list(EqualizeHistMode), default=Config.equalizehist, help=f'Equalize histogram. Modes: \n\t{EqualizeHistMode.CLAHE} - Contrast Limited Adaptive Histogram Equalization, {EqualizeHistMode.HEQ_YUV} - Global Histogram Equalization (YUV), {EqualizeHistMode.HEQ_HSV} - Global Histogram Qqualization (HSV), {EqualizeHistMode.OTHER} - Placeholder for tests.')
    parser.add_argument('-c', '--crop', help=f'Crop images using face detection.', action='store_true')
    parser.add_argument('--interactive', help=f'Ask which image to use each time - original, or cropped.', action='store_true')

    args, rest = parser.parse_known_args()
    sys.argv = sys.argv[:1] + rest

    Config.setup(args)

def load_images():
    try:
        return sorted([fn for fn in os.listdir(Config.imgpath) if fn.endswith(Config.imgextensions)])
    except:
        logger.error(f"Getting images from directory '{Config.imgpath}' failed.")
        sys.exit(1)

def get_image(name):
    foundImgs = [f for f in os.listdir(Config.imgpath) if re.match(rf".*{name}.*", f) and any(f.endswith(ext) for ext in Config.imgextensions)]
    logger.debug(f"Matched photos: {foundImgs}")

    if len(foundImgs) == 1:
        return foundImgs[0]

    if not foundImgs:
        return None

    # We found more images...choose one
    i = 0
    for img in foundImgs:
        print(f"[{i}] " + img)
        i += 1

    print("Which image should be used?")
    i = input("Enter one number [0]: ")

    if i.isnumeric() and i < len(foundImgs) and i > 0:
        i = int(i)
    else:
        logger.warning(f"'{i}' is not an integer! Choosing the first image.")
        i = 0

    return foundImgs[i]

def do():
    # TODO try-catch
    pp = PDFPrinter(Config.output)

    xLeftLimit = Config.spacing.xLeftLimit
    yTopLimit = Config.spacing.yTopLimit
    xRightLimit = Config.spacing.xRightLimit
    yBottomLimit = Config.spacing.yBottomLimit
    xIncrement = Config.spacing.xIncrement
    yIncrement = Config.spacing.yIncrement

    if Config.direction == PrintDirection.NORMAL:
        xInit= xLeftLimit
        yInit = yTopLimit
    else:
        xInit = xRightLimit
        yInit = yBottomLimit

    x,y = xInit, yInit

    # For debug message only.
    i = 0
    with open(Config.peoplecsv) as f:
        rows = sum(1 for line in f)-1

    with open(Config.peoplecsv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = sorted(reader, key=lambda d: (d['country'], d['name']))
        for row in data:
            i += 1

            pi = PersonInfo(row)

            logger.info(f"Exporting ({i}/{rows}) {pi.name}")

            # Print photo, if needed
            if Config.mode != PrintMode.TEXT_ONLY:
                try:
                    foundImg = get_image(pi.name)

                    # TODO refactor this if statement
                    if foundImg is None:
                        logger.error(f"!!! Could not find an image for '{pi.name}'. Skipping photo print...")
                    else:
                        imgpath = os.path.join(Config.imgpath, foundImg)

                        if Config.interactive or Config.crop or Config.equalizehist:
                            try:
                                vis = FaceDetector.run(imgpath, "haarcascade_frontalface_default.xml")
                                tmpfile = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()) + ".jpg")
                                cv2.imwrite(tmpfile, vis)
                                imgpath = tmpfile
                            except Exception as e:
                                logger.error(f"!!! FaceDetector thrown an Exception!\n{str(e)}")
                                logger.warning(f"Skipping the person completely...")
                                continue

                        pp.set_coordintates(x, y)
                        pp.print_photo(imgpath, pi)
                except Exception as e:
                    logger.error(f"!!! Could not print the image!\n{str(e)}")

            # Print person info, if needed
            if Config.mode != PrintMode.PHOTO_ONLY:
                xText, yText = x, y

                # If we print both photo and text, move init position of text next to the photo
                if Config.mode != PrintMode.TEXT_ONLY:
                    xText += CardSpacing.textDelta
                    yText += CardSpacing.rowDelta

                pp.set_coordintates(xText, yText)
                pp.print_person_info(pi)

            # Compute new coordinates
            x += xIncrement

            # Check for need to increment/decrement row
            if x < xLeftLimit or x > xRightLimit:
                x = xInit
                y += yIncrement
            else:
                # Print person delimiter (for easier cutting of prints)
                xDelim = x - (Config.spacing.xSpacing / 2) # x already incremented, get between cols
                yDelim = y + yIncrement - (Config.spacing.ySpacing / 3) # we did not increment row, do it here and get between the two

                if Config.mode == PrintMode.TEXT_ONLY:
                    # Init position for printing of photos is top-left but for text it's bottom-right
                    yDelim -= CardSpacing.rowDelta

                pp.print_delimiter(xDelim, yDelim, xDelim - Config.spacing.xIncrement, yDelim - Config.spacing.yIncrement)

            # Check if a new page should be added
            if y < yTopLimit or y > yBottomLimit:
                logger.debug(f"Height limit reached. Adding a new page.")
                y = yInit
                pp.add_page()

    pp.output()
    cv2.destroyAllWindows()

def main():
    parse_args()
    logger.debug(Config.info())

    #imagelist = load_images()

    do()

if __name__ == "__main__":
    main()
