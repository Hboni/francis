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

    assert np.sum(core.erode(square, 1)) == 4**3
    assert np.sum(core.erode(square, 2)) == 2**3


def test_dilation(square):

    assert np.sum(core.dilate(square, 1)) == 8**3
    assert np.sum(core.dilate(square, 2)) == 10**3
