#!/bin/bash -ex

source ../../routing/common_functions.sh
exit_if_no_env_var SPEC_LOCATION_PREFIX

cd ${SPEC_LOCATION_PREFIX}
find . -type f -name '*tmp_*.robot' -delete -print
find . -type f -name '*dev_*.robot' -delete -print
rm -rf spec/lib/
