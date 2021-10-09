""" Merge changes from mitf-artifacts/mitf/success_geo_nodes-dev to mitf-artifacts/mitf/success_geo_nodes"""

import json
from argparse import ArgumentParser
import os
import subprocess
import tempfile
import shutil
from deepdiff import DeepDiff
from pprint import pprint

SUCCESS_GEO_NODES_PATH = "mitf/success_geo_nodes"


def update_base(basefile, newfile, dry_run):
    with open(basefile) as f:
        base = json.load(f)
    with open(newfile) as f:
        new = json.load(f)
    base_old = base.copy()
    base.update(new)
    pprint(DeepDiff(base_old, base), indent=2)
    if not dry_run:
        print("Update file %s" % (basefile))
        with open(basefile, 'w') as f:
            json.dump(base, f)


def upload_to_s3(path_to_success_geo_nodes, file):
    try:
        subprocess.call("aws s3 cp %s/%s s3://mitf-artifacts/%s/%s" % (
            path_to_success_geo_nodes, file, SUCCESS_GEO_NODES_PATH, file), shell=True)
        key = os.path.join(SUCCESS_GEO_NODES_PATH, file)
        subprocess.call("aws s3api put-object-acl --bucket mitf-artifacts"
                        " --key %s --grant-full-control"
                        " 'emailaddress=\"I_EXT_AWS_CCI_RD@here.com\","
                        "emailaddress=\"I_EXT_AWS_ROUTING_RD@here.com\","
                        "emailaddress=\"I_EXT_AWS_CONTDELIV_P@here.com\","
                        "emailaddress=\"I_EXT_AWS_ROUTING_MAPDATA_RD@here.com\"'" % (key), shell=True)
    except Exception as e:
        print("Failed to upload file to s3: %s" % (e))


def main(dry_run):
    local_success_geo_nodes = tempfile.mktemp()
    local_success_geo_nodes_dev = tempfile.mktemp()
    aws_success_geo_nodes = "s3://mitf-artifacts/" + SUCCESS_GEO_NODES_PATH
    aws_success_geo_nodes_dev = "s3://mitf-artifacts/mitf/success_geo_nodes-dev"
    try:
        subprocess.call("aws s3 sync %s %s" % (aws_success_geo_nodes, local_success_geo_nodes), shell=True)
        subprocess.call("aws s3 sync %s %s" % (aws_success_geo_nodes_dev, local_success_geo_nodes_dev), shell=True)
    except Exception as e:
        print("Failed to download files from s3: %s" % (e))
    for _file in os.listdir(local_success_geo_nodes_dev):
        print("Processing %s" % (_file))
        if _file in os.listdir(local_success_geo_nodes):
            print("Merging changes")
            update_base(os.path.join(local_success_geo_nodes, _file), os.path.join(local_success_geo_nodes_dev, _file), dry_run)
            if not dry_run:
                print("Sync changes to s3 bucket")
                upload_to_s3(local_success_geo_nodes, _file)
        else:
            print("Creating new file")
            if not dry_run:
                print("Sync changes to s3 bucket")
                upload_to_s3(local_success_geo_nodes_dev, _file)
    shutil.rmtree(local_success_geo_nodes)
    shutil.rmtree(local_success_geo_nodes_dev)


if __name__ == "__main__":
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    options = opt_parser.parse_args()
    if options.dry_run:
        print("Running in dry_run mode: no changes will be applied to s3 buckets")
    else:
        print("Running in production mode: changes from -dev bucket will be merged into production bucket")
    main(options.dry_run)
