# convert the latitude/longitude coordinates to the HERE Tile ID
import math
import unittest
from baseconvert import BaseConverter


def check_digits_num(bin_start):
    if len(bin_start) == 13:
        bin_start = bin_start[:1] + '' + bin_start[1 + 1:]
    elif len(bin_start) == 14:
        bin_start = bin_start[:0] + '' + bin_start[1 + 1:]
    return bin_start


def interleaved_num(a_x_cor, a_y_cor):
    return "".join(["%s%s" % (k, v) for k, v in zip(a_y_cor, a_x_cor)])


def to_base_4(long_bin):
    base4v = BaseConverter(input_base=2, output_base=4, string=True)
    return base4v(long_bin)


def convert_tile_id(y_coordinata, x_coordinata, level):
    # for level 12 tiles, the latitude/longitude range
    x_tile = int((180 + x_coordinata) / (360 / (2 ** level)))
    a_x_bin = check_digits_num(bin(x_tile))
    y_tile = math.floor((90 + y_coordinata) / (360 / (2 ** level)))
    a_y_bin = check_digits_num(bin(y_tile))
    num_base_4 = to_base_4(interleaved_num(a_x_bin, a_y_bin))
    num_base_10 = num_base_4.rjust(13, '1')
    partition_id = int(num_base_10, 4)
    return partition_id


class PartitionByCoordsTestCase(unittest.TestCase):
    def test_fra(self):
        level = 12
        expected = 23595506
        lat = 48.97789222693959
        lon = 2.470016718535561
        self.assertEqual(convert_tile_id(lat, lon, level), expected)

    # def test_partition_in_usa(self):
    #     level = 12
    #     expected = 20797560
    #     lat = 48.402208
    #     lon = -4.493086
    #     self.assertEqual(convert_tile_id(lat, lon, level), expected)
    #
    # def test_partition_in_afr(self):
    #     level = 12
    #     expected = 21550951
    #     lat = -31.879325
    #     lon = 22.101703
    #     self.assertEqual(convert_tile_id(lat, lon, level), expected)

    # def test_partition_in_mex(self):
    #     expected = 18464000
    #     lat = -25.279134
    #     lon = -57.617324
    #     self.assertEqual(convert_tile_id(lat, lon), expected)

if __name__ == '__main__':
    unittest.main()