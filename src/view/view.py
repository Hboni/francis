from PyQt5 import QtWidgets, QtCore, QtGui, uic
from src import RSC_DIR, DEFAULT, CONFIG_DIR, update_default
from src.view import graph, graph_bricks
import json
import os
from datetime import datetime


class View(QtWidgets.QMainWindow):
    """
    this class is a part of the MVP app design, it shows all the user interface
    and send signals for specific actions

    """
    closed = QtCore.pyqtSignal()
    moduleAdded = QtCore.pyqtSignal(graph_bricks.QGraphicsModule)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(RSC_DIR, "ui", "MainView.ui"), self)
        self.resize(*DEFAULT['window_size'])
        self.move(*DEFAULT['window_position'])

        # connect file menu
        self.actionNew.triggered.connect(self.newFile)
        self.actionOpen.triggered.connect(self.openFile)
        self.actionSave.triggered.connect(self.saveFile)
        self.actionSaveAs.triggered.connect(lambda b: self.saveAsFile(True))

        self.saveName = ""
        self.saveDir = os.path.join(RSC_DIR, "data", "out")
        self.isSaved = False

        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), "rb"))
        self.initStyle()
        self.initUI()

    def initUI(self):
        """
        This method init widgets UI for the main window
        """
        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtWidgets.QTabWidget.West)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea, QtWidgets.QTabWidget.East)

        self.settings = {'graph': {}}

        self.graphs = [graph.QGraph(self, 'horizontal')]
        self.setCentralWidget(self.graphs[0])
        self.setWindowState(QtCore.Qt.WindowActive)
        self.graphs[0].colorizeBackground(QtGui.QColor(*DEFAULT.get("background_color")))

    def initStyle(self):
        """
        This method initialize styles and useful icons
        """
        # create menu and actions for stylesheet and themes
        self.theme, self.style = None, None

        def getAction(name, function):
            name = os.path.splitext(name)[0]
            act = QtWidgets.QAction(name, self)
            act.triggered.connect(lambda: function(name))
            return act

        # add menus
        menuStyles = self.menuPreferences.addMenu('Styles')
        for style in os.listdir(os.path.join(RSC_DIR, 'qss')):
            menuStyles.addAction(getAction(style, self.loadStyle))

        menuThemes = self.menuPreferences.addMenu('Themes')
        for theme in os.listdir(os.path.join(RSC_DIR, 'theme')):
            menuThemes.addAction(getAction(theme, self.loadTheme))

        # load default style and theme
        self.loadTheme()
        self.loadStyle()

    def loadTheme(self, theme=DEFAULT['theme']):
        with open(os.path.join(RSC_DIR, "theme", theme + ".json"), "r") as f:
            self.theme = json.load(f)
        if self.style is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme['qss'])

    def loadStyle(self, style=DEFAULT['style']):
        if style is None:
            return QtWidgets.qApp.setStyleSheet('')

        with open(os.path.join(RSC_DIR, "qss", style+".qss"), "r") as f:
            self.style = f.read()
        if self.theme is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme['qss'])
        else:
            QtWidgets.qApp.setStyleSheet(self.style)

    def getParameters(self, key, dic=None):
        if dic is None:
            dic = self.modules
        if isinstance(dic, dict):
            if key in dic:
                return dic.get(key)
            for v in dic.values():
                par = self.getParameters(key, v)
                if par is not None:
                    return par

    def addWidgetInDock(self, widget, side=QtCore.Qt.RightDockWidgetArea, unique=True):
        """
        put widget inside a qdock widget

        Parameters
        ----------
        widget: QWidget

        Return
        ------
        dock: QDockWidget

        """
        if unique and isinstance(widget.parent(), QtWidgets.QDockWidget):
            dock = widget.parent()
            self.restoreDockWidget(dock)
        else:
            dock = QtWidgets.QDockWidget()
            dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
            dock.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)

            docks = self.findChildren(QtWidgets.QDockWidget)

            dock.setWidget(widget)
            self.addDockWidget(side, dock)

            # tabify dock to existant docks
            for dk in docks:
                if self.dockWidgetArea(dk) == side:
                    self.tabifyDockWidget(dk, dock)
                    break

        dock.show()
        dock.raise_()
        return dock

    def updateWindowName(self):
        if self.isSaved:
            self.setWindowTitle(os.path.splitext(self.saveName)[0])
        else:
            self.setWindowTitle("*unsaved file")

    def openDialog(self, name, question, default=QtWidgets.QMessageBox.Yes):
        dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, name, question,
                                       QtWidgets.QMessageBox.Yes |
                                       QtWidgets.QMessageBox.No |
                                       QtWidgets.QMessageBox.Cancel,
                                       parent=self)
        dialog.setDefaultButton(default)
        return dialog.exec()

    def askSaveCurrentFile(self):
        if self.graphs[0].getSettings() == self.settings.get('graph') and self.isSaved or not self.graphs[0].modules:
            return QtWidgets.QMessageBox.No
        else:
            return self.openDialog("save file", "Do you want to save the current file ?")

    def browseFile(self, mode='r', ext="*.iag"):
        dialog = QtWidgets.QFileDialog()
        if mode == 'r':
            filename, _ = dialog.getOpenFileName(self, "Open file", filter=ext)
        elif mode == 'w':
            defPath = os.path.join(self.saveDir, self.saveName)
            filename, _ = dialog.getSaveFileName(self, 'Save file', defPath, filter=ext)
        return filename

    def newFile(self):
        from src.app import main
        main()
        resp = self.askSaveCurrentFile()
        if resp == QtWidgets.QMessageBox.Cancel:
            return
        elif resp == QtWidgets.QMessageBox.Yes:
            self.saveFile()
        self.graphs[0].deleteAll()
        self.isSaved = False
        self.updateWindowName()

    def openFile(self, openLast=False):
        if openLast:
            filename = DEFAULT.get("last_filename")
        else:
            resp = self.askSaveCurrentFile()
            if resp == QtWidgets.QMessageBox.Cancel:
                return
            elif resp == QtWidgets.QMessageBox.Yes:
                self.saveFile()
            filename = self.browseFile('r')
        if os.path.isfile(filename):
            with open(filename, 'r') as fp:
                self.settings = json.load(fp)
            self.graphs[0].setSettings(self.settings['graph'])
            self.saveDir, self.saveName = os.path.split(filename)
            self.isSaved = True
        self.updateWindowName()

    def saveFile(self):
        if self.isSaved:
            self.settings['graph'] = self.graphs[0].getSettings()
            with open(os.path.join(self.saveDir, self.saveName), 'w') as fp:
                json.dump(self.settings, fp, indent=4)
        else:
            return self.saveAsFile(False)

    def saveAsFile(self, findNewName=True):
        if findNewName or not self.saveName:
            self.saveName = "save_{}.iag".format(datetime.now().strftime('%d%m%Y %Hh%Mm%S'))
        filename = self.browseFile('w')
        if filename:
            self.saveDir, self.saveName = os.path.split(filename)
            self.isSaved = True
            self.saveFile()
            self.updateWindowName()

    def closeEvent(self, event):
        resp = self.askSaveCurrentFile()
        if resp == QtWidgets.QMessageBox.Cancel:
            return event.ignore()
        elif resp == QtWidgets.QMessageBox.Yes:
            self.saveFile()

        self.closed.emit()
        bck = self.graphs[0].backgroundBrush().color()
        update_default(window_size=[self.size().width(), self.size().height()],
                       window_position=[self.pos().x(), self.pos().y()],
                       last_filename=os.path.join(self.saveDir, self.saveName),
                       background_color=[bck.red(), bck.green(), bck.blue()])
        QtWidgets.QMainWindow.closeEvent(self, event)
