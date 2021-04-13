from PyQt5 import QtWidgets
import os
import nibabel as nib
from src.model import core
from src import DATA_DIR, OUT_DIR, _IMAGES_STACK
from src.utils import store_image
DATA_DIR


def get_parent_names(widget):
    """
    get parent names of the node associated to the widget
    """
    return [p.name for p in widget.node.parents]


def browse_savepath(widget):
    """
    open a browse window to define the nifti save path
    """
    name = get_parent_names(widget)[0]
    filename, extension = QtWidgets.QFileDialog.getSaveFileName(widget.node.graph, 'Save file',
                                                                os.path.join(OUT_DIR, name), filter=".nii.gz")
    widget.path.setText(filename+extension)
    widget.path.setToolTip(filename+extension)


def save_image(widget):
    """
    save the parent image as nifti file at specified path
    """
    parent_name = get_parent_names(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    ni_img = nib.Nifti1Image(_IMAGES_STACK[parent_name], None)
    nib.save(ni_img, widget.path.text())
    print("done")


def browse_image(widget):
    """
    open a browse window to select a nifti file
    then update path in the corresponding QLineEdit
    """
    global DATA_DIR
    dialog = QtWidgets.QFileDialog()
    filename, _ = dialog.getOpenFileName(widget.node.graph, "Select a file...", DATA_DIR)
    DATA_DIR = os.path.dirname(filename)
    widget.path.setText(filename)
    widget.path.setToolTip(filename)


def load_image(widget):
    """
    load nifti file, store inside the image stack dictionnaries
    and create the rendering widget to put image inside
    """
    try:
        im = nib.load(widget.path.text()).get_fdata()
    except (nib.filebasedimages.ImageFileError, FileNotFoundError) as e:
        return print(e)
    if len(im.shape) != 3:
        return "for now loaded images must be of size 3"
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def update_erosion(widget):
    """
    compute 3d erosion on the parent image
    and store the eroded image into image stack dictionnaries
    """
    parent_name = get_parent_names(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.erode(_IMAGES_STACK[parent_name], widget.spin.value())
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def update_dilation(widget):
    """
    compute 3d dilation on the parent image
    and store the dilated image into image stack dictionnaries
    """
    parent_name = get_parent_names(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.dilate(_IMAGES_STACK[parent_name], widget.spin.value())
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def update_threshold(widget):
    """
    compute 3d thresholding on the parent image
    and store the thresholded image into image stack dictionnaries
    """
    parent_name = get_parent_names(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))
    im = core.apply_threshold(_IMAGES_STACK[parent_name],
                              widget.spin.value(), widget.reversed.isChecked())
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def add_images(widget):
    """
    compute addition of all input images
    """
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        ref_parent_name = widget.reference.currentText()
        im = core.add_images([_IMAGES_STACK[ref_parent_name]], value=value)
    else:
        parent_names = get_parent_names(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        im = core.add_images([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def substract_images(widget):
    """
    compute substraction of all input images from the reference image
    """
    ref_parent_name = widget.reference.currentText()
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        im = core.substract_images(_IMAGES_STACK[ref_parent_name], value=value)
    else:
        parent_names = get_parent_names(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        parent_names.remove(ref_parent_name)
        im = core.substract_images(_IMAGES_STACK[ref_parent_name],
                                   [_IMAGES_STACK[parent_name] for parent_name in parent_names])
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def multiply_images(widget):
    """
    compute multiplication of all input images
    """
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        ref_parent_name = widget.reference.currentText()
        im = core.multiply_images([_IMAGES_STACK[ref_parent_name]], value=value)
    else:
        parent_names = get_parent_names(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        im = core.multiply_images([_IMAGES_STACK[parent_name] for parent_name in parent_names])
    store_image(im, widget.node.name)
    widget.node.updateSnap()


def divide_images(widget):
    """
    compute division of all input images
    """
    ref_parent_name = widget.reference.currentText()
    if widget.singleValue.isChecked():
        try:
            value = float(widget.value.text())
        except ValueError as e:
            return print(e)
        im = core.divide_images(_IMAGES_STACK[ref_parent_name], value=value)
    else:
        parent_names = get_parent_names(widget)
        for parent_name in parent_names:
            if parent_name not in _IMAGES_STACK:
                return print("'{}' not in image stack".format(parent_name))
        parent_names.remove(ref_parent_name)
        im = core.divide_images(_IMAGES_STACK[ref_parent_name],
                                [_IMAGES_STACK[parent_name] for parent_name in parent_names])
    store_image(im, widget.node.name)
    widget.node.updateSnap()
