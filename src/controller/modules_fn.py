from PyQt5 import QtWidgets
import os
import numpy as np
import nibabel as nib
from src.model import core
from src import DATA_DIR, OUT_DIR, IMAGES_STACK, _IMAGES_STACK
DATA_DIR


def storeImage(im, name):
    """
    store raw image and (0, 255)-scaled image, 0 is nan values

    Parameters
    ----------
    im: numpy.array
    name: str
    """
    _IMAGES_STACK[name] = im
    im_c = im.astype(np.float64)

    # scale image in range (1, 255)
    mini, maxi = np.nanmin(im_c), np.nanmax(im_c)
    if mini == maxi:
        mini = 0
        if maxi <= 0:
            maxi = 1
    im_c = (im_c - mini) / (maxi - mini) * 254 + 1

    # set 0 as nan values
    im_c[np.isnan(im_c)] = 0

    # convert and store
    im_c = im_c.astype(np.uint8)
    IMAGES_STACK[name] = im_c


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
    if parent_name not in _IMAGES_STACK.keys():
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
    im = nib.load(widget.path.text()).get_data()
    # print("image description:\nshape: {0}\ndtype: {1}\nunique values: {2}".format(im.shape, im.dtype, np.unique(im)))
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
    if parent_name not in _IMAGES_STACK.keys():
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
    if parent_name not in _IMAGES_STACK.keys():
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
    if parent_name not in _IMAGES_STACK.keys():
        return print("'{}' not in image stack".format(parent_name))
    im = core.applyThreshold(_IMAGES_STACK[parent_name],
                             widget.spin.value(), widget.reversed.isChecked())
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def addImages(widget):
    """
    compute addition of all input images
    """
    parent_names = getParentNames(widget)
    for parent_name in parent_names:
        if parent_name not in _IMAGES_STACK.keys():
            return print("'{}' not in image stack".format(parent_name))
    im = core.addImages([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def substractImages(widget):
    """
    compute substraction of all input images from the reference image
    """
    parent_names = getParentNames(widget)
    for parent_name in parent_names:
        if parent_name not in _IMAGES_STACK.keys():
            return print("'{}' not in image stack".format(parent_name))
    ref_parent_name = widget.reference.currentText()
    parent_names.remove(ref_parent_name)
    im = core.substractImages(_IMAGES_STACK[ref_parent_name],
                              [_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def multiplyImages(widget):
    """
    compute multiplication of all input images
    """
    parent_names = getParentNames(widget)
    for parent_name in parent_names:
        if parent_name not in _IMAGES_STACK.keys():
            return print("'{}' not in image stack".format(parent_name))
    im = core.multiplyImages([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()


def divideImages(widget):
    """
    compute division of all input images
    """
    parent_names = getParentNames(widget)
    for parent_name in parent_names:
        if parent_name not in _IMAGES_STACK.keys():
            return print("'{}' not in image stack".format(parent_name))
    im = core.divideImages([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    storeImage(im, widget.node.name)
    widget.node.updateSnap()
