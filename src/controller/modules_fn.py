from PyQt5 import QtWidgets
import os
import nibabel as nib
from src.model import core
from src import DATA_DIR, OUT_DIR, _IMAGES_STACK
from src.utils import storeImage
DATA_DIR


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
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    ni_img = nib.Nifti1Image(_IMAGES_STACK[parent_name], None)
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
    load nifti file, store inside the image stack dictionnaries
    and create the rendering widget to put image inside
    """
    try:
        im = nib.load(widget.path.text()).get_data()
    except (nib.filebasedimages.ImageFileError, FileNotFoundError) as e:
        return print(e)
    if len(im.shape) != 3:
        return "for now loaded images must be of size 3"
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def updateErosion(widget):
    """
    compute 3d erosion on the parent image
    and store the eroded image into image stack dictionnaries
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.erode(_IMAGES_STACK[parent_name], widget.spin.value())
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def updateDilation(widget):
    """
    compute 3d dilation on the parent image
    and store the dilated image into image stack dictionnaries
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.dilate(_IMAGES_STACK[parent_name], widget.spin.value())
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def updateThreshold(widget):
    """
    compute 3d thresholding on the parent image
    and store the thresholded image into image stack dictionnaries
    """
    parent_name = getParentNames(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.applyThreshold(_IMAGES_STACK[parent_name],
                             widget.spin.value(), widget.reversed.isChecked())
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def addImages(widget):
    """
    compute addition of all input images
    """
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        ref_parent_name = widget.reference.currentText()
        im = core.addImages([_IMAGES_STACK[ref_parent_name]], value=value)
    else:
        parent_names = getParentNames(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        im = core.addImages([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def substractImages(widget):
    """
    compute substraction of all input images from the reference image
    """
    ref_parent_name = widget.reference.currentText()
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        im = core.substractImages(_IMAGES_STACK[ref_parent_name], value=value)
    else:
        parent_names = getParentNames(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        parent_names.remove(ref_parent_name)
        im = core.substractImages(_IMAGES_STACK[ref_parent_name],
                                  [_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def multiplyImages(widget):
    """
    compute multiplication of all input images
    """
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        ref_parent_name = widget.reference.currentText()
        im = core.multiplyImages([_IMAGES_STACK[ref_parent_name]], value=value)
    else:
        parent_names = getParentNames(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        im = core.multiplyImages([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def divideImages(widget):
    """
    compute division of all input images
    """
    ref_parent_name = widget.reference.currentText()
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        im = core.divideImages(_IMAGES_STACK[ref_parent_name], value=value)
    else:
        parent_names = getParentNames(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        parent_names.remove(ref_parent_name)
        im = core.divideImages(_IMAGES_STACK[ref_parent_name],
                               [_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()
