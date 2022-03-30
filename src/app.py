import sys

from PyQt5 import QtWidgets

from src.model.model import Model
from src.presenter.presenter import Presenter
from src.view.view import View


def main():
    """
    this function initialize the application and the MVP app design

    """
    app = QtWidgets.QApplication(sys.argv)

    # UI
    view = View()
    # background processes
    model = Model()
    # bridge between processes and UI
    Presenter(view, model)

    # open session
    view.show()
    app.exec()
