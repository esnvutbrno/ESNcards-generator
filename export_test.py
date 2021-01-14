#!/bin/python3

import argparse
import logging
import os
import sys

from fpdf import FPDF

logging.basicConfig(filename='/dev/stdout/',
                    format='%(asctime)s %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class A4:
    """A4 Paper Size in mm"""
    width = 210
    height = 297

class Config:
    imgpath = ""
    peoplecsv = ""
    imgextensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')

    @staticmethod
    def __str__():
        return f"imgpath={Config.imgpath}, peoplecsv={Config.peoplecsv}, imgextensions={Config.imgextensions}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', default="/tmp/ESNcard/imgs/", help='folder with images to be processed (default: \'/tmp/ESNcard/imgs/\')')
    parser.add_argument('--peoplecsv', default="/tmp/ESNcard/people.csv", help='CSV file with students and their details (default: \'/tmp/ESNcard/people.csv\')')

    args, rest = parser.parse_known_args()
    sys.argv = sys.argv[:1] + rest
    
    Config.imgpath = args.imgpath
    Config.peoplecsv = args.peoplecsv

def load_images():
    try:
        return sorted([fn for fn in os.listdir(Config.imgpath) if fn.endswith(Config.imgextensions)])
    except:
        logger.error(f"Getting images from directory '{Config.imgpath}' failed.")
        sys.exit(1)

def do(imagelist):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()

    xInit = 10
    yInit = 10
    xIncrement = 0x7D
    yIncremet = 40

    x,y,w,h = xInit,yInit,27,37

    for image in imagelist:
        logger.debug(f"Exporting image {image}")
        pdf.image(Config.imgpath + image, x, y, w, h)

        x ^= xIncrement # switch between xInit and middle of the page

        # time to increment row
        if x == xInit:
            y += yIncremet
        # check if new page should be added
        if y > A4.height - yIncremet:
            logger.debug(f"Height limit reached. Adding a new page.")
            x,y = xInit,yInit
            pdf.add_page()

    pdf.output("/tmp/ESNcard/images.pdf", "F")

def main():
    parse_args()

    imagelist = load_images()

    do(imagelist)

if __name__ == "__main__":
    main()