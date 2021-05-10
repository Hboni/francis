import numpy as np


def protector(foo):
    def inner(*args, **kwargs):
        try:
            return foo(*args, **kwargs)
        except Exception as e:
            return e
    return inner


def get_minimum_dtype(arr):
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


def dict_from_list(dict_to_complete, element_list):
    """
    convert a list of elements into a one-branch dictionary

    Parameters
    ----------
    dict_to_complete
    element_list: list

    """
    if element_list:
        element = element_list.pop(0)
        dict_to_complete.setdefault(element, {})
    if element_list:
        dict_from_list(dict_to_complete.get(element), element_list)
