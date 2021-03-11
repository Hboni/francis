# Test of basic application usage

import pytest
from src.app import MainWindow
from PyQt5 import QtCore


@pytest.fixture
def francis():
    # Launch Francis
    return MainWindow()


def test_francis_launch(qtbot, francis):
    # win = MainWindow()
    # win.show()
    qtbot.addWidget(francis)


def test_load_image(qtbot, francis):
    # win = MainWindow()
    qtbot.addWidget(francis)
    qtbot.mouseClick(francis, QtCore.Qt.RightButton)
