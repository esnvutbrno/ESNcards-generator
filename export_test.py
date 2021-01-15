#!/bin/python3

import argparse
import logging
import os
import sys

from enum import IntEnum
from fpdf import FPDF


logging.basicConfig(filename='/dev/stdout/',
                    format='[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PrintMode(IntEnum):
    PHOTO_ONLY = 1  # Printing only images to normal paper
    TEXT_ONLY = 2   # Printing only descriptions to transparent foil 
    ALL = 3         # Printing everything with classical layout

class A4:
    """A4 paper size in mm"""
    w = 210
    h = 297

class PhotoSize:
    """Desired photo size in mm"""
    w = 27
    h = 37

class TextSize:
    """Expected text block size in mm"""
    w = 46
    h = 40

class Spacing:
    """The most efficient spacing based on printing mode selected"""
    xInit = 10
    yInit = 10
    xIncrement = 0
    yIncrement = 0

    def __init__(self, mode):
        if mode == PrintMode.PHOTO_ONLY:
            self.xIncrement = PhotoSize.w + (PhotoSize.w >> 3) # Photo width + 12.5% for spacing
            
        elif mode == PrintMode.TEXT_ONLY:
            self.xIncrement = A4.w / 2
        else:
            self.xIncrement = PhotoSize.w + 6 + TextSize.w + 6

        self.yIncrement = PhotoSize.h + (PhotoSize.h >> 3) # Photo height + 12.5% for spacing
    
class Config():
    imgextensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    imgpath = ""
    peoplecsv = ""
    spacing = None

    @staticmethod
    def info():
        return f"imgpath={Config.imgpath}, peoplecsv={Config.peoplecsv}, imgextensions={Config.imgextensions}, spacing:{Config.spacing.xInit, Config.spacing.yInit, Config.spacing.xIncrement, Config.spacing.yIncrement}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', default="/tmp/ESNcard/imgs/", help='folder with images to be processed (default: \'/tmp/ESNcard/imgs/\')')
    parser.add_argument('--peoplecsv', default="/tmp/ESNcard/people.csv", help='CSV file with students and their details (default: \'/tmp/ESNcard/people.csv\')')
    parser.add_argument('--mode', type=int, default=f"{PrintMode.PHOTO_ONLY}", help=f'Printing mode\n\t{PrintMode.PHOTO_ONLY} - Photo only\n\t{PrintMode.TEXT_ONLY} - Text only\n\t{PrintMode.ALL} - All (default: {PrintMode.ALL})')

    args, rest = parser.parse_known_args()
    sys.argv = sys.argv[:1] + rest
    
    if args.mode < 1 or args.mode > 3:
        raise ValueError("Invalid mode specified.")

    Config.imgpath = args.imgpath
    Config.peoplecsv = args.peoplecsv
    Config.spacing = Spacing(args.mode)

def load_images():
    try:
        return sorted([fn for fn in os.listdir(Config.imgpath) if fn.endswith(Config.imgextensions)])
    except:
        logger.error(f"Getting images from directory '{Config.imgpath}' failed.")
        sys.exit(1)

def do(imagelist):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    xInit = Config.spacing.xInit
    yInit = Config.spacing.yInit
    xIncrement = Config.spacing.xIncrement
    yIncrement = Config.spacing.xIncrement
    x,y,w,h = xInit, yInit, PhotoSize.w, PhotoSize.h
    i = 0

    for image in imagelist:
        i += 1
        logger.debug(f"Exporting image ({i}/{len(imagelist)}) {image}")
        pdf.image(Config.imgpath + image, x, y, w, h)

        x += xIncrement
        
        # check for need to increment row
        if x >= A4.w - xInit - xIncrement:
            x = xInit    
            y += yIncrement

        # check if a new page should be added
        if y >= A4.h - yInit - yIncrement:
            logger.debug(f"Height limit reached. Adding a new page.")
            y = yInit
            pdf.add_page()

    pdf.output("/tmp/ESNcard/images.pdf", "F")

def main():
    parse_args()
    logger.debug(Config.info())

    imagelist = load_images()

    do(imagelist)

if __name__ == "__main__":
    main()