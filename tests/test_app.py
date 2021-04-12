# Test of basic application usage

import pytest
import os

from src.view.app import MainWindow
from src.controller.connection import Connector
from PyQt5 import QtCore


@pytest.fixture
def test_image_path():
    return os.path.join(os.getcwd(),
                        'data/cvs_avg35_inMNI152.nii.gz')


@pytest.fixture
def francis():
    # Launch Francis
    win = MainWindow()
    conn = Connector()
    conn.connect_view_to_model(win)
    return win


def test_francis_launch(qtbot, francis):
    # win = MainWindow()
    # win.show()
    qtbot.addWidget(francis)

    assert not francis.graph.nodes


def test_load_image(qtbot, francis, test_image_path):
    """Select load image node and load the demonstration image"""
    load_image_node = 'load image'
    qtbot.addWidget(francis)
    francis.graph.addNode(load_image_node)

    # Click on Load image btn
    with qtbot.waitSignal(francis.graph.nodeClicked,
                          timeout=2000,
                          raising=True):
        qtbot.mouseClick(francis.graph.nodes[load_image_node].button,
                         QtCore.Qt.LeftButton)
    # Fill the widget with the image path
    assert os.path.exists(test_image_path)
    francis.graph.nodes[load_image_node].path = test_image_path
    # Click on apply
    qtbot.mouseClick(francis.graph.nodes[load_image_node].parameters.itemAt(0).widgets.apply,
                     QtCore.Qt.LeftButton)

    assert len(francis.graph.nodes) == 1


def test_add_nodes(qtbot, francis):
    qtbot.addWidget(francis)
    francis.graph.addNode('multiply image')
    assert len(francis.graph.nodes) == 1
    francis.graph.addNode('load image')
    assert len(francis.graph.nodes) == 2
