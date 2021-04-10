MODULES = {
    "load image": {
        "type": "primary",
        "ui": "LoadImage.ui",
        "function": "load_image"
    },
    "threshold image": {
        "type": "secondary",
        "menu": "thresholding",
        "ui": "ThresholdImage.ui",
        "function": "update_threshold"
    },
    "add images": {
        "type": "secondary",
        "menu": "operation",
        "ui": "AddImages.ui",
        "function": "add_images"
    },
    "substract images": {
        "type": "secondary",
        "menu": "operation",
        "ui": "SubstractImages.ui",
        "function": "substract_images"
    },
    "multiply images": {
        "type": "secondary",
        "menu": "operation",
        "ui": "MultiplyImages.ui",
        "function": "multiply_images"
    },
    "divide images": {
        "type": "secondary",
        "menu": "operation",
        "ui": "DivideImages.ui",
        "function": "divide_images"
    },
    "erode image": {
        "type": "secondary",
        "menu": "morpho/basics",
        "ui": "ErodeImage.ui",
        "function": "update_erosion"
    },
    "dilate image": {
        "type": "secondary",
        "menu": "morpho/basics",
        "ui": "DilateImage.ui",
        "function": "update_dilation"
    },
    "save image": {
        "type": "secondary",
        "ui": "SaveImage.ui",
        "function": "save_image"
    },
    "delete": {
        "type": "secondary"
    }
}
