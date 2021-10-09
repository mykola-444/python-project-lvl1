#!/bin/bash
set -xe

source map-integration-testing/ci/routing/common_functions.sh

# Check and set mandatory variables
exit_if_no_env_var LDM_REGION_DVN
exit_if_no_env_var MITF_PATH
set_env_var_if_not_set DB_PATH ${SOURCE_DATA_PATH}
set_env_var_if_not_set DVN_DB_PATH ${DB_PATH}/${LDM_REGION_DVN}
set_env_var_if_not_set TEST_CASE_NUMBER $1
set_env_var_if_not_set ENABLED_GENERATORS $2


REGION=$(get_region ${LDM_REGION_DVN})
MARKET=$(get_market ${REGION})
declare -A maps=([eu]=EU [na]=NA [rw]=ROW [twn]=TWN)

CONFIG_PARAMS=''
if [[ -z ${ENABLED_GENERATORS} ]]; then
    echo "Using default generators from config/acceptance_config_example.cfg"
else
    echo "Using enabled generators only: ${ENABLED_GENERATORS}"
    CONFIG_PARAMS="GENERATORS=${ENABLED_GENERATORS}"
fi

export PYTHONPATH=${PYTHONPATH}:${MITF_PATH}/map-integration-testing/ci/routing

# Generate Indexes
if [[ ! -f ${DVN_DB_PATH}/${REGION}_common.db3 ]]; then
    ln -s ${DVN_DB_PATH}/${REGION}.db3 ${DVN_DB_PATH}/${REGION}_common.db3
fi
./map-integration-testing/ci/routing/create_db_indexes.sh "${DVN_DB_PATH}" "${REGION}"

# Generate config
CONFIG=/tmp/${LDM_REGION_DVN}_config.cfg
python3 map-integration-testing/ci/routing/create_config.py --params ${CONFIG_PARAMS} \
                                                                "DB_NAME=${REGION}" \
                                                                "LDM_DATABASE_PATH=${DVN_DB_PATH}" \
                                                                "TEST_CASE_NUMBER=${TEST_CASE_NUMBER}" \
                                                                "MARKET=${maps[$MARKET]}" \
                                                            --config_template ${MITF_PATH}/map-integration-testing/config/acceptance_config_example.cfg \
                                                            --output ${CONFIG}

cd map-integration-testing

OUTPUT="/tmp/mitf_output"

python3 test_data_generator_runner/run.py --loglevel INFO  \
                                          --config ${CONFIG} \
                                          --output_folder ${OUTPUT} \
                                          --mp

cp ./VERSION ${OUTPUT}/MITF_VERSION

cd ${OUTPUT}

tar -czvf /workspace/tests.tgz ./
