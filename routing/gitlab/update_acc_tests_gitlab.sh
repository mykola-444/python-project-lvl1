#!/bin/bash -ex

WORKSPACE=$(pwd)
SPEC_LOCATION_PREFIX=build/share/here/routing
LIB_LOCATION=libs
SPEC_LIST=list_of_specs_to_modify.txt
grep -nri "@file" ${LIB_LOCATION} | awk '{print $4}' | sed 's/^/international\//' | sort -u > list_of_specs_to_modify.txt
cat ${SPEC_LIST}

for file in ${LIB_LOCATION}/*/*.robot; do
  lib=$(echo "$file" | sed 's/[^_]*$//')
  lib_list+=(${lib::${#lib}-1})
done

uniq_lib_list=($(printf "%s\n" "${lib_list[@]}" | sort -u))
touch test_runner.cfg
export PYTHONPATH="${WORKSPACE}/tools"

for lib in ${uniq_lib_list[@]}; do
  python3 tools/ci/routing/acceptance/acceptance_tests_updater_dev.py \
    --lib ${lib} --sources ${SPEC_LOCATION_PREFIX}/spec/international/ \
    --config test_runner.cfg --no_debug_tag --router_type ols
done

cd ${SPEC_LOCATION_PREFIX}/spec
tar -czf ${WORKSPACE}/spec.tgz __init__.robot lib/ setup.robot $(find -name "dev_*.robot")
