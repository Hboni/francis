from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src import DATA_DIR, IMAGES_STACK
import os
import numpy as np
from src import ui
import nibabel as nib
import copy
from src import core



def getParentNames(widget):
    return [p.name for p in widget.node.parents]


def browseImage(widget):
    global DATA_DIR
    dialog = QtWidgets.QFileDialog(widget)
    filename, _ = dialog.getOpenFileName(widget, "Select a file...", DATA_DIR)
    DATA_DIR = os.path.dirname(filename)
    widget.path.setText(filename)


def loadImage(widget):
    im = nib.load(widget.path.text()).get_data().astype(np.uint8)
    render = ui.MRIrender(im)
    widget.visu.addWidget(render)
    IMAGES_STACK[widget.name.text()] = im

def updateErosion(widget):
    # initialize
    im = core.erode(IMAGES_STACK[getParentNames(widget)[0]], widget.spin.value())

    if widget.visu.itemAt(0) is None:
        render = ui.MRIrender(im)
        widget.visu.addWidget(render)
    else:
        widget.visu.itemAt(0).widget().updateMRI(im)
    IMAGES_STACK[widget.name.text()] = im
