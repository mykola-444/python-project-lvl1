#!/bin/bash -ex


. map-integration-testing/ci/routing/common_functions.sh

function verify_env_vars {
    exit_if_no_env_var MAP_PATH_PREFIX
    exit_if_no_env_var LDM_REGION_DVN
    exit_if_no_env_var MITF_PATH
    exit_if_no_env_var MAP_FORMAT
    exit_if_no_env_var GENERATE_SUCCESS_GEO_NODES
    exit_if_no_env_var SUCCESS_GEO_NODES_RUNNER
    exit_if_no_env_var DESIRED_TC_QTY
    set_env_var_if_not_set GENERATORS ""
    set_env_var_if_not_set AWS_DEFAULT_REGION us-east-1
    set_env_var_if_not_set MODE dev
}

if [[ ${MAP_FORMAT} == "BRF2" ]]; then
    TEST_RUNNER=$MITF_PATH/share/here/tests/test-routing-integration
else
    TEST_RUNNER=$MITF_PATH/installdir/bin/test-routing-integration
fi

# input: MAP_FORMAT, MAP_VERSION, MAP_PATH, CONFIG_PATH
# results: configuration file CONFIG_PATH
function generate_config {
    python3 map-integration-testing/ci/routing/create_config.py \
        --params \
        "MAP_FORMAT=$1" \
        "MAP_VERSION=$2" \
        "MAP_PATH=$3" \
        "GENERATORS=${GENERATORS}" \
        "TEST_CASE_NUMBER=${DESIRED_TC_QTY}" \
        "TEST_RUNNER=${TEST_RUNNER}" \
    --config_template map-integration-testing/config/routing_config_example.cfg \
    --output test_runner.cfg
}

####################################################################
# main code
verify_env_vars
REGION=$(get_region $LDM_REGION_DVN)
MARKET=$(get_market $REGION)

set -a
case $MAP_FORMAT in
    "F8" )
        source map-config/map_format8.config
        generate_config "F8" $map_version $MAP_PATH_PREFIX/$file_routing_server_world_cdt
        ;;
    "NDS_OLYMPIA" )
        source map-config/map_nds.config
        generate_config "NDS" $(eval echo \$client_map_version_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_${MARKET}_nds)
        ;;
    "NDS_STANDARD" )
        source map-config/map_nds_standard.config
        generate_config "NDS" $(eval echo \$client_map_version_standard_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_standard_${MARKET}_nds)
        ;;
    "NDS_MOTEGI" )
        source map-config/map_nds_vanilla.config
        generate_config "NDS" $(eval echo \$client_map_version_vanilla_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_vanilla_${MARKET}_nds)
        ;;
    "NDS_DONINGTON" )
        source map-config/map_nds_donington.config
        generate_config "NDS" $(eval echo \$client_map_version_donington_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_donington_${MARKET}_nds)
        ;;
    "NDS_BONNEVILLE" )
        source map-config/map_nds_bonneville.config
        generate_config "NDS" $(eval echo \$client_map_version_bonneville_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_bonneville_${MARKET}_nds)
        ;;
    "NDS_SUPERSET" )
        source map-config/map_nds_superset.config
        generate_config "NDS" $(eval echo \$client_map_version_superset_${MARKET}) $MAP_PATH_PREFIX/$(eval echo \$file_client_superset_${MARKET}_nds)
        ;;
    "NDS_SPARTA" )
        source map-config/map/sparta/mapdb/${MARKET}.config
        generate_config "NDS" $(eval echo \$client_map_version) $MAP_PATH_PREFIX/$(eval echo \$file_client_nds)
        ;;
    "BRF" )
        source map-config/map_format8.config
        source map-config/map_format8_brf.config
        generate_config "BRF" $map_version $MAP_PATH_PREFIX/$folder_routing_server_brf
        ;;
    "BRF2" )
        source map-config/map/ols/routing/hmc_plus_japan.config
        generate_config "BRF" $map_version $MAP_PATH_PREFIX/$folder_routing_server_brf
        ;;
esac

cd map-integration-testing
if [ $GENERATE_SUCCESS_GEO_NODES == 'true' ]; then
    PYTHONPATH=$MITF_PATH/map-integration-testing \
        python3 test_runner/run.py \
            --loglevel DEBUG \
            --result_output_folder $MITF_PATH/tests_output/ \
            --test_data_path $MITF_PATH/mitf_dumps \
            --config $MITF_PATH/test_runner.cfg \
            --allure \
            --success_geo_nodes $MITF_PATH/${REGION}_SUCCESS_GEO_NODES.json
        # allure_rep is generated
        tar czf $MITF_PATH/allure_rep.tgz allure_rep

    if [ $MODE == "dev" ] && [ ${SUCCESS_GEO_NODES_RUNNER} == "sgn_generate" ]; then
        echo "Publishing generated ${REGION}_SUCCESS_GEO_NODES.json to s3 bucket"
        aws s3 cp $MITF_PATH/${REGION}_SUCCESS_GEO_NODES.json s3://mitf-artifacts/mitf/success_geo_nodes-dev/
        aws s3api put-object-acl \
            --bucket mitf-artifacts \
            --key mitf/success_geo_nodes-dev/${REGION}_SUCCESS_GEO_NODES.json \
            --grant-full-control 'emailaddress="I_EXT_AWS_CCI_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_MAPDATA_RD@here.com",emailaddress="I_EXT_AWS_CONTDELIV_P@here.com"'
    fi
else
    PYTHONPATH=$MITF_PATH/map-integration-testing \
        python3 test_runner/run.py \
            --loglevel DEBUG \
            --result_output_folder $MITF_PATH/tests_output/ \
            --test_data_path $MITF_PATH/mitf_dumps \
            --config $MITF_PATH/test_runner.cfg
fi

PYTHONPATH=$MITF_PATH/map-integration-testing \
python3 $MITF_PATH/map-integration-testing/ci/routing/generate_xml_coverage.py  --config $MITF_PATH/test_runner.cfg --path_to_xmls $MITF_PATH/tests_output/ --template $MITF_PATH/map-integration-testing/utils/web/templates/xml_coverage.j2 --output index.html

cd $MITF_PATH/tests_output/
# xml tests artifact
echo "Generating artifact: tests_xml.tgz"
tar -czf $MITF_PATH/tests_xml.tgz *

if [ $MODE == "rc" ]; then
    echo "Publishing generated ${REGION}_SUCCESS_GEO_NODES.json to s3 bucket"
    aws s3 cp $MITF_PATH/${REGION}_SUCCESS_GEO_NODES.json s3://mitf-artifacts/mitf/success_geo_nodes-rc/
    aws s3api put-object-acl \
        --bucket mitf-artifacts \
        --key mitf/success_geo_nodes-rc/${REGION}_SUCCESS_GEO_NODES.json \
        --grant-full-control 'emailaddress="I_EXT_AWS_CCI_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_MAPDATA_RD@here.com",emailaddress="I_EXT_AWS_CONTDELIV_P@here.com"'

    echo "Publishing generated xmls to s3 bucket"
    aws s3 cp $MITF_PATH/tests_xml.tgz s3://mitf-artifacts/mitf/xml-rc/${LDM_REGION_DVN}/tests.tgz
    aws s3api put-object-acl \
        --bucket mitf-artifacts \
        --key mitf/xml-rc/${LDM_REGION_DVN}/tests.tgz \
        --grant-full-control 'emailaddress="I_EXT_AWS_CCI_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_MAPDATA_RD@here.com",emailaddress="I_EXT_AWS_CONTDELIV_P@here.com"'
fi
