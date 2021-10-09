import nagini
import os
from argparse import ArgumentParser
from collections import defaultdict


def get_partitions_country_map(catalog, countries=None):
    layer = catalog.layer_by_id("indexed-locations")
    schema = layer.read_schema()
    print("Get country data from 'indexed-locations' layer")
    blob_data = layer.read_partitions(partition_ids=countries)
    partitions_country_map = defaultdict()
    for chunk in blob_data:
        decoded_data = schema.decode_blob(chunk)
        for tile_id in decoded_data.tile_id:
            partitions_country_map[tile_id] = decoded_data.partition_name
        print(decoded_data.partition_name)
    return partitions_country_map


def main():
    parser = ArgumentParser(description="Get HMC tile IDs")
    parser.add_argument("--countries", dest="countries", help="Comma separated countries")
    parser.add_argument("--output", dest="output", help="File with partitions", required=True)
    parser.add_argument("--hrn", dest="hrn", help="hrn to get data from. Use \
                            hrn:here:data:::here-map-content-japan-2 for Japan",
                        required=True, default="hrn:here:data:::rib-2")
    options = parser.parse_args()
    olp = nagini.resource('olp')
    catalog = olp.catalog_by_hrn(options.hrn)
    road_attr_layer = catalog.layer_by_id("road-attributes")
    if options.countries:
        partitions_country_map = get_partitions_country_map(catalog, options.countries.split(","))
        partitions = list(set(partitions_country_map.keys()))
    else:
        partitions = [k for k in road_attr_layer.list_partition_ids()]
    dirname = os.path.dirname(options.output)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(options.output, "w") as f_:
        f_.write(",".join(partitions))
    print("INFO: Total partition number: {}".format(len(partitions)))
    print("INFO: Done!")


if __name__ == "__main__":
    main()
