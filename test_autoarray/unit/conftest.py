from os import path

import numpy as np
import pytest

import autoarray as aa
from autoarray import conf

from test_autoarray.mock import mock_mask
from test_autoarray.mock import mock_grids
from test_autoarray.mock import mock_convolution

directory = path.dirname(path.realpath(__file__))


@pytest.fixture(autouse=True)
def set_config_path():
    conf.instance = conf.Config(
        path.join(directory, "test_files/config"), path.join(directory, "output")
    )


# MASK #


@pytest.fixture(name="mask_7x7")
def make_mask_7x7():
    mask_2d = np.array(
        [
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, False, False, False, True, True],
            [True, True, False, False, False, True, True],
            [True, True, False, False, False, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
        ]
    )

    return mock_mask.MockMask(mask_2d=mask_2d, pixel_scales=(1.0, 1.0), sub_size=1)


@pytest.fixture(name="sub_mask_7x7")
def make_sub_mask_7x7():
    mask_2d = np.array(
        [
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, False, False, False, True, True],
            [True, True, False, False, False, True, True],
            [True, True, False, False, False, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
        ]
    )

    return mock_mask.MockMask(mask_2d=mask_2d, sub_size=2)


@pytest.fixture(name="mask_7x7_1_pix")
def make_mask_7x7_1_pix():
    mask_2d = np.array(
        [
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, False, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
            [True, True, True, True, True, True, True],
        ]
    )

    return mock_mask.MockMask(mask_2d=mask_2d)


@pytest.fixture(name="blurring_mask_7x7")
def make_blurring_mask_7x7():
    blurring_mask_2d = np.array(
        [
            [True, True, True, True, True, True, True],
            [True, False, False, False, False, False, True],
            [True, False, True, True, True, False, True],
            [True, False, True, True, True, False, True],
            [True, False, True, True, True, False, True],
            [True, False, False, False, False, False, True],
            [True, True, True, True, True, True, True],
        ]
    )

    return mock_mask.MockMask(blurring_mask_2d=blurring_mask_2d)


@pytest.fixture(name="mask_6x6")
def make_mask_6x6():
    mask_2d = np.array(
        [
            [True, True, True, True, True, True],
            [True, True, True, True, True, True],
            [True, True, False, False, True, True],
            [True, True, False, False, True, True],
            [True, True, True, True, True, True],
            [True, True, True, True, True, True],
        ]
    )

    return mock_mask.MockMask(mask_2d=mask_2d)


# GRIDS #


@pytest.fixture(name="grid_7x7")
def make_grid_7x7(mask_7x7):
    return aa.grid_masked.from_mask(mask=mask_7x7)


@pytest.fixture(name="sub_grid_7x7")
def make_sub_grid_7x7(sub_mask_7x7):
    return aa.grid_masked.from_mask(mask=sub_mask_7x7)


@pytest.fixture(name="blurring_grid_7x7")
def make_blurring_grid_7x7(blurring_mask_7x7):
    return aa.grid_masked.from_mask(mask=blurring_mask_7x7)


# CONVOLVERS #


@pytest.fixture(name="convolver_7x7")
def make_convolver_7x7(mask_7x7, blurring_mask_7x7, psf_3x3):
    return mock_convolution.MockConvolver(
        mask=mask_7x7, blurring_mask=blurring_mask_7x7, kernel=psf_3x3
    )
