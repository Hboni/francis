import os
import pickle

import imageio
import imageio.core.util
import nibabel as nib
import numpy as np
from skimage import morphology


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
        if ext == ".txt":
            with open(path, "r") as f:
                data = f.read()
        elif ext == ".pkl":
            with open(path, "rb") as f:
                data = pickle.load(f)
        elif ext == ".nii" or path.endswith(".nii.gz"):
            data = nib.load(path).get_fdata()
        elif ext in [".png", ".jpg"]:
            data = imageio.imread(path)
            if data.ndim == 3:
                # remove alpha channel
                if data.shape[2] == 4:
                    data = data[:, :, :3]
                # convert to gray if same value everywhere in each r, g, b canal
                if data.shape[2] == 3 and (data[:, :, 0] == data[:, :, 1]).all() \
                        and (data[:, :, 1] == data[:, :, 2]).all():
                    data = data[:, :, 0]
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
        if ext == ".txt":
            with open(path, "w") as f:
                f.write(str(data))
        elif ext == ".pkl":
            with open(path, "wb") as f:
                pickle.dump(data, f)
        elif isinstance(data, np.ndarray):
            if ext in [".nii.gz", ".nii"]:
                ni_img = nib.Nifti1Image(data, None)
                nib.save(ni_img, path)
            elif ext in [".png", ".jpg"]:
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
                        new_path = os.path.join(root, tail + str(i) + ext)
                        self.save(data[i], new_path)
                    return "images are saved in directory {}".format(root)

                imageio.imwrite(path, data)
        return "saved as {}".format(path)

    def extract_channel(self, im, channel='red'):
        """
        extract channel from image

        Parameters
        ----------
        im: 2D numpy array
        channel: {'red', 'green', 'blue'}, default='red'

        Return
        ------
        result: 2D numpy array

        """
        if im.ndim != 3 or im.shape[2] != 3:
            raise Exception("You cannot extract red, green or blue channel from this image")
        idx = ['red', 'green', 'blue'].index(channel)
        return im[:, :, idx]

    def get_img_infos(self, im, info='max'):
        """
        get info of the input image

        Parameters
        ----------
        im: 2D/3D numpy array
        info: {'max', 'min', 'mean'}, default='max'

        Return
        -------
        value: float
            info you want to extract from the image
        """
        value = eval("np.{0}(im)".format(info))
        return value

    def apply_basic_morpho(self, im, size, operation="erosion", round_shape=True):
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
            selem = (
                morphology.ball(size) if round_shape else morphology.cube(size * 2 + 1)
            )
        elif len(im.shape) == 2:
            selem = (
                morphology.disk(size)
                if round_shape
                else morphology.square(size * 2 + 1)
            )

        function = eval("morphology." + operation)
        return function(im, selem)

    def apply_operation(self, arr, elements=[], operation="add"):
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

        function = eval("np." + operation)
        for element in elements:
            arr = function(arr, element, dtype=np.float64)
        return arr

    def apply_formula(self, formula, elements):
        """
        This function calculate complexe operations between float/int and images
        it handles parenthesis grouping and operator priorities.
        And it calls "apply_operation" to do pear operations recursively.

        Parameters
        ----------
        formula: str
        elements: dict
            this dictionary contains data (image or float/int...)

        Return
        ------
        result: np.ndarray or int/float
            the result type depends on the formula.

        Example
        -------
        formula = "( 3 x [key_1] + 4 x [key_2] ) ÷ [key_3]"
        elements = {'key_1': np.array([...]),   # image
                    'key_2': np.array([...]),   # image
                    'key_3': 2}                 # integer

        This will recursively apply (call self.apply_operation method):
            - M1 = multiplication of key_1 image and 3
            - M2 = multiplication of key_2 image and 4
            - A1 = addition of M1 and M2
            - result = division of A1 and key_3 value
        """
        # operations ordered on priorities
        operations = ['multiply', 'divide', 'add', 'subtract']
        signs = ['x', '÷', '+', '-']

        # initialize formula
        formula = formula.replace(',', '.')
        formula = formula.replace(' ', '')

        # add space where we need to split formula
        formula = list(formula)
        for i, f in reversed(list(enumerate(formula))):
            # check if '-' is minus and not subtract
            if f == '-' and (i == 0 or formula[i-1] in signs + ['(']):
                formula[i] = "-1 x "
            elif f in signs + ['(', ')']:
                formula[i] = " {} ".format(f)
        formula = "".join(formula)
        # split formula
        formula = formula.split(' ')
        formula = [f for f in formula if f]

        def apply_formula_recursively(fml, elems, elem_id=0):
            if len(fml) == 1:
                if fml[0].startswith('['):
                    res = elems[fml[0][1:-1]]
                else:
                    res = eval(fml[0])
            # apply pear operation (with one operator and two elements)
            # example [Load_1] x 5
            elif len(fml) == 3 and fml[1] in signs:
                op_sign = fml.pop(1)
                for i, f in enumerate(fml):
                    if f.startswith('['):
                        fml[i] = elems[f[1:-1]]
                    else:
                        fml[i] = eval(f)
                for operation, sign in zip(operations, signs):
                    if op_sign == sign:
                        res = self.apply_operation(fml[0], fml[1], operation)
            else:
                # recursively apply formula on group in parenthesis
                if '(' in fml:
                    for i, f in enumerate(fml):
                        if f == '(':
                            start = i
                        elif f == ')':
                            end = i + 1
                            break
                    sub_fml = fml[start+1:end-1]

                # recursively apply formula on prioritary pear operations
                else:
                    for sign in signs:
                        if sign in fml:
                            start = fml.index(sign) - 1
                            end = fml.index(sign) + 2
                            break
                    sub_fml = fml[start:end]

                # do recusrsivity
                name = "_ID{}".format(elem_id)
                elem_id += 1
                res, elem_id = apply_formula_recursively(sub_fml, elems, elem_id)
                elems[name] = res
                fml = fml[:start] + ["[{}]".format(name)] + fml[end:]
                res, elem_id = apply_formula_recursively(fml, elems, elem_id)
            return res, elem_id

        result, _ = apply_formula_recursively(formula, elements)
        return result

    def apply_threshold(self, im, threshold, reverse=False, thresholdInPercentage=False):
        """
        Apply binary threshold on the input image

        Parameters
        ----------
        im: 2d/3d numpy array
        threshold: float
            Pixel value, image=1 above threshold, image=0 below threshold
        reverse: bool, default=False
            If True invert 0 and 1 in output
        thresholdInPercentage: bool, default=False

        Returns
        -------
        mask: 2d/3d numpy array
            Binarized input image with same size as im

        """
        if thresholdInPercentage:
            mini, maxi = np.min(im), np.max(im)
            threshold = mini + threshold * (maxi - mini) / 100
        mask = im < threshold if reverse else im > threshold
        return mask.astype(np.uint8)
