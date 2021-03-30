import numpy as np


def getMinimumDtype(arr):
    """
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
