from PyQt5 import QtWidgets, QtCore, QtGui


def menu_from_dict(acts, activation_function=None, menu=None):
    """
    create a menu on right-click, based on 'acts' dictionnary

    Parameters
    ----------
    acts: dict
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
    for a, subacts in acts.items():
        if not subacts:
            act = menu.addAction(a)
            if activation_function is not None:
                def connect(action):
                    action.triggered.connect(lambda: activation_function(action))
                connect(act)
        else:
            submenu = menu.addMenu(a)
            menu_from_dict(subacts, activation_function, submenu)
    return menu


def delete_layout(layout):
    """
    delete the selected layout

    Parameters
    ----------
    layout: QLayout

    """
    if layout is None:
        return
    empty_layout(layout)
    layout.deleteLater()
    QtCore.QObjectCleanupHandler().add(layout)


def empty_layout(layout):
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
            delete_layout(item.layout())


class QViewWidget(QtWidgets.QWidget):
    """
    resizable and movable widget inside QGraphicsScene

    Parameters
    ----------
    resizable: bool, default=True
        if True add a grip at the bootom right corner to resize the widget
    handleSize: tuple of 4 float, default=(0, -20, 0, 0)
        size of the handle to move the view widget (left, top, right, bottom)
    handleColor: QtGui.QColor, default=(180, 200, 180)
        rgb color of the handle

    """
    sizeChanged = QtCore.pyqtSignal()
    positionChanged = QtCore.pyqtSignal()

    def __init__(self, resizable=True, handleSize=(0, -20, 0, 0), handleColor=None):
        super().__init__()
        self.handleSize = handleSize
        self.handleColor = handleColor
        self._state = None
        self.currentPosition = None
        self.state = 'released'
        self.initUI(resizable)

    def initUI(self, resizable):
        """
        initialize widget with footer and handle

        Parameters
        ----------
        resizable: bool
            if True add sizegrip to footer
        """
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)

        # create left and right footer
        hbox = QtWidgets.QHBoxLayout()
        self.leftfoot = QtWidgets.QLabel()
        self.rightfoot = QtWidgets.QLabel()
        hbox.addWidget(self.leftfoot)
        hbox.addStretch(0)
        hbox.addWidget(self.rightfoot)

        # add size gripto footer  if rezizable
        if resizable:
            self.sizeGrip = QtWidgets.QSizeGrip(self)
            hbox.addWidget(self.sizeGrip)

        vbox.addWidget(QtWidgets.QWidget())
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        # create handle to move widget
        self.handle = self.RectItem(self)
        self.handle.setPen(QtGui.QPen(QtCore.Qt.transparent))
        if self.handleColor is not None:
            self.handle.setBrush(self.handleColor)

        # initialize self function from handle functions
        self.moveBy = self.handle.moveBy
        self.pos = self.handle.pos

        self.proxy = QtWidgets.QGraphicsProxyWidget(self.handle)
        self.proxy.setWidget(self)

    def setWidget(self, widget):
        """
        update the central widget with new widget

        Parameters
        ----------
        widget: QWidget
        """
        inter = set(widget.__dict__).intersection(set(self.__dict__))
        if inter:
            return print("FAILED setWidget: you cannot set widget in QViewWidget " +
                         "containing parameters like:\n " + " ".join(list(inter)))

        self.layout().replaceWidget(self.layout().itemAt(0).widget(), widget)
        self.__dict__.update(widget.__dict__)

    class RectItem(QtWidgets.QGraphicsRectItem):
        """
        graphic item which allow to move the widget in graphic view

        Parameters
        ----------
        parent: QViewWidget
        """
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
                self.parent.currentPosition = self.parent.handle.pos()
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

    def addToScene(self, scene):
        """
        add widget to a specified scene

        Parameters
        ----------
        handle_size: tuple of size 4
            (left, top, right, bottom)
        """
        self.sizeChanged.connect(lambda: self.handle.setRect(QtCore.QRectF(self.geometry().adjusted(*self.handleSize))))
        self.sizeChanged.emit()
        scene.addItem(self.handle)
