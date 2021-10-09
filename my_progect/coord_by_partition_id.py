# convert the latitude/longitude coordinates to the HERE Tile ID
import math
import unittest
from baseconvert import BaseConverter

TILE_LEVEL = 12


def check_digits_num(bin_start):
    '''Check and correct binary lenth .'''
    if len(bin_start) == 13:
        bin_start = bin_start[:1] + '' + bin_start[1 + 1:]
    elif len(bin_start) == 14:
        bin_start = bin_start[:0] + '' + bin_start[1 + 1:]
    return bin_start


def to_base_4(long_bin):
    '''Convert from  binary value to a base 4 integer.'''
    base4v = BaseConverter(input_base=2, output_base=4, string=True)
    return base4v(long_bin)


def to_base_10(test, short_bin):
    '''Convert from  from base 4 to base 10.'''
    base4v = BaseConverter(input_base=4, output_base=10, string=True)
    converted_partition = int(base4v(short_bin))
    print("The coordinates", test, "correspond to the Partition ID", converted_partition)
    return converted_partition


def convert_tile_id(y_coordinata, x_coordinata):
    '''Convert from the latitude/longitude coordinates to Partition ID.'''
    delta_for_tile = 360 / (2 ** TILE_LEVEL)
    x_tile = math.floor(((180 + x_coordinata) / delta_for_tile))
    a_x_bin = check_digits_num(bin(x_tile))
    y_tile = math.floor((90 + y_coordinata) / delta_for_tile)
    a_y_bin = check_digits_num(bin(y_tile))
    num_base_4 = to_base_4("".join(["%s%s" % (k, v) for k, v in zip(a_y_bin, a_x_bin)]))
    num_base_10 = num_base_4.rjust(13, '0')
    partition_id = to_base_10((x_coordinata, y_coordinata), num_base_10)
    return partition_id


class PartitionByCoordsTestCase(unittest.TestCase):
    def test_fra(self):
        expected = 23595506
        lat = 48.97789222693959
        lon = 2.470016718535561
        self.assertEqual(convert_tile_id(lat, lon), expected)

    def test_partition_in_usa(self):
        expected = 20797560
        lat = 48.402208
        lon = -4.493086
        self.assertEqual(convert_tile_id(lat, lon), expected)

    def test_partition_in_afr(self):
        expected = 21550951
        lat = -31.879325
        lon = 22.101703
        self.assertEqual(convert_tile_id(lat, lon), expected)

    def test_partition_in_mex(self):
        expected = 18464000
        lat = -25.279134
        lon = -57.617324
        self.assertEqual(convert_tile_id(lat, lon), expected)


if __name__ == '__main__':
    unittest.main()
