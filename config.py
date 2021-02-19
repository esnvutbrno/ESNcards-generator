from enum import IntEnum

class PrintMode(IntEnum):
    PHOTO_ONLY = 1  # Printing only images to normal paper
    TEXT_ONLY = 2   # Printing only descriptions to transparent foil
    ALL = 3         # Printing everything with classical layout

class PrintDirection(IntEnum):
    NORMAL = 1     # Photos (and text) are being placed from the top to the bottom of the page
    REVERSED = 2   # Photos (and text) are being placed from the bottom to the top

class EqualizeHistMode(IntEnum):
    CLACHE = 1     # Contrast Limited Adaptive Histogram Equalization
    HEQ_YUV = 2    # Global Histogram Qqualization - convertion from BRG to YUV
    HEQ_HSV = 3    # Global Histogram Qqualization - convertion from BRG to HSV
    OTHER = 4


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
    textDelta = 30      # space between photo and text block
    dateDelta = 35      # space between text column and date column
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

    xSpacing = 2        # Space between cards on the paper
    ySpacing = 4        # Space between cards on the papier
    photoTextSpacing = 6# Space between right side of the photo and text.

    def __init__(self, mode, order):
        # Y increment
        if mode == PrintMode.TEXT_ONLY:
            self.yIncrement = TextSize.h # Text height
        else:
            self.yIncrement = PhotoSize.h # Photo height

        self.yIncrement += self.ySpacing

        # X increment
        if mode == PrintMode.PHOTO_ONLY:
            self.xIncrement = PhotoSize.w # Photo width
        elif mode == PrintMode.TEXT_ONLY:
            self.xIncrement = TextSize.w # Text width
        else:
            self.xIncrement = PhotoSize.w + self.photoTextSpacing + TextSize.w

        self.xIncrement += self.xSpacing

        # Set generator direction
        if order == PrintDirection.REVERSED:
            self.xIncrement *= -1
            self.yIncrement *= -1

        self.xLeftLimit = self.xBorder
        self.yTopLimit = self.yBorder
        self.xRightLimit = A4Size.w - self.xBorder - abs(self.xIncrement)
        self.yBottomLimit = A4Size.h - self.yBorder - abs(self.yIncrement)

class Config:
    imgextensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    spacing = None
    imgpath = "./pictures/"
    peoplecsv = "./students.csv"
    output = "./output-<mode>.pdf"
    mode = PrintMode.ALL
    direction = PrintDirection.NORMAL
    crop = False
    equalizehist = None
    facedetect = True
    debug = False

    @staticmethod
    def info():
        return f"""Configuration:
                    imgextensions={Config.imgextensions},
                    spacing:{Config.spacing.xBorder, Config.spacing.yBorder, Config.spacing.xIncrement, Config.spacing.yIncrement},
                    imgpath: {Config.imgpath},
                    peoplecsv: {Config.peoplecsv},
                    output: {Config.output},
                    mode: {Config.mode},
                    direction: {Config.direction},
                    crop: {Config.crop},
                    equalizehist: {Config.equalizehist},
                    facedetect: {Config.facedetect},
                    debug: {Config.debug}"""

    @staticmethod
    def setup(args):
        if args.imgpath is not None:
            Config.imgpath = args.imgpath + "/"

        if args.peoplecsv is not None:
            Config.peoplecsv = args.peoplecsv

        if args.mode is not None:
            if args.mode < PrintMode.PHOTO_ONLY or args.mode > PrintMode.ALL:
                raise ValueError("Invalid print mode specified.")

            Config.mode = args.mode

        if args.output is not None:
            Config.output = args.output
        else:
            Config.output = f"./output-{Config.mode}.pdf"

        if args.direction is not None:
            Config.direction = args.direction

        if args.crop is not None:
            Config.crop = args.crop

        if args.equalizehist is not None:
            if args.equalizehist < EqualizeHistMode.CLACHE or args.equalizehist > EqualizeHistMode.OTHER:
                raise ValueError("Invalid equalizehist mode specified.")

            Config.equalizehist = args.equalizehist

        if args.facedetect is not None:
            Config.facedetect = args.facedetect

        if args.debug is not None:
            Config.debug = args.debug

        Config.spacing = ContentSpacing(Config.mode, Config.direction)


