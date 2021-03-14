from PyQt5 import QtWidgets, uic, QtCore, QtGui
from src import DATA_DIR, OUT_DIR, IMAGES_STACK
import os
import numpy as np
import nibabel as nib
import copy
from src.model import core

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
    filename, extension = QtWidgets.QFileDialog.getSaveFileName(widget.parent().parent(), 'Save file',
                            os.path.join(OUT_DIR, name), filter=".nii.gz")
    widget.path.setText(filename+extension)
    widget.path.setToolTip(filename+extension)

def saveImage(widget):
    """
    save the parent image as nifti file at specified path
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in IMAGES_STACK.keys():
        return print("'{}' not in image stack".format(parent_name))
    ni_img = nib.Nifti1Image(IMAGES_STACK[parent_name], None)
    nib.save(ni_img, widget.path.text())
    print("done")

def browseImage(widget):
    """
    open a browse window to select a nifti file
    then update path in the corresponding QLineEdit
    """
    global DATA_DIR
    dialog = QtWidgets.QFileDialog()
    filename, _ = dialog.getOpenFileName(widget.parent().parent(), "Select a file...", DATA_DIR)
    DATA_DIR = os.path.dirname(filename)
    widget.path.setText(filename)
    widget.path.setToolTip(filename)

def loadImage(widget):
    """
    load nifti file, store inside the IMAGES_STACK dictionnary
    and create the rendering widget to put image inside
    """
    im = nib.load(widget.path.text()).get_data().astype(np.uint8)
    print("image description:\nshape: {0}\ndtype: {1}\nunique values: {2}".format(im.shape, im.dtype, np.unique(im)))
    if len(im.shape) != 3:
        return "for now loaded images must be of size 3"
    IMAGES_STACK[widget.node.name] = im
    widget.node.updateSnap()

def updateErosion(widget):
    """
    compute 3d erosion on the parent image
    and store the eroded image into IMAGES_STACK dictionnary
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in IMAGES_STACK.keys():
        return print("'{}' not in image stack".format(parent_name))
    im = core.erode(IMAGES_STACK[parent_name], widget.spin.value())
    IMAGES_STACK[widget.node.name] = im
    widget.node.updateSnap()

def updateDilation(widget):
    """
    compute 3d dilation on the parent image
    and store the dilated image into IMAGES_STACK dictionnary
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in IMAGES_STACK.keys():
        return print("'{}' not in image stack".format(parent_name))
    im = core.dilate(IMAGES_STACK[parent_name], widget.spin.value())
    IMAGES_STACK[widget.node.name] = im
    widget.node.updateSnap()

def updateThreshold(widget):
    """
    compute 3d thresholding on the parent image
    and store the thresholded image into IMAGES_STACK dictionnary
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in IMAGES_STACK.keys():
        return print("'{}' not in image stack".format(parent_name))
    im = core.applyThreshold(IMAGES_STACK[parent_name],
                             widget.spin.value(), widget.reversed.isChecked())
    IMAGES_STACK[widget.node.name] = im
    widget.node.updateSnap()
