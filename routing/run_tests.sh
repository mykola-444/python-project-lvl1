#!/bin/bash -ex

. map-integration-testing/ci/routing/common_functions.sh

function verify_env_vars {
    exit_if_no_env_var MAP_PATH_PREFIX
    exit_if_no_env_var LDM_REGION_DVN
    exit_if_no_env_var MITF_PATH
    exit_if_no_env_var MAP_FORMAT
}

####################################################################
# main code
verify_env_vars

REGION=$(get_region $LDM_REGION_DVN)
MARKET=$(get_market $REGION)
declare -A maps=([eu]=EU [na]=NA [rw]=ROW)

set -a
case $MAP_FORMAT in
    "F8" )
        source map-config/map_format8.config
        OPT="--cdt $MAP_PATH_PREFIX/$file_routing_server_world_cdt"
        ;;
    "NDS_OLYMPIA" )
        source map-config/map_nds.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_STANDARD" )
        source map-config/map_nds_standard.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_standard_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_MOTEGI" )
        source map-config/map_nds_vanilla.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_vanilla_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_DONINGTON" )
        source map-config/map_nds_map_nds_bonneville.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_vanilla_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_BONNEVILLE" )
        source map-config/map_nds_bonneville.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_bonneville_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_SUPERSET" )
        source map-config/map_nds_superset.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_superset_${MARKET}_nds)  --routing-mode CAR"
        ;;
    "NDS_SPARTA" )
        source map-config/map/sparta/mapdb/${MARKET}.config
        OPT="--nds $MAP_PATH_PREFIX/$(eval echo \$file_client_nds) --routing-mode CAR"
        ;;
    "BRF" )
        source map-config/map_format8.config
        source map-config/map_format8_brf.config
        OPT="--brf $MAP_PATH_PREFIX/$folder_routing_server_brf"
        ;;
    "BRF2" )
        source map-config/map/ols/routing/hmc_plus_japan.config
        OPT="--brf $MAP_PATH_PREFIX/$folder_routing_server_brf"
        ;;
esac

# create main xml file:
cat << EOF > ci.xml
<?xml version='1.0' encoding='UTF-8'?>
<route_test>
  <route_test dir="mitf_tests"/>
</route_test>
EOF

if [[ ${MAP_FORMAT} == "BRF2" ]]; then
    ./share/here/tests/test-routing-integration \
        $OPT \
        --test ./ci.xml
else
    installdir/bin/with-ld-preloads test-routing-integration \
        $OPT \
        --test ./ci.xml
fi
