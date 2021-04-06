from PyQt5 import QtWidgets, uic, QtGui
from src.view.graph import Graph
from src import UI_DIR, CONFIG_DIR, utils
import mergedeep
import os
import json


class MainWindow(QtWidgets.QMainWindow):
    """
    main window where widgets and menu are displayed
    """
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_DIR, "Home.ui"), self)
        self.settings = {}
        self.initUI()

    def initUI(self):
        """
        initialize graph and basic connections/shortcuts
        """
        self.initModules()
        self.graph = Graph(self, 'horizontal')
        self.graph.nodeClicked.connect(self.showHideParameters)
        self.setCentralWidget(self.graph)

        save_sc = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        save_sc.activated.connect(self.guisave)

        restore_sc = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+R'), self)
        restore_sc.activated.connect(self.guirestore)

    def initModules(self):
        """
        load json to create module and right-clic menu
        """
        # load modules settings
        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), 'rb'))
        # initalize right-clic-menu
        self.menu = {}
        for k, values in self.modules.items():
            lst = [values['type']]
            if 'menu' in values:
                lst += values['menu'].split('/')
            lst.append(k)
            self.menu = mergedeep.merge(self.menu, utils.dict_from_list(lst))

    def guirestore(self):
        """
        restore graph architecture and node settings
        """
        # restore graph architecture
        graph_settings_path = os.path.join(CONFIG_DIR, 'graph.json')
        if os.path.isfile(graph_settings_path):
            with open(graph_settings_path, 'r') as infile:
                settings = json.load(infile)
                self.graph.restoreGraph(settings)

    def guisave(self):
        """
        save graph architecture and node settings
        """
        # save graph architecture
        with open(os.path.join(CONFIG_DIR, 'graph.json'), 'w') as outfile:
            json.dump(self.graph.settings, outfile, sort_keys=False, indent=4)

    def showHideParameters(self, node):
        """
        show or hide node parameters

        Parameters
        ----------
        node: graph.Node
            the node from Graph that contains parameters
        """
        if node.parameters.itemAt(0) is not None:
            widget = node.parameters.itemAt(0).widget()
            if widget.isHidden():
                widget.show()
            else:
                widget.hide()
