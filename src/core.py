from skimage import morphology
import copy

def erode(im, size):
    eroded = copy.copy(im)
    for i in range(len(im)):
        eroded[i] = morphology.erosion(im[i], morphology.square(size))
    return eroded
