from PyQt5 import QtWidgets, uic, QtCore, QtGui


def menuFromDict(acts, activation_function=None, menu=None):
    """
    create a menu on right-click, based on 'acts' dictionnary

    Parameters
    ----------
    acts: list or dict
        actions to insert in menu
    activation_function: function, optionnal
        function that takes a QAction as argument and apply the requested action
    menu: QMenu, optionnal
        menu to fill

    Return
    ------
    menu: QMenu

    """
    if menu is None:
        menu = QtWidgets.QMenu()
    for a in acts:
        if a is None:
            menu.addSeparator()
        elif isinstance(a, dict):
            for suba, subacts in a.items():
                submenu = menu.addMenu(suba)
                menuFromDict(subacts, activation_function, submenu)
        else:
            act = menu.addAction(a)
            if activation_function is not None:
                def connect(action, s):
                    action.triggered.connect(lambda: activation_function(action))
                connect(act, a)
    return menu


def deleteLayout(layout):
    """
    delete the selected layout

    Parameters
    ----------
    layout: QLayout

    """
    if layout is None:
        return
    emptyLayout(layout)
    layout.deleteLater()
    QtCore.QObjectCleanupHandler().add(layout)


def emptyLayout(layout):
    """
    delete all children (widget and layout) of the selected layout

    Parameters
    ----------
    layout: QLayout
    """
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            deleteLayout(item.layout())


class QViewWidget(QtWidgets.QWidget):
    sizeChanged = QtCore.pyqtSignal()
    positionChanged = QtCore.pyqtSignal()

    def __init__(self, ui_path):
        super().__init__()
        uic.loadUi(ui_path, self)
        self._state = None
        self.current_position = None
        self.state = 'released'
        self.initUI()

    def initUI(self):
        # add size grip
        sizeGrip = QtWidgets.QSizeGrip(self)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sizeGrip, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.vbox.addLayout(layout)

        # create handle to move widget
        self.handle = self.RectItem(self)
        self.handle.setPen(QtGui.QPen(QtCore.Qt.transparent))

        # initialize self function from handle functions
        self.moveBy = self.handle.moveBy
        self.pos = self.handle.pos

        self.proxy = QtWidgets.QGraphicsProxyWidget(self.handle)
        self.proxy.setWidget(self)

    class RectItem(QtWidgets.QGraphicsRectItem):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                          QtWidgets.QGraphicsItem.ItemIsFocusable |
                          QtWidgets.QGraphicsItem.ItemIsSelectable |
                          QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges)

        def itemChange(self, change, value):
            if change in [QtWidgets.QGraphicsItem.ItemPositionChange,
                          QtWidgets.QGraphicsItem.ItemVisibleChange]:
                self.parent.positionChanged.emit()
                self.parent.current_position = self.parent.handle.pos()
            return QtWidgets.QGraphicsRectItem.itemChange(self, change, value)

        def mousePressEvent(self, event=None):
            self.parent.state = 'pressed'
            self.setSelected(True)
            return QtWidgets.QGraphicsRectItem.mousePressEvent(self, event)

        def mouseReleaseEvent(self, event=None):
            self.parent.state = 'released'
            self.setSelected(False)
            return QtWidgets.QGraphicsRectItem.mouseReleaseEvent(self, event)

    def resizeEvent(self, event):
        self.sizeChanged.emit()
        return QtWidgets.QWidget.resizeEvent(self, event)

    def addToScene(self, scene, handle_size=(0, -20, 0, 0), color=(180, 200, 180)):
        """
        Parameters
        ----------
        handle_size: tuple of size 4
            (left, top, right, bottom)
        """
        self.handle.setBrush(QtGui.QColor(*color))
        self.sizeChanged.connect(lambda: self.handle.setRect(QtCore.QRectF(self.geometry().adjusted(*handle_size))))
        self.sizeChanged.emit()
        scene.addItem(self.handle)
