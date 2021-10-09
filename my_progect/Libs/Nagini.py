################### CODE DUPE FROM NAGINI - BEGIN #################
from baseconvert import base


def tile_id_from_coordinate(lon, lat, zoom_level):
    if zoom_level < 0:
        raise ValueError("Tile zoom level cannot be negative.")

    tile_x, tile_y = _calculate_tile_indices(lon, lat, zoom_level)
    print(tile_x, tile_y)
    return _encode_as_tile_id(tile_x, tile_y, zoom_level)


def _tile_width_at_level(zoom_level):
    return float(360 / (2 ** zoom_level))


def _calculate_tile_indices(lon, lat, zoom_level):
    tile_x = int((lon + 180) / _tile_width_at_level(zoom_level))
    tile_y = int((lat + 90) / _tile_width_at_level(zoom_level))
    print(tile_x, tile_y)
    return tile_x, tile_y


def _encode_as_tile_id(tile_x, tile_y, zoom_level):
    assert tile_x.bit_length() <= zoom_level
    assert tile_y.bit_length() <= zoom_level

    interleaved_bits = _perfect_shuffle(tile_y, tile_x)
    print(interleaved_bits)
    interleaved_bits = (0b1 << (2 * zoom_level)) + interleaved_bits
    print(interleaved_bits)
    quadkey = base(interleaved_bits, 10, 4, string=True)
    print(quadkey)

    return str(int(quadkey, 4))


def _deinterleave(interleaved):
    return interleaved[0::2], interleaved[1::2]


def _perfect_shuffle(a, b):
    x = (a << 32) | b

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
################### CODE DUPE FROM NAGINI - END ###################

print(tile_id_from_coordinate(-4.493086, 48.402208, 12))
