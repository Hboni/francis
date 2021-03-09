from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src.view.graph import Graph
from src import MAIN_DIR, UI_DIR, DATA_DIR, CONFIG_DIR
import sys
import os
import json


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_DIR, "Home.ui"), self)
        self.settings = {}
        self.initUI()

    def initUI(self):
        self.initModules()
        self.graph = Graph(self)
        self.graph.addNode("load image")
        self.graph.nodeClicked.connect(self.showHideParameters)
        self.setCentralWidget(self.graph)

    def initModules(self):
        # load modules settings
        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), 'rb'))
        # initalize right-clic-menu
        self.menu = {}
        for k, values in self.modules.items():
            v = values['type']
            if v not in self.menu.keys():
                self.menu[v] = [k]
            else:
                self.menu[v].append(k)


    def restoreSettings(self, widget):
        name = widget.name.text()
        if name not in self.settings.keys():
            return
        for k, v in self.settings[name]:
            print(k, v)

    def storeSettings(self, widget):
        name = widget.name.text()
        self.settings[name] = {}

    def showHideParameters(self, node):
        if node.parameters.itemAt(0) is not None:
            widget = node.parameters.itemAt(0).widget()
            if widget.isHidden():
                widget.show()
            else:
                widget.hide()
