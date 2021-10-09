#!/bin/bash -ex

source map-integration-testing/ci/routing/common_functions.sh

case ${TOPIC} in
    "FORMAT8_FEAT_DAL_MAP_VERSION"* )
        PREFIX="f8_feat_dal_"
        ;;
    "FORMAT8_HLS_ROUTING_MAP_VERSION"* )
        PREFIX="f8_hls_routing_"
        ;;
    *"NDS"*"SPARTA"*"MAP_VERSION"* )
        PREFIX="nds_2.5.2_"
        ;;
    * )
        PREFIX="nds_2.4.2_"
        ;;
esac

function verify_env_vars {
    exit_if_no_env_var PATH_TO_XMLS
    exit_if_no_env_var TOPIC
}

function cleanup_xmls {
    INVESTIGATION_LIST=/tmp/${PREFIX}investigation_list.yaml
    aws s3 cp s3://mitf-artifacts/mitf/success_geo_nodes-investigation-list/${PREFIX}investigation_list.yaml \
              ${INVESTIGATION_LIST}
    python3 map-integration-testing/ci/routing/investigation_list_filter.py --investigation_list ${INVESTIGATION_LIST} \
                                                                            --xmls_path ${PATH_TO_XMLS}
}

###################################################################

verify_env_vars
cleanup_xmls
