from enum import IntEnum

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

    def __init__(self, mode, order):
        # Y increment
        if mode == PrintMode.TEXT_ONLY:
            self.yIncrement = TextSize.h # Text height
        else:
            self.yIncrement = PhotoSize.h # Photo height

        self.yIncrement += 4 # row spacing

        # X increment
        if mode == PrintMode.PHOTO_ONLY:
            self.xIncrement = PhotoSize.w # Photo width
        elif mode == PrintMode.TEXT_ONLY:
            self.xIncrement = TextSize.w # Text width
        else:
            self.xIncrement = PhotoSize.w + 6 + TextSize.w # Photo width + 6mm space + Text width

        self.xIncrement += 2 # column spacing

        # Set generator direction
        if order == PrintOrder.REVERSED:
            self.xIncrement *= -1
            self.yIncrement *= -1

        self.xLeftLimit = self.xBorder
        self.yTopLimit = self.yBorder
        self.xRightLimit = A4Size.w - self.xBorder - abs(self.xIncrement)
        self.yBottomLimit = A4Size.h - self.yBorder - abs(self.yIncrement)
