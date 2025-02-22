import numpy as np
from scipy.linalg import block_diag
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu
from typing import Dict, List, Optional, Union

from autoconf import cached_property
from autoarray.numba_util import profile_func

from autoarray.structures.arrays.two_d.array_2d import Array2D
from autoarray.structures.grids.two_d.grid_2d_irregular import Grid2DIrregular
from autoarray.structures.visibilities import Visibilities
from autoarray.inversion.linear_obj import LinearObj
from autoarray.inversion.regularization.abstract import AbstractRegularization
from autoarray.inversion.linear_eqn.imaging import AbstractLEqImaging
from autoarray.inversion.linear_eqn.interferometer import AbstractLEqInterferometer
from autoarray.inversion.inversion.settings import SettingsInversion
from autoarray.preloads import Preloads

from autoarray import exc
from autoarray.inversion.inversion import inversion_util


class AbstractInversion:
    def __init__(
        self,
        data: Union[Visibilities, Array2D],
        leq: Union[AbstractLEqImaging, AbstractLEqInterferometer],
        regularization_list: Optional[List[AbstractRegularization]] = None,
        settings: SettingsInversion = SettingsInversion(),
        preloads: Preloads = Preloads(),
        profiling_dict: Optional[Dict] = None,
    ):
        """
        An inversion uses linear matrix
        Parameters
        ----------
        data
        leq
        regularization_list
        settings
        preloads
        profiling_dict
        """
        self.data = data

        self.leq = leq
        self.regularization_list = regularization_list

        self.settings = settings
        self.preloads = preloads
        self.profiling_dict = profiling_dict

    @property
    def linear_obj_list(self):
        return self.leq.linear_obj_list

    @property
    def mapper_list(self):
        return self.leq.mapper_list

    @property
    def has_mapper(self):
        return self.leq.has_mapper

    @property
    def has_one_mapper(self):
        return self.leq.has_one_mapper

    @property
    def noise_map(self):
        return self.leq.noise_map

    @cached_property
    @profile_func
    def regularization_matrix(self) -> Optional[np.ndarray]:
        """
        The regularization matrix H is used to impose smoothness on our inversion's reconstruction. This enters the
        linear algebra system we solve for using D and F above and is given by
        equation (12) in https://arxiv.org/pdf/astro-ph/0302587.pdf.

        A complete description of regularization is given in the `regularization.py` and `regularization_util.py`
        modules.

        For multiple mappers, the regularization matrix is computed as the block diagonal of each individual mapper.
        The scipy function `block_diag` has an overhead associated with it and if there is only one mapper and
        regularization it is bypassed.
        """
        if self.preloads.regularization_matrix is not None:
            return self.preloads.regularization_matrix

        if not self.has_mapper:
            return None

        if self.has_one_mapper:
            return self.regularization_list[0].regularization_matrix_from(
                mapper=self.linear_obj_list[0]
            )

        return block_diag(
            *[
                reg.regularization_matrix_from(mapper=mapper)
                for (reg, mapper) in zip(self.regularization_list, self.mapper_list)
            ]
        )

    @cached_property
    @profile_func
    def reconstruction(self):
        raise NotImplementedError

    @property
    def reconstruction_dict(self) -> Dict[LinearObj, np.ndarray]:
        return self.leq.source_quantity_dict_from(source_quantity=self.reconstruction)

    @property
    def mapped_reconstructed_data_dict(
        self
    ) -> Dict[LinearObj, Union[Array2D, Visibilities]]:
        """
        Using the reconstructed source pixel fluxes we map each source pixel flux back to the image plane and
        reconstruct the image data.

        This uses the unique mappings of every source pixel to image pixels, which is a quantity that is already
        computed when using the w-tilde formalism.

        Returns
        -------
        Array2D
            The reconstructed image data which the inversion fits.
        """
        return self.leq.mapped_reconstructed_data_dict_from(
            reconstruction=self.reconstruction
        )

    @property
    def mapped_reconstructed_image_dict(self) -> Dict[LinearObj, Array2D]:
        """
        Using the reconstructed source pixel fluxes we map each source pixel flux back to the image plane and
        reconstruct the image data.

        This uses the unique mappings of every source pixel to image pixels, which is a quantity that is already
        computed when using the w-tilde formalism.

        Returns
        -------
        Array2D
            The reconstructed image data which the inversion fits.
        """
        return self.leq.mapped_reconstructed_image_dict_from(
            reconstruction=self.reconstruction
        )

    @cached_property
    @profile_func
    def mapped_reconstructed_data(self) -> Union[Array2D, Visibilities]:
        """
        Using the reconstructed source pixel fluxes we map each source pixel flux back to the image plane and
        reconstruct the image data.

        This uses the unique mappings of every source pixel to image pixels, which is a quantity that is already
        computed when using the w-tilde formalism.

        Returns
        -------
        Array2D
            The reconstructed image data which the inversion fits.
        """
        return sum(self.mapped_reconstructed_data_dict.values())

    @cached_property
    def mapped_reconstructed_image(self) -> Array2D:
        """
        Using the reconstructed source pixel fluxes we map each source pixel flux back to the image plane and
        reconstruct the image data.

        This uses the unique mappings of every source pixel to image pixels, which is a quantity that is already
        computed when using the w-tilde formalism.

        Returns
        -------
        Array2D
            The reconstructed image data which the inversion fits.
        """
        return sum(self.mapped_reconstructed_image_dict.values())

    @cached_property
    @profile_func
    def regularization_term(self):
        """
        Returns the regularization term of an inversion. This term represents the sum of the difference in flux
        between every pair of neighboring pixels.

        This is computed as:

        s_T * H * s = solution_vector.T * regularization_matrix * solution_vector

        The term is referred to as *G_l* in Warren & Dye 2003, Nightingale & Dye 2015.

        The above works include the regularization_matrix coefficient (lambda) in this calculation. In PyAutoLens,
        this is already in the regularization matrix and thus implicitly included in the matrix multiplication.
        """
        return np.matmul(
            self.reconstruction.T,
            np.matmul(self.regularization_matrix, self.reconstruction),
        )

    @cached_property
    @profile_func
    def log_det_curvature_reg_matrix_term(self):
        """
        The log determinant of [F + reg_coeff*H] is used to determine the Bayesian evidence of the solution.

        This uses the Cholesky decomposition which is already computed before solving the reconstruction.
        """
        raise NotImplementedError

    @cached_property
    @profile_func
    def log_det_regularization_matrix_term(self) -> float:
        """
        The Bayesian evidence of an inversion which quantifies its overall goodness-of-fit uses the log determinant
        of regularization matrix, Log[Det[Lambda*H]].

        Unlike the determinant of the curvature reg matrix, which uses an existing preloading Cholesky decomposition
        used for the source reconstruction, this uses scipy sparse linear algebra to solve the determinant efficiently.

        Returns
        -------
        float
            The log determinant of the regularization matrix.
        """
        if self.preloads.log_det_regularization_matrix_term is not None:
            return self.preloads.log_det_regularization_matrix_term

        try:

            lu = splu(csc_matrix(self.regularization_matrix))
            diagL = lu.L.diagonal()
            diagU = lu.U.diagonal()
            diagL = diagL.astype(np.complex128)
            diagU = diagU.astype(np.complex128)

            return np.real(np.log(diagL).sum() + np.log(diagU).sum())

        except RuntimeError:

            try:
                return 2.0 * np.sum(
                    np.log(np.diag(np.linalg.cholesky(self.regularization_matrix)))
                )
            except np.linalg.LinAlgError:
                raise exc.InversionException()

    @property
    def errors_with_covariance(self):
        raise NotImplementedError

    @property
    def errors(self):
        raise NotImplementedError

    @property
    def brightest_reconstruction_pixel_list(self):

        brightest_reconstruction_pixel_list = []

        for mapper in self.mapper_list:

            brightest_reconstruction_pixel_list.append(
                np.argmax(self.reconstruction_dict[mapper])
            )

        return brightest_reconstruction_pixel_list

    @property
    def brightest_reconstruction_pixel_centre_list(self):

        brightest_reconstruction_pixel_centre_list = []

        for mapper in self.mapper_list:

            brightest_reconstruction_pixel = np.argmax(self.reconstruction_dict[mapper])

            centre = Grid2DIrregular(
                grid=[mapper.source_pixelization_grid[brightest_reconstruction_pixel]]
            )

            brightest_reconstruction_pixel_centre_list.append(centre)

        return brightest_reconstruction_pixel_centre_list

    @property
    def error_dict(self) -> Dict[LinearObj, np.ndarray]:
        return self.leq.source_quantity_dict_from(source_quantity=self.errors)

    @property
    def regularization_weights_mapper_dict(self) -> Dict[LinearObj, np.ndarray]:

        regularization_weights_dict = {}

        for mapper, reg in zip(self.mapper_list, self.regularization_list):

            regularization_weights = reg.regularization_weights_from(mapper=mapper)

            regularization_weights_dict[mapper] = regularization_weights

        return regularization_weights_dict

    @property
    def residual_map_mapper_dict(self) -> Dict[LinearObj, np.ndarray]:

        return {
            mapper: inversion_util.inversion_residual_map_from(
                reconstruction=self.reconstruction_dict[mapper],
                data=self.data,
                slim_index_for_sub_slim_index=mapper.source_grid_slim.mask.slim_index_for_sub_slim_index,
                sub_slim_indexes_for_pix_index=mapper.sub_slim_indexes_for_pix_index,
            )
            for mapper in self.mapper_list
        }

    @property
    def normalized_residual_map_mapper_dict(self) -> Dict[LinearObj, np.ndarray]:

        return {
            mapper: inversion_util.inversion_normalized_residual_map_from(
                reconstruction=self.reconstruction_dict[mapper],
                data=self.data,
                noise_map_1d=self.noise_map.slim,
                slim_index_for_sub_slim_index=mapper.source_grid_slim.mask.slim_index_for_sub_slim_index,
                sub_slim_indexes_for_pix_index=mapper.sub_slim_indexes_for_pix_index,
            )
            for mapper in self.mapper_list
        }

    @property
    def chi_squared_map_mapper_dict(self) -> Dict[LinearObj, np.ndarray]:

        return {
            mapper: inversion_util.inversion_chi_squared_map_from(
                reconstruction=self.reconstruction_dict[mapper],
                data=self.data,
                noise_map_1d=self.noise_map.slim,
                slim_index_for_sub_slim_index=mapper.source_grid_slim.mask.slim_index_for_sub_slim_index,
                sub_slim_indexes_for_pix_index=mapper.sub_slim_indexes_for_pix_index,
            )
            for mapper in self.mapper_list
        }

    @property
    def total_mappers(self):
        return len(self.mapper_list)
