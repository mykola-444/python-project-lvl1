''' convert the latitude/longitude coordinates to the HERE Tile ID '''''
import unittest


def convert_tile_id(y_coordinata, x_coordinata, level):
    '''Convert from the latitude/longitude coordinates to Partition ID.'''
    ''' we can used r:10 for identifier  block in WxTest '''
    tile_y = int((180 + y_coordinata) / (360 / (2 ** level)))
    tile_x = int((90 + x_coordinata) / (360 / (2 ** level)))
    print(tile_y, tile_x)
    partition_id = (0b1 << (2 * level)) + quadkey_morton(tile_x, tile_y)
    #print(quadkey_morton(tile_x, tile_y))
    return partition_id


def quadkey_morton(tile_a, tile_b):
    '''Convert tiles into Morton code quadkey'''
    x = (tile_a << 32) | tile_b
    t = (x ^ (x >> 16)) & 0x00000000FFFF0000
    x = x ^ t ^ (t << 16)
    t = (x ^ (x >> 8)) & 0x0000FF000000FF00
    x = x ^ t ^ (t << 8)
    t = (x ^ (x >> 4)) & 0x00F000F000F000F0
    x = x ^ t ^ (t << 4)
    t = (x ^ (x >> 2)) & 0x0C0C0C0C0C0C0C0C
    x = x ^ t ^ (t << 2)
    t = (x ^ (x >> 1)) & 0x2222222222222222
    x = x ^ t ^ (t << 1)
    return x


class PartitionByCoordsTestCase(unittest.TestCase):
    def test_fra(self):
        level = 12
        expected = 19677287
        lat = 45.4955
        lon = -122.77054
        self.assertEqual(convert_tile_id(lon, lat, level), expected)

    # def test_partition_in_usa(self):
    #     level = 12
    #     expected = 20797560
    #     lat = 48.402208
    #     lon = -4.493086
    #     self.assertEqual(convert_tile_id(lon, lat, level), expected)
    #
    # def test_partition_in_afr(self):
    #     level = 12
    #     expected = 21550951
    #     lat = -31.879325
    #     lon = 22.101703
    #     self.assertEqual(convert_tile_id(lon, lat, level), expected)
    #
    # def test_partition_in_mex(self):
    #     level = 12
    #     expected = 18464000
    #     lat = -25.279134
    #     lon = -57.617324
    #     self.assertEqual(convert_tile_id(lon, lat, level), expected)


if __name__ == '__main__':
    unittest.main()
