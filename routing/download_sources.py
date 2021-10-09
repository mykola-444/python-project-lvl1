#!/usr/bin/python

import os
import shutil
from argparse import ArgumentParser

from awscli.clidriver import create_clidriver

from ci_helpers import get_region_from_dvn


def prepare_cache(db_path, dvn, use_cache=False):
    dvn_path = os.path.join(db_path, dvn)
    region = get_region_from_dvn(dvn)
    # Automatically remove cached data for dvns of the same region
    for dir_name in os.listdir(db_path):
        dir_path = os.path.join(db_path, dir_name)
        if os.path.isdir(dir_path) and dir_name.startswith(region) and dir_name != dvn:
            print("Removing cached data for the older LDM={} of Region={}".format(dvn, region))
            shutil.rmtree(dir_path)
    # Remove cached data if set
    if os.path.exists(dvn_path) and use_cache == "False":
        print("Removing cached data for LDM={}".format(dvn))
        shutil.rmtree(dvn_path)
    if not os.path.exists(dvn_path):
        os.makedirs(dvn_path)


def aws_cli(cmd):
    old_env = dict(os.environ)
    try:
        # Environment
        os.environ['LC_CTYPE'] = 'en_US.UTF-8'
        # Run awscli in the same process
        exit_code = create_clidriver().main(cmd)
        # Deal with problems
        if exit_code > 0:
            raise RuntimeError('AWS CLI exited with code {} for command: {}'.format(exit_code,
                                                                                    " ".join(cmd)))
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def download_dbs(db_path, dvn):
    dvn_path = os.path.join(db_path, dvn)
    s3_path_to_db = "s3://maps-sources-us-east-1/ldm/sqlite/%s" % dvn
    region = get_region_from_dvn(dvn)
    if "TWN" in region or "ANT" in region:
        db_suffix = "_.db3"
    else:
        db_suffix = "_common.db3"
    common_db_path = os.path.join(dvn_path, "%s%s" % (region, db_suffix))
    # indexes are created and database is modified
    # to avoid file downloading simple check is added
    if not os.path.exists(common_db_path):
        aws_cli(['s3', 'sync', s3_path_to_db, dvn_path, '--exclude', '*',
                 '--include', '*%s' % db_suffix, '--delete', '--force-glacier-transfer'])
    aws_cli(['s3', 'sync', s3_path_to_db, dvn_path, '--exclude', '*',
             '--include', '*.db3', '--exclude', '*%s' % db_suffix, '--force-glacier-transfer'])


if __name__ == "__main__":
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--db_path", dest="db_path",
                            help="Path to source data db", required=True)
    opt_parser.add_argument("--dvn", dest="dvn",
                            help="ldm region dvn", required=True)
    opt_parser.add_argument("--use_cache", dest="use_cache",
                            help="Use cached source data", default=False)
    options = opt_parser.parse_args()
    prepare_cache(options.db_path, options.dvn, options.use_cache)
    download_dbs(options.db_path, options.dvn)
