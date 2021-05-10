from PyQt5 import QtCore
from src import _IMAGES_STACK, IMAGES_STACK
import numpy as np
import copy
RUNNERS = []


class Runner(QtCore.QThread):
    """
    QThread that activate a function with arguments

    Parameters
    ----------
    target: function
    *args, **kwargs: function arguments
    """
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs

        # where the function result is stored
        self.out = None

    def run(self):
        self.out = self._target(*self._args, **self._kwargs)


def view_manager(threadable=True):
    """
    this decorator manage the loading gif and threading

    Parameters
    ----------
    threadable: bool, default=True
        if True, the model function will be processed inside a QThread (if allowed)

    """
    def decorator(foo):
        def inner(presenter, widget):
            # start gif animation
            widget.node.gif.start()

            function, args = foo(presenter, widget)

            def updateView(output):
                if isinstance(output, Exception):
                    widget.node.gif.fail("[{0}] {1}".format(type(output).__name__, output))
                else:
                    store_image(output, widget.node.name)
                    widget.node.updateSnap()
                    widget.node.gif.stop()

            # start the process inside a QThread
            if threadable and presenter.threading_enabled:
                runner = Runner(function, **args)
                RUNNERS.append(runner)  # needed to keep a trace of the QThread
                runner.finished.connect(lambda: updateView(runner.out))
                runner.finished.connect(lambda: RUNNERS.remove(runner))
                runner.start()
            else:
                updateView(function(**args))
        return inner
    return decorator


def get_image(name):
    if name not in _IMAGES_STACK:
        print("'{}' not in image stack".format(name))
        return None
    return _IMAGES_STACK[name]


def store_image(im, name):
    """
    store raw sparsed image and (0, 255)-scaled image, 0 is nan values

    Parameters
    ----------
    im: numpy.array
    name: str
    """
    # initialize
    _IMAGES_STACK[name] = im
    im_c = im.astype(np.float64) if im.dtype != np.float64 else copy.copy(im)
    im_c[np.isinf(im_c)] = np.nan

    # scale image in range (1, 255)
    mini, maxi = np.nanmin(im_c), np.nanmax(im_c)
    if mini == maxi:
        mini = 0
        maxi = max(maxi, 1)
    im_c = (im_c - mini) / (maxi - mini) * 254 + 1

    # set 0 as nan values
    im_c[np.isnan(im_c)] = 0

    # convert and store
    im_c = im_c.astype(np.uint8)
    IMAGES_STACK[name] = im_c
