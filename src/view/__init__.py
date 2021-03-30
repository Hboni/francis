from PyQt5 import QtGui

CMAP = {
    'binary': [QtGui.qRgba(0, 0, 0, 255), QtGui.qRgba(255, 255, 255, 255)],
    'rednan': [QtGui.qRgba(255, 0, 0, 255)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)],  # nans are red
    'classic': [QtGui.qRgba(0, 0, 0, 0)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)]  # nans are transparent
}
