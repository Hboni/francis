from skimage import morphology
import copy
import numpy as np

def erode(im, size, round_shape=True):
    """
    return an eroded image
    im: 2d or 3d array
    size:   int:    generate an element of size (size*2+1)
    round_shape: str:    if True the elemnt is ball or disk
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
    return a dilated image
    im: 2d or 3d array
    round_shape: str:    if True the elemnt is ball or disk
    size:   int:    generate an element of size (size*2+1)
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
    return a binary image
    im: ndarray
    threshold:  int or float:   pixel value
    """
    if reverse:
        mask = im < threshold
    else:
        mask = im > threshold
    return mask.astype(np.uint8)*255
