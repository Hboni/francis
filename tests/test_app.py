# Test of basic application usage

import os

import numpy as np
import pytest
from PyQt5 import QtCore

from src.model.model import Model
from src.presenter.presenter import Presenter
from src.view.view import View


@pytest.fixture
def francis():
    # Launch Francis
    view = View(nopopup=True)
    model = Model()
    Presenter(view, model, threading_enabled=False)
    view.newFile()
    return view


@pytest.fixture
def load_module(qtbot, francis):
    load_module_name = "Load"
    qtbot.addWidget(francis)
    francis.graph().addModule(load_module_name)
    return francis.graph().modules[load_module_name]


@pytest.fixture(params=[2, 3])
def image_test(request):
    if request.param == 2:
        img = np.zeros((100, 100))
        img[25:75, 25:75] = 1
    elif request.param == 3:
        img = np.zeros((100, 100, 100))
        img[25:75, 25:75, 25:75] = 1
    return img


@pytest.fixture(
    params=[
        os.path.join(os.getcwd(), "resources/data/Lena.png"),
        os.path.join(os.getcwd(), "resources/data/cvs_avg35_inMNI152.nii.gz"),
    ]
)
def image_filepath(request):
    return request.param


@pytest.fixture()
def text_filepath():
    return os.path.join(os.getcwd(), "resources/data/simple_text.txt")


def test_francis_launch(qtbot, francis):
    qtbot.addWidget(francis)
    assert not francis.graph().modules


def test_delete_module(qtbot, load_module, francis):
    francis.graph().deleteBranch(load_module)
    assert not francis.graph().modules


def test_add_modules(qtbot, francis):
    qtbot.addWidget(francis)
    parent_module = francis.graph().addModule("Load")
    assert len(francis.graph().modules) == 1

    francis.graph().addModule("ThresholdImage", parent_module)
    assert len(francis.graph().modules) == 2


def test_show_text(qtbot, francis, load_module, text_filepath):
    qtbot.keyClicks(load_module.parameters.path, text_filepath)
    with qtbot.waitSignal(load_module.displayed, timeout=10000):
        qtbot.mouseClick(load_module.play, QtCore.Qt.LeftButton)

    assert len(francis.graph().modules) == 1
    assert load_module.result.toPlainText()


def test_show_image(qtbot, francis, load_module, image_test):
    """Select load image node and load the demonstration image"""
    load_module.showResult(image_test)
    assert len(francis.graph().modules) == 1
    # As the window is not displayed, the value load_node.snap.isVisible is False
    assert load_module.result.pixmap is not None


def test_image_click(qtbot, francis, load_module, image_filepath):
    assert not load_module.rightfoot.text()
    assert not load_module.leftfoot.text()

    qtbot.keyClicks(load_module.parameters.path, image_filepath)
    with qtbot.waitSignal(load_module.displayed, timeout=10000):
        qtbot.mouseClick(load_module.play, QtCore.Qt.LeftButton)
    # Click on the image
    qtbot.mouseClick(load_module.result, QtCore.Qt.LeftButton)

    assert load_module.rightfoot.text()
    assert load_module.leftfoot.text()
