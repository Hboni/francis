from skimage import morphology
import numpy as np
import nibabel as nib
import imageio
import os
import pickle
import imageio.core.util


# remove imageio warnings
def silence_imageio_warning(*args, **kwargs):
    pass


imageio.core.util._precision_warn = silence_imageio_warning


class Model:
    def load(self, path):
        """
        this method has a vocation to load any type of file

        Parameters
        ----------
        path: str
            handled extensions: nii, nii.gz, png, jpg, txt, pkl

        Return
        ------
        data: any type of data

        """
        root, ext = os.path.splitext(path)
        if ext == '.txt':
            with open(path, 'r') as f:
                data = f.read()
        elif ext == '.pkl':
            with open(path, 'rb') as f:
                data = pickle.load(f)
        elif ext == '.nii' or path.endswith('.nii.gz'):
            data = nib.load(path).get_fdata()
        elif ext in ['.png', '.jpg']:
            data = imageio.imread(path)
        else:
            raise TypeError("{} not handle yet".format(ext))
        return data

    def save(self, data, path):
        """
        this method has a vocation to save any type of file

        Parameters
        ----------
        data: any type of data
        path: str

        Return
        ------
        result: str
            message to inform the saved path

        """
        root, ext = os.path.splitext(path)
        if ext == '.txt':
            with open(path, 'w') as f:
                f.write(str(data))
        elif ext == '.pkl':
            with open(path, 'wb') as f:
                pickle.dump(data, f)
        elif ext in ['.nii.gz', '.nii']:
            ni_img = nib.Nifti1Image(data, None)
            nib.save(ni_img, path)
        elif ext in ['.png', '.jpg']:
            data = np.squeeze(data)
            if data.ndim == 3 and np.min(data.shape) < 5:
                # save 3d image as rgb or rgba image if possible
                # (smaller dimension send to the end)
                data = np.rollaxis(data, np.argmin(data.shape), data.ndim)
            elif data.ndim > 2:
                # 3D image can be saved as a list of 2D images in a directory
                # work for ndimage recursively
                if not os.path.exists(root):
                    os.makedirs(root)
                head, tail = os.path.split(root)
                for i in range(data.shape[0]):
                    new_path = os.path.join(root, tail+str(i)+ext)
                    self.save(data[i], new_path)
                return "images are saved in directory {}".format(root)

            imageio.imwrite(path, data)
        return "saved as {}".format(path)

    def get_img_infos(self, im, info='max'):
        """
        get info of the input image

        Parameters
        ----------
        im: 2D/3D numpy array
        info: {'max', 'min', 'mean'}, default='max'

        Returns
        -------
        value: float
            info you want to extract from the image
        """
        value = eval("np.{0}(im)".format(info))
        return value

    def apply_basic_morpho(self, im, size, operation='erosion', round_shape=True):
        """
        Apply basic morphological operation on the input image

        Parameters
        ----------
        im: 2d/3d numpy array
        size: int
            Generate an element of size (size*2+1)
        operation: {'erosion', 'dilation', 'binary_erosion', 'binary_dilation'}, default='erosion'
        round_shape: str, default=True
            If True the element is ball (3d) or disk (2d),
            else the element is cube (3d) or square (2d)

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
        return function(im, selem)

    def apply_operation(self, arr, elements=[], operation='add'):
        """

        Parameters
        ----------
        arr: 2d/3d array
        elements: list of 2d/3d arrays or float, default=[]
        operation: {'add', 'multiply', 'subtract', 'divide'}, default='add'
        output_minimize_bytes: bool, default=True

        Return
        ------
        arr: 2d/3d array

        """
        if not isinstance(elements, list):
            elements = [elements]

        function = eval("np."+operation)
        for element in elements:
            arr = function(arr, element, dtype=np.float64)
        return arr

    def apply_threshold(self, im, threshold, reverse=False):
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
