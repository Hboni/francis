import os
from src import RSC_DIR, TMP_DIR
from src.presenter import utils
from PyQt5 import QtWidgets
import numpy as np
import shutil


class Presenter():
    """
    This class is part of the MVP app design, it acts as a bridge between
    the Model and the View

    Parameters
    ----------
    view: view.View
    model: model.Model, default=None
    threading_enabled: bool, default=True
        if False, disable threading handled by the manager =(thread_mode=0)

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
        self.init_tmp_dir()

    def init_tmp_dir(self):
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.makedirs(TMP_DIR)

    # ---------------------------- process handle -----------------------------#
    def terminateProcesses(self):
        """
        Terminates all running processes
        """
        for graph in self._view.graphs.values():
            for module in graph.modules.values():
                if module.runner:
                    module.runner.terminate()

    # --------------------- PRIOR  AND POST FUNCTION CALL ---------------------#
    def prior_manager(self, module, thread_mode=0):
        """
        This method is called by the manager before the model method process

        Parameters
        ----------
        module: QGraphicsModule
        thread_mode: {0, 1, 2}, default=0

        Return
        ------
        result: bool
            if False, do not process

        """

        # start loading
        if thread_mode == 1:
            module.setState('loading', suspendable=False)
        elif thread_mode == 2:
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
        This method is called by the manager after the model method process
        It manage the output of the model method based on the output type

        Parameters
        ----------
        module: QGraphicsModule
        output: Exception, str, pd.DataFrame, np.array, ...

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
        connect play, pause and stop buttons to model method handling

        Parameters
        ----------
        module: QGraphicsModule

        """
        parameters = self._view.getParameters(module.type)
        activation_function = eval('self.'+parameters['function'])

        # connect start, pause, stop buttons
        def play():
            if module.state == "pause":
                if module.runner:
                    module.runner.resume()
                module.setState("loading")
            elif self._model is not None:
                activation_function(module)

        def pause():
            if module.runner:
                module.runner.suspend()
            module.setState("pause")

        def stop():
            if module.runner:
                module.runner.terminate()

        module.play.clicked.connect(play)
        module.pause.clicked.connect(pause)
        module.stop.clicked.connect(stop)

        self.init_module_custom_connections(module)

    def init_module_custom_connections(self, module):
        """
        initialize connections between module widgets and custom functions
        initialize widgets updating if necessary

        Parameters
        ----------
        module: QGraphicsModule

        """
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
        open a browse window to define the data save path based on the parent
        data type. Any type of data can be saved as .pkl
        """
        name = module.get_parent_name()
        result = module.getData(name)

        # init extensions and
        if isinstance(result, np.ndarray):
            extensions = ["PNG (*.png)", "NIFTI (*.nii)", "JPEG (*.jpg)"]
            dim = len(result.shape)
            if dim == 2:
                init_extension = extensions[0]
            elif dim == 3:
                init_extension = extensions[1]
        elif result is None or isinstance(result, Exception):
            extensions = ["PNG (*.png)", "NIFTI (*.nii)", "JPEG (*.jpg)", "TEXT (*.txt)"]
            init_extension = None
        else:
            extensions = ["TEXT (*.txt)"]
            init_extension = extensions[0]

        extensions.append("compressed (*.pkl)")
        if init_extension is None:
            init_extension = extensions[-1]

        filename, extension = QtWidgets.QFileDialog.getSaveFileName(module.graph, 'Save file',
                                                                    os.path.join(self._out_dir, name),
                                                                    filter=";;".join(extensions),
                                                                    initialFilter=init_extension)
        if filename:
            module.parameters.path.setText(filename)
            module.parameters.path.setToolTip(filename)

    def browse_path(self, module):
        """
        open a browse window to select a file and update path widget
        """
        dialog = QtWidgets.QFileDialog()
        filename, ok = dialog.getOpenFileName(module.graph, "Select a file...", self._data_dir,
                                              filter="*.nii.gz *.nii *.png *.jpg *.txt *.pkl")
        if ok:
            module.parameters.path.setText(filename)
            module.parameters.path.setToolTip(filename)

    # ----------------------------- MODEL CALL --------------------------------#
    @utils.manager(2)
    def call_save(self, module):
        """
        save the parent image as nifti file at specified path
        """
        parent_name = module.get_parent_name()
        function = self._model.save
        args = {"data": module.getData(parent_name),
                "path": module.parameters.path.text()}
        return function, args

    @utils.manager(2)
    def call_load(self, module):
        """
        load any type of data
        """
        function = self._model.load
        args = {"path": module.parameters.path.text()}
        return function, args

    @utils.manager(2)
    def call_get_img_infos(self, module):
        """
        get image info
        """
        parent_name = module.get_parent_name()

        function = self._model.get_img_infos
        args = {"im": module.getData(parent_name),
                "info": module.parameters.infos.currentText()}
        return function, args

    @utils.manager(2)
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

    @utils.manager(2)
    def call_apply_operation(self, module):
        """
        compute operations between multiple images
        """
        parent_names = module.get_parent_names()
        ref_parent_name = module.parameters.reference.currentText()
        parent_names.remove(ref_parent_name)

        function = self._model.apply_operation
        args = {"arr": module.getData(ref_parent_name),
                "elements": module.getData(parent_names),
                "operation": utils.get_checked(module.parameters, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @utils.manager(2)
    def call_apply_simple_operation(self, module):
        """
        compute simple operations between an image and a float
        """
        parent_name = module.get_parent_name()

        function = self._model.apply_operation
        args = {"arr": module.getData(parent_name),
                "elements": float(module.parameters.value.text()),
                "operation": utils.get_checked(module.parameters, ['add', 'multiply', 'subtract', 'divide'])}
        return function, args

    @utils.manager(2)
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
