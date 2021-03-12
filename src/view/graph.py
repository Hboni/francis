from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src.view import ui
import os
import copy
import json
import numpy as np
from src import UI_DIR, IMAGES_STACK
import pandas as pd

class Link(QtWidgets.QGraphicsPathItem):
    def __init__(self, junction1, junction2):
        super().__init__()
        self.j1, self.j2 = junction1, junction2
        self._path = QtGui.QPainterPath()
        self._path.moveTo(self.j1.pos())
        self._path.lineTo(self.j2.pos())
        self.j1.links.append((self, 0))
        self.j2.links.append((self, 1))
        self.setPath(self._path)

    def updateElement(self, index, pos):
        self._path.setElementPositionAt(index, pos.x(), pos.y())
        self.setPath(self._path)

class Junction(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, node):
        rad = 0
        super(Junction, self).__init__(-rad, -rad, 2*rad, 2*rad)
        self.node = node
        self.links = []
        self.setZValue(1)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            for link, index in self.links:
                link.updateElement(index, value.toPoint())
        return QtWidgets.QGraphicsEllipseItem.itemChange(self, change, value)


class Node(QtWidgets.QWidget):
    rightClicked = QtCore.pyqtSignal(int)
    def __init__(self, graph, type, name, parents=[], position=(0,0)):
        super().__init__()
        self.graph = graph
        self.type = type
        self.name = name
        uic.loadUi(os.path.join(UI_DIR, "Node.ui"), self)

        self.button.setText(name)
        self.button.mousePressEvent = self._mousePressEvent
        self.button.mouseMoveEvent = self._mouseMoveEvent
        self.button.mouseReleaseEvent = self._mouseReleaseEvent
        self.current_branch = []
        self.childs = []
        self.parents = parents
        self.junction_up = Junction(self)
        self.junction_down = Junction(self)
        self.moveAt(QtCore.QPointF(*position))
        self.isSelected = False
        self.snap.wheelEvent = self._wheelEvent

        self.current_slice = None


    def delete(self):
        for j in [self.junction_up, self.junction_down]:
            for l1,_ in j.links:
                self.graph.scene.removeItem(l1)
            self.graph.scene.removeItem(j)
        self.proxy.deleteLater()
        self.deleteLater()

    def select(self):
        self.button.setStyleSheet("QPushButton {font-weight: bold;}")
        self.isSelected = True

    def unselect(self):
        self.button.setStyleSheet("QPushButton {font-weight: normal;}")
        self.isSelected = False

    def _wheelEvent(self, event):
        if self.current_slice is not None:
            step = 1
            if event.angleDelta().y() > 0:
                self.current_slice += step
            else:
                self.current_slice -= step
            self.updateSnap()

    def _mousePressEvent(self, event=None):
        if event.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit(1)
        elif event.button() == QtCore.Qt.LeftButton:
            self._state = 'pressed'
            self._prev_screenPos = event.screenPos()
            self._init_screenPos = event.screenPos() - self.junction_up.pos()
            self.updateCurrentBranch()
            return QtWidgets.QPushButton.mousePressEvent(self.button, event)

    def _mouseMoveEvent(self, event=None):
        self._state = 'moved'
        if self.graph.holdShift:
            self.move(event.screenPos()-self._prev_screenPos)
        else:
            self.moveAt(event.screenPos()-self._init_screenPos)
        self._prev_screenPos = event.screenPos()
        return QtWidgets.QPushButton.mouseMoveEvent(self.button, event)

    def _mouseReleaseEvent(self, event=None):
        return QtWidgets.QPushButton.mouseReleaseEvent(self.button, event)

    def addToScene(self, scene):
        scene.addItem(self.junction_up)
        scene.addItem(self.junction_down)
        self.proxy = QtWidgets.QGraphicsProxyWidget(self.junction_up)
        self.proxy.setWidget(self)
        self.proxy.setPos(-self.width()/2, 0)
        self.proxy.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.junction_down.setPos(0, self.height())
        self.raise_()

    def pos(self):
        return self.junction_up.pos()

    def moveAt(self, pos):
        self.junction_up.setPos(pos)
        self.junction_down.setPos(pos+QtCore.QPointF(0, self.height()))

    def move(self, deltapos, recursive=True):
        self.junction_up.setPos(self.pos()+deltapos)
        self.junction_down.setPos(self.pos()+deltapos+QtCore.QPointF(0, self.height()))
        if recursive:
            for node in self.current_branch:
                node.move(deltapos, recursive=False)

    def getChilds(self, recursive=True):
        childs = self.childs
        for child in self.childs:
            childs += child.getChilds(recursive)
        return childs

    def updateCurrentBranch(self):
        self.current_branch = set(self.getChilds())

    def updateSnap(self, sync=True):
        if self.name not in IMAGES_STACK.keys():
            return
        im = IMAGES_STACK[self.name]
        s1, s2, s3 = im.shape
        if self.current_slice is None:
            self.current_slice = int(s1 / 2)
        elif self.current_slice < 0:
            self.current_slice = 0
        elif self.current_slice >= s1:
            self.current_slice = s1-1
        qim = QtGui.QImage(im[self.current_slice].copy(),
                           s2, s3, QtGui.QImage.Format_Indexed8)
        # qim.setColorTable([QtGui.qRgb(0, 0, 0)]*50+[QtGui.qRgb(255,255,255)]*50+[QtGui.qRgb(255, 0, 0)]*50)
        self.snap.setPixmap(QtGui.QPixmap(qim))
        self.snap.update()
        if sync:
            for node in self.childs+self.parents:
                if node.current_slice != self.current_slice:
                    node.current_slice = self.current_slice
                    node.updateSnap(sync)


class Graph(QtWidgets.QWidget):
    nodeClicked = QtCore.pyqtSignal(Node)
    def __init__(self, mainwin):
        super().__init__()
        self.mainwin = mainwin
        uic.loadUi(os.path.join(UI_DIR, "Graph.ui"), self)
        self.setWindowState(QtCore.Qt.WindowMaximized);
        self.scene = QtWidgets.QGraphicsScene()
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setScene(self.scene)
        self.view.contextMenuEvent = lambda e: self.openMenu()
        self.installEventFilter(self)
        self.holdShift = False
        self.holdCtrl = False
        self._mouse_position = QtCore.QPoint(0,0)
        self.nodes = {}
        self.settings = {}


    def clearSelection(self):
        for node in self.nodes.values():
            node.unselect()

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                if event.button() == QtCore.Qt.LeftButton:
                    self.clearSelection()
            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = True
                elif event.key() == QtCore.Qt.Key_Control:
                    self.holdCtrl = True
                elif event.key() == QtCore.Qt.Key_Escape:
                    self.clearSelection()
            elif event.type() == QtCore.QEvent.KeyRelease:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = False
                elif event.key() == QtCore.Qt.Key_Control:
                    self.holdCtrl = False
        return super(Graph, self).eventFilter(obj, event)

    def bind(self, parent, child):
        self.scene.addItem(Link(parent.junction_down, child.junction_up))

    def getUniqueName(self, name):
        i = 1
        names = self.nodes.keys()
        new_name = copy.copy(name)
        while new_name in names:
            new_name = "{0}_{1}".format(name, i)
            i += 1
        return new_name

    def getSelectedNodes(self):
        return [n for n in self.nodes.values() if n.isSelected]


    def openMenu(self, node=None):
        if node is None:
            acts = self.mainwin.menu['primary']
            nodes = []
        else:
            acts = self.mainwin.menu['secondary']
            nodes = [node]
        nodes += self.getSelectedNodes()
        nodes = list(set(nodes))
        def activate(action):
            type = action.text()
            if type == "rename":
                self.renameNode(node)
            elif type in ["delete", "delete all"]:
                self.deleteBranch(node)
            elif type == "empty":
                self.deleteBranch(node, childs_only=True)
            else:
                self.addNode(action.text(), nodes)
        menu = ui.menuFromDict(acts, activation_function=activate)
        pos = QtGui.QCursor.pos()
        self._mouse_position = self.view.mapToScene(self.view.mapFromGlobal(pos))
        menu.exec_(QtGui.QCursor.pos())

    def renameNode(self, node):
        print('rename')

    def deleteBranch(self, parent, childs_only=False):
        """
        delete node and its children recursively
        """
        #delete children if has no other parent
        for child in parent.childs:
            child.parents.remove(parent)
            if len(child.parents) == 0:
                self.deleteBranch(child)
        # delete data
        if parent.name in IMAGES_STACK.keys():
            del IMAGES_STACK[parent.name]
        # remove node from parent children
        for p in parent.parents:
            p.childs.remove(parent)
        # delete node and links
        parent.delete()
        del self.nodes[parent.name]

    def restoreGraph(self, settings):
        for k, values in settings.items():
            self.addNode(**values)

    def addNode(self, type, parents=[]):
        if not isinstance(parents, list):
            parents = [parents]
        for i, parent in enumerate(parents):
            if isinstance(parent, str):
                parents[i] = self.nodes[parent]
        name = self.getUniqueName(type)
        node = Node(self, type, name, parents)
        node.addToScene(self.scene)
        def emitNodeClick():
            if self.holdCtrl:
                node.select()
            elif node._state == 'pressed':
                self.nodeClicked.emit(node)

        node.button.clicked.connect(emitNodeClick)
        node.rightClicked.connect(lambda: self.openMenu(node))
        for i, parent in enumerate(parents):
            self.bind(parent, node)
            if i == 0:
                node.moveAt(parent.pos()+QtCore.QPointF(300, len(parent.childs)*350))
            parent.childs.append(node)
        if len(parents) == 0:
            node.moveAt(self._mouse_position+QtCore.QPoint(node.width()/2, 0))
        self.nodes[name] = node
        self.settings[name] = {'type': type, 'parents': [p.name for p in parents]}
        return node
