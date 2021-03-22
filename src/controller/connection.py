import os
from PyQt5 import QtWidgets, uic
from src import UI_DIR
from src.controller import modules_fn
modules_fn  # avoid pre-commit to fail, modules_fn is used inside eval()


class Connector:
    def connectViewToModel(self, window):
        """
        connect the view to the model functions

        Parameters
        ----------
        window: MainWindow

        """
        self.window = window
        self.window.graph.nodeClicked.connect(self.activateNode)

    def activateNode(self, node):
        """
        apply connection between node widgets and model

        Parameters
        ----------
        node: graph.Node

        """
        parameters = self.window.modules[node.type]

        if node.parameters.itemAt(0) is None:
            widget = uic.loadUi(os.path.join(UI_DIR, parameters['ui']))
            widget.node = node

            # connect buttons to functions
            def conn(w, function):
                w = widget.__dict__[w]
                if isinstance(w, (QtWidgets.QPushButton, QtWidgets.QToolButton)):
                    w.clicked.connect(lambda: eval(function)(widget))
                elif isinstance(w, (QtWidgets.QSpinBox)):
                    w.valueChanged.connect(lambda: eval(function)(widget))
                elif isinstance(w, (QtWidgets.QCheckBox)):
                    w.stateChanged.connect(lambda: eval(function)(widget))
            for b, f in parameters["connection"].items():
                conn(b, f)

            # start functions
            if "start" in parameters.keys():
                eval(parameters['start'])
            node.parameters.addWidget(widget)
