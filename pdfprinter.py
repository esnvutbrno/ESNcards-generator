import os
from fpdf import FPDF, set_global

from common import PhotoSize, TextDeltas, CardSpacing

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

    def print_photo(self, img, name):
        x = self.xCurrent
        y = self.yCurrent

        self.pdf.image(img, x, y, PhotoSize.w, PhotoSize.h)

        # Write name below the image
        xText = x
        yText = y + PhotoSize.h + 2 # photo height + spacing

        self.pdf.set_font_size(6)
        self.pdf.text(xText, yText, name)

    def print_person_info(self, pi):
        self.pdf.set_font_size(8)

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
        self.pdf.text(x + TextDeltas.xBirthday + CardSpacing.dayDelta + CardSpacing.dayDelta,
                y + TextDeltas.yBirthday,
                pi.birthday.strftime("%y")) # year

        self.pdf.text(x + TextDeltas.xValidity,
                y + TextDeltas.yValidity,
                pi.validity.strftime("%d")) # day
        self.pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta,
                y + TextDeltas.yValidity,
                pi.validity.strftime("%m")) # month
        self.pdf.text(x + TextDeltas.xValidity + CardSpacing.dayDelta + CardSpacing.dayDelta,
                y + TextDeltas.yValidity,
                pi.validity.strftime("%y")) # year

    def output(self):
        self.pdf.output(self.path, "F")

    def add_page(self):
        self.pdf.add_page()