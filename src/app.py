from src.presenter.presenter import Presenter
from src.view.view import View
from src.model.model import Model
from PyQt5 import QtWidgets
import sys


def main():
    app = QtWidgets.QApplication(sys.argv)

    view = View()
    model = Model()
    Presenter(view, model)

    view.show()
    sys.exit(app.exec())
