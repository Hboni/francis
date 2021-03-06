from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src.graph import Graph
from src import modules_fn
from src import MAIN_DIR, UI_DIR, DATA_DIR
import sys
import os
import json


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_DIR, "Home.ui"), self)
        self.graph = Graph(self)
        self.setCentralWidget(self.graph)
        self.initModules()
        self.graph.nodeClicked.connect(self.activateNode)
        self.settings = {}

    def initModules(self):
        # load modules settings
        self.modules = json.load(open(os.path.join(MAIN_DIR, "modules.json"), 'rb'))
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



    def activateNode(self, node):
        parameters = self.modules[node.type]
        widget = uic.loadUi(os.path.join(UI_DIR, parameters['ui']))
        widget.name.setText(node.name)
        widget.type.setText(node.type)
        widget.node = node

        # connect buttons to functions
        def conn(w, function):
            w = widget.__dict__[w]
            if isinstance(w, QtWidgets.QPushButton):
                w.clicked.connect(lambda: eval(function)(widget))
            elif isinstance(w, (QtWidgets.QDial, QtWidgets.QSpinBox)):
                w.valueChanged.connect(lambda: eval(function)(widget))

        for b, f in parameters["connection"].items():
            conn(b, f)

        # restore widget settings
        self.restoreSettings(widget)

        # add widget to window
        win = QtWidgets.QMainWindow(self)
        win.setCentralWidget(widget)
        win.show()
