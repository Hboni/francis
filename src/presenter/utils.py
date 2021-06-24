from PyQt5 import QtCore
from src import RSC_DIR
import functools
import multiprocessing
import os
import pickle


class Runner(QtCore.QThread):
    """
    QThread that activate a function with arguments

    Parameters
    ----------
    target: function
    *args, **kwargs: function arguments
    """
    def __init__(self, name, target, args):
        super().__init__()
        self._name = name
        self._target = target
        self._args = args
        self.proc = None

        # where the function result is stored
        self.out = None

    def run(self):
        self.proc = multiprocessing.Process(target=decorator(self._name, self._target), args=[(self._args)])
        self.proc.start()
        self.proc.join()
        path = os.path.join(RSC_DIR, "data", "tmp", self._name)
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                self.out = pickle.load(f)
            try:
                os.remove(path)
            except PermissionError as e:
                print("cannot delete {0}, {1}".format(path, e))


class decorator(object):
    def __init__(self, name, target):
        self.name = name
        self.target = target

    def __call__(self, kwargs):
        try:
            res = self.target(**kwargs)
        except Exception as e:
            res = e

        # pickle save result in tmp dir
        save_path = os.path.join(RSC_DIR, "data", "tmp", self.name)
        with open(save_path, 'wb') as f:
            pickle.dump(res, f)


def delete_runner(module):
    del module.runner.out
    module.runner = None


def manager(threadable=True):
    """
    this decorator manage threading

    Parameters
    ----------
    threadable: bool, default=True
        if True, the model function will be processed inside a QThread (if allowed)

    """
    def decorator(foo):
        @functools.wraps(foo)
        def inner(presenter, module):
            cont = presenter.prior_manager(module)
            if not cont:
                return
            function, args = foo(presenter, module)

            # start the process inside a QThread
            if threadable and presenter.threading_enabled:
                # runner = Runner(function, **args)
                module.runner = Runner(module.name, function, args)
                module.runner.finished.connect(lambda: (presenter.post_manager(module, module.runner.out),
                                                        delete_runner(module)))
                module.runner.start()
            else:
                presenter.post_manager(module, function(**args))
        return inner
    return decorator


def get_checked(widget, names=None, first_only=True):
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
