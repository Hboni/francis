from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src import DATA_DIR, OUT_DIR, IMAGES_STACK
import os
import numpy as np
from src import ui
import nibabel as nib
import copy
from src import core



def getParentNames(widget):
    """
    get parent names of the node associated to the widget
    """
    return [p.name for p in widget.node.parents]

def browseSavepath(widget):
    """
    open a browse window to define the nifti save path
    """
    name = getParentNames(widget)[0]
    filename, extension = QtWidgets.QFileDialog.getSaveFileName(widget, 'Save file',
                            os.path.join(OUT_DIR, name), filter=".nii.gz")
    widget.path.setText(filename+extension)

def saveImage(widget):
    """
    save the parent image as nifti file at specified path
    """
    name = getParentNames(widget)[0]
    ni_img = nib.Nifti1Image(IMAGES_STACK[name], None)
    nib.save(ni_img, widget.path.text())
    print("done")

def browseImage(widget):
    """
    open a browse window to select a nifti file
    then update path in the corresponding QLineEdit
    """
    global DATA_DIR
    dialog = QtWidgets.QFileDialog(widget)
    filename, _ = dialog.getOpenFileName(widget, "Select a file...", DATA_DIR)
    DATA_DIR = os.path.dirname(filename)
    widget.path.setText(filename)


def loadImage(widget):
    """
    load nifti file, store inside the IMAGES_STACK dictionnary
    and create the rendering widget to put image inside
    """
    im = nib.load(widget.path.text()).get_data().astype(np.uint8)
    render = ui.MRIrender(im)
    ui.emptyLayout(widget.visu)
    widget.visu.addWidget(render)
    IMAGES_STACK[widget.name.text()] = im

def updateErosion(widget):
    """
    compute 3d erosion on the parent image
    and store the eroded image into IMAGES_STACK dictionnary
    """
    im = core.erode(IMAGES_STACK[getParentNames(widget)[0]], widget.spin.value())

    if widget.visu.itemAt(0) is None:
        render = ui.MRIrender(im)
        widget.visu.addWidget(render)
    else:
        widget.visu.itemAt(0).widget().updateMRI(im)
    IMAGES_STACK[widget.name.text()] = im

def updateDilation(widget):
    """
    compute 3d dilation on the parent image
    and store the dilated image into IMAGES_STACK dictionnary
    """
    im = core.dilate(IMAGES_STACK[getParentNames(widget)[0]], widget.spin.value())

    if widget.visu.itemAt(0) is None:
        render = ui.MRIrender(im)
        widget.visu.addWidget(render)
    else:
        widget.visu.itemAt(0).widget().updateMRI(im)
    IMAGES_STACK[widget.name.text()] = im

def updateThreshold(widget):
    """
    compute 3d thresholding on the parent image
    and store the thresholded image into IMAGES_STACK dictionnary
    """
    im = core.applyThreshold(IMAGES_STACK[getParentNames(widget)[0]],
                             widget.spin.value(), widget.reversed.isChecked())

    if widget.visu.itemAt(0) is None:
        render = ui.MRIrender(im)
        widget.visu.addWidget(render)
    else:
        widget.visu.itemAt(0).widget().updateMRI(im)
    IMAGES_STACK[widget.name.text()] = im
