#!/usr/bin/python
"""
Verifies if all XMLs available on S3
"""
import os
import subprocess
from argparse import ArgumentParser

import boto3

from resolve_dvns import get_regions_countries


def get_non_existing_s3_regions(regions, bucket, prefix):
    """
    Returns list of non-existing regions on S3
    """
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket)
    non_existing_regions = list()
    for region in regions[:]:
        if not list(bucket.objects.filter(Prefix=os.path.join(prefix, region))):
            non_existing_regions.append(region)
    return non_existing_regions


def main(options):
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    bucket = options.mitf_bucket
    print("INFO: Using mitf bucket - {}".format(bucket))
    regions, countries = get_regions_countries(options.map_config)
    s3_non_existing_regions = get_non_existing_s3_regions(regions, bucket, prefix="mitf/acc")
    if s3_non_existing_regions:
        print("WARNING: cannot find the following regions on S3:\n%s" % s3_non_existing_regions)
    for region in regions:
        reg_dvn = region[:region.rfind("_")]
        path_to_reg_dvn_libs = os.path.join(options.path_to_libs, reg_dvn)
        if not os.path.exists(path_to_reg_dvn_libs):
            os.makedirs(path_to_reg_dvn_libs)
        if region in s3_non_existing_regions:
            continue
        subprocess.call(
            "aws s3 cp s3://%s/mitf/acc/%s/filtered_test_libs.tgz %s/filtered_test_libs.tgz" % (
                bucket, region, path_to_reg_dvn_libs),
            shell=True)
        subprocess.call("tar -xzf %s/filtered_test_libs.tgz --directory %s" %
                        (path_to_reg_dvn_libs, path_to_reg_dvn_libs), shell=True)
        subprocess.call("rm -rf %s/filtered_test_libs.tgz" % (path_to_reg_dvn_libs),
                        shell=True)


if __name__ == "__main__":
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--map_config", dest="map_config",
                            help="Path to map config", required=True)
    opt_parser.add_argument("--path_to_libs", dest="path_to_libs",
                            help="Path to xmls", required=True)
    opt_parser.add_argument("--mitf_bucket", dest="mitf_bucket",
                            help="MITF bucket name", default="mitf-artifacts")
    options = opt_parser.parse_args()

    main(options)
