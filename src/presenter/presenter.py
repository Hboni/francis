from PyQt5 import uic
from src import UI_DIR, CONFIG_DIR
import json
from PyQt5 import QtWidgets, QtCore
import os
import nibabel as nib
from src import DATA_DIR, OUT_DIR
from src.presenter.utils import view_manager, store_image, get_image
from src.view import ui
DATA_DIR


class Presenter:
    """
    connect the view to the model methods

    Parameters
    ----------
    view: View
    model: Model

    """

    def __init__(self, view, model):
        self._view = view
        self._model = model
        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), "rb"))
        self._view.initMenu(self.modules)
        self._view.graph.nodeClicked.connect(self.activate_node)
        self._view.presenter = self

    def activate_node(self, node):
        """
        apply connection between node widgets and model and initialize widgets

        Parameters
        ----------
        node: graph.Node

        """
        if node.parameters.itemAt(0) is not None:
            return

        t = node.type
        parameters = self.modules[t]

        widget = uic.loadUi(os.path.join(UI_DIR, parameters['ui']))
        widget.node = node
        node.parameters.addWidget(widget)

        # add loading gif to widget
        node.gif = ui.Gif()
        node.parameters.addWidget(node.gif)
        node.parameters.setAlignment(node.gif, QtCore.Qt.AlignHCenter)

        activation_function = eval("self."+parameters['function'])
        widget.apply.clicked.connect(lambda: activation_function(widget))

        if t == "threshold image":
            widget.spin.valueChanged.connect(lambda: activation_function(widget))
            widget.reversed.stateChanged.connect(lambda: activation_function(widget))

        elif t == "load image":
            widget.browse.clicked.connect(lambda: self.browse_image(widget))

        elif t == "save image":
            widget.browse.clicked.connect(lambda: self.browse_savepath(widget))

        elif t == "operation between images":
            for rb in [widget.add, widget.multiply]:
                rb.clicked.connect(lambda: widget.reference.setEnabled(False))
            for rb in [widget.divide, widget.subtract]:
                rb.clicked.connect(lambda: widget.reference.setEnabled(True))
            widget.add.clicked.emit()

            # rename parent name inside reference combobox
            widget.reference.addItems(ui.get_parent_names(widget))

            def updateParentName(name, new_name):
                current_index = widget.reference.currentIndex()
                ind = widget.reference.findText(name)
                widget.reference.removeItem(ind)
                widget.reference.insertItem(ind, new_name)
                widget.reference.setCurrentIndex(current_index)
            for parent in node.parents:
                parent.nameChanged.connect(updateParentName)

    def browse_savepath(self, widget):
        """
        open a browse window to define the nifti save path
        """
        name = ui.get_parent_names(widget)[0]
        filename, extension = QtWidgets.QFileDialog.getSaveFileName(widget.node.graph, 'Save file',
                                                                    os.path.join(OUT_DIR, name), filter=".nii.gz")
        widget.path.setText(filename+extension)
        widget.path.setToolTip(filename+extension)

    def browse_image(self, widget):
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

    def save_image(self, widget):
        """
        save the parent image as nifti file at specified path
        """
        parent_name = ui.get_parent_names(widget)[0]
        ni_img = nib.Nifti1Image(get_image(parent_name), None)
        nib.save(ni_img, widget.path.text())
        print("done")

    def load_image(self, widget):
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

    @view_manager(True)
    def update_threshold(self, widget):
        """
        compute 3d thresholding on the parent image
        and store the thresholded image into image stack dictionnaries
        """
        parent_name = ui.get_parent_names(widget)[0]

        function = self._model.apply_threshold
        args = {"im": get_image(parent_name),
                "threshold": widget.spin.value(),
                "reverse": widget.reversed.isChecked()}
        return function, args

    @view_manager(True)
    def operation_between_images(self, widget):
        parent_names = ui.get_parent_names(widget)
        ref_parent_name = widget.reference.currentText()
        parent_names.remove(ref_parent_name)

        function = self._model.apply_operation
        args = {"arr": get_image(ref_parent_name),
                "elements": [get_image(parent_name) for parent_name in parent_names],
                "operation": ui.get_checked_radiobutton(widget, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @view_manager(True)
    def operation_with_single_value(self, widget):
        parent_name = ui.get_parent_names(widget)[0]

        function = self._model.apply_operation
        args = {"arr": get_image(parent_name),
                "elements": float(widget.value.text()),
                "operation": ui.get_checked_radiobutton(widget, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @view_manager(True)
    def morpho_basics(self, widget):
        """
        compute 3d morphological operation on the parent image
        and store the modified image into image stack dictionnaries
        """
        parent_name = ui.get_parent_names(widget)[0]
        operation = ui.get_checked_radiobutton(widget, ['erosion', 'dilation', 'opening', 'closing'])
        if widget.binary.isChecked():
            operation = "binary_" + operation

        function = self._model.apply_basic_morpho
        args = {"im": get_image(parent_name),
                "size": widget.size.value(),
                "operation": operation,
                "round_shape": True}
        return function, args
