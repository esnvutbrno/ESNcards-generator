import os
from enum import Enum
from fpdf import FPDF, set_global

from config import PhotoSize, TextDeltas, CardSpacing, Config

set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(__file__), 'fonts'))


class DelimiterStyle(Enum):
    CROSS = 'cross'
    FRAME = 'frame'

    def __str__(self):
        return self.value


class PDFPrinter:
    xCurrent = 0
    yCurrent = 0

    def __init__(self, path):
        self.path = path

        self.pdf = FPDF('P', 'mm', 'A4')
        self.page_setup()

    def page_setup(self):
        self.pdf.add_font("NotoSans", style="", fname="NotoSans-Regular.ttf", uni=True)
        self.pdf.add_font("NotoSans", style="B", fname="NotoSans-Bold.ttf", uni=True)
        self.pdf.add_font("NotoSans", style="I", fname="NotoSans-Italic.ttf", uni=True)
        self.pdf.add_font("NotoSans", style="BI", fname="NotoSans-BoldItalic.ttf", uni=True)
        self.pdf.set_font("NotoSans", size=8)

        self.pdf.add_page()

    def set_coordintates(self, x, y):
        self.xCurrent = x
        self.yCurrent = y

    def print_photo(self, img, pi):
        x = self.xCurrent
        y = self.yCurrent

        self.pdf.image(img, x, y, PhotoSize.w, PhotoSize.h)

        # Write name below the image
        xText = x
        yText = y + PhotoSize.h + 2  # photo height + spacing (TODO get rid of magic constant)

        self.pdf.set_font_size(6)  # TODO get rid of magic constant
        self.pdf.text(xText, yText, f'{pi.nationality}: {pi.name}')  # + "," + pi.before_arrival)

    def print_person_info(self, pi):
        self.pdf.set_font_size(8)  # TODO get rid of magic constant

        x = self.xCurrent
        y = self.yCurrent

        self.pdf.text(x + TextDeltas.xName, y + TextDeltas.yName, pi.name)
        self.pdf.text(x + TextDeltas.xNationality, y + TextDeltas.yNationality, pi.nationality)
        self.pdf.text(x + TextDeltas.xFaculty, y + TextDeltas.yFaculty, pi.faculty)
        self.pdf.text(x + TextDeltas.xSection, y + TextDeltas.ySection, pi.section)

        self.pdf.text(x + TextDeltas.xBirthday,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%d"))  # day
        self.pdf.text(x + TextDeltas.xBirthday + CardSpacing.dayDelta,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%m"))  # month
        self.pdf.text(x + TextDeltas.xBirthday + 2 * CardSpacing.dayDelta,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%y"))  # year

        self.pdf.text(x + TextDeltas.xValidity,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%d"))  # day
        self.pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%m"))  # month
        self.pdf.text(x + TextDeltas.xValidity + 2 * CardSpacing.dayDelta,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%y"))  # year

    def __print_cross(self, x, y):
        delimX1 = x - Config.spacing.xSpacing / 3.0
        delimX2 = x + Config.spacing.xSpacing / 3.0

        delimY1 = y - Config.spacing.ySpacing / 3.0
        delimY2 = y + Config.spacing.ySpacing / 3.0

        self.pdf.line(delimX1, y, delimX2, y)
        self.pdf.line(x, delimY1, x, delimY2)

    def __print_frame(self, x, y):
        """ We rely on coordinates being top-left. Disgusting, I know..."""
        # Add abs() value so it always goes down-right direction no matter what printing direction is set
        delimX1 = x + abs(Config.spacing.xIncrement)
        delimY1 = y + abs(Config.spacing.yIncrement)

        self.pdf.dashed_line(delimX1, y, x, y)
        self.pdf.dashed_line(x, delimY1, x, y)

    def print_delimiter(self, x, y, style):
        if not isinstance(style, DelimiterStyle):
            raise TypeError("Wrong delimiter style!")

        if style == DelimiterStyle.CROSS:
            self.__print_cross(x, y)
        elif style == DelimiterStyle.FRAME:
            self.__print_frame(x, y)

    def output(self):
        self.pdf.output(self.path, "F")

    def add_page(self):
        self.pdf.add_page()
