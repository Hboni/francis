from PyQt5 import QtWidgets, uic, QtGui
from src.view.graph import Graph
from src import UI_DIR, CONFIG_DIR, utils, DESIGN_DIR
from src.view import STYLE_SHEETS
import json
import os


class View(QtWidgets.QMainWindow):
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
        self.graph = Graph(self, 'horizontal')
        self.graph.nodeClicked.connect(self.showHideParameters)
        self.setCentralWidget(self.graph)

        save_sc = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        save_sc.activated.connect(self.guisave)

        restore_sc = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+R'), self)
        restore_sc.activated.connect(self.guirestore)

        # edit style sheet
        def connectStyle(name):
            eval("self."+name).triggered.connect(lambda: self.resetStylesheet(name))
        for style_sheet in STYLE_SHEETS:
            connectStyle(style_sheet)
        self.currentStyle = None
        reset_style = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+G'), self)
        reset_style.activated.connect(self.resetStylesheet)

    def resetStylesheet(self, name=None):
        if name is None:
            name = self.currentStyle
        if name is not None:
            with open(os.path.join(DESIGN_DIR, "stylesheet", name+".qss"), "r") as f:
                QtWidgets.qApp.setStyleSheet(f.read())
            self.currentStyle = name

    def initMenu(self, modules):
        """
        create right-clic menu from modules
        """
        # initalize right-clic-menu
        self.menu = {}
        for k, values in modules.items():
            lst = [values['type']]
            if 'menu' in values:
                lst += values['menu'].split('/')
            lst.append(k)
            utils.dict_from_list(self.menu, lst)

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
