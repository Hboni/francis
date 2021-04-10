import os
from PyQt5 import uic
from src import UI_DIR
from src.controller import modules_fn, MODULES


class Connector:
    def connect_view_to_model(self, window):
        """
        connect the view to the model functions

        Parameters
        ----------
        window: MainWindow

        """
        self.window = window
        self.window.initMenu(MODULES)
        self.window.graph.nodeClicked.connect(self.activate_node)

    def activate_node(self, node):
        """
        apply connection between node widgets and model

        Parameters
        ----------
        node: graph.Node

        """
        t = node.type
        parameters = MODULES[t]

        if node.parameters.itemAt(0) is None:
            widget = uic.loadUi(os.path.join(UI_DIR, parameters['ui']))
            widget.node = node
            node.parameters.addWidget(widget)

            def activate():
                return eval("modules_fn.{}".format(parameters['function']))(widget)

            if t == "load image":
                widget.browse.clicked.connect(lambda: modules_fn.browse_image(widget))
                widget.apply.clicked.connect(activate)
            elif t == "threshold image":
                widget.spin.valueChanged.connect(activate)
                widget.reversed.stateChanged.connect(activate)
                widget.spin.valueChanged.emit(0)
            elif t in ["add images", "substract images", "multiply images", "subdivide images"]:
                widget.reference.currentIndexChanged.connect(activate)
                widget.apply.clicked.connect(activate)
                widget.reference.addItems(modules_fn.get_parent_names(widget))
                if t in ["add images", "multiply images"]:
                    widget.singleValue.stateChanged.connect(widget.reference.setEnabled)
                    widget.singleValue.stateChanged.emit(False)
            elif t in ["erode image", "dilate image"]:
                widget.spin.valueChanged.connect(activate)
                widget.spin.valueChanged.emit(0)
