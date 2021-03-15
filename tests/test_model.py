import pytest
import numpy as np
from src.model import core


@pytest.fixture
def square():
    # Initialize a sphere
    sq_arr = np.zeros((10, 10, 10))
    sq_arr[2:8, 2:8, 2:8] = 1
    return sq_arr

def test_erode(square):
    assert np.sum(core.erode(square, 1, round_shape=False)) == 4**3
    assert np.sum(core.erode(square, 2, round_shape=False)) == 2**3
    assert np.sum(core.erode(square, 1, round_shape=True)) == 4**3
    assert np.sum(core.erode(square, 2, round_shape=True)) == 2**3

def test_dilation(square):
    assert np.sum(core.dilate(square, 1, round_shape=False)) == 8**3
    assert np.sum(core.dilate(square, 2, round_shape=False)) == 10**3
    assert np.sum(core.dilate(square, 1, round_shape=True)) == 432
    assert np.sum(core.dilate(square, 2, round_shape=True)) == 728
