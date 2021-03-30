from enum import Enum

class PrintMode(Enum):
    PHOTO_ONLY = 'photo'  # Printing only images to normal paper
    TEXT_ONLY = 'text'    # Printing only descriptions to transparent foil
    ALL = 'all'           # Printing everything with classical layout

    def __str__(self):
        return self.value

class PrintDirection(Enum):
    NORMAL = 'normal'     # Photos (and text) are being placed from the top to the bottom of the page
    REVERSED = 'reversed' # Photos (and text) are being placed from the bottom to the top

    def __str__(self):
        return self.value

class EqualizeHistMode(Enum):
    CLACHE = 'clache'     # Contrast Limited Adaptive Histogram Equalization
    HEQ_YUV = 'heq_yuv'   # Global Histogram Qqualization - convertion from BRG to YUV
    HEQ_HSV = 'heq_hsv'   # Global Histogram Qqualization - convertion from BRG to HSV
    OTHER = 'other'       # Placeholder

    def __str__(self):
        return self.value


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
    """Space between initial coordinations (0,0) of objects of the card (i.e. photo, text, etc)"""
    rowDelta = 6.8      # space between rows of text
    textDelta = 30      # space between photo and text block
    dateDelta = 33      # space between text column and date column
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
    xBorder = 8         # Border on each side of the page
    yBorder = 8         # Border on the top and the bottom if the page
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
    imgpath = "pictures"
    peoplecsv = "students.csv"
    output = "output-<mode>.pdf"
    mode = PrintMode.ALL
    direction = PrintDirection.NORMAL
    crop = False
    equalizehist = None
    facedetect = False
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
        Config.imgpath = args.imgpath
        Config.peoplecsv = args.peoplecsv
        Config.mode = args.mode

        if hasattr(args, 'output') and args.output is not None:
            Config.output = args.output
        else:
            Config.output = f"output-{Config.mode}.pdf"

        Config.direction = args.direction
        Config.crop = args.crop
        Config.equalizehist = args.equalizehist
        Config.facedetect = args.facedetect
        Config.debug = args.debug

        Config.spacing = ContentSpacing(Config.mode, Config.direction)


