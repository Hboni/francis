import numpy as np
import copy
from src import _IMAGES_STACK, IMAGES_STACK


def getMinimumDtype(arr):
    """
    This function is temporary and not optimized at all
    This function find the minimal dtype of an array of type float or int

    Parameters
    ----------
    arr: numpy.array

    Return
    ------
    result: numpy.dtype or None
    """
    for dt in [np.uint8, np.int8, np.uint16, np.int16, np.float16,
               np.uint32, np.int32, np.float32, np.uint64, np.int64, np.float64]:
        if np.array_equal(arr, arr.astype(dt), equal_nan=True):
            return dt


def storeImage(im, name):
    """
    store raw image and (0, 255)-scaled image, 0 is nan values

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


def dict_from_list(liste):
    """
    convert a list of elements into a one-branch dictionary

    Parameters
    ----------
    liste: list

    Return
    ------
    result: dict
    """
    if len(liste) == 0:
        return {}
    elif len(liste) == 1:
        return {liste[0]: {}}
    elif len(liste) > 1:
        return {liste[0]: dict_from_list(liste[1:])}
