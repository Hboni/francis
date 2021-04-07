from src.view.app import MainWindow
from src.controller.connection import Connector
from PyQt5 import QtWidgets
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    conn = Connector()
    conn.connect_view_to_model(win)
    app.exec()
