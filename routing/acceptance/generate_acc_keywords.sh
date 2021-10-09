#!/bin/bash -ex

. /workspace/map-integration-testing/ci/routing/common_functions.sh

function verify_env_vars {
    exit_if_no_env_var MITF_PATH
    set_env_var_if_not_set MODE dev
}

####################################################################
# main code
verify_env_vars

# All parameters are not important for this step - so just copying the example:
cp /workspace/map-integration-testing/config/acceptance_config_example.cfg /tmp/test_runner.cfg

# Generate acceptance keyword libs from cPickle dumps:
cd ./map-integration-testing/
PYTHONPATH=/workspace/map-integration-testing \
  python3 ./test_runner/run.py \
    --loglevel DEBUG \
    --result_output_folder ../mitf_acc_lib/ \
    --test_data_path ../mitf_dumps/ \
    --config /tmp/test_runner.cfg  \

# DEBUG: List all robot lib:
find ../mitf_acc_lib -type f

cd ../mitf_acc_lib
# libs artifact
echo "Generating artifact: test_libs.tgz"
tar -czf ../test_libs.tgz *

