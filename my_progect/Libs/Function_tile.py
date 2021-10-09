#convert the latitude/longitude coordinates to the HERE Tile ID
# str(i).ljust(14, '0')
from baseconvert import BaseConverter
import math

def check_digits_num(bin_start):
   if len(bin_start) == 13:
       #print(bin_start)
       bin_start=bin_start[:1]+''+bin_start[1+1:]
       #bin_start=str(bin_start).ljust(14, '0')
       print("1", bin_start)
   if len(bin_start) == 14:
       #print(bin_start)
       bin_start = bin_start[:0] + '' + bin_start[1 + 1:]
       print("2", bin_start)
   return bin_start

def interleaved_num(a_x_cor, a_y_cor):
     return "".join(["%s%s"%(k,v) for k, v in zip(a_y_cor, a_x_cor)])


def to_base_4(long_bin):
    #print(long_bin)
    base4v = BaseConverter(input_base=2, output_base=4, string=True)
    #print(base4v(long_bin))
    return base4v(long_bin)

# def to_base_10(Short_bin):
#     print(Short_bin)
#     base4v = BaseConverter(input_base=4, output_base=10, string=True)
#     print("The coordinates", test, "correspond to the partisans", base4v(Short_bin))
#     print(base4v(Short_bin))



def convert_tile_id(test_coordinate):
    #for level 12 tiles, the latitude/longitude range
    tile=12
    delta_for_tile=360/(2**tile)
    print(delta_for_tile)
    #Parse coordinatas
    x_coordinata=float(test_coordinate.split(', ')[1])
    y_coordinata=float(test_coordinate.split(',')[0])
    #find Tile
    x_tile = int((180 + x_coordinata) / delta_for_tile)
    print((180 + x_coordinata) / delta_for_tile)
    print(x_tile,bin(x_tile))
    a_x_cor= check_digits_num(bin(x_tile))

    y_tile = int((90+y_coordinata)/delta_for_tile)
    print((90 + y_coordinata) / delta_for_tile)
    print(y_tile, bin(y_tile))
    a_y_cor = check_digits_num(bin(y_tile))

    #print(a_x_cor, a_y_cor)
    print("kkkk", interleaved_num(a_x_cor, a_y_cor))
    s = to_base_4(interleaved_num(a_x_cor, a_y_cor))
    print(s)

    num_base_10 = s.rjust(13, '1')
    partition_id = int(num_base_10, 4)
    print(partition_id)




test="40.417433, -3.707727"
convert_tile_id(test)

