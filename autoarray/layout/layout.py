from autoarray.structures.arrays.one_d.array_1d import Array1D
from autoarray.structures.arrays.two_d.array_2d import Array2D
from autoarray.layout.region import Region1D
from autoarray.layout.region import Region2D

from autoarray.layout import layout_util


class Layout1D:
    def __init__(self, shape_1d, prescan=None, overscan=None):
        """
        Abstract base class for a layout, which defines the regions a signal, its input normalization and other
        properties.
        """

        self.shape_1d = shape_1d

        if isinstance(prescan, tuple):
            prescan = Region1D(region=prescan)

        if isinstance(overscan, tuple):
            overscan = Region1D(region=overscan)

        self.prescan = prescan
        self.overscan = overscan

    def extract_overscan_array_1d_from(self, array):
        return Array1D.manual_native(
            array=array.native[self.overscan.slice],
            header=array.header,
            pixel_scales=array.pixel_scales,
        )


class Layout2D:
    def __init__(
        self,
        shape_2d,
        original_roe_corner=(1, 0),
        parallel_overscan=None,
        serial_prescan=None,
        serial_overscan=None,
    ):
        """
        Abstract base class for a charge injection pattern_ci, which defines the regions charge injections appears \
         on a charge-injection frame_ci, the input normalization and other properties.

        Parameters
        -----------
        normalization
            The normalization of the charge injection lines.
        regions: [(int,)]
            A list of the integer coordinates specifying the corners of each charge injection region \
            (top-row, bottom-row, left-column, right-column).
        """

        self.shape_2d = shape_2d
        self.original_roe_corner = original_roe_corner

        if isinstance(parallel_overscan, tuple):
            parallel_overscan = Region2D(region=parallel_overscan)

        if isinstance(serial_prescan, tuple):
            serial_prescan = Region2D(region=serial_prescan)

        if isinstance(serial_overscan, tuple):
            serial_overscan = Region2D(region=serial_overscan)

        self.parallel_overscan = parallel_overscan
        self.serial_prescan = serial_prescan
        self.serial_overscan = serial_overscan

    @classmethod
    def rotated_from_roe_corner(
        cls,
        roe_corner,
        shape_native,
        parallel_overscan=None,
        serial_prescan=None,
        serial_overscan=None,
    ):

        parallel_overscan = layout_util.rotate_region_via_roe_corner_from(
            region=parallel_overscan, shape_native=shape_native, roe_corner=roe_corner
        )
        serial_prescan = layout_util.rotate_region_via_roe_corner_from(
            region=serial_prescan, shape_native=shape_native, roe_corner=roe_corner
        )
        serial_overscan = layout_util.rotate_region_via_roe_corner_from(
            region=serial_overscan, shape_native=shape_native, roe_corner=roe_corner
        )

        return Layout2D(
            original_roe_corner=roe_corner,
            shape_2d=shape_native,
            parallel_overscan=parallel_overscan,
            serial_prescan=serial_prescan,
            serial_overscan=serial_overscan,
        )

    def after_extraction(self, extraction_region):

        parallel_overscan = layout_util.region_after_extraction(
            original_region=self.parallel_overscan, extraction_region=extraction_region
        )
        serial_prescan = layout_util.region_after_extraction(
            original_region=self.serial_prescan, extraction_region=extraction_region
        )
        serial_overscan = layout_util.region_after_extraction(
            original_region=self.serial_overscan, extraction_region=extraction_region
        )

        return Layout2D(
            original_roe_corner=self.original_roe_corner,
            shape_2d=self.shape_2d,
            parallel_overscan=parallel_overscan,
            serial_prescan=serial_prescan,
            serial_overscan=serial_overscan,
        )

    def new_rotated_from(self, roe_corner):

        parallel_overscan = layout_util.rotate_region_via_roe_corner_from(
            region=self.parallel_overscan,
            shape_native=self.shape_2d,
            roe_corner=roe_corner,
        )
        serial_prescan = layout_util.rotate_region_via_roe_corner_from(
            region=self.serial_prescan,
            shape_native=self.shape_2d,
            roe_corner=roe_corner,
        )
        serial_overscan = layout_util.rotate_region_via_roe_corner_from(
            region=self.serial_overscan,
            shape_native=self.shape_2d,
            roe_corner=roe_corner,
        )

        return Layout2D(
            original_roe_corner=roe_corner,
            shape_2d=self.shape_2d,
            parallel_overscan=parallel_overscan,
            serial_prescan=serial_prescan,
            serial_overscan=serial_overscan,
        )

    def original_orientation_from(self, array):
        return layout_util.rotate_array_via_roe_corner_from(
            array=array, roe_corner=self.original_roe_corner
        )

    def extract_parallel_overscan_array_2d_from(self, array):
        """
        Extract an arrays of all of the parallel trails in the parallel overscan region, that are to the side of a
        charge-injection scans from a charge injection frame_ci.

        The diagram below illustrates the arrays that is extracted from a frame_ci:

        ---KEY---
        ---------

        [] = read-out electronics   [==========] = read-out register

        [xxxxxxxxxx]                [..........] = parallel prescan       [ssssssssss] = parallel overscan
        [xxxxxxxxxx] = CCD panel    [pppppppppp] = parallel overscan    [cccccccccc] = charge injection region
        [xxxxxxxxxx]                [tttttttttt] = parallel / parallel charge injection region trail

        P = Parallel Direction      S = Serial Direction

               [ppppppppppppppppppppp]
               [ppppppppppppppppppppp]
          [...][xxxxxxxxxxxxxxxxxxxxx][sss]
          [...][ccccccccccccccccccccc][tst]
        | [...][ccccccccccccccccccccc][sts]    |
        | [...][xxxxxxxxxxxxxxxxxxxxx][sss]    | Direction
        P [...][xxxxxxxxxxxxxxxxxxxxx][sss]    | of
        | [...][ccccccccccccccccccccc][tst]    | clocking
          [...][ccccccccccccccccccccc][sts]    |

        []     [=====================]
               <---------S----------

        The extracted frame_ci keeps just the trails following all charge injection scans and replaces all other
        values with 0s:

               [000000000000000000000]
               [000000000000000000000]
          [000][000000000000000000000][000]
          [000][000000000000000000000][tst]
        | [000][000000000000000000000][sts]    |
        | [000][000000000000000000000][000]    | Direction
        P [000][000000000000000000000][000]    | of
        | [000][000000000000000000000][tst]    | clocking
          [000][000000000000000000000][sts]    |

        []     [=====================]
               <---------S----------
        """

        return Array2D.manual(
            array=array.native[self.parallel_overscan.slice],
            header=array.header,
            pixel_scales=array.pixel_scales,
        )

    def extract_serial_overscan_array_from(self, array):
        """
        Extract an arrays of all of the serial trails in the serial overscan region, that are to the side of a
        charge-injection scans from a charge injection frame_ci.

        The diagram below illustrates the arrays that is extracted from a frame_ci:

        ---KEY---
        ---------

        [] = read-out electronics   [==========] = read-out register

        [xxxxxxxxxx]                [..........] = serial prescan       [ssssssssss] = serial overscan
        [xxxxxxxxxx] = CCD panel    [pppppppppp] = parallel overscan    [cccccccccc] = charge injection region
        [xxxxxxxxxx]                [tttttttttt] = parallel / serial charge injection region trail

        P = Parallel Direction      S = Serial Direction

               [ppppppppppppppppppppp]
               [ppppppppppppppppppppp]
          [...][xxxxxxxxxxxxxxxxxxxxx][sss]
          [...][ccccccccccccccccccccc][tst]
        | [...][ccccccccccccccccccccc][sts]    |
        | [...][xxxxxxxxxxxxxxxxxxxxx][sss]    | Direction
        P [...][xxxxxxxxxxxxxxxxxxxxx][sss]    | of
        | [...][ccccccccccccccccccccc][tst]    | clocking
          [...][ccccccccccccccccccccc][sts]    |

        []     [=====================]
               <---------S----------

        The extracted frame_ci keeps just the trails following all charge injection scans and replaces all other
        values with 0s:

               [000000000000000000000]
               [000000000000000000000]
          [000][000000000000000000000][000]
          [000][000000000000000000000][tst]
        | [000][000000000000000000000][sts]    |
        | [000][000000000000000000000][000]    | Direction
        P [000][000000000000000000000][000]    | of
        | [000][000000000000000000000][tst]    | clocking
          [000][000000000000000000000][sts]    |

        []     [=====================]
               <---------S----------
        """

        return Array2D.manual(
            array=array.native[self.serial_overscan.slice],
            header=array.header,
            pixel_scales=array.pixel_scales,
        )

    def parallel_overscan_binned_array_1d_from(self, array):
        parallel_overscan_array = self.extract_parallel_overscan_array_2d_from(
            array=array
        )
        return parallel_overscan_array.binned_across_columns

    def serial_overscan_binned_array_1d_from(self, array):
        serial_overscan_array = self.extract_serial_overscan_array_from(array=array)
        return serial_overscan_array.binned_across_rows

    @property
    def serial_trails_columns(self):
        return self.serial_overscan[3] - self.serial_overscan[2]
