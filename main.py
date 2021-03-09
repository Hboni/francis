from src.view.app import MainWindow
from src.controller.connection import Connector
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    conn = Connector()
    conn.connectViewToModel(win)
    app.exec()
