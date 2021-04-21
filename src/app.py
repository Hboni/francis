from src.presenter.presenter import Presenter
from src.view.view import View
from src.model.model import Model
from PyQt5 import QtWidgets
from src import DESIGN_DIR
from src.view import STYLE_SHEET
import sys
import os


def main():
    app = QtWidgets.QApplication(sys.argv)

    # set style sheet
    if STYLE_SHEET:
        with open(os.path.join(DESIGN_DIR, "stylesheet", STYLE_SHEET), "r") as f:
            app.setStyleSheet(f.read())

    view = View()
    model = Model()
    Presenter(view, model)

    view.show()
    sys.exit(app.exec())
