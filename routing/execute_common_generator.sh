#!/bin/bash -ex

. map-integration-testing/ci/routing/common_functions.sh

TEST_CASE_NUMBER=$1
USE_CACHE=$2

function verify_env_vars {
    exit_if_no_env_var LDM_REGION_DVN
    exit_if_no_env_var MITF_PATH
    exit_if_no_env_var DB_PATH
    set_env_var_if_not_set AWS_DEFAULT_REGION us-east-1
    set_env_var_if_not_set USE_CACHE False
    set_env_var_if_not_set DVN_DB_PATH $DB_PATH/$LDM_REGION_DVN
    if [[ $USE_CACHE == 'true' ]]; then
        USE_CACHE=True
    else
        USE_CACHE=False
    fi

}

####################################################################
# main code

verify_env_vars

REGION=$(get_region $LDM_REGION_DVN)
MARKET=$(get_market $REGION)
PRIORITY_COUNTRIES="${MITF_PATH}/map-integration-testing/ci/routing/priority_countries.json"
declare -A maps=([eu]=EU [na]=NA [rw]=ROW)

export DB_PATH=${DB_PATH}
export PYTHONPATH+=${MITF_PATH}/map-integration-testing/ci/routing

${MITF_PATH}/map-integration-testing/ci/routing/download_sources.py --db_path $DB_PATH --dvn $LDM_REGION_DVN --use_cache $USE_CACHE
# Generate Indexes
if [ ! -f ${DVN_DB_PATH}/${REGION}_common.db3 ]; then
    ln -s ${DVN_DB_PATH}/${REGION}.db3 ${DVN_DB_PATH}/${REGION}_common.db3
fi
sqlite3 ${DVN_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_LINK_FN ON LDM_LINK(FROM_NODE_ID)"
sqlite3 ${DVN_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_X_Y_PID ON LDM_JUNCTION(X, Y, PARTITION_ID)"

# Generate config
CONFIG=/tmp/${LDM_REGION_DVN}_config.cfg
python map-integration-testing/ci/routing/create_config.py \
    --params ${CONFIG_PARAMS} \
            "DB_NAME=${REGION}" \
            "LDM_DATABASE_PATH=${DVN_DB_PATH}" \
            "TEST_CASE_NUMBER=${TEST_CASE_NUMBER}" \
            "MARKET=${maps[$MARKET]}" \
    --config_template ${MITF_PATH}/map-integration-testing/config/research_config_example.cfg \
    --output $CONFIG

cd map-integration-testing
cat $CONFIG

OUTPUT="/tmp/mitf_rnd_tests"
PYTHONPATH=${MITF_PATH}/map-integration-testing \
    python test_data_generator_runner/run.py \
        --loglevel DEBUG  \
        --config $CONFIG \
        --output_folder $OUTPUT \
        --ref_client_link
PYTHONPATH=${MITF_PATH}/map-integration-testing \
python ${MITF_PATH}/map-integration-testing/ci/routing/generate_ref_client_links.py --config $CONFIG --test_data_path ${OUTPUT} --template ${MITF_PATH}/map-integration-testing/utils/web/templates/ref_client_links.j2 --output ${MITF_PATH}/index.html
