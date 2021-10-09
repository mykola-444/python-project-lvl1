#!/usr/bin/env bash
set -xe

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var MITF_PATH
exit_if_no_env_var MAP_FORMAT

if [[ ${MAP_FORMAT} == "BRF" ]]; then
    SPEC_LOCATION_PREFIX=/workspace/test_routing_component/share/here/routing
    PYTHONPATH=${MITF_PATH} \
    python3 ${MITF_PATH}/ci/routing/acceptance/acceptance_filter_geo_nodes.py -r /workspace/xunit.xml \
                                                                              -p /workspace/pass.json

    LIB_LOCATION=/workspace/test_libs
    PYTHONPATH=${MITF_PATH} \
    python3 ${MITF_PATH}/ci/routing/acceptance/filter_kwd_libs.py --lib ${LIB_LOCATION} \
                                                                  --sources ${SPEC_LOCATION_PREFIX}/spec_orig/international/ \
                                                                  -g /workspace/pass.json \
                                                                  -o /workspace/output
else
    echo "Unsupported map format"
    exit 1
fi