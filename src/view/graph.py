from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src.view import ui, CMAP, GRAPH_PARAMETERS
import os
import copy
from src import UI_DIR, IMAGES_STACK, _IMAGES_STACK
import numpy as np


class Link(QtWidgets.QGraphicsPolygonItem):
    """
    graphic line between two graphic points

    Parameters
    ----------
    junction1/junction2: Junction
        the two points to link

    """
    def __init__(self, parent, child, width=5, arrowWidth=10, arrowLen=10, space=20,
                 color=QtGui.QColor(0, 150, 0), borderWidth=2, borderColor=QtGui.QColor(0, 150, 0)):
        super().__init__()
        self._parent = parent
        self._child = child
        self.setZValue(-1)
        self.setPen(QtGui.QPen(borderColor, borderWidth))
        self.setBrush(color)
        self.width = width
        self.arrowWidth = arrowWidth
        self.arrowLen = arrowLen
        self.space = space
        self.updatePos()

    def intersects(self, line, rect, ref_position):
        points = [rect.bottomLeft(), rect.bottomRight(), rect.topRight(), rect.topLeft()]
        for i in range(4):
            border = QtCore.QLineF(ref_position + points[i-1], ref_position + points[i])
            intersect, intersection_point = line.intersects(border)
            if intersect == QtCore.QLineF.BoundedIntersection:
                return intersection_point
        return QtCore.QPointF()

    def updatePos(self):
        r1, r2 = self._parent.rect(), self._child.rect()
        line = QtCore.QLineF(self._parent.pos() + r1.center(),
                             self._child.pos() + r2.center())
        unit = (line.unitVector().p2() - line.unitVector().p1())
        normal = (line.normalVector().unitVector().p2() - line.normalVector().unitVector().p1())

        p1 = self.intersects(line, r1, self._parent.pos()) + unit * self.space
        p2 = self.intersects(line, r2, self._child.pos()) - unit * self.space

        p11 = p1 + normal * self.width
        p12 = p1 - normal * self.width
        p21 = p2 + normal * self.width - unit * self.arrowLen
        p22 = p2 - normal * self.width - unit * self.arrowLen
        p23 = p2 + normal * self.arrowWidth - unit * self.arrowLen
        p24 = p2 - normal * self.arrowWidth - unit * self.arrowLen

        if np.sign((p22 - p12).x()) == np.sign(unit.x()) and np.sign((p22 - p12).y()) == np.sign(unit.y()):
            self.setPolygon(QtGui.QPolygonF([p11, p21, p23, p2, p24, p22, p12, p11]))
        else:
            self.setPolygon(QtGui.QPolygonF([p23, p2, p24, p23]))


class Node(ui.QViewWidget):
    """
    movable widget inside the graph associated to a pipeline's step

    Parameters
    ----------
    graph: Graph
    type: str
        type of node associated to specific widget and functions
    name: str
        unique name
    parents: list of Node, default=[]
        nodes whose outputs are self input
    position: tuple, default=(0,0)
        position of the node in the graphic view

    """
    nameChanged = QtCore.pyqtSignal(str, str)

    def __init__(self, graph, type, name, parents=[], position=(0, 0), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidget(uic.loadUi(os.path.join(UI_DIR, "Node.ui")))
        self.graph = graph
        self.type = type
        self.name = name
        self.button.setText(name)
        self.snap.wheelEvent = self.snapWheelEvent
        self.snap.mouseDoubleClickEvent = self.snapMouseDoubleClickEvent
        self.snap.mousePressEvent = self.snapMousePressEvent
        self.snap.setVisible(False)

        self.positionChanged.connect(self.moveChilds)
        self.sizeChanged.connect(self.updateSnap)
        self.sizeChanged.connect(self.updateHeight)
        self.focused.connect(self.focusNode)

        self.current_branch = []
        self.childs = []
        self.parents = parents
        self.current_slice = None
        self.cmap = 'rednan'
        self.ctable = None
        self.snap_axis = 0
        self.links = []

    def updateHeight(self):
        """
        resize widget to its minimum height
        """
        self.resize(self.width(), self.minimumHeight())

    def moveChilds(self):
        """
        if shift is holded, move node childs with it
        """
        if self.graph.holdShift:
            if self.state == 'pressed':
                self.state = 'isMoving'
                self.updateCurrentBranch()
            if self.state == 'isMoving':
                delta = self.pos() - self.currentPosition
                self.currentPosition = self.pos()
                for child in self.current_branch:
                    child.moveBy(delta.x(), delta.y())

    def mousePressEvent(self, event=None):
        self.handle.setSelected(True)

    def mouseReleaseEvent(self, event=None):
        if not self.graph.holdCtrl:
            self.handle.setSelected(False)

    @property
    def mid_pos(self):
        return self.width()/2, self.height()/2

    def delete(self):
        """
        delete itself and all related graphic items (links and junctions)
        """
        for link in self.links:
            self.graph.scene.removeItem(link)
        self.graph.scene.removeItem(self.handle)
        self.proxy.deleteLater()
        self.deleteLater()

    def snapWheelEvent(self, event):
        """
        update image slice on scroll wheel above image view
        """
        if self.current_slice is not None:
            step = 1
            if event.angleDelta().y() > 0:
                self.current_slice += step
            else:
                self.current_slice -= step
            self.updateSnap()

    def snapMouseDoubleClickEvent(self, event):
        """
        update image axis on double click above image view
        """
        if self.snap_axis == 2:
            self.snap_axis = 0
        else:
            self.snap_axis += 1
        self.updateSnap()

    def snapMousePressEvent(self, event):
        """
        update pixel value and position labels when clicking snap view
        """
        # set ratio between image and qpixmap
        if self.name not in _IMAGES_STACK:
            return
        ratio = _IMAGES_STACK[self.name].shape[int(self.snap_axis == 0)] / self.snap.width()
        # get click position
        click_pos = np.array([event.pos().y(), event.pos().x()])
        # define position in image
        true_pos = np.rint(click_pos * ratio).astype(int)
        x, y, z = np.insert(true_pos, self.snap_axis, self.current_slice)
        # update labels with pixel value and position
        self.rightfoot.setText(str(_IMAGES_STACK[self.name][x, y, z])+" ")
        self.leftfoot.setText("{0} {1} {2}".format(x, y, z))

    def focusNode(self, boolean):
        self.graph.setEnabledScroll(not boolean)
        self.graph.focus = self if boolean else None

    def getChilds(self):
        """
        get all children

        Return
        ------
        childs: list of Node

        """
        childs = self.childs
        for child in self.childs:
            childs += child.getChilds()
        return childs

    def rename(self, new_name):
        if self.name in IMAGES_STACK:
            IMAGES_STACK[new_name] = IMAGES_STACK.pop(self.name)
            _IMAGES_STACK[new_name] = _IMAGES_STACK.pop(self.name)
        self.button.setText(new_name)
        self.nameChanged.emit(self.name, new_name)
        self.name = new_name

    def updateCurrentBranch(self):
        """
        update the current branch as a unique list of nodes
        """
        self.current_branch = set(self.getChilds())

    def getScaledColorTable(self, im):
        """
        compute the color table scaled between min and max of image pixel values

        Parameters
        ----------
        im: 2d/ 3d numpy array

        Return
        ------
        ctable: list of qRgb
            list of all colors associated to a pixel value
            first color for pixel=0, second color for pixel=1, ...

        """
        if self.ctable is None:
            values = np.linspace(0, 255, int(np.nanmax(im)-np.nanmin(im)+1)).astype(int)
            self.ctable = [QtGui.qRgb(i, i, i) for i in values]
        return self.ctable

    def updateSnap(self, sync=True):
        """
        update image slice in snap view

        Parameters
        ----------
        sync: bool, default=True
            if True, update the children and parents image view
            to the current slice recursively

        """
        if self.name not in IMAGES_STACK:
            return
        self.snap.setVisible(True)

        im = IMAGES_STACK[self.name]
        s = im.shape[self.snap_axis]

        # set current slice
        if self.current_slice is None:
            self.current_slice = int(s / 2)
        elif self.current_slice < 0:
            self.current_slice = 0
        elif self.current_slice >= s:
            self.current_slice = s-1

        # snap axis slice
        if self.snap_axis == 0:
            im_slice = im[self.current_slice].copy()
            _, h, w = im.shape
        elif self.snap_axis == 1:
            im_slice = im[:, self.current_slice].copy()
            h, _, w = im.shape
        elif self.snap_axis == 2:
            im_slice = im[:, :, self.current_slice].copy()
            h, w, _ = im.shape

        # define qimage
        qim = QtGui.QImage(im_slice, w, h, w, QtGui.QImage.Format_Indexed8)
        qim.setColorTable(CMAP[self.cmap])

        # scale pixmap to qlabel size
        pixmap = QtGui.QPixmap(qim)
        pixmap = pixmap.scaled(self.snap.width(), self.snap.width(),
                               QtCore.Qt.KeepAspectRatio,
                               QtCore.Qt.FastTransformation)

        self.snap.setPixmap(pixmap)
        self.snap.update()

        # synchronize parents and children
        if sync:
            for node in self.childs+self.parents:
                if node.current_slice != self.current_slice:
                    node.current_slice = self.current_slice
                    node.updateSnap(sync)
                elif node.snap_axis != self.snap_axis:
                    node.snap_axis = self.snap_axis
                    node.updateSnap(sync)


class Graph(QtWidgets.QWidget):
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
    nodeClicked = QtCore.pyqtSignal(Node)

    def __init__(self, mainwin, direction='horizontal'):
        super().__init__()
        self.mainwin = mainwin
        self.direction = direction
        uic.loadUi(os.path.join(UI_DIR, "Graph.ui"), self)
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.scene = QtWidgets.QGraphicsScene()
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setScene(self.scene)
        self.view.contextMenuEvent = lambda e: self.openMenu()
        self.view.setBackgroundBrush(GRAPH_PARAMETERS['backgroundBrush'])

        self.installEventFilter(self)
        self.holdShift = False
        self.holdCtrl = False
        self._mouse_position = QtCore.QPoint(0, 0)
        self.nodes = {}
        self.settings = {}
        self.focus = None

    def bind(self, parent, child):
        """
        create a link between a parent and a child node

        Parameters
        ----------
        parent, child: Node
            nodes to visually bind
        """
        # jout = parent.addJunction()
        # jin = child.addJunction()
        link = Link(parent, child)

        parent.positionChanged.connect(link.updatePos)
        parent.sizeChanged.connect(link.updatePos)
        child.positionChanged.connect(link.updatePos)
        child.sizeChanged.connect(link.updatePos)
        child.sizeChanged.emit()

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
        self.view.verticalScrollBar().setEnabled(enable_scroll)
        self.view.horizontalScrollBar().setEnabled(enable_scroll)

    def getSelectedNodes(self):
        """
        get all selected nodes (with ctrl+click shortcut)

        Return
        ------
        result: list of Node
        """
        return [n for n in self.nodes.values() if n.handle.isSelected()]

    def eventFilter(self, obj, event):
        """
        manage keyboard shortcut and mouse events on graph view
        """
        if obj == self:
            if event.type() == QtCore.QEvent.Wheel:
                return True
            elif event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = True
                elif event.key() == QtCore.Qt.Key_Control:
                    self.holdCtrl = True
            elif event.type() == QtCore.QEvent.KeyRelease:
                if event.key() == QtCore.Qt.Key_Shift:
                    self.holdShift = False
                elif event.key() == QtCore.Qt.Key_Control:
                    self.holdCtrl = False
        return super(Graph, self).eventFilter(obj, event)

    def getUniqueName(self, name, exception=None):
        """
        find an unused name by adding _n at the end of the name

        Parameters
        ----------
        name: str
            default non-unique name of the node
        exception: None or str
            if new name is exception, keep it

        Return
        ------
        new_name: str
            unique name for the node

        """
        i = 1
        new_name = copy.copy(name)
        while new_name in self.nodes and new_name != exception:
            new_name = "{0}_{1}".format(name, i)
            i += 1
        return new_name

    def openMenu(self, node=None):
        """
        open menu on right-clic at clicked position

        Parameters
        ----------
        node: Node, default None
            if None open a menu with primary actions (load, ...)
            else open a menu with secondary actions (erosion, ...)

        """
        node = self.focus
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
        menu = ui.menu_from_dict(acts, activation_function=activate)
        pos = QtGui.QCursor.pos()
        self._mouse_position = self.view.mapToScene(self.view.mapFromGlobal(pos))
        menu.exec_(QtGui.QCursor.pos())

    def renameNode(self, node):
        # open input dialog
        new_name, valid = QtWidgets.QInputDialog.getText(self, "user input", "new name",
                                                         QtWidgets.QLineEdit.Normal, node.type)
        if valid:
            new_name = self.getUniqueName(new_name, exception=node.name)
            self.nodes[new_name] = self.nodes.pop(node.name)
            node.rename(new_name)

    def deleteBranch(self, parent, childs_only=False):
        """
        delete node, its children and the associated data recursively

        Parameters
        ----------
        parent: Node
        child_only: bool, default=False
            if True do not delete the parent node else delete parent and children

        """
        # delete children if has no other parent
        for child in parent.childs:
            child.parents.remove(parent)
            if not child.parents:
                self.deleteBranch(child)
        # delete data
        if parent.name in IMAGES_STACK:
            del _IMAGES_STACK[parent.name]
            del IMAGES_STACK[parent.name]
        # remove node from parent children
        for p in parent.parents:
            p.childs.remove(parent)
        # delete node and links
        parent.delete()
        del self.nodes[parent.name]

    def restoreGraph(self, settings):
        """
        restore graph architecture

        Parameters
        ----------
        settings: dict
            the dict-like description of the graph

        """
        for k, values in settings.items():
            self.addNode(**values)

    def addNode(self, type, parents=[]):
        """
        create a Node with specified parent Nodes

        Parameters
        ----------
        type: str
            type of node
        parents: list of Node or Node

        """
        if not isinstance(parents, list):
            parents = [parents]
        for i, parent in enumerate(parents):
            if isinstance(parent, str):
                parents[i] = self.nodes[parent]
        name = self.getUniqueName(type)
        node = Node(self, type, name, parents,
                    handleColor=GRAPH_PARAMETERS['handleColor'],
                    handleSize=GRAPH_PARAMETERS['handleSize'])
        node.addToScene(self.scene, )

        node.button.clicked.connect(lambda: self.nodeClicked.emit(node))

        # resize widget in order to update widget minimum height
        node.button.clicked.connect(lambda: node.resize(node.width(), node.height()+1))

        if not parents:
            x, y = self._mouse_position.x(), self._mouse_position.y()
            node.moveBy(x, y)
        else:
            child_pos = None
            parent_pos = None
            for i, parent in enumerate(parents):
                self.bind(parent, node)
                if len(parent.childs) > 0:
                    pos = parent.childs[-1].pos()
                    if child_pos is None or pos.x() > child_pos.x():
                        child_pos = pos
                pos = parent.pos()
                if parent_pos is None or pos.x() > parent_pos.x():
                    parent_pos = pos
                parent.childs.append(node)

            if child_pos is None or parent_pos.x() >= child_pos.x():
                node.moveBy(parent_pos.x()+300, parent_pos.y())
            else:
                node.moveBy(child_pos.x(), child_pos.y()+400)

        self.nodes[name] = node
        self.settings[name] = {'type': type, 'parents': [p.name for p in parents]}
        return node
