#!/usr/bin/python
"""
Get dvns list for a given map
"""
from argparse import ArgumentParser
from resolve_dvns import get_regions_countries


if __name__ == "__main__":
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--map_config", dest="map_config",
                            help="Map config path", required=True)
    opt_parser.add_argument("--dvn_list", dest="dvn_list", default="",
                            help="Store comma separated dvn list in this file.")
    opt_parser.add_argument("--generate_options", dest="generate_options", default=True,
                            help="Generate options file for each DVN")
    opt_parser.add_argument("--regions", dest="regions", default="",
                            help="Comma separated list of regions.")
    options = opt_parser.parse_args()
    dvns, _ = get_regions_countries(options.map_config)
    if options.regions:
        regions = [region.strip() for region in options.regions.split(',')]
        dvns = {dvn for dvn in dvns for region in regions if dvn[:dvn.rfind("_")] == region}
    dvn_list = ','.join(dvns)
    print("DVNs list: %s" % dvn_list)
    # optionally save dvn list to a file
    if options.dvn_list:
        with open(options.dvn_list, 'w') as _file:
            _file.write(dvn_list)
    # generate options files
    if options.generate_options is True:
        for dvn in dvns:
            filename = "%s.options" % (dvn)
            with open(filename, 'w') as f:
                f.write("LDM_REGION_DVN=" + dvn)
                print("Generated: %s" % filename)
