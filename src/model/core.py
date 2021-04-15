from skimage import morphology
import numpy as np
# from src.utils import get_minimum_dtype


def apply_basic_morpho(im, size, operation='erosion', round_shape=True):
    """
    Apply basic morphological operation on the input image

    Parameters
    ----------
    im: 2d/3d numpy array
    size: int
        Generate an element of size (size*2+1)
    round_shape: str, default=True
        If True the element is ball (3d) or disk (2d),
        else the element is cube (3d) or square (2d)
    operation: {'erosion', 'dilation', 'binary_erosion', 'binary_dilation'}, default='erosion'

    Returns
    -------
    result: 2d/3d numpy array
        Transformed input image with same size as im

    """
    if size == 0:
        return im
    if len(im.shape) == 3:
        selem = morphology.ball(size) if round_shape else morphology.cube(size*2+1)
    elif len(im.shape) == 2:
        selem = morphology.disk(size) if round_shape else morphology.square(size*2+1)

    function = eval("morphology."+operation)
    out = function(im, selem)
    return out


def apply_operation(arr, elements=[], operation='add'):
    """

    Parameters
    ----------
    arr: 2d/3d array
    elements: list of 2d/3d arrays or float, default=[]
    operation: {'add', 'multiply', 'subtract', 'divide'}, default='add'
    output_minimize_bytes: bool, default=True

    Return
    ------
    result: 2d/3d array

    """
    if not isinstance(elements, list):
        elements = [elements]

    function = eval("np."+operation)
    for element in elements:
        arr = function(arr, element, dtype=np.float64)

    return arr


def apply_threshold(im, threshold, reverse=False):
    """
    Apply binary threshold on the input image

    Parameters
    ----------
    im: 2d/3d numpy array
    threshold: float
        Pixel value, image=1 above threshold, image=0 below threshold
    reverse: bool, default=False
        If True invert 0 and 1 in output

    Returns
    -------
    mask: 2d/3d numpy array
        Binarized input image with same size as im

    """
    mask = im < threshold if reverse else im > threshold
    return mask.astype(np.uint8)
