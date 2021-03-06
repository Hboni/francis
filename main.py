from src.app import MainWindow
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec()
