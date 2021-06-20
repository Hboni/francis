from PyQt5 import QtWidgets, QtCore, QtGui
from src.view.utils import menu_from_dict
from src.view.graph_bricks import QGraphicsModule, QGraphicsLink
from src import DEFAULT, RESULT_STACK
import copy


# stack under, raise, show

class QGraph(QtWidgets.QGraphicsView):
    """
    widget containing a view to display a tree-like architecture with nodes
    and branches

    Parameters
    ----------
    mainwin: MainWindow
        QMainWindow where the graph is displayed
    direction: {'horizontal', 'vertical'}, default='horizontal'
        direction of the pipeline;
        horizontal is left to right, vertical is top to bottom

    """
    moduleAdded = QtCore.pyqtSignal(QGraphicsModule)

    def __init__(self, mainwin, direction='vertical'):
        super().__init__()
        self._view = mainwin
        self.direction = direction
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.scene = QtWidgets.QGraphicsScene()
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setScene(self.scene)
        self.contextMenuEvent = lambda e: self.openMenu()
        self.setBackgroundBrush(eval(self._view.theme['background_brush']))

        self.selectAll = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+A'), self)
        self.selectAll.activated.connect(self.selectModules)

        self.installEventFilter(self)
        self.holdShift = False
        self._mouse_position = QtCore.QPoint(0, 0)
        self.modules = {}
        self.lastFocus = None
        self.isFocused = False
        self.higherZValue = 0

    def bind(self, parent, child):
        """
        create a link between a parent and a child module

        Parameters
        ----------
        parent, child: Module
            modules to visually bind
        """

        link = QGraphicsLink(parent, child, **self._view.theme['arrow'])

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
        result: list of Module
        """
        return [n for n in self.modules.values() if n.isSelected() and n not in exceptions]

    def eventFilter(self, obj, event):
        """
        manage keyboard shortcut and mouse events on graph view
        """
        if obj == self:
            if event.type() == QtCore.QEvent.Wheel:
                return True
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.unselectModules()
            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = True
                elif event.key() == QtCore.Qt.Key_Control:
                    self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            elif event.type() == QtCore.QEvent.KeyRelease:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = False
                elif event.key() == QtCore.Qt.Key_Control:
                    self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        return QtWidgets.QGraphicsView.eventFilter(self, obj, event)

    def unselectModules(self):
        for module in self.modules.values():
            module.selected.setChecked(False)

    def selectModules(self, modules=None):
        if modules is None:
            modules = self.modules
        for module in modules.values():
            module.selected.setChecked(True)

    def getUniqueName(self, name, exception=None):
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
        i = 1
        new_name = copy.copy(name)
        while new_name in self.modules and new_name != exception:
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
                self.colorizeBackground()
            else:
                nparents = self._view.getParameters(type).get('nparents')
                if not parents:
                    self.addModule(type)
                else:
                    if parents and nparents in [1, None]:
                        for p in parents:
                            self.addModule(type, [p])
                    elif nparents == -1 or nparents == len(parents):
                        self.addModule(type, parents)
                    else:
                        self._view.setStatusTip("This module must have {0} \
                                                 parents, got {1}".format(nparents, len(parents)))

        # build and connect right-click menu
        if self.isFocused:
            menu = menu_from_dict(self._view.modules.get('secondary'), activate)
            parents += [self.lastFocus] + self.getSelectedModules()
            parents = list(set(parents))
        else:
            menu = menu_from_dict(self._view.modules.get('primary'), activate)

        # show menu at mouse position
        pos = QtGui.QCursor.pos()
        self._mouse_position = self.mapToScene(self.mapFromGlobal(pos))
        menu.exec_(QtGui.QCursor.pos())

    def renameModule(self, module, new_name=None):
        if new_name is None:
            new_name, valid = QtWidgets.QInputDialog.getText(self, "user input", "new name",
                                                             QtWidgets.QLineEdit.Normal, module.name)
            if not valid:
                return
        new_name = self.getUniqueName(new_name, exception=module.name)
        self.modules[new_name] = self.modules.pop(module.name)
        if module.name in RESULT_STACK:
            RESULT_STACK[new_name] = RESULT_STACK.pop(module.name)
        module.rename(new_name)

    def releaseData(self, module):
        if module.name in RESULT_STACK:
            del RESULT_STACK[module.name]

    def colorizeModule(self, module, new_color=None):
        if new_color is None:
            new_color = QtWidgets.QColorDialog.getColor(module.color)
        if isinstance(new_color, list) or new_color.isValid():
            module.setColor(new_color)

    def colorizeBackground(self, new_color=None):
        if new_color is None:
            new_color = QtWidgets.QColorDialog.getColor(self.backgroundBrush().color())
        if isinstance(new_color, list) or new_color.isValid():
            self.setBackgroundBrush(new_color)

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

    def addModule(self, type, parents=None, position=None, size=None, color=None, name=None):
        """
        create a module with specified parent modules

        Parameters
        ----------
        type: str
            type of module
        parents: list of QGraphicsModule or QGraphicsModule

        """
        if name is None:
            name = self.getUniqueName(type)
        if size is None:
            size = DEFAULT['module_size']
        if color is None:
            color = self._view.getParameters(type).get('color')
        if parents is None:
            parents = []
        if not isinstance(parents, list):
            parents = [parents]

        for i, parent in enumerate(parents):
            if isinstance(parent, str):
                parents[i] = self.modules[parent]

        module = QGraphicsModule(self, type, name, parents)
        module.addToScene(self.scene)

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
            if self.direction == 'vertical':
                Xs = [c.pos().x() + c.width() for c in max_y_parent.childs if c is not module]
                x = max_y_parent.pos().x() if not Xs else max(Xs) + DEFAULT['space_between_modules'][0]
                y = max_y_parent.pos().y() + max_y_parent.height() + DEFAULT['space_between_modules'][1]
            else:
                Ys = [c.pos().y() + c.height() for c in max_x_parent.childs if c is not module]
                x = max_x_parent.pos().x() + max_x_parent.width() + DEFAULT['space_between_modules'][0]
                y = max_x_parent.pos().y() if not Ys else max(Ys) + DEFAULT['space_between_modules'][1]

        # set state
        if position is not None:
            x, y = position

        module.moveBy(x, y)
        self.modules[name] = module
        self.moduleAdded.emit(module)

        module.resize(*size)
        module.setColor(color)
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
            module = self.addModule(**values['state'])
            if not isinstance(module, Exception):
                module.setSettings(values)

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
