#!/bin/bash
set -ex

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var LDM_REGION_DVN
exit_if_no_env_var MITF_PATH
exit_if_no_env_var DB_PATH
exit_if_no_env_var CONFIG_TEMPLATE
set_env_var_if_not_set AWS_DEFAULT_REGION us-east-1
set_env_var_if_not_set BUCKET mitf-artifacts
set_env_var_if_not_set ORIG_COVERAGE false
set_env_var_if_not_set SKIP_S3_UPLOAD false
set_env_var_if_not_set USE_INVESTIGATION_LIST false
set_env_var_if_not_set USE_CACHE True
set_env_var_if_not_set ORIGIN_LDM_REGION_DVN ${LDM_REGION_DVN}
MODE=$1; TEST_CASE_NUMBER=$2; ENABLED_GENERATORS=$3; SUCCESS_GEO_NODES_RUNNER=$4; GEO_NODES_ARG=$5

CONFIG_TEMPLATE_PATH="${MITF_PATH}/map-integration-testing/config/${CONFIG_TEMPLATE}"
REGION=$(get_region ${LDM_REGION_DVN})
MARKET=$(get_market ${REGION})
declare -A maps=([eu]=EU [na]=NA [rw]=ROW [twn]=TWN)

export PYTHONPATH+=${MITF_PATH}/map-integration-testing/ci/routing

CONFIG_PARAMS=''
if [[ -z ${ENABLED_GENERATORS} ]]; then
    echo "INFO: Using default generators from config/${CONFIG_TEMPLATE}"
else
    echo "WARN: Using enabled generators only: ${ENABLED_GENERATORS}"
    CONFIG_PARAMS="GENERATORS=${ENABLED_GENERATORS}"
fi

# if LOCAL_RUN var is set - it's supposed that you have LDMs in place:
if [[ ${LOCAL_RUN} == "false" ]]; then
    # Check LDM DBs availability
    if [[ -z $(aws s3api list-objects-v2 --bucket ${LDM_BUCKET} \
                                         --prefix ${LDM_KEY_PREFIX}/${REGION} \
                                         --query "Contents[?StorageClass=='STANDARD'].Key" \
                                         --output text | sed 's/\t/\n/g' | grep ${ORIGIN_LDM_REGION_DVN}) ]]; then
        echo "ERROR: Please note that given LDM ${ORIGIN_LDM_REGION_DVN} is not AVAILABLE"
        # Redefine LDM name (the newest one of the given Region)
        export LDM_REGION_DVN=$(aws s3 ls ${LDM_BUCKET}/${LDM_KEY_PREFIX}/${REGION}  --recursive | sort \
                                                                                                 | tail -n 1 \
                                                                                                 | awk '{print $4}' \
                                                                                                 | awk -F '/' '{print $3}')
        echo "WARN: Please not that for further processing new LDM ${LDM_REGION_DVN} has been selected"
    fi

    # Define/redefine DVN_DB_PATH variable
    set_env_var_if_not_set DVN_DB_PATH "${DB_PATH}/${LDM_REGION_DVN}"
    # Download sources
    python3 ${MITF_PATH}/map-integration-testing/ci/routing/download_sources.py --db_path ${DB_PATH} \
                                                                                --dvn ${LDM_REGION_DVN} \
                                                                                --use_cache ${USE_CACHE}
else
    echo "WARN: Local run - enabled"
    set_env_var_if_not_set DVN_DB_PATH "${DB_PATH}/${LDM_REGION_DVN}"

fi

echo "INFO: Verifying if LDM DBs existing status ..."
check_if_exist ${DVN_DB_PATH}

if [[ ${LDM_REGION_DVN} == HMC_* ]]; then
    python3 ./map-integration-testing/adapters/olp/sqlite/create_indices.py ${DVN_DB_PATH}/HMC_common.db3
    python3 ./map-integration-testing/adapters/olp/sqlite/create_indices.py ${DVN_DB_PATH}/HMC-ADDITIONAL.db3
else
    ./map-integration-testing/ci/routing/create_db_indexes.sh ${DVN_DB_PATH} ${REGION}
fi

# Generate config
CONFIG=/tmp/${LDM_REGION_DVN}_config.cfg
python3 map-integration-testing/ci/routing/create_config.py --params ${CONFIG_PARAMS} \
                                                                "DB_NAME=${REGION}" \
                                                                "LDM_DATABASE_PATH=${DVN_DB_PATH}" \
                                                                "TEST_CASE_NUMBER=${TEST_CASE_NUMBER}" \
                                                                "MARKET=${maps[$MARKET]}" \
                                                            --config_template ${CONFIG_TEMPLATE_PATH} \
                                                            --output ${CONFIG}
# Working directory changed
cd map-integration-testing

PREDEFINED_SUCCESS_GEO_NODES=/tmp/${REGION}_SUCCESS_GEO_NODES.json
######################################## PRODUCTION ################################################
if [[ ${MODE} == "production" ]]; then
    echo "WARN: Run production"
    aws s3 cp s3://${BUCKET}/mitf/success_geo_nodes/${REGION}_SUCCESS_GEO_NODES.json ${PREDEFINED_SUCCESS_GEO_NODES}
    declare -a prefixes=("f8_feat_dal_" "f8_hls_routing_" "nds_2.5.2_" "nds_2.4.2_")
    INVESTIGATION_LIST="/tmp/investigation_list.yaml"
    COMBINED_INVESTIGATION_LIST="/tmp/combined_investigation_list.yaml"
    if [[ -e ${COMBINED_INVESTIGATION_LIST} ]]; then rm ${COMBINED_INVESTIGATION_LIST}; fi
    for i in "${prefixes[@]}"
        do
            aws s3 cp s3://mitf-artifacts/mitf/success_geo_nodes-investigation-list/"${i}"investigation_list.yaml \
                                                                               /tmp/"${i}"investigation_list.yaml
            < /tmp/"${i}"investigation_list.yaml grep -Ev "^\s*(#|$)" >> ${COMBINED_INVESTIGATION_LIST}
        done

    sort -u ${COMBINED_INVESTIGATION_LIST} -o ${COMBINED_INVESTIGATION_LIST}

    awk -F': ' '{lines[$1] = (lines[$1] ? lines[$1] ";" $2 : $0)}
    END {for (line in lines) print lines[line]}' ${COMBINED_INVESTIGATION_LIST} |
    awk '{ gsub(/\";"/, ";"); print $0 }' | sort -d > ${INVESTIGATION_LIST}
    OUTPUT="/tmp/mitf_output"
    PYTHONPATH=${MITF_PATH}/map-integration-testing \
    python3 ci/routing/generate_data_by_predefined_geo_nodes.py --predefined_geo_nodes ${PREDEFINED_SUCCESS_GEO_NODES} \
                                                                --config ${CONFIG} \
                                                                --output ${OUTPUT} \
                                                                --investigation_list ${INVESTIGATION_LIST}
    create_dir_if_not_exists ${OUTPUT}
    cp ./VERSION ${OUTPUT}/MITF_VERSION
    # Working directory changed
    cd ${OUTPUT}
    # Archive artifacts
    if [[ ${ORIGIN_LDM_REGION_DVN} != ${LDM_REGION_DVN} ]]
    then
        archive_and_upload_on_aws "tests.tgz" ${BUCKET} "mitf/xml/${ORIGIN_LDM_REGION_DVN}"
        rm ${MITF_PATH}/tests.tgz
        echo "WARN: tests for ${ORIGIN_LDM_REGION_DVN} generated from ${LDM_REGION_DVN}" > README.txt
    else
        archive_and_upload_on_aws "tests.tgz" ${BUCKET} "mitf/xml/${LDM_REGION_DVN}"
    fi
######################################## RESEARCH ##################################################
elif [[ "${MODE}" == "research" ]] && [[ ${SUCCESS_GEO_NODES_RUNNER} == "sgn_run" ]]; then
    echo "INFO: Run research with success geo nodes"
    if [[ "${ORIG_COVERAGE}" == "true" ]]; then
        aws s3 cp s3://${BUCKET}/mitf/success_geo_nodes-orig_coverage/${REGION}_SUCCESS_GEO_NODES.json ${PREDEFINED_SUCCESS_GEO_NODES}
    else
        aws s3 cp s3://${BUCKET}/mitf/success_geo_nodes-dev/${REGION}_SUCCESS_GEO_NODES.json ${PREDEFINED_SUCCESS_GEO_NODES}
    fi
    INVESTIGATION_LIST_PARAMS=''
    INVESTIGATION_LIST=/tmp/investigation_list.yaml
    if [[ "${USE_INVESTIGATION_LIST}" == "true" ]]; then
        aws s3 cp s3://mitf-artifacts/mitf/success_geo_nodes-investigation-list-dev/investigation_list.yaml $INVESTIGATION_LIST
        INVESTIGATION_LIST_PARAMS="--investigation_list $INVESTIGATION_LIST"
    fi
    OUTPUT="/tmp/mitf_rnd_tests"
    PYTHONPATH=${MITF_PATH}/map-integration-testing \
    python3 ci/routing/generate_data_by_predefined_geo_nodes.py --predefined_geo_nodes ${PREDEFINED_SUCCESS_GEO_NODES} \
                                                                --config ${CONFIG} \
                                                                --output ${OUTPUT} \
                                                                --generate_xml \
                                                                ${INVESTIGATION_LIST_PARAMS}
    cp ./VERSION ${OUTPUT}/MITF_VERSION
################################ RESEARCH (GENERATE SGN)############################################
elif [[ ${MODE} == "research" ]] && [[ ${SUCCESS_GEO_NODES_RUNNER} == "sgn_generate" ]]; then
    echo "Run research"
    OUTPUT="/tmp/mitf_rnd_tests"
    GEO_NODES=${GEO_NODES_ARG}

    if [[ ${LDM_REGION_DVN} == HMC_* ]]; then
        MP_ARG="--shuffle"
    fi

    if [[ -z ${GEO_NODES_ARG} ]]; then
        export PYTHONPATH=$PYTHONPATH:${MITF_PATH}/map-integration-testing
        echo "$(timeout 21600 \
        python3 test_data_generator_runner/run.py --loglevel INFO  \
                                                  --config ${CONFIG} \
                                                  --mp \
                                                  --ttl 14400 \
                                                  --output_folder ${OUTPUT} \
                                                  ${MP_ARG})"
    else
        export PYTHONPATH=$PYTHONPATH:${MITF_PATH}/map-integration-testing
        echo "$(timeout 21600 \
        python3 test_data_generator_runner/run.py --loglevel INFO  \
                                                  --config ${CONFIG} \
                                                  --output_folder ${OUTPUT} \
                                                  --geo_nodes ${GEO_NODES} \
                                                  ${MP_ARG})"
    fi
    cp ./VERSION ${OUTPUT}/MITF_VERSION
else
    echo "ERROR: Undetermined MODE: ${MODE}"
    exit 1
fi

if [[ ${MODE} == "research" ]]; then
    cd ${OUTPUT}
    if [[ ${LDM_REGION_DVN} == HMC_* ]]; then
        if [[ ${SKIP_S3_UPLOAD} == "false" ]]; then
            if [[ ${CONFIG_TEMPLATE} == "routing_config_example.cfg" ]]; then
                # TODO (asmirnov): Replace with routing_hmc_config_example.cfg or whatever it is named
                archive_and_upload_on_aws "tests.tgz" ${BUCKET} "mitf/hmc/int/${TARGET}/${LDM_REGION_DVN}"
            elif [[ ${CONFIG_TEMPLATE} == "hmc_config_example.cfg" ]]; then
                archive_and_upload_on_aws "tests.tgz" ${BUCKET} "mitf/hmc/acc/${TARGET}/${LDM_REGION_DVN}"
            fi
        fi
    else
        tar -czvf ${MITF_PATH}/tests.tgz ./
    fi
fi

ls ${MITF_PATH}

PYTHONPATH=${MITF_PATH}/map-integration-testing \
python3 ${MITF_PATH}/map-integration-testing/ci/routing/generate_ref_client_links.py --config ${CONFIG} \
                                                                                     --test_data_path ${OUTPUT} \
                                                                                     --template ${MITF_PATH}/map-integration-testing/utils/web/templates/ref_client_links.j2 \
                                                                                     --output ${MITF_PATH}/index.html
