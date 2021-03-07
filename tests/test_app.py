# Test of basic application usage

from src.app import MainWindow


def test_francis_launch(qtbot):
    win = MainWindow()
    win.show()
    qtbot.addWidget(win)
