#!/bin/bash -xe

source ../../routing/common_functions.sh
exit_if_no_env_var SPEC_LOCATION_PREFIX
exit_if_no_env_var LIB_LOCATION

declare -a lib_list
declare -a uniq_lib_list

for file in ${LIB_LOCATION}/*/*.robot ; do
    lib=$(echo "$file" | sed 's/[^_]*$//')
    lib_list+=(${lib::${#lib}-1})
done

uniq_lib_list=($(printf "%s\n" "${lib_list[@]}" | sort -u))

for lib in ${uniq_lib_list[@]} ; do
    python3 ${HOME}/here/map-integration-testing/ci/routing/acceptance/acceptance_tests_updater_dev.py --lib ${lib} -d \
                                                                    --sources ${SPEC_LOCATION_PREFIX}/spec/international/ \
                                                                    --config ${HOME}/here/map-integration-testing/config/acceptance_config.cfg
done
