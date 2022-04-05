import os

import numpy as np
import pytest
from src.model.model import Model

mdl = Model()


@pytest.fixture
def cube():
    cube_arr = np.zeros((10, 10, 10))
    cube_arr[2:8, 2:8, 2:8] = 1
    return cube_arr


@pytest.fixture
def square():
    sq_arr = np.zeros((10, 10))
    sq_arr[2:8, 2:8] = 1
    return sq_arr


@pytest.fixture
def grey_scale():
    return np.array([[i] * 10 for i in range(10)])


@pytest.fixture(params=[
    os.path.join(os.getcwd(), 'resources/data/cvs_avg35_inMNI152.nii.gz'),
    os.path.join(os.getcwd(), 'resources/data/Lena.png'),
    os.path.join(os.getcwd(), 'resources/data/lena_mean.pkl'),
    os.path.join(os.getcwd(), 'resources/data/simple_text.txt')
])
def test_file_path(request):
    return request.param


@pytest.fixture(scope='module', params=[
    os.path.join(os.getcwd(), 'resources/data/out/saved_image.nii'),
    os.path.join(os.getcwd(), 'resources/data/out/saved_image.png'),
    os.path.join(os.getcwd(), 'resources/data/out/saved_pickle.pkl'),
    os.path.join(os.getcwd(), 'resources/data/out/saved_text.txt')
    ])
def test_file_write_path(request):
    if os.path.exists(request.param):
        os.remove(request.param)
    return request.param


def test_load_file(test_file_path):
    if test_file_path.endswith('.txt'):
        assert mdl.load(test_file_path) == "Hello there!\n"
    else:
        assert isinstance(mdl.load(test_file_path).shape, tuple)


def test_save_file(test_file_path, test_file_write_path):
    data = mdl.load(test_file_path)
    mdl.save(data, test_file_write_path)
    root, ext = os.path.splitext(test_file_write_path)
    if ext == ".png" and test_file_path.endswith(".nii.gz"):
        assert os.path.exists(root)
        assert os.path.exists(os.path.join(root, "saved_image0.png"))
    elif test_file_path.endswith(ext):
        mdl.save(data, test_file_write_path)
        assert os.path.exists(test_file_write_path)


def test_get_img_infos(square):
    assert mdl.get_img_infos(square, info="max") == 1


def test_erode(cube, square):
    assert np.sum(mdl.apply_basic_morpho(cube, 0, 'erosion', round_shape=False)) == 6**3
    assert np.sum(mdl.apply_basic_morpho(cube, 1, 'erosion', round_shape=False)) == 4**3
    assert np.sum(mdl.apply_basic_morpho(cube, 2, 'erosion', round_shape=False)) == 2**3

    assert np.sum(mdl.apply_basic_morpho(square, 0, 'erosion', round_shape=False)) == 6**2
    assert np.sum(mdl.apply_basic_morpho(square, 1, 'erosion', round_shape=True)) == 4**2
    assert np.sum(mdl.apply_basic_morpho(square, 2, 'erosion', round_shape=True)) == 2**2

    assert np.array_equal(
        mdl.apply_basic_morpho(square, 1, "erosion", round_shape=True),
        mdl.apply_basic_morpho(square, 1, "erosion", round_shape=False),
    )

    assert np.array_equal(
        mdl.apply_basic_morpho(
            mdl.apply_basic_morpho(cube, 1, "dilation", round_shape=False),
            1,
            "erosion",
            round_shape=False,
        ),
        cube,
    )


def test_dilation(cube, square):
    assert np.sum(mdl.apply_basic_morpho(cube, 0, 'dilation', round_shape=False)) == 6**3
    assert np.sum(mdl.apply_basic_morpho(cube, 1, 'dilation', round_shape=False)) == 8**3
    assert np.sum(mdl.apply_basic_morpho(cube, 2, 'dilation', round_shape=False)) == 10**3
    assert np.sum(mdl.apply_basic_morpho(cube, 1, 'dilation', round_shape=True)) == 432
    assert np.sum(mdl.apply_basic_morpho(cube, 2, 'dilation', round_shape=True)) == 728

    assert np.sum(mdl.apply_basic_morpho(square, 0, 'dilation', round_shape=False)) == 6**2
    assert np.sum(mdl.apply_basic_morpho(square, 1, 'dilation', round_shape=False)) == 8**2
    assert np.sum(mdl.apply_basic_morpho(square, 2, 'dilation', round_shape=False)) == 10**2
    assert np.sum(mdl.apply_basic_morpho(square, 1, 'dilation', round_shape=True)) == 8**2 - 4

    assert np.array_equal(
        mdl.apply_basic_morpho(
            mdl.apply_basic_morpho(cube, 1, "erosion", round_shape=False),
            1,
            "dilation",
            round_shape=False,
        ),
        cube,
    )


def test_threshold(grey_scale):
    assert np.sum(mdl.apply_threshold(grey_scale, 2) > 0) == 7*10
    assert np.sum(mdl.apply_threshold(grey_scale, 2) > 0) == 7*10
    assert np.sum(mdl.apply_threshold(grey_scale, 5) > 0) == 4*10
    assert np.sum(mdl.apply_threshold(grey_scale, 4, True) > 0) == 4*10
    assert np.sum(mdl.apply_threshold(grey_scale, 7, True) > 0) == 7*10
    assert np.sum(mdl.apply_threshold(grey_scale, 50, thresholdInPercentage=True) > 0) == 5*10
    assert np.sum(mdl.apply_threshold(grey_scale, 50, True, thresholdInPercentage=True) > 0) == 5*10


def test_add_value(cube, square):
    assert np.max(mdl.apply_operation(square, 2, operation="add")) == np.max(square) + 2
    assert np.max(mdl.apply_operation(square, 0, operation="add")) == np.max(square)
    assert np.max(mdl.apply_operation(cube, 2, operation="add")) == np.max(cube) + 2
    assert np.max(mdl.apply_operation(cube, 0, operation="add")) == np.max(cube)


def test_add_image(cube, square):
    assert np.sum(mdl.apply_operation(square, square, operation="add")) == 2 * np.sum(
        square
    )
    assert np.sum(
        mdl.apply_operation(square, [square, square, square], operation="add")
    ) == 4 * np.sum(square)
    assert np.sum(mdl.apply_operation(cube, cube, operation="add")) == 2 * np.sum(cube)
    assert np.sum(
        mdl.apply_operation(cube, [cube, cube, cube], operation="add")
    ) == 4 * np.sum(cube)


def test_subtract_value(cube, square):
    assert (
        np.max(mdl.apply_operation(square, 2, operation="subtract"))
        == np.max(square) - 2
    )
    assert np.max(mdl.apply_operation(square, 0, operation="subtract")) == np.max(
        square
    )
    assert (
        np.max(mdl.apply_operation(cube, 2, operation="subtract")) == np.max(cube) - 2
    )
    assert np.max(mdl.apply_operation(cube, 0, operation="subtract")) == np.max(cube)


def test_subtract_image(cube, square):
    assert np.sum(mdl.apply_operation(square, square, operation="subtract")) == 0
    assert np.sum(
        mdl.apply_operation(square, [square, square, square], operation="subtract")
    ) == -2 * np.sum(square)
    assert np.sum(mdl.apply_operation(cube, cube, operation="subtract")) == 0
    assert np.sum(
        mdl.apply_operation(cube, [cube, cube, cube], operation="subtract")
    ) == -2 * np.sum(cube)


def test_multiply_value(cube, square):
    assert np.max(mdl.apply_operation(square, 5, operation="multiply")) == 5
    assert np.min(mdl.apply_operation(square, -4, operation="multiply")) == -4
    assert np.max(mdl.apply_operation(square, 0, operation="multiply")) == 0
    assert np.max(mdl.apply_operation(cube, 5, operation="multiply")) == 5
    assert np.min(mdl.apply_operation(cube, -4, operation="multiply")) == -4
    assert np.max(mdl.apply_operation(cube, 0, operation="multiply")) == 0


def test_multiply_image(cube, square):
    self_multiply = mdl.apply_operation(square, square, operation="multiply")
    assert np.array_equal(self_multiply, square)


def test_divide_value(cube, square):
    assert np.max(mdl.apply_operation(square, 2, operation="divide")) == 0.5
    assert np.min(mdl.apply_operation(square, -2, operation="divide")) == -0.5
