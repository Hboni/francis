import json
import os

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget, QMessageBox

from src import CONFIG_DIR, DEFAULT, RSC_DIR, update_default
from src.view.graph import QGraph
from src.view.graph_bricks import QGraphicsModule


class View(QtWidgets.QMainWindow):
    """
    this class is a part of the MVP app design, it shows all the user interface
    and send signals for specific actions

    """

    closed = QtCore.pyqtSignal()
    moduleAdded = QtCore.pyqtSignal(QGraphicsModule)

    def __init__(self, nopopup: bool = False):
        super().__init__()
        self.nopopup = nopopup
        uic.loadUi(os.path.join(RSC_DIR, "ui", "MainView.ui"), self)
        self.resize(*DEFAULT["window_size"])
        self.move(*DEFAULT["window_position"])

        # connect file menu
        self.actionNew.triggered.connect(self.newFile)
        self.actionSave.triggered.connect(self.saveFile)
        self.actionOpen.triggered.connect(lambda b: self.openFile())
        self.actionSaveAs.triggered.connect(self.saveAsFile)
        self.initNewFile.clicked.connect(self.newFile)

        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), "rb"))
        self.initStyle()
        self.initUI()

    def initUI(self):
        """
        This method init widgets UI for the main window
        """
        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtWidgets.QTabWidget.West)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea, QtWidgets.QTabWidget.East)

        self.graphs = {}

        self.tabWidget.clear()
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.tabWidget.hide()

        self.setWindowState(QtCore.Qt.WindowActive)
        self.setWindowTitle("Francis")

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
        menuStyles = self.menuPreferences.addMenu("Styles")
        for style in os.listdir(os.path.join(RSC_DIR, "qss")):
            menuStyles.addAction(getAction(style, self.loadStyle))

        menuThemes = self.menuPreferences.addMenu("Themes")
        for theme in os.listdir(os.path.join(RSC_DIR, "theme")):
            menuThemes.addAction(getAction(theme, self.loadTheme))

        # load default style and theme
        self.loadTheme()
        self.loadStyle()

    def loadTheme(self, theme: str = DEFAULT["theme"]):
        with open(os.path.join(RSC_DIR, "theme", theme + ".json"), "r") as f:
            self.theme = json.load(f)
        if self.style is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme["qss"])

    def loadStyle(self, style: str = DEFAULT["style"]):
        if style is None:
            return QtWidgets.qApp.setStyleSheet("")

        with open(os.path.join(RSC_DIR, "qss", style + ".qss"), "r") as f:
            self.style = f.read()
        if self.theme is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme["qss"])
        else:
            QtWidgets.qApp.setStyleSheet(self.style)

    def getParameters(self, key: str, dic: dict = None) -> str:
        if dic is None:
            dic = self.modules
        if isinstance(dic, dict):
            if key in dic:
                return dic.get(key)
            for v in dic.values():
                par = self.getParameters(key, v)
                if par is not None:
                    return par

    def addWidgetInDock(
        self,
        widget: QtWidgets.QWidget,
        side: Qt.DockWidgetArea = Qt.RightDockWidgetArea,
        unique: bool = True,
    ) -> QDockWidget:
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
            dock.setAllowedAreas(
                QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea
            )
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

    def openDialog(
        self,
        name: str,
        question: str,
        default: QMessageBox.StandardButton = QMessageBox.Yes,
    ) -> QMessageBox.StandardButton:
        dialog = QMessageBox(
            QMessageBox.Question,
            name,
            question,
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            parent=self,
        )
        dialog.setDefaultButton(default)
        return dialog.exec()

    def colorizeBackground(self, new_color: QtGui.QColor = None):
        if new_color is None:
            new_color = QtWidgets.QColorDialog.getColor(
                QtGui.QColor(*DEFAULT.get("background_color"))
            )
        for gf in self.graphs.values():
            gf.setBackgroundBrush(new_color)
        DEFAULT["background_color"] = [
            new_color.red(),
            new_color.green(),
            new_color.blue(),
        ]

    def closeTab(self, index: int):
        graph = self.tabWidget.widget(index)
        resp = graph.askSaveFile()
        if resp == QtWidgets.QMessageBox.Yes:
            graph.saveFile()
        elif resp == QtWidgets.QMessageBox.No:
            del self.graphs[graph.name]
            self.tabWidget.removeTab(index)
        if self.tabWidget.count() == 0:
            self.tabWidget.hide()
            self.initNewFile.show()

    def restoreTabs(self):
        filenames = DEFAULT.get("filenames")
        for filename in filenames:
            self.openFile(filename)
        currentTabInd = DEFAULT.get("current_tab")
        self.tabWidget.setCurrentIndex(currentTabInd)

    def browseFile(self, mode="r", ext: str = "*.iag") -> str:
        dialog = QtWidgets.QFileDialog()
        if mode == "r":
            filename, _ = dialog.getOpenFileName(self, "Open file", filter=ext)
        elif mode == "w":
            defPath = self.tabWidget.currentWidget().getDefaultPath()
            filename, _ = dialog.getSaveFileName(self, "Save file", defPath, filter=ext)
        return filename

    def graph(self) -> QGraph:
        return self.tabWidget.currentWidget()

    def newFile(self) -> QGraph:
        gf = QGraph(self, "horizontal")
        self.graphs[gf.name] = gf
        gf.setBackgroundBrush(QtGui.QColor(*DEFAULT.get("background_color")))
        self.tabWidget.addTab(gf, gf.saveName)
        self.tabWidget.setCurrentWidget(gf)
        self.tabWidget.show()
        self.initNewFile.hide()
        gf.updateName(False)
        return gf

    def openFile(self, filename: str = None):
        if filename is None:
            filename = self.browseFile("r")
        if os.path.isfile(filename):
            gf = self.newFile()
            gf.restore(filename)

    def saveFile(self):
        self.tabWidget.currentWidget().saveFile()

    def saveAsFile(self):
        self.tabWidget.currentWidget().saveAsFile()

    def askSaveFiles(self) -> QMessageBox.StandardButton:
        for gf in self.graphs.values():
            if (
                gf.modules
                and (gf.getSettings() != gf.settings or not gf.savePathIsSet)
                and not self.nopopup
            ):
                return self.openDialog(
                    "save files",
                    "Do you want to close without saving ?",
                    default=QtWidgets.QMessageBox.No,
                )
        return QtWidgets.QMessageBox.Yes

    def closeEvent(self, event):
        resp = self.askSaveFiles()
        if resp == QtWidgets.QMessageBox.Yes:
            self.closed.emit()
            update_default(
                window_size=[self.size().width(), self.size().height()],
                window_position=[self.pos().x(), self.pos().y()],
                current_tab=self.tabWidget.currentIndex(),
                filenames=[
                    self.tabWidget.widget(i).getSavePath()
                    for i in range(self.tabWidget.count())
                ],
            )
            QtWidgets.QMainWindow.closeEvent(self, event)
        else:
            event.ignore()
