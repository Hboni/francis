# Test of basic application usage

import pytest
import os

from src.view.app import MainWindow
from src.controller.connection import Connector
from PyQt5 import QtCore


@pytest.fixture(scope='module')
def test_image_path():
    return os.path.join(os.getcwd(),
                        'data/cvs_avg35_inMNI152.nii.gz')


@pytest.fixture(scope='module')
def test_image_write_path():
    saved_path = os.path.join(os.getcwd(),
                              'data/saved_image.nii.gz')
    if os.path.exists(saved_path):
        os.remove(saved_path)
    return saved_path


@pytest.fixture
def francis():
    # Launch Francis
    win = MainWindow()
    conn = Connector()
    conn.connect_view_to_model(win)
    return win


@pytest.fixture
def load_node(qtbot, francis):
    load_image_node = 'load image'
    qtbot.addWidget(francis)
    francis.graph.addNode(load_image_node)
    return francis.graph.nodes[load_image_node]


def test_francis_launch(qtbot, francis):
    # win = MainWindow()
    # win.show()
    qtbot.addWidget(francis)

    assert not francis.graph.nodes


def test_load_image(qtbot, francis, load_node, test_image_path):
    """Select load image node and load the demonstration image"""

    # Click on Load image btn
    with qtbot.waitSignal(francis.graph.nodeClicked,
                          timeout=2000,
                          raising=True):
        qtbot.mouseClick(load_node.button,
                         QtCore.Qt.LeftButton)
    # Fill the widget with the image path
    load_node.parameters.itemAt(0).widget().path.setText(test_image_path)

    # Click on apply
    qtbot.mouseClick(load_node.parameters.itemAt(0).widget().apply,
                     QtCore.Qt.LeftButton)

    assert len(francis.graph.nodes) == 1
    # As the window is not displayed, the value load_node.snap.isVisible is False
    assert load_node.current_slice is not None


def test_save_image(qtbot, load_node, francis,
                    test_image_path, test_image_write_path):

    # Click on Load image btn
    with qtbot.waitSignal(francis.graph.nodeClicked,
                          timeout=2000,
                          raising=True):
        qtbot.mouseClick(load_node.button,
                         QtCore.Qt.LeftButton)
    # Fill the widget with the image path
    load_node.parameters.itemAt(0).widget().path.setText(test_image_path)

    # Click on apply
    qtbot.mouseClick(load_node.parameters.itemAt(0).widget().apply,
                     QtCore.Qt.LeftButton)
    francis.graph.addNode('save image', load_node)
    save_node = francis.graph.nodes['save image']

    with qtbot.waitSignal(francis.graph.nodeClicked,
                          timeout=2000,
                          raising=True):
        qtbot.mouseClick(save_node.button,
                         QtCore.Qt.LeftButton)

    save_node.parameters.itemAt(0).widget().path.setText(test_image_write_path)
    qtbot.mouseClick(save_node.parameters.itemAt(0).widget().apply,
                     QtCore.Qt.LeftButton)

    assert len(francis.graph.nodes) == 2
    assert os.path.exists(test_image_write_path)


def test_delete_node(qtbot, load_node, francis):
    francis.graph.deleteBranch(load_node)
    assert not francis.graph.nodes


def test_add_nodes(qtbot, francis):
    qtbot.addWidget(francis)
    parent_node = francis.graph.addNode('load image')
    assert len(francis.graph.nodes) == 1

    francis.graph.addNode('multiply images', parent_node)
    assert len(francis.graph.nodes) == 2
