from PyQt5 import QtGui, QtCore

STYLE_SHEET = "AMOLED.qss"
STYLE_SHEET = "Aqua.qss"
STYLE_SHEET = "ConsoleStyle.qss"
STYLE_SHEET = "ElegantDark.qss"
STYLE_SHEET = "Fibrary.qss"
STYLE_SHEET = "Hookmark.qss"
STYLE_SHEET = "ManjaroMix.qss"
STYLE_SHEET = "NeonButtons.qss"
STYLE_SHEET = "SpyBot.qss"
STYLE_SHEET = "Toolery.qss"
STYLE_SHEET = "Ubuntu.qss"
STYLE_SHEET = "MaterialDark.qss"
STYLE_SHEET = "MacOS.qss"
STYLE_SHEET = None

CMAP = {
    'binary': [QtGui.qRgba(0, 0, 0, 255), QtGui.qRgba(255, 255, 255, 255)],
    'rednan': [QtGui.qRgba(255, 0, 0, 255)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)],  # nans are red
    'classic': [QtGui.qRgba(0, 0, 0, 0)]+[QtGui.qRgba(i, i, i, 255) for i in range(1, 256)]  # nans are transparent
}


GRAPH_PARAMETERS = {
    "backgroundBrush": QtGui.QBrush(QtGui.QColor(0, 0, 0, 10), QtCore.Qt.CrossPattern),

    "handleSize": (0, -20, 0, 0),  # left, top, right, bottom
    "handleColor": QtGui.QColor(150, 150, 150, 180),  # r, g, b, alpha

    "junctionSize": (5, 5),  # in, out
    "junctionColor": (QtGui.QColor(150, 150, 150), QtGui.QColor(150, 150, 150)),  # int, out

    "lineWidth": 2,
    "lineColor": QtGui.QColor(150, 150, 150),
    "lineDegree": 40,
}
