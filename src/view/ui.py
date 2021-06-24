from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src.view import utils
from src import RSC_DIR
import os
import numpy as np
import traceback
import copy


def setButtonIcon(button, img, append=False):
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(os.path.join(RSC_DIR, "icon", img)), QtGui.QIcon.Normal, QtGui.QIcon.On)
    if not append:
        button.setText("")
    button.setIcon(icon)
    button.setFlat(True)
    button.setCursor(QtCore.Qt.PointingHandCursor)


def showError(level, error):
    """
    level: {NoIcon, Qestion, Information, Warning, Critical}
    """
    msg = "{0}\n{1}".format(type(error).__name__, error)
    dialog = QtWidgets.QMessageBox(eval("QtWidgets.QMessageBox."+level),
                                   level, msg, QtWidgets.QMessageBox.Ok)
    dialog.setDetailedText("".join(traceback.format_tb(error.__traceback__)[1:]))
    dialog.exec()


class QGrap(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QtCore.QEvent.Leave:
                QtWidgets.QApplication.restoreOverrideCursor()
            if event.type() in [QtCore.QEvent.Enter, QtCore.QEvent.MouseButtonRelease]:
                # !!! mouse release is not detected because its event is rejected !!!
                QtWidgets.QApplication.restoreOverrideCursor()
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)
            elif event.type() == QtCore.QEvent.MouseButtonPress:
                QtWidgets.QApplication.restoreOverrideCursor()
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.ClosedHandCursor)
        return QtWidgets.QWidget.eventFilter(self, obj, event)


class QFormatLine(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(RSC_DIR, 'ui', 'modules', 'bricks', 'formatLine.ui'), self)

        self.types.currentIndexChanged.connect(self.hideFormat)
        self.format.hide()

        self.types.currentIndexChanged.connect(self.hideUnit)
        self.unit.hide()

    def hideFormat(self):
        self.format.show() if self.types.currentText() == 'datetime' else self.format.hide()

    def hideUnit(self):
        self.unit.show() if self.types.currentText() == 'timedelta' else self.unit.hide()


class QTypeForm(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.form = QtWidgets.QFormLayout()
        self.setLayout(self.form)
        self.rows = {}

    def addRow(self, name):
        row = uic.loadUi(os.path.join(RSC_DIR, 'ui', 'modules', 'bricks', 'formatLine.ui'))
        row.types.currentTextChanged.connect(lambda txt: self.hideDetails(row, txt))
        row.format.hide()
        row.unit.hide()

        self.form.addRow(name, row)
        self.rows[name] = row

    def addRows(self, names):
        for name in names:
            self.addRow(name)

    def hideDetails(self, row, txt):
        row.format.hide()
        row.unit.hide()
        if txt == 'datetime':
            row.format.show()
        elif txt == 'timedelta':
            row.unit.show()


class QGridButtonGroup(QtWidgets.QWidget):
    def __init__(self, max_col=3, max_row=None):
        super().__init__()
        self._grid = QtWidgets.QGridLayout()
        self.group = QtWidgets.QButtonGroup()
        self.max_col = max_col
        self.max_row = max_row
        self._current_row, self._current_col = 0, 0
        self.setLayout(self._grid)

    def checkFirst(self):
        if self.group.buttons():
            self.group.buttons()[0].setChecked(True)

    def checkAll(self, state=True):
        for b in self.group.buttons():
            b.setChecked(state)

    def checkedButtonText(self):
        checked_button = self.group.checkedButton()
        if checked_button:
            return checked_button.text()

    def checkedButtonsText(self):
        checked_buttons = []
        for b in self.group.buttons():
            if b.isChecked():
                checked_buttons.append(b.text())
        return checked_buttons

    def computePositions(self, n):
        if self.max_row is None and self.max_col is None:
            return np.ceil(np.sqrt(n)), np.ceil(np.sqrt(n))
        elif self.max_row is not None:
            return np.ceil(n / self.max_row), self.max_row
        elif self.max_col is not None:
            return np.ceil(n / self.max_col), self.max_col

    def addWidgets(self, widget_type, names, checkable=True):
        if widget_type in [QtWidgets.QPushButton, QtWidgets.QCheckBox]:
            self.group.setExclusive(False)
        positions = self.computePositions(len(names))
        i = 0
        for row in range(int(positions[0])):
            for col in range(int(positions[1])):
                if i < len(names):
                    widget = widget_type(names[i])
                    if checkable and isinstance(widget, QtWidgets.QPushButton):
                        widget.setCheckable(True)
                    self._grid.addWidget(widget, row, col)
                    self.group.addButton(widget)
                    i += 1


class QCustomTableWidget(QtWidgets.QWidget):
    def __init__(self, data=None):
        super().__init__()
        uic.loadUi(os.path.join(RSC_DIR, 'ui', 'TableWidget.ui'), self)
        setButtonIcon(self.save, "save.png")
        setButtonIcon(self.release, "release.png")
        setButtonIcon(self.quickPlot, "plot.png")

        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        if data is not None:
            self.setData(data)

    def updateVheader(self, index):
        model = PandasModel(self.data, index-1)
        proxyModel = QtCore.QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        self.table.setModel(proxyModel)

    def setData(self, data):
        try:
            self.Vheader.addItems([''] + list(data.columns.astype(str)))
        except TypeError:
            pass
        self.Vheader.currentIndexChanged.connect(self.updateVheader)
        self.rightfoot.setText("{0} x {1}    ({2} {3})".format(*data.shape, *utils.getMemoryUsage(data)))
        self.leftfoot.hide()
        self.data = data
        self.updateVheader(0)


class QImageRenderer(QtWidgets.QLabel):
    syncSignal = QtCore.pyqtSignal()

    def __init__(self, img, parent):
        QtWidgets.QWidget.__init__(self)
        self.img = self.formatImage(img)
        self.dimension = len(self.img.shape)
        if self.dimension == 3:
            self.axis = 0
            self.currentSlice = None
        self.pixmap = None
        self._parent = parent
        self.updateSnap()

    def formatImage(self, img):
        img = img.astype(np.float64) if img.dtype != np.float64 else copy.copy(img)
        img[np.isinf(img)] = np.nan

        # scale image in range (1, 255)
        mini, maxi = np.nanmin(img), np.nanmax(img)
        if mini == maxi:
            mini = 0
            maxi = max(maxi, 1)
        img = (img - mini) / (maxi - mini) * 254 + 1

        # set 0 as nan values
        img[np.isnan(img)] = 0

        # convert and store
        img = img.astype(np.uint8)
        return img

    def wheelEvent(self, event):
        if self.dimension != 3:
            return
        if self.currentSlice is not None:
            step = 1
            if event.angleDelta().y() > 0:
                self.currentSlice += step
            else:
                self.currentSlice -= step
        self.updateSnap()
        self.syncSignal.emit()

    def mouseDoubleClickEvent(self, event):
        """
        update image axis on double click above image view
        """
        if self.dimension != 3:
            return
        if self.axis == 2:
            self.axis = 0
        else:
            self.axis += 1
        self.updateSnap()
        self.syncSignal.emit()

    def getSliceParams(self):
        if self.dimension == 2:
            return self.img, self.img.shape[1], self.img.shape[0]
        elif self.dimension == 3:
            s = self.img.shape[self.axis]

            # set current slice
            if self.currentSlice is None:
                self.currentSlice = int(s / 2)
            elif self.currentSlice < 0:
                self.currentSlice = 0
            elif self.currentSlice >= s:
                self.currentSlice = s-1

            # snap axis slice
            if self.axis == 0:
                im_slice = self.img[self.currentSlice].copy()
                _, h, w = self.img.shape
            elif self.axis == 1:
                im_slice = self.img[:, self.currentSlice].copy()
                h, _, w = self.img.shape
            elif self.axis == 2:
                im_slice = self.img[:, :, self.currentSlice].copy()
                h, w, _ = self.img.shape

            return im_slice, w, h

    def updateSnap(self):
        im, w, h = self.getSliceParams()
        qim = QtGui.QImage(im, w, h, w, QtGui.QImage.Format_Indexed8)
        qim.setColorTable([QtGui.qRgba(255, 0, 0, 255)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)])
        self.pixmap = QtGui.QPixmap(qim)
        self.pixmap = self.pixmap.scaledToWidth(self._parent.width() - 2,
                                                QtCore.Qt.FastTransformation)
        self.setPixmap(self.pixmap)
        self.update()


class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, df, header_index=-1, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        if header_index == -1:
            self._data = df
        else:
            header_colname = df.columns[header_index]
            self._data = df.set_index(header_colname)

    def format(self, value):
        return '' if str(value) in ['nan', 'NaT'] else str(value)

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return self.format(self._data.iloc[index.row(), index.column()])

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.format(self._data.columns[col])
        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self.format(self._data.index[col])


class QMultiWidget(QtWidgets.QWidget):
    def __init__(self, widgets=[], names=[]):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.tab = QtWidgets.QTabWidget()
        layout.addWidget(self.tab)
        self.apply = QtWidgets.QPushButton('apply')
        layout.addWidget(self.apply)
        self.setLayout(layout)
        self.widgets = {}
        for widget, name in zip(widgets, names):
            self.addWidget(widget, name)

    def addWidget(self, widget, name):
        self.tab.addTab(widget, name)
        self.tab.setCurrentIndex(0)
        self.widgets[name] = widget
        return widget


class QCustomSizeGrip(QtWidgets.QSizeGrip):
    def __init__(self, parent):
        super(QCustomSizeGrip, self).__init__(parent)
        self._parent = parent

    def mouseMoveEvent(self, event=None):
        if event is None:
            x, y = 0, 0
        else:
            x, y = event.pos().x(), event.pos().y()

        if self._parent.resultArea.isHidden():
            height = 1
        elif isinstance(self._parent.result, QImageRenderer):
            s = self._parent.result.pixmap.size()
            areaWidth = self._parent.resultArea.width()
            calculatedAreaHeight = areaWidth * s.height() / s.width()
            height = calculatedAreaHeight + self._parent.height() - self._parent.resultArea.height()
            self._parent.result.updateSnap()
        else:
            height = self._parent.height() + y

        self._parent.resize(self._parent.width() + x, height)


class QCustomDialog(QtWidgets.QDialog):
    def __init__(self, title, uipath, parent=None):
        super(QCustomDialog, self).__init__(parent)
        uic.loadUi(uipath, self)
        self.setWindowTitle(title)
        self.out = None
        self.initConnections()

    def initConnections(self):
        def connect(widget):
            w.clicked.connect(lambda: self.accept(widget.text()))
        for w in self.__dict__.values():
            if isinstance(w, QtWidgets.QPushButton):
                connect(w)

    def accept(self, out):
        self.out = out
        QtWidgets.QDialog.accept(self)
