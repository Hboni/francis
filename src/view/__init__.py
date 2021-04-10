from PyQt5 import QtGui, QtCore

CMAP = {
    'binary': [QtGui.qRgba(0, 0, 0, 255), QtGui.qRgba(255, 255, 255, 255)],
    'rednan': [QtGui.qRgba(255, 0, 0, 255)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)],  # nans are red
    'classic': [QtGui.qRgba(0, 0, 0, 0)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)]  # nans are transparent
}

GRAPH_PARAMETERS = {
    "backgroundBrush": QtGui.QBrush(QtGui.QColor(0, 0, 0, 10), QtCore.Qt.CrossPattern),

    "handleSize": (0, -20, 0, 0),  # left, top, right, bottom
    "handleColor": QtGui.QColor(180, 200, 180, 180),  # r, g, b, alpha

    "junctionSize": (5, 5),  # in, out
    "junctionColor": (QtGui.QColor(0, 150, 0), QtGui.QColor(0, 150, 0, 0)),  # int, out

    "lineWidth": 2,
    "lineColor": QtGui.QColor(0, 150, 0),
    "lineDegree": 40,
}
