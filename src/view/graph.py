import copy
import json
import os
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from src import DEFAULT, RSC_DIR
from src.view.graph_bricks import QGraphicsLink, QGraphicsModule
from src.view.utils import menu_from_dict

# stack under, raise, show


class QGraph(QtWidgets.QGraphicsView):
    """
    widget containing a view to display a tree-like architecture with nodes
    and branches

    Parameters
    ----------
    mainwin: MainWindow
        QMainWindow where the graph is displayed
    direction: {'horizontal', 'vertical'}, default='vertical'
        direction of the pipeline;
        horizontal is left to right, vertical is top to bottom

    """

    def __init__(self, mainwin, direction="vertical"):
        super().__init__()
        self._view = mainwin
        self.direction = direction
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.scene = QtWidgets.QGraphicsScene()
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setScene(self.scene)
        self.contextMenuEvent = lambda e: self.openMenu()
        self.selectAll = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+A"), self)
        self.selectAll.activated.connect(self.selectModules)
        self.installEventFilter(self)
        self.holdShift = False
        self.holdCtrl = False
        self._mouse_position = QtCore.QPoint(0, 0)
        self.modules = {}
        self.lastFocus = None
        self.isFocused = False
        self.higherZValue = 0
        self.settings = {}
        self.saveName = self.getUniqueName("# not saved", dic=self._view.graphs)
        self.name = self.saveName
        self.saveDir = os.path.join(RSC_DIR, "data", "out")
        self.savePathIsSet = False
        self.resultStack = {}

    def bind(self, parent, child):
        """
        create a link between a parent and a child module

        Parameters
        ----------
        parent, child: QGraphicsModule
            modules to visually bind
        """

        link = QGraphicsLink(parent, child, **DEFAULT["arrow"])
        parent.positionChanged.connect(link.updatePos)
        child.positionChanged.connect(link.updatePos)
        parent.links.append(link)
        child.links.append(link)
        self.scene.addItem(link)

    def setEnabledScroll(self, enable_scroll=True):
        """
        enable/disable view scrolling

        Parameters
        ----------
        enable_scroll: bool, default True
        """
        self.verticalScrollBar().setEnabled(enable_scroll)
        self.horizontalScrollBar().setEnabled(enable_scroll)

    def getSelectedModules(self, exceptions=[]):
        """
        get all selected modules (with ctrl+click shortcut)

        Return
        ------
        result: list of QGraphicsModule
        """
        return [
            n for n in self.modules.values() if n.isSelected() and n not in exceptions
        ]

    def eventFilter(self, obj, event):
        """
        manage keyboard shortcut and mouse events on graph view
        """
        if obj == self:
            if event.type() == QtCore.QEvent.Wheel:
                if self.holdCtrl:
                    self.zoom(event)
                return True
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.unselectModules()
            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = True
                elif event.key() == QtCore.Qt.Key_Control:
                    self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
                    self.holdCtrl = True
            elif event.type() == QtCore.QEvent.KeyRelease:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = False
                elif event.key() == QtCore.Qt.Key_Control:
                    self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                    self.holdCtrl = False
        return QtWidgets.QGraphicsView.eventFilter(self, obj, event)

    def zoom(self, event):
        delta = event.angleDelta().y() / 300
        return self.scale(1 + delta, 1 + delta)

    def unselectModules(self):
        for module in self.modules.values():
            module.selected.setChecked(False)

    def selectModules(self, modules=None):
        if modules is None:
            modules = self.modules
        for module in modules.values():
            module.selected.setChecked(True)

    def getUniqueName(self, name, exception=None, dic=None):
        """
        find an unused name by adding _n at the end of the name

        Parameters
        ----------
        name: str
            default non-unique name of the module
        exception: None or str
            if new name is exception, keep it

        Return
        ------
        new_name: str
            unique name for the module

        """
        if dic is None:
            dic = self.modules
        i = 1
        new_name = copy.copy(name)
        while new_name in dic and new_name != exception:
            new_name = "{0}_{1}".format(name, i)
            i += 1
        return new_name

    def openMenu(self, module=None):
        """
        open menu on right-clic at clicked position

        Parameters
        ----------
        module: QGraphicsModule, default None
            if None open a menu with primary actions (load, ...)
            else open a menu with secondary and tertiary actions (erosion, ...)

        """
        parents = []

        def activate(action):
            type = action._type
            if type in ["delete", "delete all"]:
                for p in parents:
                    self.deleteBranch(p)
            elif type == "rename":
                self.renameModule(self.lastFocus)
            elif type == "changeColor":
                self.colorizeModule(self.lastFocus)
            elif type == "colorBackground":
                self._view.colorizeBackground()
            else:
                nparents = self._view.getParameters(type).get("nparents")
                if not parents:
                    self.addModule(type)
                else:
                    if parents and nparents in [1, None]:
                        for p in parents:
                            self.addModule(type, [p])
                    elif nparents == -1 or nparents == len(parents):
                        self.addModule(type, parents)
                    else:
                        self._view.setStatusTip(
                            "This module must have {0} \
                                                 parents, got {1}".format(
                                nparents, len(parents)
                            )
                        )

        # build and connect right-click menu
        if self.isFocused:
            menu = menu_from_dict(self._view.modules.get("secondary"), activate)
            parents += [self.lastFocus] + self.getSelectedModules()
            parents = list(set(parents))
        else:
            menu = menu_from_dict(self._view.modules.get("primary"), activate)

        # show menu at mouse position
        pos = QtGui.QCursor.pos()
        self._mouse_position = self.mapToScene(self.mapFromGlobal(pos))
        menu.exec_(QtGui.QCursor.pos())

    def renameModule(self, module, new_name=None):
        if new_name is None:
            new_name, valid = QtWidgets.QInputDialog.getText(
                self, "user input", "new name", QtWidgets.QLineEdit.Normal, module.name
            )
            if not valid:
                return
        new_name = self.getUniqueName(new_name, exception=module.name)
        self.modules[new_name] = self.modules.pop(module.name)
        if module.name in self.resultStack:
            self.resultStack[new_name] = self.resultStack.pop(module.name)
        module.rename(new_name)

    def releaseData(self, module):
        if module.name in self.resultStack:
            del self.resultStack[module.name]

    def colorizeModule(self, module, new_color=None):
        if new_color is None:
            new_color = QtWidgets.QColorDialog.getColor(module.color)
        if isinstance(new_color, list) or new_color.isValid():
            module.setColor(new_color)

    def deleteAll(self):
        while self.modules:
            self.deleteBranch(list(self.modules.values())[0])

    def deleteBranch(self, parent, childs_only=False):
        """
        delete module, its children and the associated data recursively

        Parameters
        ----------
        parent: QGraphicsModule
        child_only: bool, default=False
            if True do not delete the parent module else delete parent and children

        """
        if parent.name not in self.modules:
            return
        # delete data
        self.releaseData(parent)
        # delete children if has no other parent
        for child in parent.childs:
            child.parents.remove(parent)
            if not child.parents:
                self.deleteBranch(child)
        # remove module from parent children
        for p in parent.parents:
            p.childs.remove(parent)
        # delete module and links
        parent.delete()
        del self.modules[parent.name]

    def getData(self, name):
        if isinstance(name, list):
            return [self.getData(n) for n in name]
        else:
            return copy.copy(self.resultStack.get(name))

    def storeData(self, name, data):
        self.resultStack[name] = data

    def addModule(
        self,
        type,
        parents=None,
        parentNames=None,
        position=None,
        width=None,
        color=None,
        name=None,
    ):
        """
        create a module with specified parent modules

        Parameters
        ----------
        type: str
            type of module
        parents: list of QGraphicsModule or QGraphicsModule

        """
        # initialize
        if name is None:
            name = self.getUniqueName(type)
        if width is None:
            width = DEFAULT["module_width"]
        if color is None:
            color = self._view.getParameters(type).get("color")

        if parents is None:
            if parentNames is not None:
                parents = [self.modules[pn] for pn in parentNames]
            else:
                parents = []
        elif not isinstance(parents, list):
            parents = [parents]

        # create module
        module = QGraphicsModule(self, type, name, parents)
        module.addToScene(self.scene)

        # bind module to parents and find best position
        if not parents:
            x, y = self._mouse_position.x(), self._mouse_position.y()
        else:
            max_x_parent = parents[0]
            max_y_parent = parents[0]
            for parent in parents:
                if parent.pos().x() > max_x_parent.pos().x():
                    max_x_parent = parent
                if parent.pos().y() > max_y_parent.pos().y():
                    max_y_parent = parent
                self.bind(parent, module)
                parent.childs.append(module)
            if self.direction == "vertical":
                Xs = [
                    c.pos().x() + c.width()
                    for c in max_y_parent.childs
                    if c is not module
                ]
                x = (
                    max_y_parent.pos().x()
                    if not Xs
                    else max(Xs) + DEFAULT["space_between_modules"][0]
                )
                y = (
                    max_y_parent.pos().y()
                    + max_y_parent.height()
                    + DEFAULT["space_between_modules"][1]
                )
            else:
                Ys = [
                    c.pos().y() + c.height()
                    for c in max_x_parent.childs
                    if c is not module
                ]
                x = (
                    max_x_parent.pos().x()
                    + max_x_parent.width()
                    + DEFAULT["space_between_modules"][0]
                )
                y = (
                    max_x_parent.pos().y()
                    if not Ys
                    else max(Ys) + DEFAULT["space_between_modules"][1]
                )

        if position is not None:
            x, y = position

        # set state
        module.moveBy(x, y)
        self.modules[name] = module
        self._view.moduleAdded.emit(module)
        module.modified.connect(lambda: self.updateName(False))
        module.resize(width, 1)
        module.setColor(color)
        module.modified.emit()
        return module

    def setSettings(self, settings):
        """
        restore graph architecture and module parameters

        Parameters
        ----------
        settings: dict
            the dict-like description of the graph

        """
        for name, values in settings.items():
            module = self.addModule(**values.get("state"))
            if not isinstance(module, Exception):
                module.setSettings(values)
        return settings

    def getSettings(self):
        """
        get graph architecture and module parameters

        Return
        ------
        settings: dict

        """
        settings = {}
        orderedModules = []
        modules = list(self.modules.values())
        while modules:
            module = modules.pop(0)
            if not module.parents or set(module.parents).intersection(orderedModules):
                settings[module.name] = module.getSettings()
                orderedModules.append(module)
            else:
                modules.append(module)
        return settings

    def getDateName(self):
        return "graph_{}.iag".format(datetime.now().strftime("%d%m%Y %Hh%Mm%S"))

    def getSavePath(self):
        return os.path.join(self.saveDir, self.saveName)

    def getDefaultPath(self):
        if self.saveName.startswith("# not saved"):
            saveName = self.getDateName()
        else:
            saveName = self.saveName
        return os.path.join(self.saveDir, saveName)

    def updateName(self, isSaved=True):
        """
        update the name of the graph based on the save name
        """
        new_name = os.path.splitext(self.saveName)[0]
        index = self._view.tabWidget.indexOf(self)
        if not isSaved or not self.savePathIsSet:
            self._view.tabWidget.setTabText(index, "* " + new_name)
        else:
            self._view.tabWidget.setTabText(index, new_name)
        self._view.graphs[new_name] = self._view.graphs.pop(self.name)
        self.name = new_name

    def askSaveFile(self):
        if (
            self.getSettings() == self.settings
            and self.savePathIsSet
            or not self.modules
        ):
            return QtWidgets.QMessageBox.No
        else:
            return self._view.openDialog(
                "save file", "Do you want to save the current file ?"
            )

    def restore(self, filename):
        """
        restore graph modules, name and save path
        """
        if not os.path.isfile(filename):
            return
        with open(filename, "r") as fp:
            settings = json.load(fp)
        self.settings = self.setSettings(settings)
        self.saveDir, self.saveName = os.path.split(filename)
        self.savePathIsSet = True
        self.updateName()

    def saveFile(self, filename=None):
        """
        save graph modules as save path
        """
        if self.savePathIsSet:
            filename = os.path.join(self.saveDir, self.saveName)
        if filename:
            self.settings = self.getSettings()
            with open(filename, "w") as fp:
                json.dump(self.settings, fp, indent=4)
            self.saveDir, self.saveName = os.path.split(filename)
            self.savePathIsSet = True
            self.updateName()
        else:
            self.saveAsFile(False)

    def saveAsFile(self, findNewName=True):
        if findNewName or not self.saveName:
            self.saveName = self.getDateName()
        filename = self._view.browseFile("w")
        if filename:
            self.saveFile(filename)
