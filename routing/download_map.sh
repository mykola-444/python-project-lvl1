#!/bin/bash -ex

# SCRIPT INPUT PARAMETERS
# ENVIRONMENT VARIABLES:
#   MAP_PATH_PREFIX
#   FORCE_DOWNLOAD
#   MAP_FORMAT
# map-config data in map-config directory

# input parameter: variable
# exit if variable is not set
function exit_if_no_env_var {
    if [ -z $(eval echo \${$1}) ]; then
        echo "Variable $1 is not set"
        exit 1
    else
        echo "$1=$(eval echo \${$1})"
    fi
}

function download_map_data() {
    if [[ -z ${map_aws_s3_bucket_url} ]]; then
        bucket_url='s3://'
    elif [[ ${map_aws_s3_bucket_url} != 's3://' ]]; then
        bucket_url=${map_aws_s3_bucket_url}/
    else
        bucket_url=${map_aws_s3_bucket_url}
    fi

    if [[ ! -z $format8_s3_bucket && "$1" == *"routing_server"* ]]; then
        bucket_url=${format8_s3_bucket}/
    fi

    if [[ ${bucket_url} == 's3://' ]]; then
        bucket_url='s3://'${aws_s3_bucket}'/' # HMC+JAPAN
    fi

    set -x
    if [[ "$1" == *"file"* ]]; then
            mkdir -p $MAP_PATH_PREFIX/$(dirname ${!1})
        [[ -f $MAP_PATH_PREFIX/${!1} ]] || aws s3 cp ${bucket_url}${!1} $MAP_PATH_PREFIX/${!1}
    elif [[ "$1" == *"folder"* ]]; then
        mkdir -p $MAP_PATH_PREFIX/$(dirname ${!1})
        aws s3 sync ${bucket_url}${!1} $MAP_PATH_PREFIX/${!1}
    fi
}

function download_map_config() {
    local MAP_CONFIG=$1
    source $MAP_CONFIG
    echo "Map version $map_version"
    echo "Syncing data from $MAP_CONFIG"
    while read param;
    do
        name=(${param//=/ })
    if [[ $MAP_FORMAT == NDS* ]]; then
        if [[ $name == *"folder_client"*  || "$name" == *"folder_metadata"* ]]; then
            download_map_data ${name}
        fi
    else
          download_map_data ${name}
    fi
    done < $MAP_CONFIG
}

function check_map_data() {
    if [[ ${map_aws_s3_bucket_url} != 's3://' ]]; then
        bucket_url=${map_aws_s3_bucket_url}/
    else
        bucket_url=${map_aws_s3_bucket_url}
    fi

    if [[ ! -z $format8_s3_bucket && "$1" == *"routing_server"* ]]; then
        bucket_url=${format8_s3_bucket}/
    fi

    set -x
    if [[ "$1" == *"file"* ]] || [[ "$1" == *"folder"* ]]; then
        if [ -e $MAP_PATH_PREFIX/${!1} ]; then
            echo 0
        else
            echo 1
        fi
    else
        echo 0
    fi
}

function check_map_config() {
    local MAP_CONFIG=$1
    source $MAP_CONFIG
    #echo "Map version $map_version"
    #echo "Checking if data from $MAP_CONFIG is present locally"
    local result=0
    while read param;
    do
        name=(${param//=/ })
        if [ $(check_map_data ${name}) == 1 ]; then
            result=1
            break
        fi
    done < $MAP_CONFIG
    echo $result
}

function remove_old_maps () {
    rm -rf $MAP_PATH_PREFIX/*
}

function main() {
    exit_if_no_env_var MAP_PATH_PREFIX
    exit_if_no_env_var FORCE_DOWNLOAD
    exit_if_no_env_var MAP_FORMAT
    local MAP_CONFIG
    # map format processing
    case $MAP_FORMAT in
        "F8" )
            MAP_CONFIG=map-config/map_format8.config
            # reduce F8 map size: remove lines with client and bundle
            sed -i '/client\|bundle/d' $MAP_CONFIG
            # remove bom files (some of them are absent, they are not required for tests generation
            sed -i '/bom-/d' $MAP_CONFIG
            ;;
        "HLS_BRF"|"OLS_BRF" )
            MAP_CONFIG=map-config/map_format8_brf.config
            ;;
        "HLS_BRF2"|"OLS_BRF2" )
            # MAP_CONFIG=map-config/map/ols/routing/int.config
            MAP_CONFIG=map-config/map/ols/routing/hmc_plus_japan.config
            ;;
        "NDS_OLYMPIA" )
            MAP_CONFIG=map-config/map_nds.config
            ;;
        "NDS_STANDARD" )
            MAP_CONFIG=map-config/map_nds_standard.config
            ;;
        "NDS_MOTEGI" )
            MAP_CONFIG=map-config/map_nds_vanilla.config
            ;;
        "NDS_DONINGTON" )
            MAP_CONFIG=map-config/map_nds_donington.config
            ;;
        "NDS_BONNEVILLE" )
            MAP_CONFIG=map-config/map_nds_bonneville.config
            ;;
        "NDS_SUPERSET" )
            MAP_CONFIG=map-config/map_nds_superset.config
            ;;
        "NDS_SPARTA" )
            # create one file with sparta parameters
            # options names in sparta configs are the same
            # workaround: add market name
            cp map-config/map/sparta/mapdb/eu.config eu.config
            cp map-config/map/sparta/mapdb/na.config na.config
            cp map-config/map/sparta/mapdb/rw.config rw.config
            sed -i 's/_nds=/_eu_nds=/' eu.config
            sed -i 's/_nds=/_na_nds=/' na.config
            sed -i 's/_nds=/_rw_nds=/' rw.config
            cat eu.config na.config rw.config > map_nds_sparta.config
            MAP_CONFIG=map_nds_sparta.config
            ;;
        * )
            echo "MAP_FORMAT=$MAP_FORMAT is not supported"
            exit 1
            ;;
    esac

    if [ ! -f $MAP_CONFIG ]; then
        echo "File MAP_CONFIG=$MAP_CONFIG does not exist"
        exit 1
    fi
    # Download map in any case if FORCE_DOWNLOAD=true
    local result=1
    if [ $FORCE_DOWNLOAD != true ]; then
        result=$(check_map_config $MAP_CONFIG)
    fi
    if [ $result == 0 ]; then
        echo "Map is already present. Skipping sync"
    else
        echo "Map is not present locally or FORCE_DOWNLOAD is used"
        remove_old_maps
        download_map_config $MAP_CONFIG
        # TODO: revert changes for BRF supporting
        # if [[ ${MAP_FORMAT} == "BRF" ]]; then
        #     download_map_config $MAP_CONFIG_BRF
        # fi
    fi
}

########
main
