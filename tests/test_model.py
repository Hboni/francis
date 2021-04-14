import pytest
import numpy as np
from src.model import core


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
    return np.array([[i]*10 for i in range(10)])


def test_erode(cube, square):
    assert np.sum(core.apply_basic_morpho(cube, 1, 'erosion', round_shape=False)) == 4**3
    assert np.sum(core.apply_basic_morpho(cube, 2, 'erosion', round_shape=False)) == 2**3

    assert np.sum(core.apply_basic_morpho(square, 1, 'erosion', round_shape=True)) == 4**2
    assert np.sum(core.apply_basic_morpho(square, 2, 'erosion', round_shape=True)) == 2**2

    assert np.array_equal(core.apply_basic_morpho(square, 1, 'erosion', round_shape=True),
                          core.apply_basic_morpho(square, 1, 'erosion', round_shape=False))

    assert np.array_equal(
        core.apply_basic_morpho(
            core.apply_basic_morpho(cube, 1, 'dilation', round_shape=False),
            1, 'erosion', round_shape=False
        ),
        cube)


def test_dilation(cube, square):
    assert np.sum(core.apply_basic_morpho(cube, 1, 'dilation', round_shape=False)) == 8**3
    assert np.sum(core.apply_basic_morpho(cube, 2, 'dilation', round_shape=False)) == 10**3
    assert np.sum(core.apply_basic_morpho(cube, 1, 'dilation', round_shape=True)) == 432
    assert np.sum(core.apply_basic_morpho(cube, 2, 'dilation', round_shape=True)) == 728

    assert np.sum(core.apply_basic_morpho(square, 1, 'dilation', round_shape=False)) == 8**2
    assert np.sum(core.apply_basic_morpho(square, 2, 'dilation', round_shape=False)) == 10**2
    assert np.sum(core.apply_basic_morpho(square, 1, 'dilation', round_shape=True)) == 8**2 - 4

    assert np.array_equal(
        core.apply_basic_morpho(
            core.apply_basic_morpho(cube, 1, 'erosion', round_shape=False),
            1, 'dilation', round_shape=False
        ),
        cube)


def test_threshold(grey_scale):
    assert np.sum(core.apply_threshold(grey_scale, 2) > 0) == 7*10
    assert np.sum(core.apply_threshold(grey_scale, 5) > 0) == 4*10
    assert np.sum(core.apply_threshold(grey_scale, 4, True) > 0) == 4*10
    assert np.sum(core.apply_threshold(grey_scale, 7, True) > 0) == 7*10


def test_add_value(cube, square):
    assert np.max(core.apply_operation(square, 2, operation='add')) == np.max(square) + 2
    assert np.max(core.apply_operation(square, 0, operation='add')) == np.max(square)
    assert np.max(core.apply_operation(cube, 2, operation='add')) == np.max(cube) + 2
    assert np.max(core.apply_operation(cube, 0, operation='add')) == np.max(cube)


def test_add_image(cube, square):
    assert np.sum(core.apply_operation(square, square, operation='add')) == 2 * np.sum(square)
    assert np.sum(core.apply_operation(square, [square, square, square], operation='add')) == 4 * np.sum(square)
    assert np.sum(core.apply_operation(cube, cube, operation='add')) == 2 * np.sum(cube)
    assert np.sum(core.apply_operation(cube, [cube, cube, cube], operation='add')) == 4 * np.sum(cube)


def test_subtract_value(cube, square):
    assert np.max(core.apply_operation(square, 2, operation='subtract')) == np.max(square) - 2
    assert np.max(core.apply_operation(square, 0, operation='subtract')) == np.max(square)
    assert np.max(core.apply_operation(cube, 2, operation='subtract')) == np.max(cube) - 2
    assert np.max(core.apply_operation(cube, 0, operation='subtract')) == np.max(cube)


def test_subtract_image(cube, square):
    assert np.sum(core.apply_operation(square, square, operation='subtract')) == 0
    assert np.sum(core.apply_operation(square, [square, square, square], operation='subtract')) == -2 * np.sum(square)
    assert np.sum(core.apply_operation(cube, cube, operation='subtract')) == 0
    assert np.sum(core.apply_operation(cube, [cube, cube, cube], operation='subtract')) == -2 * np.sum(cube)


def test_multiply_value(cube, square):
    assert np.max(core.apply_operation(square, 5, operation='multiply')) == 5
    assert np.min(core.apply_operation(square, -4, operation='multiply')) == -4
    assert np.max(core.apply_operation(square, 0, operation='multiply')) == 0
    assert np.max(core.apply_operation(cube, 5, operation='multiply')) == 5
    assert np.min(core.apply_operation(cube, -4, operation='multiply')) == -4
    assert np.max(core.apply_operation(cube, 0, operation='multiply')) == 0


def test_multiply_image(cube, square):
    self_multiply = core.apply_operation(square, square, operation='multiply')
    assert np.array_equal(self_multiply, square)


def test_divide_value(cube, square):
    assert np.max(core.apply_operation(square, 2, operation='divide')) == 0.5
    assert np.min(core.apply_operation(square, -2, operation='divide')) == -0.5
