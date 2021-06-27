from PyQt5 import QtWidgets, uic, QtCore, QtGui
import os
from src import RSC_DIR
from src.view import utils, ui
import pandas as pd
import numpy as np


class QGraphicsModule(QtWidgets.QWidget):
    focused = QtCore.pyqtSignal(bool)
    saveDataClicked = QtCore.pyqtSignal()
    positionChanged = QtCore.pyqtSignal()
    nameChanged = QtCore.pyqtSignal(str, str)
    modified = QtCore.pyqtSignal()
    displayed = QtCore.pyqtSignal()
    """
    movable widget inside the graph associated to a pipeline's step

    Parameters
    ----------
    graph: QGraph
    type: str
        type of module associated to specific widget and functions
    name: str
        unique name
    parents: list of Module, default=[]
        modules whose outputs are self input

    """
    def __init__(self, graph, type, name, parents=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph = graph
        self.type = type
        self.name = name
        self.parents = parents
        self.childs = []
        self.links = []
        self.color = None

        self.last_position = QtCore.QPointF(0, 0)
        self.initialPosition = None

        self._item = self.QCustomRectItem(self)
        self._proxy = QtWidgets.QGraphicsProxyWidget(self._item)
        self._proxy.setWidget(self)

        self.moveBy = self._item.moveBy
        self.pos = self._item.pos

        self.getData = self.graph.getData

        self.propagation_child = None
        self.heights = {}

        self.runner = None

        self.setToolTip(type)
        self.initUI(name)

    def initUI(self, name):
        uic.loadUi(os.path.join(RSC_DIR, "ui", "ModuleTemplate.ui"), self)

        self.sizeGrip = utils.replaceWidget(self.sizeGrip, ui.QCustomSizeGrip(self))

        self.grap = utils.replaceWidget(self.grap, ui.QGrap())
        self.openButton.setText(name)
        self._item.setRect(QtCore.QRectF(self.geometry().adjusted(0, 0, 0, 0)))

        params = uic.loadUi(os.path.join(RSC_DIR, 'ui', 'modules', self.type+'.ui'))
        self.parameters = utils.replaceWidget(self.parameters, params)

        self.parameters.hide()
        self.resultArea.hide()

        self.footer.mousePressEvent = self.footerMousePressEvent
        self.isFront = False

        ui.setButtonIcon(self.play, "play.png")
        ui.setButtonIcon(self.stop, "stop.png")
        ui.setButtonIcon(self.pause, "pause.png")

        self.initConnections()
        self.setState()

        self.connectParametersModifications()

    def sendFront(self):
        if self.isFront:
            self._item.graphicsEffect().setEnabled(False)
        else:
            effect = QtWidgets.QGraphicsDropShadowEffect()
            effect.setOffset(20, 20)
            effect.setBlurRadius(20)
            self._item.setGraphicsEffect(effect)
        self.isFront = not self.isFront
        self.focusModule(True)

    def getNparents(self):
        return len(self.parents)

    def resizeEvent(self, event):
        rect = self._item.rect()
        rect.setWidth(self.width())
        rect.setHeight(self.height())
        self._item.setRect(rect)
        for link in self.links:
            link.updatePos()
        return QtWidgets.QWidget.resizeEvent(self, event)

    def enterEvent(self, event):
        self.focused.emit(True)
        return QtWidgets.QWidget.enterEvent(self, event)

    def leaveEvent(self, event):
        self.focused.emit(False)
        return QtWidgets.QWidget.leaveEvent(self, event)

    def footerMousePressEvent(self, event):
        """
        send module to front when footer is clicked
        """
        self.sendFront()
        return QtWidgets.QWidget.mousePressEvent(self.footer, event)

    def initConnections(self):
        self.positionChanged.connect(self.moveSelection)
        self.focused.connect(self.focusModule)
        self.selected.stateChanged.connect(self.changeChildSelection)
        self.openButton.clicked.connect(self.openParameters)

    class QCustomRectItem(QtWidgets.QGraphicsRectItem):
        """
        graphic item which allow to move the widget in graphic view

        Parameters
        ----------
        parent: QViewWidget
        """
        def __init__(self, parent):
            super().__init__()
            self._parent = parent
            self.setZValue(0)
            self.setAcceptHoverEvents(True)
            self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                          QtWidgets.QGraphicsItem.ItemIsFocusable |
                          QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges)

        def itemChange(self, change, value):
            if change == QtWidgets.QGraphicsItem.ItemPositionChange:
                self._parent.deltaPosition = value - self.pos()
                self._parent.positionChanged.emit()
            return QtWidgets.QGraphicsRectItem.itemChange(self, change, value)

    def setState(self, state=None, suspendable=True):
        """
        set state of the progress bar and of pause, pplay, stop buttons

        Parameters
        ----------
        state: {'loading', 'pause', 'valid', 'fail', None}, default=None
        suspendable: bool, default=True
            if True, 'pause' button is shown and process is suspendable

        """
        self.state = state
        if state == 'loading':
            self.play.hide()
            self.pause.setVisible(suspendable)
            self.stop.show()
            col, maxi = QtGui.QColor(0, 0, 0, 0), 0
        elif state == "pause":
            self.play.show()
            self.pause.hide()
            self.stop.show()
            col, maxi = QtGui.QColor(255, 150, 0, 255), 1
        else:
            maxi = 1
            self.play.show()
            self.pause.hide()
            self.stop.hide()
            if state == 'valid':
                col = QtGui.QColor(0, 200, 0, 255)
            elif state == 'fail':
                col = QtGui.QColor(255, 0, 0, 255)
            else:
                col = QtGui.QColor(0, 0, 0, 0)

        # set background color of the progress bar
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, col)
        self.loading.setAutoFillBackground(True)
        self.loading.setPalette(pal)
        # if maxi to 0, the progress bar will run over and over
        self.loading.setMaximum(maxi)

    def isSelected(self):
        return self.selected.isChecked()

    def addToScene(self, scene):
        scene.addItem(self._item)

    def get_parent_names(self):
        return [p.name for p in self.parents]

    def get_parent_name(self):
        return self.parents[0].name

    def moveSelection(self):
        if self is self.graph.lastFocus:
            for node in self.graph.getSelectedModules(exceptions=[self]):
                node.moveBy(self.deltaPosition.x(), self.deltaPosition.y())

    def setInitialPosition(self):
        self.initialPosition = self.pos()

    def changeChildSelection(self, state):
        if self.graph.holdShift:
            for child in self.childs:
                child.selected.setChecked(state)

    @property
    def mid_pos(self):
        return self.width()/2, self.height()/2

    def delete(self):
        """
        delete itself and all related graphic items (QGraphicLinks)
        """
        # delete links
        while self.links:
            self.graph.scene.removeItem(self.links[0])
            self.links[0].delete()

        # delete wild widget if in dock
        if isinstance(self.parameters.parent(), QtWidgets.QDockWidget):
            self.parameters.parent().close()
        if isinstance(self.result.parent(), QtWidgets.QDockWidget):
            self.result.parent().close()

        self.graph.scene.removeItem(self._item)
        self._proxy.deleteLater()
        self.deleteLater()

    def focusModule(self, boolean):
        """
        if boolean is True, put this module on top of the others
        """
        self.graph.setEnabledScroll(not boolean)
        self.graph.isFocused = boolean
        if boolean:
            self.graph.higherZValue += 1
            self._item.setZValue(self.graph.higherZValue + self.isFront * 1000)
            self.graph.lastFocus = self

    def getChilds(self):
        """
        get all children

        Return
        ------
        childs: list of Module

        """
        childs = self.childs
        for child in self.childs:
            childs += child.getChilds()
        return childs

    def rename(self, new_name):
        self.openButton.setText(new_name)
        self.nameChanged.emit(self.name, new_name)
        self.name = new_name

    def setColor(self, new_color):
        """
        set the color of the header and footer of the module

        Parameters
        ----------
        new_color: list of (r, g, b) or QColor

        """
        if isinstance(new_color, list):
            new_color = QtGui.QColor(*new_color)
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, new_color)
        for w in [self.header, self.footer]:
            w.setAutoFillBackground(True)
            w.setPalette(pal)
        self.color = new_color

    def addWidgetInDock(self, widget, side, unique=True):
        if widget is None:
            return
        dock = self.graph._view.addWidgetInDock(widget, side, unique)
        self.nameChanged.connect(lambda _, newname: dock.setWindowTitle(newname))
        dock.setWindowTitle(self.name)

    def connectParametersModifications(self):
        """
        send 'modified' signal at each time the module is moved/modified
        """
        self.positionChanged.connect(self.modified.emit)
        self.nameChanged.connect(self.modified.emit)
        for widget in self.parameters.__dict__.values():
            modifFunction = utils.getModifiedFunction(widget)
            if modifFunction:
                modifFunction.connect(self.modified.emit)

    def setSettings(self, settings):
        """
        set settings of module (=state) and parameters widgets

        Parameters
        ----------
        settings: dict

        """
        if settings is None:
            return
        for name, w in sorted(self.parameters.__dict__.items()):
            if name in settings['parameters']:
                utils.setValue(w, settings['parameters'][name])

        state = settings['state']
        self.graph.renameModule(self, state['name'])
        self.graph.colorizeModule(self, state['color'])

    def getSettings(self):
        """
        get settings of module (=state) and parameters widgets
        """
        settings = {'parameters': {}}
        for name, w in self.parameters.__dict__.items():
            value = utils.getValue(w)
            if value is not None:
                settings['parameters'][name] = value
        settings['state'] = {'name': self.name,
                             'type': self.type,
                             'parentNames': [p.name for p in self.parents],
                             'position': [self.pos().x(), self.pos().y()],
                             'width': self.width(),
                             'color': [self.color.red(), self.color.green(), self.color.blue(), self.color.alpha()]}

        return settings

    def openParameters(self):
        self.parameters.setVisible(self.parameters.isHidden())
        self.updateHeight(force=True)

    def releaseData(self):
        self.graph.releaseData(self)
        self.showResult("Data released")

    def getBranch(self, branch=[]):
        for node in self.childs + self.parents:
            if node not in branch:
                branch.append(node)
                node.getBranch(branch)
        return branch

    def showResult(self, result=None):
        """
        This function create widget from result and show it. The created widget
        depends on the result type

        Parameters
        ----------
        result: any type data

        """
        # create the output widget depending on output type
        if result is None:
            return
        elif isinstance(result, Exception):
            new_widget = QtWidgets.QTextBrowser()
            new_widget.setPlainText(type(result).__name__+"\n"+str(result))
            new_widget.setStyleSheet("color: red;")
            ui.showError("Warning", result)
        elif isinstance(result, pd.DataFrame):
            new_widget = ui.QCustomTableWidget(result)
            new_widget.save.clicked.connect(self.saveDataClicked.emit)
            new_widget.release.clicked.connect(self.releaseData)
        elif isinstance(result, np.ndarray):
            new_widget = ui.QImageRenderer(result, self)
            new_widget.mousePressEvent = self.snapMousePressEvent
            new_widget.syncSignal.connect(self.synchronizeImages)
        else:
            new_widget = QtWidgets.QTextBrowser()
            new_widget.setPlainText(str(result))
        # replace current output widget with the new one
        self.result = utils.replaceWidget(self.result, new_widget)
        self.resultArea.show()
        self.displayed.emit()
        self.updateHeight()

    def updateHeight(self, force=False):
        if force:
            QtWidgets.qApp.sendPostedEvents()
            QtWidgets.qApp.sync()
        self.sizeGrip.mouseMoveEvent()

    def snapMousePressEvent(self, event):
        """
        update pixel value and position labels when clicking image view
        """
        # set ratio between image and qpixmap
        im = self.graph.resultStack.get(self.name)
        if im is not None:
            if self.result.slicable:
                ratio = im.shape[int(self.result.axis == 0)] / self.result.width()
            else:
                ratio = im.shape[1] / self.result.width()

            # get click position
            click_pos = np.array([event.pos().y(), event.pos().x()])
            # define position in image
            true_pos = np.rint(click_pos * ratio).astype(int)
            try:
                if im.ndim == 2:
                    x, y, z = *true_pos, ''
                    value = im[x, y]
                    self.rightfoot.setText("%d " % im[x, y])
                elif self.result.slicable:
                    x, y, z = np.insert(true_pos, self.result.axis, self.result.currentSlice)
                    value = im[x, y, z]
                else:
                    x, y, z = *true_pos, ''
                    value = "(" + " ".join(im[x, y].astype(str)) + ")"
                self.leftfoot.setText("{0} {1} {2}".format(x, y, z))
                self.rightfoot.setText(str(value))
            except IndexError as e:
                # click outside image
                print(e)

    def synchronizeImages(self):
        for node in self.getBranch():
            res = node.result
            if isinstance(res, ui.QImageRenderer):
                if res.currentSlice != self.result.currentSlice:
                    res.currentSlice = self.result.currentSlice
                    res.updateSnap()
                elif res.axis != self.result.axis:
                    res.axis = self.result.axis
                    res.updateSnap()


def ceval(arg):
    try:
        return eval(arg)
    except (NameError, TypeError):
        return arg


class QGraphicsLink(QtWidgets.QGraphicsPolygonItem):
    """
    graphic arrow between two graphic points

    Parameters
    ----------
    parent/child: Module
        the two nodes to link
    width: float, default=5
        width of the arrow line
    arrowWidth: float, default=10
        width of the arrow head
    arrowLen: float, default=10
        length of the arrow head
    space: float, default=20
        space between arrow extremity and nodes
    color: QColor, default=QtGui.QColor(0, 150, 0)
        color of the arrow background
    borderWidth: float, default=2
        width of the arrow border
    borderColor: QColor, default=QtGui.QColor(0, 150, 0)
        color of the arrow border

    """
    def __init__(self, parent, child, width=5, arrowWidth=10, arrowLen=10, space=[0, 20],
                 color=QtGui.QColor(0, 150, 0), borderWidth=2, borderColor=QtGui.QColor(0, 150, 0)):
        super().__init__()
        self._parent = parent
        self._child = child
        self.setZValue(-1)
        self.setPen(QtGui.QPen(ceval(borderColor), borderWidth))
        self.setBrush(ceval(color))
        self.width = width
        self.arrowWidth = arrowWidth
        self.arrowLen = arrowLen
        self.space = space
        self.updatePos()

    def intersects(self, line, rect, ref_position):
        """
        This method find the intersection between widget rect and line
        by checking the intersection between line and each rect border line.
        As the line comes from inside the rect, only one intersection exists

        Parameters
        ----------
        line: QLineF
        rect: QRect
            rect of the widget
        ref_position: QPoint
            absolute position of the rect int the graph

        Return
        ------
        result: QPointF
            first position found of the intersection
        """
        points = [rect.bottomLeft(), rect.bottomRight(), rect.topRight(), rect.topLeft()]
        for i in range(4):
            border = QtCore.QLineF(ref_position + points[i-1], ref_position + points[i])
            try:
                intersection_type, intersection_point = line.intersects(border)
            except AttributeError:
                intersection_point = QtCore.QPointF()
                intersection_type = line.intersect(border, intersection_point)
            if intersection_type == QtCore.QLineF.BoundedIntersection:
                return intersection_point
        return QtCore.QPointF()

    def delete(self):
        """
        delete connection between link and parent/child
        """
        self._parent.positionChanged.disconnect(self.updatePos)
        self._child.positionChanged.disconnect(self.updatePos)
        self._parent.links.remove(self)
        self._child.links.remove(self)

    def updatePos(self):
        """
        This method create the arrow between child and parent
        """
        # build direction line
        r1, r2 = self._parent.rect(), self._child.rect()
        line = QtCore.QLineF(self._parent.pos() + r1.center(),
                             self._child.pos() + r2.center())

        # build unit vectors
        unit = (line.unitVector().p2() - line.unitVector().p1())
        normal = (line.normalVector().unitVector().p2() - line.normalVector().unitVector().p1())

        # get arrow point
        p1 = self.intersects(line, r1, self._parent.pos()) + unit * self.space[0]
        p2 = self.intersects(line, r2, self._child.pos()) - unit * self.space[1]
        p11 = p1 + normal * self.width
        p12 = p1 - normal * self.width
        p21 = p2 + normal * self.width - unit * self.arrowLen
        p22 = p2 - normal * self.width - unit * self.arrowLen
        p23 = p2 + normal * self.arrowWidth - unit * self.arrowLen
        p24 = p2 - normal * self.arrowWidth - unit * self.arrowLen

        # build arrow
        if np.sign((p22 - p12).x()) == np.sign(unit.x()) and np.sign((p22 - p12).y()) == np.sign(unit.y()):
            self.setPolygon(QtGui.QPolygonF([p11, p21, p23, p2, p24, p22, p12, p11]))
        else:
            self.setPolygon(QtGui.QPolygonF())
