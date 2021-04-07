from skimage import morphology
import numpy as np
from src.utils import get_minimum_dtype


def erode(im, size, round_shape=True):
    """
    Apply morphological erosion on the input image

    Parameters
    ----------
    im: 2d/3d numpy array
    size: int
        Generate an element of size (size*2+1)
    round_shape: str, default=True
        If True the element is ball (3d) or disk (2d),
        else the element is cube (3d) or square (2d)

    Returns
    -------
    result: 2d/3d numpy array
        Eroded input image with same size as im

    """
    if size == 0:
        return im
    if len(im.shape) == 3:
        selem = morphology.ball(size) if round_shape else morphology.cube(size*2+1)
    elif len(im.shape) == 2:
        selem = morphology.disk(size) if round_shape else morphology.square(size*2+1)
    return morphology.erosion(im, selem)


def dilate(im, size, round_shape=True):
    """
    Apply morphological dilation on the input image

    Parameters
    ----------
    im: 2d/3d numpy array
    size: int
        Generate an element of size (size*2+1)
    round_shape: str, default=True
        If True the element is ball (3d) or disk (2d),
        else the element is cube (3d) or square (2d)

    Returns
    -------
    result: 2d/3d numpy array
        Dilated input image with same size as im

    """
    if size == 0:
        return im
    if len(im.shape) == 3:
        selem = morphology.ball(size) if round_shape else morphology.cube(size*2+1)
    elif len(im.shape) == 2:
        selem = morphology.disk(size) if round_shape else morphology.square(size*2+1)
    return morphology.dilation(im, selem)


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


def add_images(ims, value=None):
    """
    apply sum to each pixel of all input images

    Parameters
    ----------
    ims: list of 2d/ 3d numpy array
    value: float or None, default=None

    Return
    ------
    im_sum: 2d/3d numpy array
    """
    im_sum = ims[0].astype(float)
    if value is not None:
        im_sum += value
    else:
        for im in ims[1:]:
            im_sum += im.astype(float)
    im_sum = im_sum.astype(get_minimum_dtype(im_sum))
    return im_sum


def substract_images(ref_im, ims=[], value=None):
    """
    apply substraction of set of images or a single value to a reference image

    Parameters
    ----------
    ref_im: 2d/ 3d numpy array
        the reference image index from which we want to subtract other images
    ims: list of 2d/ 3d numpy array
    value: float or None, default=None

    Return
    ------
    im_sub: 2d/3d numpy array

    """

    im_sub = ref_im.astype(float)
    if value is not None:
        im_sub -= value
    else:
        for im in ims:
            im_sub -= im.astype(float)
    im_sub = im_sub.astype(get_minimum_dtype(im_sub))
    return im_sub


def multiply_images(ims, value=None):
    """
    apply multiplication to each pixel of all input images

    Parameters
    ----------
    ims: list of 2d/ 3d numpy array
    value: float or None, default=None

    Return
    ------
    im_mult: 2d/3d numpy array
    """
    im_mult = ims[0].astype(float)
    if value is not None:
        im_mult *= value
    else:
        for im in ims[1:]:
            im_mult *= im.astype(float)
    im_mult = im_mult.astype(get_minimum_dtype(im_mult))
    return im_mult


def divide_images(ref_im, ims=[], value=None):
    """
    apply division of set of images or a single value to a reference image

    Parameters
    ----------
    ref_im: 2d/ 3d numpy array
        the reference image index from which we want to divide other images
    ims: list of 2d/ 3d numpy array, default=[]
    value: float or None, default=None

    Return
    ------
    im_div: 2d/3d numpy array
    """
    im_div = ref_im.astype(float)
    if value is None:
        for im in ims:
            im_div /= im.astype(float)
    else:
        im_div /= value
    im_div = im_div.astype(get_minimum_dtype(im_div))
    return im_div
