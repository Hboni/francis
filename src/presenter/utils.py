import functools
import os
import pickle
from datetime import datetime
from enum import Enum
from multiprocessing import Process

import psutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget

from src import TMP_DIR


def call_target(target, args: dict, tmp_path: str = None):
    """
    call a function with arguments, if an error occurs return the exception

    Parameters
    ----------
    target: function or class method
    args: dict
        argument of the target
    tmp_path: str, default=None
        if specified, save the target result as a temporary .pkl file

    Return
    ------
    res: target result or Exception

    """
    try:
        res = target(**args)
    except Exception as e:
        res = e
        print("".join(traceback.format_tb(res.__traceback__)[1:]))
    if tmp_path is not None:
        with open(tmp_path, "wb") as f:
            pickle.dump(res, f)
    return res


class Runner(QtCore.QThread):
    """
    QThread that activate a function with arguments

    Parameters
    ----------
    target: function or class method
    args: target arguments
    mode: bool, default=False
        if True, call the target inside a Process

    """

    def __init__(self, target, args: dict, in_process: bool = False):
        super().__init__()
        self.target = target
        self.args = args
        self.tmp_path = os.path.join(TMP_DIR, str(datetime.now().timestamp()))
        self.in_process = in_process
        self.proc = None

        # where the function result is stored
        self.out = None

    def suspend(self):
        if self.proc:
            psutil.Process(self.proc.pid).suspend()

    def resume(self):
        if self.proc:
            psutil.Process(self.proc.pid).resume()

    def terminate(self):
        if self.proc:
            psutil.Process(self.proc.pid).terminate()
        else:
            return QtCore.QThread.terminate(self)

    def run(self):
        if self.in_process:
            self.proc = Process(
                target=call_target, args=[self.target, self.args, self.tmp_path]
            )
            self.proc.start()
            self.proc.join()
        else:
            call_target(self.target, self.args, self.tmp_path)

        self.receive()

    def receive(self):
        """
        load the result saved in the temporary file by the 'call_target' function
        and delete the file.
        """
        if os.path.isfile(self.tmp_path):
            with open(self.tmp_path, "rb") as f:
                self.out = pickle.load(f)
            try:
                os.remove(self.tmp_path)
            except PermissionError as e:
                print("cannot delete {0}, {1}".format(self.tmp_path, e))


def delete_runner(module):
    del module.runner.out
    module.runner = None


class ThreadMode(Enum):
    NO_THREAD_NO_SUBPROCESS = 0
    THREAD = 1
    SUBPROCESS = 2


def manager(thread_mode: ThreadMode = 0):
    """
    this decorator manage threading

    Parameters
    ----------
    thread_mode: {0, 1, 2}, default=0
        0: no thread nor subprocess
        1: thread enabled (terminate thread when possible)
            warning: termination may be dangerous
        2: subprocess enabled (suspend, resume and terminate process instantly)
            warning: use 2 more seconds at each time to build the Process

    """

    def decorator(foo):
        @functools.wraps(foo)
        def inner(presenter, module):
            cont = presenter.prior_manager(module, thread_mode)
            if not cont:
                return
            function, args = foo(presenter, module)

            # start the process inside a QThread
            if not presenter.threading_enabled or thread_mode == 0:
                presenter.post_manager(module, call_target(function, args))
            else:
                module.runner = Runner(function, args, thread_mode == 2)
                module.runner.finished.connect(
                    lambda: (
                        presenter.post_manager(module, module.runner.out),
                        delete_runner(module),
                    )
                )
                module.runner.start()

        return inner

    return decorator


def get_checked(
    widget: QWidget, names: list[str] = None, first_only: bool = True
) -> bool:
    """
    get checked childs of a widget

    Parameters
    ----------
    widget: QWidget
        parent widget
    names: list of str, default=None
        names of checkable widget child
    first_only: bool, default=True
        if True return only the first checked widget name

    Return
    ------
    result: str or list of str

    """
    checked = []
    if names is None:
        for name, w in widget.__dict__.items():
            if w.isChecked():
                checked.append(name)
    else:
        for name in names:
            w = widget.__dict__.get(name)
            if w and w.isChecked():
                if first_only:
                    return name
                checked.append(name)
    return checked
