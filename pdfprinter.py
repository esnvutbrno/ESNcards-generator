import os
from fpdf import FPDF, set_global

from config import PhotoSize, TextDeltas, CardSpacing, ContentSpacing

set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(__file__),'fonts'))

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
        yText = y + PhotoSize.h + 2 # photo height + spacing (TODO get rid of magic constant)

        self.pdf.set_font_size(6) # TODO get rid of magic constant
        self.pdf.text(xText, yText, pi.name + ", " + pi.before_arrival) # TODO handle too long names

    def print_person_info(self, pi):
        self.pdf.set_font_size(8) # TODO get rid of magic constant

        x = self.xCurrent
        y = self.yCurrent

        self.pdf.text(x + TextDeltas.xName,          y + TextDeltas.yName, pi.name)
        self.pdf.text(x + TextDeltas.xNationality,   y + TextDeltas.yNationality, pi.nationality)
        self.pdf.text(x + TextDeltas.xFaculty,       y + TextDeltas.yFaculty, pi.faculty)
        self.pdf.text(x + TextDeltas.xSection,       y + TextDeltas.ySection, pi.section)

        self.pdf.text(x + TextDeltas.xBirthday,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%d")) # day
        self.pdf.text(x + TextDeltas.xBirthday + CardSpacing.dayDelta,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%m")) # month
        self.pdf.text(x + TextDeltas.xBirthday + 2*CardSpacing.dayDelta,
                      y + TextDeltas.yBirthday,
                      pi.birthday.strftime("%y")) # year

        self.pdf.text(x + TextDeltas.xValidity,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%d")) # day
        self.pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%m")) # month
        self.pdf.text(x + TextDeltas.xValidity + 2*CardSpacing.dayDelta,
                      y + TextDeltas.yValidity,
                      pi.validity.strftime("%y")) # year

    def print_delimiter(self, x, y):
        delimX1 = x - ContentSpacing.xSpacing/2
        delimX2 = delimX1 + ContentSpacing.xSpacing/2
        delimX0 = delimX1 + (delimX2-delimX1)/2
        delimY1 = y - ContentSpacing.ySpacing/3
        delimY2 = delimY1 + ContentSpacing.ySpacing/2
        delimY0 = delimY1 + (delimY2-delimY1)/2

        self.pdf.line(delimX1, delimY0, delimX2, delimY0)
        self.pdf.line(delimX0, delimY1, delimX0, delimY2)

    def output(self):
        self.pdf.output(self.path, "F")

    def add_page(self):
        self.pdf.add_page()