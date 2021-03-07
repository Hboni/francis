from skimage import morphology
import copy

def erode(im, size):
    eroded = copy.copy(im)
    if size > 1:
        for i in range(len(im)):
            eroded[i] = morphology.erosion(im[i], morphology.square(size))
    return eroded
