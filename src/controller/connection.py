import os
from PyQt5 import uic
from src import UI_DIR, CONFIG_DIR
from src.controller import modules_fn
import json


class Connector:
    def connect_view_to_model(self, window):
        """
        connect the view to the model functions

        Parameters
        ----------
        window: MainWindow

        """
        self.window = window
        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), "rb"))
        self.window.initMenu(self.modules)
        self.window.graph.nodeClicked.connect(self.activate_node)

    def activate_node(self, node):
        """
        apply connection between node widgets and model

        Parameters
        ----------
        node: graph.Node

        """
        t = node.type
        parameters = self.modules[t]

        if node.parameters.itemAt(0) is None:
            widget = uic.loadUi(os.path.join(UI_DIR, parameters['ui']))
            widget.node = node
            node.parameters.addWidget(widget)

            def activate():
                return eval("modules_fn.{}".format(parameters['function']))(widget)

            if t == "threshold image":
                widget.spin.valueChanged.connect(activate)
                widget.reversed.stateChanged.connect(activate)
                widget.spin.valueChanged.emit(0)

            else:
                widget.apply.clicked.connect(activate)

                if t == "load image":
                    widget.browse.clicked.connect(lambda: modules_fn.browse_image(widget))

                elif t == "save image":
                    widget.browse.clicked.connect(lambda: modules_fn.browse_savepath(widget))

                elif t == "operation between images":
                    for rb in [widget.add, widget.multiply]:
                        rb.clicked.connect(lambda: widget.reference.setEnabled(False))
                    for rb in [widget.divide, widget.subtract]:
                        rb.clicked.connect(lambda: widget.reference.setEnabled(True))
                    widget.add.clicked.emit()

                    # rename parent name inside reference combobox
                    widget.reference.addItems(modules_fn.get_parent_names(widget))

                    def updateParentName(name, new_name):
                        current_index = widget.reference.currentIndex()
                        ind = widget.reference.findText(name)
                        widget.reference.removeItem(ind)
                        widget.reference.insertItem(ind, new_name)
                        widget.reference.setCurrentIndex(current_index)
                    for parent in widget.node.parents:
                        parent.nameChanged.connect(updateParentName)
