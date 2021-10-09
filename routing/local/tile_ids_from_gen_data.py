"""
This script can be used to get HMC tile ids from the data generated using LDMs.
Useful to form list of partitions for adpters
"""
import pickle
import json
from argparse import ArgumentParser
from pathlib import Path
from adapters.olp.utils.coords_to_partition_id import convert_tile_id
from adapters.olp.utils.partition import Partition


def get_tile_ids(json_data):
    tile_ids = list()
    for item in json_data:
        if ("point" in item or "start" in item or "end" in item):
            if not any(substr in item for substr in ["tmc", "exit", "inside", "alter"]):
                tile_id = convert_tile_id(float(json_data[item][1]), float(json_data[item][0]), 12)
                tile_ids.append(tile_id)

    return tile_ids


if __name__ == "__main__":
    parser = ArgumentParser(description="Get HMC tile IDs out of data generated from LDM")
    parser.add_argument("-i", "--input_dir", type=str, dest="data_path",
                        help="Path to the dir with generated data (in JSON format!)",
                        required=True)
    parser.add_argument("-f", "--format", type=str, dest="format", choices=["cpickle", "json"],
                        help="Format of data files generated from LDM", default="cpickle")
    parser.add_argument("-a", "--include_adjuscent", type=bool, dest="adjuscent",
                        help="If specified, adjuscent partitions will be included to the output",
                        default=False)
    options = parser.parse_args()
    tiles = list()
    if options.format == "cpickle":
        data_files = Path(options.data_path).rglob('*.dump')
    else:
        data_files = Path(options.data_path).rglob('*.json')
    for filename in data_files:
        # Matrix routes are not supported by this script currently:
        if "matrix" in str(filename):
            continue
        with open(filename, "rb") as fh:
            if options.format == "cpickle":
                try:
                    pickle_data = pickle.loads(fh.read())
                    json_data = json.loads(json.dumps(pickle_data))
                except Exception as err:
                    print("Error \"%s\" in file \"%s\"" % (err, filename))
                    continue
            else:
                json_data = json.loads(fh.read())
            tiles.append(get_tile_ids(json_data))

    partitions = [item for sublist in tiles for item in sublist]
    if not options.adjuscent:
        print(str(set(partitions)).replace(" ", "")[1:-1])
    else:
        # TODO (asmirnov): Hardcoded. options.adjuscent should be changed from bool to int in [0, 4, 16]
        breadth = 16
        if breadth == 4:
            for partition in partitions:
                for i in Partition(Partition(partition).parent().value).children():
                    if i.value not in partitions:
                        partitions.append(i.value)
        elif breadth == 16:
            for partition in partitions:
                for parent in Partition(Partition(partition).parent().parent().value).children():
                    for i in parent.children():
                        if i.value not in partitions:
                            partitions.append(i.value)
        print(str(set(partitions)).replace(" ", "")[1:-1])
