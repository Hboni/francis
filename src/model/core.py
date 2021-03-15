from skimage import morphology
import copy
import numpy as np

def erode(im, size):
    if size == 0:
        return im
    if len(im.shape) == 3:
        selem = morphology.ball(size)
    elif len(im.shape) == 2:
        selem = morphology.disk(size)
    eroded = morphology.erosion(im, selem)
    return eroded

def dilate(im, size):
    if size == 0:
        return im
    if len(im.shape) == 3:
        selem = morphology.ball(size)
    elif len(im.shape) == 2:
        selem = morphology.disk(size)
    dilated = morphology.dilation(im, selem)
    return dilated

def applyThreshold(im, threshold, reverse=False):
    mask = np.zeros_like(im)
    if reverse:
        mask[im < threshold] = 255
    else:
        mask[im > threshold] = 255
    return mask
