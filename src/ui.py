from PyQt5 import QtWidgets, uic, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from src import UI_DIR
import os
import numpy as np

def menuFromDict(acts, activation_function=None, menu=None):
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

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


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
        for i in range(3):
            self.initView(i)
            self.initSlider(i)

    def resizeEvent(self, event):
        _current_shape = [self.__dict__["view1"].itemAt(0).widget().size().width(),
                               self.__dict__["view0"].itemAt(0).widget().size().width(),
                               self.__dict__["view0"].itemAt(0).widget().size().height()]
        self.ratios = [j-i for i, j in zip(self._true_shape, _current_shape)]

    def updateMRI(self, mri):
        self._mri = mri
        for i in range(3):
            slider = self.__dict__["view{}_slider".format(i)]
            slider.valueChanged.emit(slider.value())


    def initView(self, i):
        label = MyLabel()
        label.setCursor(QtCore.Qt.CrossCursor)
        self.__dict__["view{}".format(i)].addWidget(label)
        nums = [0, 1, 2]
        nums.remove(i)
        label.cursorMoved.connect(lambda: self.setSlice(label.y, nums[0]))
        label.cursorMoved.connect(lambda: self.updateCursor(label.x, nums[0], line='vertical'))
        label.cursorMoved.connect(lambda: self.setSlice(label.x, nums[1]))
        label.cursorMoved.connect(lambda: self.updateCursor(label.y, nums[1], line='horizontal'))

    def updateCursor(self, line_value, axis, line):
        label = self.__dict__['view{}'.format(axis)].itemAt(0).widget()
        if line == 'vertical':
            label.x = line_value
        else:
            label.y = line_value
        label.update()

    def initSlider(self, i):
        slider = self.__dict__["view{}_slider".format(i)]
        slider.setMaximum(self._mri.shape[i]-1)
        slider.valueChanged.connect(lambda v: self.setSlice(int(v), i))
        slider.setValue(int(self._mri.shape[i]/2))

    def setSlice(self, slice_num, axis):
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
        label = self.__dict__['view{}'.format(axis)].itemAt(0).widget()
        label.setPixmap(pixmap)
