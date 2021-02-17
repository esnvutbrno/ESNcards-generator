#!/usr/bin/env python3

import argparse
import csv
import logging
import os
import re
import sys

from datetime import date

from pdfprinter import PDFPrinter
from common import PrintMode, PrintOrder, CardSpacing, ContentSpacing

logging.basicConfig(filename='/dev/stdout/',
                    format='[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


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

    def parse(self, row):
        self.name = row["name"]
        self.nationality = row["country"]
        self.birthday = date(int("20" + row["Y0"] + row["Y1"]), int(row["M0"] + row["M1"]), int(row["D0"] + row["D1"]))       # FIXME fix the dirty year hack (20xx)
        self.validity = date(int("20" + row["TY0"] + row["TY1"]), int(row["TM0"] + row["TM1"]), int(row["TD0"] + row["TD1"])) # FIXME fix the dirty year hack (20xx)


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

def do():
    # TODO try-catch
    pp = PDFPrinter(Config.output)

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
            pi.parse(row)

            logger.debug(f"Exporting ({i}/{rows}) {pi.name}")

            if Config.mode != PrintMode.TEXT_ONLY:
                foundImgs = [f for f in os.listdir(Config.imgpath) if re.match(rf"{pi.name}.*", f) and any(f.endswith(ext) for ext in Config.imgextensions)]
                logger.debug(f"Matched photos: {foundImgs}") # TODO allow user to choose one

                pp.set_coordintates(x, y)
                pp.print_photo(Config.imgpath + foundImgs[0], pi.name)

            if Config.mode != PrintMode.PHOTO_ONLY:
                xText, yText = x, y

                # If we print both photo and text, move init position of text next to the photo
                if Config.mode != PrintMode.TEXT_ONLY:
                    xText += CardSpacing.textDelta
                    yText += CardSpacing.rowDelta

                pp.set_coordintates(xText, yText)
                pp.print_person_info(pi)

            x += xIncrement

            # check for need to increment/decrement row
            if x < xLeftLimit or x > xRightLimit:
                x = xInit
                y += yIncrement

            # check if a new page should be added
            if y < yTopLimit or y > yBottomLimit:
                logger.debug(f"Height limit reached. Adding a new page.")
                y = yInit
                pp.add_page()

    pp.output()

def main():
    parse_args()
    logger.debug(Config.info())

    #imagelist = load_images()

    do()

if __name__ == "__main__":
    main()
