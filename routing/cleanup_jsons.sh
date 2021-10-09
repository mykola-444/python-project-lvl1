#!/bin/bash -ex

#source map-integration-testing/ci/routing/common_functions.sh

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
    exit_if_no_env_var PATH_TO_JSONS
    exit_if_no_env_var TOPIC
    exit_if_no_env_var TEAM
}

function cleanup_jsons {
    INVESTIGATION_LIST=/tmp/${PREFIX}${TEAM}_investigation_list.yaml
    aws s3 cp s3://mitf-artifacts/mitf/success_geo_nodes-investigation-list/${PREFIX}${TEAM}_investigation_list.yaml \
              ${INVESTIGATION_LIST}

    case ${TEAM} in
        "psd" )
            python3 investigation_list_json_filter.py --investigation_list ${INVESTIGATION_LIST} \
                                                                            --jsons_path ${PATH_TO_JSONS}
            ;;
        * )
            python3 investigation_list_json_suite_filter.py --investigation_list ${INVESTIGATION_LIST} \
                                                                            --jsons_path ${PATH_TO_JSONS}
            ;;
    esac

}

###################################################################

verify_env_vars
cleanup_jsons
