from skimage import morphology
import copy

def erode(im, size):
    eroded = copy.copy(im)
    if size > 1:
        for i in range(len(im)):
            eroded[i] = morphology.erosion(im[i], morphology.square(size))
    return eroded

def dilate(im, size):
    dilated = copy.copy(im)
    if size > 1:
        for i in range(len(im)):
            dilated[i] = morphology.dilation(im[i], morphology.square(size))
    return dilated
