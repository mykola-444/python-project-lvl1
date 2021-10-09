#!/usr/bin/python

import filecmp
import os
import shutil
import sys
import tarfile
import tempfile
from argparse import ArgumentParser

import boto3
from botocore.exceptions import ClientError


def does_key_exist(bucket, path):
    client = boto3.client('s3')
    results = client.list_objects(Bucket=bucket, Prefix=path)
    return 'Contents' in results


def does_test_for_dvn_exist(dvn):
    path = 'mitf/xml/%s/tests.tgz' % dvn
    return does_key_exist('mitf-artifacts', path)


def does_source_data_for_dvn_exist(dvn):
    path = "ldm/sqlite/%s/" % dvn
    return does_key_exist('maps-sources-us-east-1', path)


def does_mitf_version_match(dvn):
    s3 = boto3.resource('s3')
    key = "mitf/xml/{}/tests.tgz".format(dvn)
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'tests.tgz')
    with open(tmpfile, 'wb'):
        try:
            s3.meta.client.download_file('mitf-artifacts', key, tmpfile)
        except ClientError as e:
            print("WARN: {} for {} [s3://mitf-artifacts/{}]".format(e, dvn, key))
            return False
    with tarfile.open(tmpfile, 'r:*') as f:
        f.extractall(path=tmpdir)
    test_mitf_version_path = os.path.join(tmpdir, 'MITF_VERSION')
    current_mitf_version_path = os.path.join('map-integration-testing', 'VERSION')
    result = os.path.exists(test_mitf_version_path) and filecmp.cmp(current_mitf_version_path,
                                                                    test_mitf_version_path)
    shutil.rmtree(tmpdir)
    return result


def does_test_for_map_exist(func, dvn_list):
    missed_dvn_list = []
    for dvn in dvn_list:
        if not func(dvn):
            missed_dvn_list.append(dvn)
    return (len(missed_dvn_list) == 0, missed_dvn_list)


def generate_option_files(dvn_list):
    ''' Generate options files for DNVS for which generation should be re-triggered
    '''
    for dvn in dvn_list:
        filename = "%s.options" % (dvn)
        with open(filename, 'w') as f:
            f.write("LDM_REGION_DVN=" + dvn)
            print("INFO: Generated: %s" % filename)


if __name__ == "__main__":
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--dnv_list", dest="dvn_list",
                            help="Comma separated list of dvns", required=True)
    options = opt_parser.parse_args()
    exit_code = 0
    dvn_list = options.dvn_list.split(',')
    print('INFO: Processing dvn list:', dvn_list)
    print('INFO: Checking if tests exist for the given dvns')
    tests_generated, missed_dvn_list = does_test_for_map_exist(does_test_for_dvn_exist, dvn_list)
    if tests_generated:
        print('INFO: Tests are present for all dvns')
    else:
        print('ERROR: Tests are absent for the following dvns:',
              missed_dvn_list)
        print('INFO: Checking if source data exist for the given dvns')
        data_exist, missed_source_data_dvn_list = does_test_for_map_exist(
            does_source_data_for_dvn_exist, missed_dvn_list)
        if not data_exist:
            print('ERROR: Source data is absent for the following dvns:',
                  missed_source_data_dvn_list)
            exit_code = 1
            # find list of dvns, for which tests are absent but source data exists
            generate_test_dvn_list = list(set(missed_dvn_list) - set(missed_source_data_dvn_list))
            generate_option_files(generate_test_dvn_list)
    print('INFO: Checking if mitf version match the current one for the given dvns')
    mitf_version_match, mismatch_dvn_list = does_test_for_map_exist(does_mitf_version_match,
                                                                    dvn_list)
    if mitf_version_match:
        print('INFO: MITF version match for all dvns')
    else:
        print('WARN: MITF version does not match for the following dvns:', mismatch_dvn_list)
        generate_option_files(mismatch_dvn_list)
    sys.exit(exit_code)
