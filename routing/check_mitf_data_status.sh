#!/bin/bash
set -xe


# Check/set mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
set_env_var_if_not_set BOT_NAME "mitf-bot"
set_env_var_if_not_set BOT_EMAIL "${BOT_NAME}\@here.com"
set_env_var_if_not_set LOG_FILE "status.log"


function get_and_process_ldm_list(){
    local map_config=$1; local log_file=$2

    # Docker preparation and execution
    source_docker_cfg map-integration-testing/ci/routing/docker.cfg
    docker pull ${DOCKER_IMAGE} && exception_docker "${BUILD_TAG}"
    docker run --env map_config=${map_config} \
               --env log_file=${log_file} \
               --name=${BUILD_TAG} \
               --interactive \
               --rm \
               --user=bldadmin \
               --volume=${WORKSPACE}:/workspace \
               --workdir=/workspace \
                ${DOCKER_IMAGE} bash -esux << "EOS"
    python3 map-integration-testing/ci/routing/get_dvn_list.py --map_config ${map_config} \
                                                               --dvn_list dvns.lst \
                                                               --generate_options False;
    dvn_list=$(cat dvns.lst);
    python3 map-integration-testing/ci/routing/check_if_tests_and_data_exist_for_dvn.py --dnv_list ${dvn_list} |
    tee -a ${log_file}
EOS
}

function get_map_config() {
    local topic=$1; local bot_name=$2

    declare -A map_configs=(
        ["FORMAT8_FEAT_DAL_MAP_VERSION"]='map_format8.config'
        ["FORMAT8_HLS_ROUTING_MAP_VERSION"]='map_format8.config'
        ["MAINLINE_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["SOP3_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["SOP4_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["SOP5_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["SOP5plus_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["SOP6_NDS_OLYMPIA_MAP_VERSION"]='map_nds.config'
        ["NDS_STANDARD_MAP_VERSION"]='map_nds_standard.config'
        ["NDS_MOTEGI_MAP_VERSION"]='map_nds_vanilla.config'
        ["NDS_BONNEVILLE_MAP_VERSION"]='map_nds_bonneville.config'
        ["NDS_DONINGTON_MAP_VERSION"]='map_nds_donington.config'
        ["NDS_SUPERSET_MAP_VERSION"]='map_nds_superset.config'
        ["NDS_ACDC_MAP_VERSION"]='map_nds_acdc.config'
        ["NDS_MAINLINE_SPARTA_EU_MAP_VERSION"]='map/sparta/mapdb/eu.config'
        ["NDS_SOP1_SPARTA_EU_MAP_VERSION"]='map/sparta/mapdb/eu.config'
        ["NDS_SOP2_SPARTA_EU_MAP_VERSION"]='map/sparta/mapdb/eu.config'
        ["NDS_SOP3_SPARTA_EU_MAP_VERSION"]='map/sparta/mapdb/eu.config'
        ["NDS_SOP4_SPARTA_EU_MAP_VERSION"]='map/sparta/mapdb/eu.config'
        ["NDS_MAINLINE_SPARTA_NA_MAP_VERSION"]='map/sparta/mapdb/na.config'
        ["NDS_SOP1_SPARTA_NA_MAP_VERSION"]='map/sparta/mapdb/na.config'
        ["NDS_SOP2_SPARTA_NA_MAP_VERSION"]='map/sparta/mapdb/na.config'
        ["NDS_SOP3_SPARTA_NA_MAP_VERSION"]='map/sparta/mapdb/na.config'
        ["NDS_SOP4_SPARTA_NA_MAP_VERSION"]='map/sparta/mapdb/na.config'
        ["NDS_MAINLINE_SPARTA_RW_MAP_VERSION"]='map/sparta/mapdb/rw.config'
        ["NDS_SOP1_SPARTA_RW_MAP_VERSION"]='map/sparta/mapdb/rw.config'
        ["NDS_SOP2_SPARTA_RW_MAP_VERSION"]='map/sparta/mapdb/rw.config'
        ["NDS_SOP3_SPARTA_RW_MAP_VERSION"]='map/sparta/mapdb/rw.config'
        ["NDS_SOP4_SPARTA_RW_MAP_VERSION"]='map/sparta/mapdb/rw.config'
    )
    local map_config="map-config/${map_configs[${topic}]}"
    local review=$(ssh gerrit.it.here.com -p 29418 \
                                          -l ${bot_name} \
                                          gerrit query --current-patch-set \
                                                       -- intopic:${topic} \
                                          project:mos/map-config \
                                          status:open \
                                          owner:mosman-bot \
                                          limit:1)
    local ref_id=$(get_ref "${review}")

    if [[ ! -z ${ref_id} ]]; then
        cd map-config
        git fetch origin ${ref_id} && git checkout FETCH_HEAD
        cd -
        get_and_process_ldm_list ${map_config} ${LOG_FILE}|| exit_code=1
    else
        echo "INFO: No changes for TOPIC=${topic} found" | tee -a ${LOG_FILE}
    fi
}

####################################################################################################
git_init "map-config" ${BOT_NAME} ${BOT_EMAIL}

# list of supported topics
TOPICS=(
        FORMAT8_FEAT_DAL_MAP_VERSION
        FORMAT8_HLS_ROUTING_MAP_VERSION
        MAINLINE_NDS_OLYMPIA_MAP_VERSION
        SOP3_NDS_OLYMPIA_MAP_VERSION
        SOP4_NDS_OLYMPIA_MAP_VERSION
        SOP5_NDS_OLYMPIA_MAP_VERSION
        SOP5plus_NDS_OLYMPIA_MAP_VERSION
        SOP6_NDS_OLYMPIA_MAP_VERSION
        NDS_STANDARD_MAP_VERSION
        NDS_MOTEGI_MAP_VERSION
        NDS_BONNEVILLE_MAP_VERSION
        NDS_DONINGTON_MAP_VERSION
        NDS_SUPERSET_MAP_VERSION
        NDS_ACDC_MAP_VERSION
        NDS_MAINLINE_SPARTA_EU_MAP_VERSION
        NDS_SOP1_SPARTA_EU_MAP_VERSION
        NDS_SOP2_SPARTA_EU_MAP_VERSION
        NDS_SOP3_SPARTA_EU_MAP_VERSION
        NDS_SOP4_SPARTA_EU_MAP_VERSION
        NDS_MAINLINE_SPARTA_NA_MAP_VERSION
        NDS_SOP1_SPARTA_NA_MAP_VERSION
        NDS_SOP2_SPARTA_NA_MAP_VERSION
        NDS_SOP3_SPARTA_NA_MAP_VERSION
        NDS_SOP4_SPARTA_NA_MAP_VERSION
        NDS_MAINLINE_SPARTA_RW_MAP_VERSION
        NDS_SOP1_SPARTA_RW_MAP_VERSION
        NDS_SOP2_SPARTA_RW_MAP_VERSION
        NDS_SOP3_SPARTA_RW_MAP_VERSION
        NDS_SOP4_SPARTA_RW_MAP_VERSION
        )

exit_code=0

for TOPIC in ${TOPICS[@]}; do
    echo "INFO: Processing TOPIC=${TOPIC}" | tee -a ${LOG_FILE}
    get_map_config "${TOPIC}" ${BOT_NAME}
done

grep -q ERROR ${LOG_FILE} && exit_code=1 || exit_code=0

echo "INFO: Execution summary" && cat ${LOG_FILE}

exit ${exit_code}
