#!/usr/bin/env python3

import argparse
import csv
import logging
import os
import re
import sys

from datetime import date
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

class PrintOrder(IntEnum):
    NORMAL = 1     # Photos (and text) are being placed from the top to the bottom of the page
    REVERSED = 2   # Photos (and text) are being placed from the bottom to the top

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
    h = 25

class CardSpacing:
    """Space between initial coordinations (0,0) of objects of the card (i.e. photo and text)"""
    rowDelta = 6.7      # space between rows of text
    textDelta = 33      # space between photo and text block
    dateDelta = 32      # space between text column and date column
    dayDelta = 5.5      # space between parts of the date

class TextDeltas:
    """Distances from initial photo position (0,0)"""
    xName = 0
    yName = 0

    xNationality = xName
    yNationality = yName + CardSpacing.rowDelta

    xBirthday = xNationality + CardSpacing.dateDelta
    yBirthday = yNationality

    xFaculty = xName
    yFaculty = yBirthday + CardSpacing.rowDelta

    xSection = xName
    ySection = yFaculty + CardSpacing.rowDelta

    xValidity = xSection + CardSpacing.dateDelta
    yValidity = ySection

class ContentSpacing:
    """The most efficient spacing based on printing mode selected"""
    xLeftLimit = 0      # Topmost X coordinate
    yTopLimit = 0       # Topmost Y coordinate
    xRightLimit = 0     # Lowermost possible X coordinate
    yBottomLimit = 0    # Lowermost possible Y coordinate
    xBorder = 5         # Border on each side of the page
    yBorder = 5         # Border on the top and the bottom if the page
    xIncrement = 0
    yIncrement = 0

    def __init__(self, mode, order):
        if mode == PrintMode.PHOTO_ONLY:
            self.xIncrement = PhotoSize.w + (PhotoSize.w >> 3) # Photo width + 12.5% for spacing
            self.yIncrement = PhotoSize.h + (PhotoSize.h >> 3) # Photo height + 12.5% for spacing

        elif mode == PrintMode.TEXT_ONLY:
            self.xIncrement = TextSize.w + 2 # Text width + print spacing
            self.yIncrement = TextSize.h + 4 # Text height + print spacing
        else:
            self.xIncrement = PhotoSize.w + 6 + TextSize.w + 2 # Photo width + 6mm space + Text width + print spacing
            self.yIncrement = PhotoSize.h + (PhotoSize.h >> 3) # Photo height + 12.5% for spacing

        if order == PrintOrder.REVERSED:
            self.xIncrement *= -1
            self.yIncrement *= -1

        self.xLeftLimit = self.xBorder
        self.yTopLimit = self.yBorder
        self.xRightLimit = A4Size.w - self.xBorder - abs(self.xIncrement)
        self.yBottomLimit = A4Size.h - self.yBorder - abs(self.yIncrement)

class Config:
    imgextensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    imgpath = "/tmp/ESNcard/imgs/"
    peoplecsv = "/tmp/ESNcard/people.csv"
    output = "/tmp/ESNcard/images.pdf"
    spacing = None
    mode = PrintMode.ALL
    order = PrintOrder.NORMAL

    @staticmethod
    def info():
        return f"imgpath={Config.imgpath}, peoplecsv={Config.peoplecsv}, output={Config.output}, imgextensions={Config.imgextensions}, mode: {Config.mode}, order: {Config.order}, spacing:{Config.spacing.xBorder, Config.spacing.yBorder, Config.spacing.xIncrement, Config.spacing.yIncrement}"

class PersonInfo:
    name = ""
    nationality = ""
    birthday = None
    faculty = "VUT Brno"
    section = "ESN VUT Brno"
    validity = None

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgpath', help=f'folder with images to be processed (default: \'{Config.imgpath}\')')
    parser.add_argument('--peoplecsv', help=f'CSV file with students and their details (default: \'{Config.peoplecsv}\')')
    parser.add_argument('--output', help=f'Output file (default: \'{Config.output}\')')
    parser.add_argument('--mode', type=int, help=f'Printing mode\n\t{PrintMode.PHOTO_ONLY} - Photo only,\t{PrintMode.TEXT_ONLY} - Text only,\t{PrintMode.ALL} - All (default: {Config.mode})')
    parser.add_argument('--order', type=int, help=f'Printing order\n\t{PrintOrder.NORMAL} - TOP -> BOTTOM,\t{PrintOrder.REVERSED} - BOTTOM -> TOP (default: {Config.order})')

    args, rest = parser.parse_known_args()
    sys.argv = sys.argv[:1] + rest

    if args.mode < 1 or args.mode > 3:
        raise ValueError("Invalid mode specified.")

    if args.imgpath is not None:
        Config.imgpath = args.imgpath + "/"

    if args.peoplecsv is not None:
        Config.peoplecsv = args.peoplecsv

    if args.output is not None:
        Config.output = args.output

    if args.mode is not None:
        Config.mode = args.mode

    if args.order is not None:
        Config.order = args.order

    Config.spacing = ContentSpacing(Config.mode, Config.order)

def load_images():
    try:
        return sorted([fn for fn in os.listdir(Config.imgpath) if fn.endswith(Config.imgextensions)])
    except:
        logger.error(f"Getting images from directory '{Config.imgpath}' failed.")
        sys.exit(1)

def print_person_info(pdf, x, y, pi):
    pdf.set_font_size(8)

    pdf.text(x + TextDeltas.xName,          y + TextDeltas.yName, pi.name)
    pdf.text(x + TextDeltas.xNationality,   y + TextDeltas.yNationality, pi.nationality)
    pdf.text(x + TextDeltas.xFaculty,       y + TextDeltas.yFaculty, pi.faculty)
    pdf.text(x + TextDeltas.xSection,       y + TextDeltas.ySection, pi.section)

    pdf.text(x + TextDeltas.xBirthday,
             y + TextDeltas.yBirthday,
             pi.birthday.strftime("%d")) # day
    pdf.text(x + TextDeltas.xBirthday + CardSpacing.dayDelta,
             y + TextDeltas.yBirthday,
             pi.birthday.strftime("%m")) # month
    pdf.text(x + TextDeltas.xBirthday + CardSpacing.dayDelta + CardSpacing.dayDelta,
             y + TextDeltas.yBirthday,
             pi.birthday.strftime("%y")) # year

    pdf.text(x + TextDeltas.xValidity,
             y + TextDeltas.yValidity,
             pi.validity.strftime("%d")) # day
    pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta,
             y + TextDeltas.yValidity,
             pi.validity.strftime("%m")) # month
    pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta + CardSpacing.dayDelta,
             y + TextDeltas.yValidity,
             pi.validity.strftime("%y")) # year

def page_setup(pdf):
    pdf.add_font("NotoSans", style="", fname="NotoSans-Regular.ttf", uni=True)
    pdf.add_font("NotoSans", style="B", fname="NotoSans-Bold.ttf", uni=True)
    pdf.add_font("NotoSans", style="I", fname="NotoSans-Italic.ttf", uni=True)
    pdf.add_font("NotoSans", style="BI", fname="NotoSans-BoldItalic.ttf", uni=True)
    pdf.set_font("NotoSans", size=8)

    pdf.add_page()

def do():
    # TODO try-catch
    pdf = FPDF('P', 'mm', 'A4')
    page_setup(pdf)

    xLeftLimit = Config.spacing.xLeftLimit
    yTopLimit = Config.spacing.yTopLimit
    xRightLimit = Config.spacing.xRightLimit
    yBottomLimit = Config.spacing.yBottomLimit
    xIncrement = Config.spacing.xIncrement
    yIncrement = Config.spacing.yIncrement

    if Config.order == PrintOrder.NORMAL:
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
        for row in reader:
            i += 1

            pi = PersonInfo()
            pi.name = row["name"]
            pi.nationality = row["country"]
            pi.birthday = date(int("20" + row["Y0"] + row["Y1"]), int(row["M0"] + row["M1"]), int(row["D0"] + row["D1"]))       # FIXME fix the dirty year hack (20xx)
            pi.validity = date(int("20" + row["TY0"] + row["TY1"]), int(row["TM0"] + row["TM1"]), int(row["TD0"] + row["TD1"])) # FIXME fix the dirty year hack (20xx)

            logger.debug(f"Exporting ({i}/{rows}) {pi.name}")

            if Config.mode != PrintMode.TEXT_ONLY:
                foundImgs = [f for f in os.listdir(Config.imgpath) if re.match(rf"{pi.name}.*", f) and any(f.endswith(ext) for ext in Config.imgextensions)]
                logger.debug(f"Matched photos: {foundImgs}")

                pdf.image(Config.imgpath + foundImgs[0], x, y, PhotoSize.w, PhotoSize.h)

                # Write name below the image
                xText = x
                yText = y + PhotoSize.h + 2 # photo height + spacing

                pdf.set_font_size(6)
                pdf.text(xText, yText, pi.name)

            if Config.mode != PrintMode.PHOTO_ONLY:
                xText, yText = x, y

                # If we print both photo and text, move init position of text next to the photo
                if Config.mode != PrintMode.TEXT_ONLY:
                    xText += CardSpacing.textDelta
                    yText += CardSpacing.rowDelta

                print_person_info(pdf, xText, yText, pi)

            x += xIncrement

            # check for need to increment/decrement row
            if x < xLeftLimit or x > xRightLimit:
                x = xInit
                y += yIncrement

            # check if a new page should be added
            if y < yTopLimit or y > yBottomLimit:
                logger.debug(f"Height limit reached. Adding a new page.")
                y = yInit
                pdf.add_page()

    pdf.output(Config.output, "F")

def main():
    parse_args()
    logger.debug(Config.info())

    #imagelist = load_images()

    do()

if __name__ == "__main__":
    main()
