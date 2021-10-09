#!/bin/bash
set -e

# Constants
MITF_AWS_S3_GRANTS='emailaddress="I_EXT_AWS_CCI_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_RD@here.com",emailaddress="I_EXT_AWS_ROUTING_MAPDATA_RD@here.com",emailaddress="I_EXT_AWS_HERE_NDS_RD@here.com",emailaddress="I_EXT_AWS_CONTDELIV_P@here.com",emailaddress="I_EXT_AWS_AUTOMOTIVE_DEVOPS_RD@here.com"'
MITF_ARTIFACTS_BUCKET="mitf-artifacts"
LDM_BUCKET="maps-sources-us-east-1"
LDM_KEY_PREFIX="ldm/sqlite"
TRC_KEY_PREFIX="mitf/test_routing_components"
AWS_DEFAULT_REGION="us-east-1"
JENKINS_JSON_API_SUFFIX="api/json?pretty=true"
VALID_LDM_NAMES=("NA" \
                 "WEU" \
                 "EEU" \
                 "SAM" \
                 "MEA" \
                 "MEA_IM2" \
                 "IND" \
                 "ANT" \
                 "AU" \
                 "APAC" \
                 "APAC_HK" \
                 "APAC_MACAU" \
                 "TWN")

function git_init() {
    local_project_dir=$1; bot_name=$2; bot_email=$3
    cd ${local_project_dir}
    git config user.name ${bot_name}
    git config user.email ${bot_email}
    cd -
    scp -p -P 29418 ${bot_name}@gerrit.it.here.com:hooks/commit-msg ${local_project_dir}/.git/hooks/
}

function check_if_change_exists() {
    gerrit_project=$1; gerrit_branch=$2; gerrit_topic=$3;
    user_name=$4; message=$5; change_status=$6

    if [[ -n ${message} ]]; then
        search_results=$(ssh gerrit.it.here.com -p 29418 \
                                                -l ${user_name} \
                                                gerrit query --current-patch-set \
                                                             --commit-message *"${message}"* \
                                                             --format json \
                                                topic:"${gerrit_topic}" \
                                                project:${gerrit_project} \
                                                branch:${gerrit_branch} \
                                                status:${change_status} \
                                                limit:1)
    else
         search_results=$(ssh gerrit.it.here.com -p 29418 \
                                                -l ${user_name} \
                                                gerrit query --current-patch-set \
                                                             --format json \
                                                topic:"${gerrit_topic}" \
                                                project:${gerrit_project} \
                                                branch:${gerrit_branch} \
                                                status:${change_status} \
                                                limit:1)
    fi

    changes_count="$(echo ${search_results} | jq -r 'select(.rowCount != null) | .rowCount')"

    if [[ ${changes_count} -gt 1 ]]; then
        echo "WARN: Multiply [${changes_count}] changes found of [${gerrit_project}] Gerrit project.\
              Please rebase manually if needed!"
    elif [[ ${changes_count} -eq 1 ]]; then
        change_url="$(echo ${search_results} | jq -r 'select(.url != null) | .url')"
        change_number="$(echo ${search_results} | jq -r 'select(.number != null) | .number')"
        change_revision="$(echo ${search_results} | jq -r 'select(.currentPatchSet.revision != null) | .currentPatchSet.revision')"
        commit_message="$(echo ${search_results} | jq -r 'select(.commitMessage != null) | .commitMessage')"
        change_ref="$(echo ${search_results} | jq -r 'select(.currentPatchSet.ref != null) | .currentPatchSet.ref')"
        echo "INFO: [${changes_count}] change (${change_url}: "${commit_message%%[$'\t\r\n:']*}") found. Rebase needed on [${change_revision}]!"
    else
        echo "INFO: [${changes_count}] change found. There are not existing related changes"
    fi
}

function check_ldm_name() {
    GIVEN_LDM=$1
    echo "INFO: Checking given LDM: ${GIVEN_LDM}"
    if [[ ${VALID_LDM_NAMES[*]} =~ ${GIVEN_LDM%%_*} ]]; then
        echo "INFO: Given LDM name [${GIVEN_LDM}] is checked and VALID"
        STATUS=1
    else
        echo "ERROR: Given LDM name [${GIVEN_LDM}] is not supported right now"
        STATUS=0
    fi
}

function get_ref() {
    echo "$1" | grep ref | cut -d':' -f2 | tr -d " \n\t"
}

function get_region {
    echo $(python3 map-integration-testing/ci/routing/get_region_from_dvn.py $1)
}

function get_market {
    case $1 in
    "WEU" )
        echo "eu" ;;
    "EEU" )
        echo "eu" ;;
    "NA" )
        echo "na" ;;
    "TWN" )
        echo "twn" ;;
    *)
        echo "rw" ;;
  esac
}

function get_sparta_market {
    case $1 in
    "WEU" )
        echo "eu" ;;
    "EEU" )
        echo "eu" ;;
    "NA" )
        echo "na" ;;
    *)
        echo "rw" ;;
  esac
}

function get_sparta_map_market {
    case $1 in
    "WEU" )
        echo "EU" ;;
    "EEU" )
        echo "EU" ;;
    "NA" )
        echo "NA" ;;
    *)
        echo "RW" ;;
  esac
}

read_map_config_file() {
    if [[ -z $2 ]]; then
        map_config_local_path="map-config"
    else
        map_config_local_path=$2
    fi
    map_format=$1;
    if [[ ${map_format} == "F8" ]]; then
        MAP_CONFIG="map_format8.config"
        # Read Map Config file
        source ${map_config_local_path}/${MAP_CONFIG}
        MAP_VERSION=${map_version}; MAP_BUCKET=${map_aws_s3_bucket_url}
        MAP_OBJECT_KEY=${file_world_cdt}; MAP_PATH=${map_path}
    elif [[ ${map_format} == "BRF" ]]; then
        BRF_CONFIG="map_format8_brf.config"
        # Read BRF Config file
        source ${map_config_local_path}/${BRF_CONFIG}
        MAP_VERSION=${map_version}; MAP_BUCKET=${map_aws_s3_bucket_url}
        BRF_VERSION=${brf_compiler_version}; MAP_OBJECT_KEY=${folder_routing_server_brf}
    else
        echo "ERROR: Unsupported MAP_FORMAT: ${MAP_FORMAT}"
        exit 1
    fi
}

function init_git() {
    cd mitf
    git config user.name ${BOT_NAME}
    git config user.email ${BOT_EMAIL}
    cd -
    scp -p -P 29418 ${BOT_NAME}@gerrit.it.here.com:hooks/commit-msg mitf/.git/hooks/
}

function get_reviewers(){
    REVIEWERS_FILE_NAME=${1}
    set_env_var_if_not_set REVIEWERS_FILE_NAME "map_routing_approvers.list"
    while read -r line
    do
        if [[ "$line" == "#"* ]] && [[ flag -eq 1 ]]; then flag=0; fi
        for item in ${line//#}
        do
            if [[ ${TOPIC} =~ $item ]] || [[ flag -eq 1 ]]
            then
                if [[ ! ${line} =~ "#" ]]; then REVIEWERS_LIST="r=${line// },$REVIEWERS_LIST"; fi
                flag=1
            fi
        done
    done < "mitf/${REVIEWERS_FILE_NAME}"
}
# input parameter: variable
# exit if variable is not set
function exit_if_no_env_var {
    if [[ -z $(eval echo \${$1}) ]]; then
        echo "ERROR: Mandatory variable $1 is not set"
        exit 1
    else
        echo "INFO: Mandatory variable $1 is set and equal to $(eval echo \${$1})"
    fi
}

# input parameters: variable default_value
# set variable to default_value if it is not defined
function set_env_var_if_not_set {
    if [[ -z $(eval echo \${$1}) ]]; then
        echo "WARN: Variable $1 is not set"
        export $1=$2
        echo "WARN: Variable $1 is set to $2"
    else
        echo "INFO: Variable $1 is set to $(eval echo \${$1})"
    fi
}

function exception_docker {
trap "{ [[ -z \"$1\" ]] ||
        docker ps -aq --filter name=\"$1\" |
        xargs --no-run-if-empty docker rm -f --volumes ||
        true;
        } &> /dev/null" EXIT
}

# input parameter: path to docker.cfg
# change docker registry to artifactory and source config file
function source_docker_cfg() {
    local config=$1
    # use docker-local.artifactory
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i "" 's/901893201569.dkr.ecr.us-east-1.amazonaws.com/docker-local.artifactory.in.here.com\/cci/' $config
    else
        sed -i 's/901893201569.dkr.ecr.us-east-1.amazonaws.com/docker-local.artifactory.in.here.com\/cci/' $config
    fi
    source $config
}

function archive_and_upload_on_aws() {
    NAME=$1
    BUCKET=$2
    AWS_PATH=$3
    LOCAL_COPY_PATH=$4
    tar -czvf ${MITF_PATH}/${NAME} ./
    if [[ -d ${LOCAL_COPY_PATH} ]]; then
        cp ${MITF_PATH}/${NAME} ${LOCAL_COPY_PATH}
    fi
    aws s3 cp ${MITF_PATH}/${NAME} s3://${BUCKET}/${AWS_PATH}/${NAME}
    aws s3api put-object-acl --bucket ${BUCKET} --key ${AWS_PATH}/${NAME} --grant-full-control ${MITF_AWS_S3_GRANTS}
}

function download_from_aws_and_unzip() {
    NAME=$1
    BUCKET=$2
    AWS_PATH=$3
    OUTPUT=$4
    aws s3 cp s3://${BUCKET}/${AWS_PATH}/${NAME} ${MITF_PATH}/${NAME}
    if [[ -d ${OUTPUT} ]]; then
        tar -xvf ${MITF_PATH}/${NAME} -C ${OUTPUT}
    else
        tar -xvf ${MITF_PATH}/${NAME}
    fi
}

function archive_and_upload_to_aws() {
    ARCHIVE_NAME=$1; BUCKET=$2; AWS_PATH=$3
    tar -czvf /tmp/${ARCHIVE_NAME} . &&
    aws s3 cp /tmp/${ARCHIVE_NAME} s3://${BUCKET}/${AWS_PATH}/${ARCHIVE_NAME} &&
    aws s3api put-object-acl --bucket ${BUCKET} \
                             --key ${AWS_PATH}/${ARCHIVE_NAME} \
                             --grant-full-control ${MITF_AWS_S3_GRANTS}
}

function create_dir_if_not_exists {
    if [[ ! -d $1 ]]; then
        echo "WARN: Directory $1 does not exist. Creating ..."
        mkdir -pv $1
    else
        echo "INFO: Directory $1 exists."
    fi
}

function check_if_exist {
    if ls $1* 1> /dev/null 2>&1; then
        echo "INFO: Some files do exist."
    else
        echo "ERROR: No files exist in $1 directory. Exiting ..."
        exit 1
    fi
}

####################################### Gerrit API ################################################
get_change_details() {
    username=$1; change_number=$2
    ssh gerrit.it.here.com -p 29418 -l ${username} gerrit query --format=JSON \
                                                                --current-patch-set \
                                                                --comments \
                                                                ${change_number} |
    jq --slurp '.[0]'
}

get_current_patch_set() {
    change_details=$1
    CURRENT_PATCH_SET_NUMBER="$(echo ${change_details} | jq --raw-output '.currentPatchSet.number')"
    echo "INFO: Current Patch-Set number [${CURRENT_PATCH_SET_NUMBER}]"
}

get_change_verification_status() {
    change_details=$1; username=$2
    verification_details="$(echo ${change_details} | jq --raw-output \
                                                        --arg username ${username} \
                         '.currentPatchSet.approvals[]? | select(.by.username == $username)')"
    VERIFICATION_TYPE="$(echo ${verification_details} | jq -r '.type')"
    VERIFICATION_STATUS="$(echo ${verification_details} | jq -r '.value')"
    GRANTED_ON="$(echo ${verification_details} | jq -r '.grantedOn')"
}

get_related_gerrit_messages() {
    change_details=$1; granted_timestamp=$2; verification_status_set_by=$3
    echo ${change_details} | jq --raw-output \
                               --arg unverified_on ${granted_timestamp} \
                               --arg unverified_by ${verification_status_set_by} \
    '.comments[]? | select(.timestamp == ($unverified_on | tonumber) and .reviewer.name == $unverified_by).message'
}

get_job_artifact() {
    build_link=$1; output_dir=$2; artifact_path=$3
    project_link=${build_link%/*}; build_number=${build_link##*/}; destination="${output_dir}/${build_number}"
    echo "INFO: Trying to get [${artifact_path}] from ${build_number} build of ${project_link} Jenkins job"
    wget -nc -v --tries=3 --timeout=120 -P ${destination} \
         "${project_link}"/"${build_number}"/s3/download/${artifact_path} &&
    echo "INFO: [${artifact_path}] successfully downloaded to [${destination}]"
}
