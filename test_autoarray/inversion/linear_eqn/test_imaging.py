import autoarray as aa
from autoarray.dataset.imaging import WTildeImaging
from autoarray.inversion.linear_eqn.imaging import LEqImagingWTilde

from autoarray.mock.mock import MockConvolver, MockLEqImaging, MockMapper

from autoarray import exc

import numpy as np
from os import path
import pytest

directory = path.dirname(path.realpath(__file__))


class TestLEqImaging:
    def test__blurred_mapping_matrix_property(
        self, convolver_7x7, rectangular_mapper_7x7_3x3
    ):

        leq = MockLEqImaging(
            convolver=convolver_7x7, linear_obj_list=[rectangular_mapper_7x7_3x3]
        )

        assert leq.blurred_mapping_matrix[0, 0] == pytest.approx(1.0, 1e-4)

        convolver = MockConvolver(blurred_mapping_matrix=np.ones((2, 2)))

        leq = MockLEqImaging(
            convolver=convolver,
            linear_obj_list=[rectangular_mapper_7x7_3x3, rectangular_mapper_7x7_3x3],
        )

        blurred_mapping_matrix = np.array([[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]])

        assert leq.blurred_mapping_matrix == pytest.approx(
            blurred_mapping_matrix, 1.0e-4
        )

    def test__w_tilde_checks_noise_map_and_raises_exception_if_preloads_dont_match_noise_map(
        self
    ):

        matrix_shape = (9, 3)

        mask = aa.Mask2D.manual(
            mask=np.array(
                [[True, True, True], [False, False, False], [True, True, True]]
            ),
            pixel_scales=1.0,
            sub_size=1,
        )

        grid = aa.Grid2D.from_mask(mask=mask)

        w_tilde = WTildeImaging(
            curvature_preload=None, indexes=None, lengths=None, noise_map_value=2.0
        )

        with pytest.raises(exc.InversionException):

            # noinspection PyTypeChecker
            LEqImagingWTilde(
                noise_map=np.ones(9),
                convolver=MockConvolver(matrix_shape),
                w_tilde=w_tilde,
                linear_obj_list=MockMapper(
                    mapping_matrix=np.ones(matrix_shape), source_grid_slim=grid
                ),
            )
