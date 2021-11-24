import numpy as np
from typing import Dict, Optional

from autoarray.inversion.pixelizations.settings import SettingsPixelization
from autoarray.structures.grids.two_d.grid_2d import Grid2D
from autoarray.structures.grids.two_d.grid_2d import Grid2DSparse
from autoarray.preloads import Preloads

from autoarray.numba_util import profile_func


class AbstractPixelization:
    def __init__(self):
        """
        Abstract base class for a pixelization, which discretizes a grid of (y,x) coordinates into pixels.

        The pixelization grid, and the grids they are used to discretize, have coordinates in one or both of the
        following two reference frames:

        - `data`: the original reference from of the masked data.

        - `source`: a reference frame where the grids in the `data` reference frame are transformed to create new grids
        of (y,x) coordinates. The transformation does not change the indexing, such that one can easily pair
        coordinates in the `source` frame to the `data` frame.

        The pixelization itself has its own (y,x) grid of coordinates, titled the `pixelization_grid`, which is
        typically much sparser than the grid associated with the original masked data. The `pixelization_grid` always
        has coordinates in the `source` reference frame but may also have coordinates in the `data` reference frame.

        For example, in the project PyAutoLens, we have a 2D image which is typically masked with a circular mask.
        Its `data_grid_slim` is a 2D grid aligned with this circle, where each (y,x) coordinate is aligned with the
        centre of an image pixel. A "lensing transformation" is performed which maps this circular grid of (y,x)
        coordinates to a new grid of coordinates in the `source` frame, where the pixelization is applied.
        """

    def mapper_from(
        self,
        source_grid_slim: Grid2D,
        source_pixelization_grid: Grid2D = None,
        data_pixelization_grid: Grid2D = None,
        hyper_image: np.ndarray = None,
        settings: SettingsPixelization = SettingsPixelization(),
        preloads: Preloads = Preloads(),
        profiling_dict: Optional[Dict] = None,
    ):
        raise NotImplementedError("pixelization_mapper_from should be overridden")

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ and self.__class__ is other.__class__

    @profile_func
    def relocate_grid_via_border(
        self,
        source_grid_slim: Grid2D,
        settings: SettingsPixelization = SettingsPixelization(),
        preloads: Preloads = Preloads(),
    ) -> Grid2D:
        """
        Relocates all coordinates of an input grid that are outside of a border defined by a grid of (y,x) coordinates
        to the edge of this border.

        The border is determined from the mask of the 2D data before any transformations of the data's grid are
        performed. The border is all pixels in this mask that are pixels at its extreme edge. These pixel indexes
        are used to then determine a grid of (y,x) coordinates in the transformed grid's reference frame, which
        points located outside are relocated to the edge of.

        A full description of relocation is given in the method abstract_grid_2d.relocated_grid_from()`.

        This is used in the project PyAutoLens to relocate the coordinates that are ray-traced near the centre of mass
        of galaxies, which are heavily demagnified and may trace to outskirts of the source-plane well beyond the
        border.

        Parameters
        ----------
        source_grid_slim
            A 2D (y,x) grid of coordinates, whose coordinates outside the border are relocated to its edge.
        """
        if preloads.relocated_grid is None:

            if settings.use_border:
                return source_grid_slim.relocated_grid_from(grid=source_grid_slim)
            return source_grid_slim

        else:

            return preloads.relocated_grid

    def relocate_pixelization_grid_via_border_from(
        self,
        source_grid_slim: Grid2D,
        source_pixelization_grid: Grid2DSparse,
        settings: SettingsPixelization = SettingsPixelization(),
    ):
        raise NotImplementedError

    def make_pixelization_grid_from(
        self,
        source_grid_slim=None,
        source_pixelization_grid=None,
        sparse_index_for_slim_index=None,
    ):
        raise NotImplementedError

    def weight_map_from(self, hyper_image: np.ndarray):

        raise NotImplementedError()

    def __str__(self):
        return "\n".join(["{}: {}".format(k, v) for k, v in self.__dict__.items()])

    def __repr__(self):
        return "{}\n{}".format(self.__class__.__name__, str(self))
