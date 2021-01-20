#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from enum import IntEnum
from fpdf import FPDF, set_global

set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(__file__),'fonts'))

logging.basicConfig(filename='/dev/stdout/',
                    format='[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PrintMode(IntEnum):
    PHOTO_ONLY = 1  # Printing only images to normal paper
    TEXT_ONLY = 2   # Printing only descriptions to transparent foil 
    ALL = 3         # Printing everything with classical layout

class A4Size:
    """A4 paper size"""
    w = 210
    h = 297

class PhotoSize:
    """Desired photo size"""
    w = 27
    h = 37

class TextSize:
    """Expected max text block size"""
    w = 46
    h = 40

class CardSpacing:
    """Space between initial coordinations (0,0) of objects of the card (i.e. photo and text)"""
    rowDelta = 8        # space between rows of text
    textDelta = 33      # space between photo and text block
    dateDelta = 31      # space between text column and date column
    dayDelta = 5        # space between parts of the date


class TextDeltas:
    """Distance from initial photo position (0,0)"""
    xName = CardSpacing.textDelta
    yName = CardSpacing.rowDelta

    xNationality = CardSpacing.textDelta
    yNationality = yName + CardSpacing.rowDelta

    xBirthday = CardSpacing.textDelta + CardSpacing.dateDelta
    yBirthday = yNationality

    xFaculty = CardSpacing.textDelta
    yFaculty = yBirthday + CardSpacing.rowDelta

    xSection = CardSpacing.textDelta
    ySection = yFaculty + CardSpacing.rowDelta

    xValidity = CardSpacing.textDelta + CardSpacing.dateDelta
    yValidity = ySection
    

class ContentSpacing:
    """The most efficient spacing based on printing mode selected"""
    xBorder = 5
    yBorder = 5
    xIncrement = 0
    yIncrement = 0

    def __init__(self, mode):
        if mode == PrintMode.PHOTO_ONLY:
            self.xIncrement = PhotoSize.w + (PhotoSize.w >> 3) # Photo width + 12.5% for spacing
            
        elif mode == PrintMode.TEXT_ONLY:
            self.xIncrement = TextSize.w + 2 # + print spacing
        else:
            self.xIncrement = PhotoSize.w + 6 + TextSize.w + 2 # Photo width + 6mm space + Text width + print spacing

        self.yIncrement = PhotoSize.h + (PhotoSize.h >> 3) # Photo height + 12.5% for spacing
    
class Config():
    imgextensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    imgpath = ""
    peoplecsv = ""
    spacing = None
    mode = None

    @staticmethod
    def info():
        return f"imgpath={Config.imgpath}, peoplecsv={Config.peoplecsv}, imgextensions={Config.imgextensions}, spacing:{Config.spacing.xBorder, Config.spacing.yBorder, Config.spacing.xIncrement, Config.spacing.yIncrement}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', default="/tmp/ESNcard/imgs/", help='folder with images to be processed (default: \'/tmp/ESNcard/imgs/\')')
    parser.add_argument('--peoplecsv', default="/tmp/ESNcard/people.csv", help='CSV file with students and their details (default: \'/tmp/ESNcard/people.csv\')')
    parser.add_argument('--mode', type=int, default=f"{PrintMode.TEXT_ONLY}", help=f'Printing mode\n\t{PrintMode.PHOTO_ONLY} - Photo only,\t{PrintMode.TEXT_ONLY} - Text only,\t{PrintMode.ALL} - All (default: {PrintMode.ALL})')

    args, rest = parser.parse_known_args()
    sys.argv = sys.argv[:1] + rest
    
    if args.mode < 1 or args.mode > 3:
        raise ValueError("Invalid mode specified.")

    Config.imgpath = args.imgpath
    Config.peoplecsv = args.peoplecsv
    Config.spacing = ContentSpacing(args.mode)
    Config.mode = args.mode

def load_images():
    try:
        return sorted([fn for fn in os.listdir(Config.imgpath) if fn.endswith(Config.imgextensions)])
    except:
        logger.error(f"Getting images from directory '{Config.imgpath}' failed.")
        sys.exit(1)

def print_person_info(pdf, x, y):
    # By default, TextDeltas count with photo width so substract it in case we are not printing photos
    if Config.mode == PrintMode.TEXT_ONLY:
        x -= PhotoSize.w

    pdf.text(x + TextDeltas.xName, y + TextDeltas.yName, "Name Surname")
    pdf.text(x + TextDeltas.xNationality, y + TextDeltas.yNationality, "Nationality")
    pdf.text(x + TextDeltas.xBirthday, y + TextDeltas.yBirthday, "DD MM YY") # TODO use CardSpacing.dayDelta
    pdf.text(x + TextDeltas.xFaculty, y + TextDeltas.yFaculty, "Faculty")
    pdf.text(x + TextDeltas.xSection, y + TextDeltas.ySection, "Section")
    pdf.text(x + TextDeltas.xValidity, y + TextDeltas.yValidity, "DD MM YY") ## TODO use CardSpacing.dayDelta


def do(imagelist):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_font("NotoSans", style="", fname="NotoSans-Regular.ttf", uni=True)
    pdf.add_font("NotoSans", style="B", fname="NotoSans-Bold.ttf", uni=True)
    pdf.add_font("NotoSans", style="I", fname="NotoSans-Italic.ttf", uni=True)
    pdf.add_font("NotoSans", style="BI", fname="NotoSans-BoldItalic.ttf", uni=True)
    pdf.set_font("NotoSans", size=6)
    
    pdf.add_page()
    
    xBorder = Config.spacing.xBorder
    yBorder = Config.spacing.yBorder
    xIncrement = Config.spacing.xIncrement
    yIncrement = Config.spacing.yIncrement
    x,y,w,h = xBorder, yBorder, PhotoSize.w, PhotoSize.h
    i = 0

    for imgpath in imagelist:
        i += 1
        logger.debug(f"Exporting image ({i}/{len(imagelist)}) {imgpath}")

        if Config.mode != PrintMode.TEXT_ONLY:
            pdf.image(Config.imgpath + imgpath, x, y, w, h)

            # Write name below the image
            xText = x + (PhotoSize.w >> 3)
            yText = y + PhotoSize.h + 2
            pdf.text(xText, yText, imgpath)

        if Config.mode != PrintMode.PHOTO_ONLY:
            print_person_info(pdf, x, y)

        x += xIncrement
        
        # check for need to increment row
        if x >= A4Size.w - xBorder - xIncrement:
            x = xBorder    
            y += yIncrement

        # check if a new page should be added
        if y >= A4Size.h - yBorder - yIncrement:
            logger.debug(f"Height limit reached. Adding a new page.")
            y = yBorder
            pdf.add_page()

    pdf.output("/tmp/ESNcard/images.pdf", "F")

def main():
    parse_args()
    logger.debug(Config.info())

    imagelist = load_images()

    do(imagelist)

if __name__ == "__main__":
    main()