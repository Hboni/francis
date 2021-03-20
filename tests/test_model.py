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
    assert np.sum(core.erode(cube, 1, round_shape=False)) == 4**3
    assert np.sum(core.erode(cube, 2, round_shape=False)) == 2**3

    assert np.sum(core.erode(square, 1, round_shape=True)) == 4**2
    assert np.sum(core.erode(square, 2, round_shape=True)) == 2**2

    assert np.array_equal(core.erode(square, 1, round_shape=True),
                          core.erode(square, 1, round_shape=False))

    assert np.array_equal(
        core.erode(
            core.dilate(cube, 1, round_shape=False),
            1, round_shape=False
        ),
        cube)


def test_dilation(cube, square):
    assert np.sum(core.dilate(cube, 1, round_shape=False)) == 8**3
    assert np.sum(core.dilate(cube, 2, round_shape=False)) == 10**3
    assert np.sum(core.dilate(cube, 1, round_shape=True)) == 432
    assert np.sum(core.dilate(cube, 2, round_shape=True)) == 728

    assert np.sum(core.dilate(square, 1, round_shape=False)) == 8**2
    assert np.sum(core.dilate(square, 2, round_shape=False)) == 10**2
    assert np.sum(core.dilate(square, 1, round_shape=True)) == 8**2 - 4

    assert np.array_equal(
        core.dilate(
            core.erode(cube, 1, round_shape=False),
            1, round_shape=False
        ),
        cube)


def test_threshold(grey_scale):
    assert np.sum(core.applyThreshold(grey_scale, 2) > 0) == 7*10
    assert np.sum(core.applyThreshold(grey_scale, 5) > 0) == 4*10
    assert np.sum(core.applyThreshold(grey_scale, 4, True) > 0) == 4*10
    assert np.sum(core.applyThreshold(grey_scale, 7, True) > 0) == 7*10
