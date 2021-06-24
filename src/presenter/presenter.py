import os
from src import RSC_DIR
from src.presenter import utils
from PyQt5 import QtWidgets
import psutil
import numpy as np


class Presenter():
    """
    This class is part of the MVP app design, it acts as a bridge between
    the Model and the View

    Parameters
    ----------
    model: model.Model
    view: view.View

    """
    def __init__(self, view, model=None, threading_enabled=True):
        self._model = model
        self._view = view
        self.threading_enabled = True
        self._data_dir = os.path.join(RSC_DIR, "data")
        self._out_dir = os.path.join(RSC_DIR, "data", "out")
        self._view.moduleAdded.connect(lambda m: self.init_module_connections(m))
        self._view.closed.connect(self.terminateProcesses)
        self._view.restoreTabs()

    # ---------------------------- process handle -----------------------------#
    def getProc(self, module):
        if module.runner is not None and module.runner.proc is not None:
            return psutil.Process(module.runner.proc.pid)

    def terminateProcesses(self):
        for graph in self._view.graphs.values():
            for module in graph.modules.values():
                proc = self.getProc(module)
                if proc:
                    proc.terminate()

    # --------------------- PRIOR  AND POST FUNCTION CALL ---------------------#
    def prior_manager(self, module):
        """
        This method is called by the utils.manager before the function call

        Parameters
        ----------
        module: QWidget
        """

        # start loading
        module.setState('loading')

        # store signal propagation
        for parent in module.parents:
            if module.getData(parent.name) is None:
                parent.propagation_child = module
                parent.play.clicked.emit()
                return False
        return True

    def post_manager(self, module, output):
        """
        This method manage the output of a model function based on the output type
        it is called by the utils.manager at the end of the model process

        Parameters
        ----------
        module: QWidget
        output: exception, str, pd.DataFrame, np.array, ...
        """
        if output is not None:
            module.graph.storeData(module.name, output)
        if output is None:
            module.setState()
        elif isinstance(output, Exception):
            module.setState('fail')
        else:
            module.setState('valid')
        module.showResult(output)

        # retropropagate signal between modules
        if module.propagation_child is not None:
            if not isinstance(output, Exception):
                module.propagation_child.play.clicked.emit()
            module.propagation_child = None

    # ------------------------------ CONNECTIONS ------------------------------#
    def init_module_connections(self, module):
        """
        initialize module parameters if necessary
        create connections between view widgets and functions

        Parameters
        ----------
        module_name: str
            name of the loaded module

        """
        parameters = self._view.getParameters(module.type)
        activation_function = eval('self.'+parameters['function'])

        # connect start, pause, stop buttons
        def play():
            if module.state == "pause":
                proc = self.getProc(module)
                if proc:
                    proc.resume()
            elif self._model is not None:
                activation_function(module)
            module.setState("loading")

        def pause():
            proc = self.getProc(module)
            if proc:
                proc.suspend()
            module.setState("pause")

        def stop():
            proc = self.getProc(module)
            if proc:
                proc.terminate()
            module.setState()

        module.play.clicked.connect(play)
        module.pause.clicked.connect(pause)
        module.stop.clicked.connect(stop)

        self.init_module_custom_connections(module)

    def init_module_custom_connections(self, module):
        if module.type == "Save":
            module.parameters.browse.clicked.connect(lambda: self.browse_savepath(module))

        elif module.type == "Load":
            module.parameters.browse.clicked.connect(lambda: self.browse_path(module))

        elif module.type == "Operation":
            for rb in [module.parameters.add, module.parameters.multiply]:
                rb.clicked.connect(lambda: module.parameters.reference.setEnabled(False))
            for rb in [module.parameters.divide, module.parameters.subtract]:
                rb.clicked.connect(lambda: module.parameters.reference.setEnabled(True))
            module.parameters.add.clicked.emit()

            # rename parent name inside reference combobox
            module.parameters.reference.addItems(module.get_parent_names())

            def updateParentName(name, new_name):
                current_index = module.parameters.reference.currentIndex()
                ind = module.parameters.reference.findText(name)
                module.parameters.reference.removeItem(ind)
                module.parameters.reference.insertItem(ind, new_name)
                module.parameters.reference.setCurrentIndex(current_index)
            for parent in module.parents:
                parent.nameChanged.connect(updateParentName)

        module.setSettings(module.graph.settings.get(module.name))

    # ----------------------------- utils -------------------------------------#
    def browse_savepath(self, module):
        """
        open a browse window to define the nifti save path
        """
        name = module.get_parent_name()
        result = module.getData(name)

        if isinstance(result, np.ndarray):
            extensions = ["PNG (*.png)", "NIFTI (*.nii)", "JPEG (*.jpg)"]
            dim = len(result.shape)
            if dim == 2:
                initfilter = extensions[0]
            elif dim == 3:
                initfilter = extensions[1]
        elif result is None or isinstance(result, Exception):
            extensions = ["PNG (*.png)", "NIFTI (*.nii)", "JPEG (*.jpg)", "TEXT (*.txt)"]
            initfilter = None
        else:
            extensions = ["TEXT (*.txt)"]
            initfilter = extensions[0]

        extensions.append("compressed (*.pkl)")
        if initfilter is None:
            initfilter = extensions[-1]

        filename, extension = QtWidgets.QFileDialog.getSaveFileName(module.graph, 'Save file',
                                                                    os.path.join(self._out_dir, name),
                                                                    filter=";;".join(extensions),
                                                                    initialFilter=initfilter)
        if filename:
            module.parameters.path.setText(filename)
            module.parameters.path.setToolTip(filename)

    def browse_path(self, module):
        """
        open a browse window to select a nifti file
        then update path in the corresponding QLineEdit
        """
        dialog = QtWidgets.QFileDialog()
        filename, ok = dialog.getOpenFileName(module.graph, "Select a file...", self._data_dir,
                                              filter="*.nii.gz *.nii *.png *.jpg *.txt *.pkl")
        if ok:
            module.parameters.path.setText(filename)
            module.parameters.path.setToolTip(filename)

    # ----------------------------- MODEL CALL --------------------------------#
    @utils.manager(True)
    def call_save(self, module):
        """
        save the parent image as nifti file at specified path
        """
        parent_name = module.get_parent_name()
        function = self._model.save
        args = {"data": module.getData(parent_name),
                "path": module.parameters.path.text()}
        return function, args

    @utils.manager(True)
    def call_load(self, module):
        """
        load any type of data
        """
        function = self._model.load
        args = {"path": module.parameters.path.text()}
        return function, args

    @utils.manager(True)
    def call_get_img_infos(self, module):
        parent_name = module.get_parent_name()

        function = self._model.get_img_infos
        args = {"im": module.getData(parent_name),
                "info": module.parameters.infos.currentText()}
        return function, args

    @utils.manager(True)
    def call_apply_threshold(self, module):
        """
        compute 3d thresholding on the parent image
        and store the thresholded image into image stack dictionnaries
        """
        parent_name = module.get_parent_name()

        function = self._model.apply_threshold
        args = {"im": module.getData(parent_name),
                "threshold": module.parameters.spin.value(),
                "reverse": module.parameters.reversed.isChecked()}
        return function, args

    @utils.manager(True)
    def call_apply_operation(self, module):
        parent_names = module.get_parent_names()
        ref_parent_name = module.parameters.reference.currentText()
        parent_names.remove(ref_parent_name)

        function = self._model.apply_operation
        args = {"arr": module.getData(ref_parent_name),
                "elements": module.getData(parent_names),
                "operation": utils.get_checked(module.parameters, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @utils.manager(True)
    def call_apply_simple_operation(self, module):
        parent_name = module.get_parent_name()

        function = self._model.apply_operation
        args = {"arr": module.getData(parent_name),
                "elements": float(module.parameters.value.text()),
                "operation": utils.get_checked(module.parameters, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @utils.manager(True)
    def call_apply_basic_morpho(self, module):
        """
        compute 3d morphological operation on the parent image
        and store the modified image into image stack dictionnaries
        """
        parent_name = module.get_parent_name()
        operation = utils.get_checked(module.parameters, ['erosion', 'dilation', 'opening', 'closing'])
        if module.parameters.binary.isChecked():
            operation = "binary_" + operation

        function = self._model.apply_basic_morpho
        args = {"im": module.getData(parent_name),
                "size": module.parameters.size.value(),
                "operation": operation,
                "round_shape": True}
        return function, args