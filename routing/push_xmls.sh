#!/bin/bash -ex

source map-integration-testing/ci/routing/common_functions.sh

function verify_env_vars {
    exit_if_no_env_var PATH_TO_XMLS
    exit_if_no_env_var TOPIC
    exit_if_no_env_var GERRIT_BRANCH
    set_env_var_if_not_set BOT_NAME aws-bot
    set_env_var_if_not_set BOT_EMAIL ${BOT_NAME}\@here.com
}

function get_ref() {
    echo "$1" | grep ref | cut -d':' -f2 | tr -d " \n\t"
}

function update_map_version(){
    source=$1
    dest=$2
    # ensure that dest directory exists (required for initial push)
    mkdir -p $(dirname ${dest})
    grep "^map_version" ${source} > ${dest}
}

function create_wrapper(){
    dest=$1
    if [[ ! -f ${dest} ]]; then
        cat <<EOF > ${dest}
<?xml version='1.0' encoding='UTF-8'?>
<route_test>
  <route_test dir="xml"/>
</route_test>
EOF
    fi
}

function push_report() {
    MAP_FORMAT=$1
    TOPIC_NAME=$2
    COMMIT_MESSAGE=$3
    MARKET=$4

    REVIEW=$(ssh gerrit.it.here.com -p 29418 -l ${BOT_NAME} gerrit query --current-patch-set \
             topic:${TOPIC_NAME} \
             project:mos/map-integration/mitf \
             status:open owner:${BOT_NAME} \
             branch:${GERRIT_BRANCH} \
             limit:1)

    REF_ID=$(get_ref "${REVIEW}")

    cd mitf
    if [[ ! -z ${REF_ID} ]]; then
        git fetch origin ${REF_ID} && git checkout FETCH_HEAD
        CREATE_PATCHSET=true
    else
        CREATE_PATCHSET=false
    fi

    cd -

    declare -A map_path=([F8]='f8/int' \
                         [NDS_OLYMPIA]='nds/olp' \
                         [NDS_STANDARD]='nds/std' \
                         [NDS_MOTEGI]='nds/mtg' \
                         [NDS_SPARTA]="nds/spt/${MARKET}" \
                         [NDS_BONNEVILLE]='nds/bon' \
                         [NDS_DONINGTON]='nds/don' \
                         [NDS_SUPERSET]='nds/sup' \
                         [NDS_ACDC]='nds/acdc')

    declare -A map_cfg=([F8]='map_format8.config' \
                        [NDS_OLYMPIA]='map_nds.config' \
                        [NDS_STANDARD]='map_nds_standard.config' \
                        [NDS_MOTEGI]='map_nds_vanilla.config' \
                        [NDS_SPARTA]="map/sparta/mapdb/${MARKET}.config" \
                        [NDS_BONNEVILLE]='map_nds_bonneville.config' \
                        [NDS_DONINGTON]='map_nds_donington.config' \
                        [NDS_SUPERSET]='map_nds_superset.config' \
                        [NDS_ACDC]='map_nds_acdc.config')

    MAP_PATH=${map_path[${MAP_FORMAT}]}
    MAP_CFG=${map_cfg[${MAP_FORMAT}]}

    update_map_version installdir/map_config/${MAP_CFG} mitf/mitf/${MAP_PATH}/map_version.cfg
    get_reviewers

    cd mitf
    # remove files if they exist
    if [[ -d mitf/${MAP_PATH}/xml ]]; then
        git rm -r mitf/${MAP_PATH}/xml/*
    fi

    mkdir -p mitf/${MAP_PATH}/xml
    cp -r ${PATH_TO_XMLS}/* mitf/${MAP_PATH}/xml/
    git add mitf/${MAP_PATH}/xml
    git add mitf/${MAP_PATH}/map_version.cfg

    create_wrapper mitf/${MAP_PATH}/mitf_ci.xml
    git add mitf/${MAP_PATH}/mitf_ci.xml

    check_if_to_commit=$(git status)
    if [[ ${check_if_to_commit} != *"nothing to commit"* ]] ; then

        if [[ ${CREATE_PATCHSET} == true ]]; then
            git commit --amend --no-edit
        else
            git commit -m "${COMMIT_MESSAGE}"
        fi

        git push origin HEAD:refs/for/${GERRIT_BRANCH}/${TOPIC_NAME}%${REVIEWERS_LIST}
    else
        echo "There is nothing to commit"
    fi
}

####################################################################

verify_env_vars;
init_git

COMMIT_MESSAGE="MITF-generated tests for ${TOPIC}"

declare -A ISSUES=( ["SOP3_NDS_OLYMPIA"]="OLYMP-44853"  \
                    ["NDS_SPARTA"]="SPARTA-13565"
                    )

case ${TOPIC} in
    "FORMAT8_FEAT_DAL_MAP_VERSION"* )
        push_report "F8" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    "FORMAT8_HLS_ROUTING_MAP_VERSION"* )
        push_report "F8" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"MAINLINE_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"SOP3_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${ISSUES["SOP3_NDS_OLYMPIA"]}: ${COMMIT_MESSAGE}"
        ;;
    *"SOP4_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${ISSUES["SOP3_NDS_OLYMPIA"]}: ${COMMIT_MESSAGE}"
        ;;
    *"SOP5_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${ISSUES["SOP3_NDS_OLYMPIA"]}: ${COMMIT_MESSAGE}"
        ;;
    *"SOP5plus_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${ISSUES["SOP3_NDS_OLYMPIA"]}: ${COMMIT_MESSAGE}"
        ;;
    *"SOP6_NDS_OLYMPIA_MAP_VERSION"* )
        push_report "NDS_OLYMPIA" "${TOPIC}" "${ISSUES["SOP3_NDS_OLYMPIA"]}: ${COMMIT_MESSAGE}"
        ;;
    *"NDS_STANDARD_MAP_VERSION"* )
        push_report "NDS_STANDARD" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS_MOTEGI_MAP_VERSION"* )
        push_report "NDS_MOTEGI" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS_BONNEVILLE_MAP_VERSION"* )
        push_report "NDS_BONNEVILLE" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS_SUPERSET_MAP_VERSION"* )
        push_report "NDS_SUPERSET" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS_DONINGTON_MAP_VERSION"* )
        push_report "NDS_DONINGTON" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS_ACDC_MAP_VERSION"* )
        push_report "NDS_ACDC" "${TOPIC}" "${COMMIT_MESSAGE}"
        ;;
    *"NDS"*"SPARTA"*"MAP_VERSION"* )
        MARKET=$(echo ${TOPIC} | grep -oP "(EU|NA|RW)" | tr '[:upper:]' '[:lower:]')
        if [[ -z ${MARKET} ]]; then
            echo "Cannot get Sparta Map Market form ${TOPIC} Topic"
            exit 1
        fi
        push_report "NDS_SPARTA" "${TOPIC}" "${COMMIT_MESSAGE}"$'\n\nRelates to: '${ISSUES["NDS_SPARTA"]} ${MARKET}
        ;;
    * )
        echo "TOPIC=${TOPIC} is not supported"
        exit 1
        ;;
esac
