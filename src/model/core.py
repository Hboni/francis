from skimage import morphology
import copy
import numpy as np


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
    eroded: 2d/3d numpy array
        Eroded input image with same size as im

    """
    if size == 0:
        return im
    if len(im.shape) == 3:
        if round_shape:
            selem = morphology.ball(size)
        else:
            selem = morphology.cube(size*2+1)
    elif len(im.shape) == 2:
        if round_shape:
            selem = morphology.disk(size)
        else:
            selem = morphology.square(size*2+1)

    eroded = morphology.erosion(im, selem)
    return eroded


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
    dilated: 2d/3d numpy array
        Dilated input image with same size as im

    """
    if size == 0:
        return im
    if len(im.shape) == 3:
        if round_shape:
            selem = morphology.ball(size)
        else:
            selem = morphology.cube(size*2+1)
    elif len(im.shape) == 2:
        if round_shape:
            selem = morphology.disk(size)
        else:
            selem = morphology.square(size*2+1)
    dilated = morphology.dilation(im, selem)
    return dilated


def applyThreshold(im, threshold, reverse=False):
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
    if reverse:
        mask = im < threshold
    else:
        mask = im > threshold
    return mask.astype(np.uint8)


def addImages(ims):
    """
    apply sum to each pixel of all input images

    Parameters
    ----------
    ims: list of 2d/ 3d numpy array

    Return
    ------
    im_sum: 2d/3d numpy array
    """
    im_sum = copy.copy(ims[0])
    for im in ims[1:]:
        im_sum += im
    return im_sum


def substractImages(ref_im, ims):
    """
    apply substraction of set of images to a reference image

    Parameters
    ----------
    ref_im: 2d/ 3d numpy array
        the reference image index from which we want to subtract other images
    ims: list of 2d/ 3d numpy array

    Return
    ------
    im_sub: 2d/3d numpy array

    """
    im_sub = copy.copy(ref_im)
    for im in ims:
        im_sub -= im
    return im_sub
