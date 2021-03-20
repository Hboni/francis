from PyQt5 import QtWidgets, uic, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from src import UI_DIR
import os
import numpy as np

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


"""
class MyLabel(QtWidgets.QLabel):
    cursorMoved = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setScaledContents(True)
        self.x, self.y = 0, 0
        self.flag = False
    def mousePressEvent(self, event):
        self.flag = True
        self.x, self.y = event.x(), event.y()
        self.update()
        self.cursorMoved.emit()
    def mouseReleaseEvent(self,event):
        self.flag = False
    def mouseMoveEvent(self,event):
        if self.flag:
            self.x, self.y = event.x(), event.y()
            self.update()
            self.cursorMoved.emit()
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, 1, QtCore.Qt.SolidLine))
        painter.drawLine(0, self.y, self.size().width(), self.y)
        painter.drawLine(self.x, 0, self.x, self.size().height())




class MRIrender(QtWidgets.QWidget):
    def __init__(self, mri):
        super().__init__()
        uic.loadUi(os.path.join(UI_DIR, 'MRIrender.ui'), self)
        self.ratios = [1,1,1]
        self._mri = mri
        self._true_shape = self._mri.shape
        self.slice_nums = [0, 0, 0]
        for i in range(3):
            self.initView(i)
            self.initSlider(i)

    def resizeEvent(self, event):
        _current_shape = [self.__dict__["view2"].itemAt(0).widget().size().width(),
                          self.__dict__["view1"].itemAt(0).widget().size().width(),
                          self.__dict__["view1"].itemAt(0).widget().size().height()]
        self.ratios = [j-i for i, j in zip(self._true_shape, _current_shape)]

    def updateMRI(self, mri):
        self._mri = mri
        for i in range(3):
            slider = self.__dict__["view{}_slider".format(i+1)]
            slider.valueChanged.emit(slider.value())


    def initView(self, i):
        label = MyLabel()
        label.setCursor(QtCore.Qt.CrossCursor)
        self.__dict__["view{}".format(i+1)].addWidget(label)
        check = self.__dict__["axis{}".format(i+1)]
        check.clicked.connect(lambda b: self.showWidget(b, i))
        check.clicked.emit(check.isChecked())
        nums = [0, 1, 2]
        nums.remove(i)
        label.cursorMoved.connect(lambda: self.setSlice(label.y, nums[0]))
        label.cursorMoved.connect(lambda: self.updateCursor(label.x, nums[0], line='vertical'))
        label.cursorMoved.connect(lambda: self.setSlice(label.x, nums[1]))
        label.cursorMoved.connect(lambda: self.updateCursor(label.y, nums[1], line='horizontal'))

    def showWidget(self, boolean, i):
        if boolean:
            self.__dict__["w{}".format(i+1)].show()
            self.setSlice(self.slice_nums[i], i)
        else:
            self.__dict__["w{}".format(i+1)].hide()



    def updateCursor(self, line_value, axis, line):
        label = self.__dict__['view{}'.format(axis+1)].itemAt(0).widget()
        if line == 'vertical':
            label.x = line_value
        else:
            label.y = line_value
        label.update()

    def initSlider(self, i):
        slider = self.__dict__["view{}_slider".format(i+1)]
        slider.setMaximum(self._mri.shape[i]-1)
        slider.valueChanged.connect(lambda v: self.setSlice(int(v), i))
        v = int(self._mri.shape[i]/2)
        slider.setValue(v)
        self.slice_nums[i] = v

    def setSlice(self, slice_num, axis):
        if not self.__dict__["axis{}".format(axis+1)].isChecked():
            return
        if 0 <= slice_num < self._mri.shape[axis]:
            if axis == 0:
                im = self._mri[slice_num].copy()
            elif axis == 1:
                im = self._mri[:,slice_num].copy()
            elif axis == 2:
                im = self._mri[:,:,slice_num].copy()
        else:
            return
        s1, s2 = [s for i, s in enumerate(self._mri.shape) if i != axis]
        qim = QtGui.QImage(im, s1, s2, QtGui.QImage.Format_Indexed8)
        pixmap = QtGui.QPixmap(qim)
        label = self.__dict__['view{}'.format(axis+1)].itemAt(0).widget()
        label.setPixmap(pixmap)
"""
