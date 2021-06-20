# Test of basic application usage

import pytest
from src.view.view import View
from src.presenter.presenter import Presenter


@pytest.fixture
def francis():
    # Launch Francis
    view = View()
    Presenter(view, threading_enabled=False)
    return view


@pytest.fixture
def load_module(qtbot, francis):
    load_image_module = 'LoadImage'
    qtbot.addWidget(francis)
    francis.graph.addModule(load_image_module)
    return francis.graph.modules[load_image_module]


def test_francis_launch(qtbot, francis):
    qtbot.addWidget(francis)
    assert not francis.graph.modules


def test_delete_module(qtbot, load_module, francis):
    francis.graph.deleteBranch(load_module)
    assert not francis.graph.modules


def test_add_modules(qtbot, francis):
    qtbot.addWidget(francis)
    parent_module = francis.graph.addModule('LoadImage')
    assert len(francis.graph.modules) == 1

    francis.graph.addModule('ThresholdImage', parent_module)
    assert len(francis.graph.modules) == 2
