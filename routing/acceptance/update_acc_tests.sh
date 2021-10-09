#!/bin/bash -ex

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var MITF_PATH
exit_if_no_env_var MAP_FORMAT
set_env_var_if_not_set MODE "dev"

# All parameters are not important for this step - so just copying the example:
cp ${MITF_PATH}/config/acceptance_config_example.cfg /tmp/test_runner.cfg

SPEC_LOCATION_PREFIX=../test_routing_component/share/here/routing
# elif [[ ${MAP_FORMAT} == "F8" ]]; then
#     SPEC_LOCATION_PREFIX=../installdir/share/here/routing
# fi

source /workspace/test_routing_component/map_config/map/ols/routing/hmc_plus_japan.config
printf "%s" "${map_version}" > /workspace/test_routing_component/share/here/routing/spec/map_version.txt

if [[ ${MAP_FORMAT} == "OLS_BRF" ]] || [[ ${MAP_FORMAT} == "OLS_BRF2" ]]; then
    ROUTER_TYPE="ols"
elif [[ ${MAP_FORMAT} == "HLS_BRF" ]] || [[ ${MAP_FORMAT} == "HLS_BRF2" ]]; then
    ROUTER_TYPE="hls"
fi

LIB_LOCATION=/workspace/test_libs
SPEC_LIST=/tmp/list_of_specs_to_modify.txt

# Save a list of specs to be modified for further packing into an artifact:
grep -nri "@file" ${LIB_LOCATION} | awk '{print $4}' | sed 's/^/international\//' | sort -u > /tmp/list_of_specs_to_modify.txt
cat ${SPEC_LIST}

cd ${MITF_PATH}
export PYTHONPATH="${MITF_PATH}:${MITF_PATH}/utils"

# Remove any part of $file starting with a space followed by -, from end of the string.
for file in ${LIB_LOCATION}/*/*.robot ; do
    lib=$(echo "$file" | sed 's/[^_]*$//')
    lib_list+=(${lib::${#lib}-1})
done

uniq_lib_list=($(printf "%s\n" "${lib_list[@]}" | sort -u))

for lib in ${uniq_lib_list[@]} ; do
    if [[ ${MODE} == "dev" ]]; then
        python3 ./ci/routing/acceptance/acceptance_tests_updater_dev.py --lib ${lib} \
                                                                        --sources ${SPEC_LOCATION_PREFIX}/spec/international/ \
                                                                        --config /tmp/test_runner.cfg \
                                                                        --no_debug_tag \
                                                                        --router_type ${ROUTER_TYPE}
        # TODO (asmirnov): Identify when we can ommit DEBUG tag and when it's still necessary
        # "--no_debug_tag" not only omits DEBUG tag but adds tag ROUTING-15269 on suite level
    else
        python3 ./ci/routing/acceptance/acceptance_tests_updater_prod.py --lib ${lib} \
                                                                         --sources ${SPEC_LOCATION_PREFIX}/spec/international/
    fi
done

cd ${SPEC_LOCATION_PREFIX}/spec

echo "INFO: Generating artifact: robot_specs.tgz"
if [[ ${MODE} == "dev" ]]; then
    cat /dev/null > ${SPEC_LIST}".dev"
    while read line
    do
        echo `dirname "$line"`"/dev_"`basename "$line"` >> ${SPEC_LIST}".dev"
    done < ${SPEC_LIST}
    # The following "post-processing" is not needed when "--no_debug_tag" is specified above
    # if [[ ${MAP_FORMAT} == "OLS" ]]; then
    #     grep -rl "    DEBUG" . | xargs sed -i 's/ \{1,\}DEBUG//g'
    # fi
    tar -czf robot_specs.tgz map_version.txt __init__.robot lib/ setup.robot $(find -name "dev_*.robot")
else
    tar -czf robot_specs.tgz map_version.txt __init__.robot lib/ setup.robot $(find -name "dev_*.robot")
fi

mv robot_specs.tgz /workspace
