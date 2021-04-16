from PyQt5 import QtWidgets
import os
import nibabel as nib
from src.model import core
from src import DATA_DIR, OUT_DIR, _IMAGES_STACK
from src.utils import store_image, get_image, protector
from src.view.ui import get_checked_radiobutton
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


@protector
def save_image(widget):
    """
    save the parent image as nifti file at specified path
    """
    parent_name = get_parent_names(widget)[0]
    ni_img = nib.Nifti1Image(get_image(parent_name), None)
    nib.save(ni_img, widget.path.text())
    print("done")


def load_image(widget):
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
    store_image(im, widget.node.name)
    widget.node.updateSnap()


@protector
def update_threshold(widget):
    """
    compute 3d thresholding on the parent image
    and store the thresholded image into image stack dictionnaries
    """
    parent_name = get_parent_names(widget)[0]
    im = core.apply_threshold(get_image(parent_name),
                              widget.spin.value(), widget.reversed.isChecked())
    store_image(im, widget.node.name)
    widget.node.updateSnap()


@protector
def operation_between_images(widget):
    parent_names = get_parent_names(widget)
    operation = get_checked_radiobutton(widget, ['add', 'multiply', 'subtract', 'divide'])
    ref_parent_name = widget.reference.currentText()
    parent_names.remove(ref_parent_name)
    im = core.apply_operation(get_image(ref_parent_name),
                              [get_image(parent_name) for parent_name in parent_names],
                              operation=operation)
    store_image(im, widget.node.name)
    widget.node.updateSnap()


@protector
def operation_with_single_value(widget):
    parent_name = get_parent_names(widget)[0]
    operation = get_checked_radiobutton(widget, ['add', 'multiply', 'subtract', 'divide'])
    im = core.apply_operation(get_image(parent_name),
                              float(widget.value.text()), operation=operation)
    store_image(im, widget.node.name)
    widget.node.updateSnap()


@protector
def morpho_basics(widget):
    """
    compute 3d morphological operation on the parent image
    and store the modified image into image stack dictionnaries
    """
    parent_name = get_parent_names(widget)[0]
    if parent_name not in _IMAGES_STACK:
        return print("'{}' not in image stack".format(parent_name))

    operation = get_checked_radiobutton(widget, ['erosion', 'dilation', 'opening', 'closing'])
    if widget.binary.isChecked():
        operation = "binary_" + operation
    im = core.apply_basic_morpho(get_image(parent_name),  widget.size.value(), operation)

    store_image(im, widget.node.name)
    widget.node.updateSnap()
