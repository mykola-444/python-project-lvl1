#!/usr/bin/env bash
set -xe

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var MAP_FORMAT
exit_if_no_env_var LDM_REGION_DVN
set -a
if [[ ${MAP_FORMAT} == "OLS_BRF" ]] || [[ ${MAP_FORMAT} == "OLS_BRF2" ]]; then
    # OPTION 1: Gemini code vs BRF2 (HMC-based)
    # OPTION 2: Gemini code vs BRF. This config is being used in GitLab Gemini pipeline at the moment
    # JOB: https://main.gitlab.in.here.com/routing/gemini/-/jobs/847013
    # COMMAND: build/bin/test-routing-acceptance --driver server.ols.json --include server.ols --uri http://localhost:8080 build/share/here/routing/spec/international --no-map-config
    if [[ ${MAP_FORMAT} == "OLS_BRF" ]]; then
        source map-config/map_format8_brf.config
    else
        # source map-config/map/ols/routing/int.config
        source map-config/map/ols/routing/hmc_plus_japan.config
    fi
    export LD_LIBRARY_PATH=$(pwd)/build/lib64/here
    BRF=${MAP_PATH_PREFIX}/${folder_routing_server_brf}/
    build/bin/gemini --brf ${BRF} --l10n build/share/here/routing/l10n --developer &
    sleep 5
    # 2019-11-28T18:00:05.453370+00:00 - INFO - Started server: 0.0.0.0:8080
    build/bin/test-routing-acceptance --driver server.ols.json --include server.ols \
        --uri http://localhost:8080 build/share/here/routing/spec/international \
        --no-map-config --http-header "x-sentry-businessfeatures=ols-pc1-route-invoke"
    rebot --nostatusrc --outputdir outputs --xunit xunit/xunit.xml \
        --log NONE --report html/report.html output.xml
    cp output.xml outputs/xunit/initial_xunit.xml
elif [[ ${MAP_FORMAT} == "HLS_BRF" ]] || [[ ${MAP_FORMAT} == "HLS_BRF2" ]]; then
    # JOB 1: https://hls.cci.in.here.com/job/hls_routing/job/sv/job/test/job/team-routing/job/server/job/psv-test-acceptance-lib-notraffic-brf-linux-x86-gcc7.2/
    # COMMAND 1: ./bin/test-routing-acceptance --driver=server.lib --include=server.lib --log=NONE --map-config=./map_config/map_format8_brf.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    # JOB 2: https://hls.cci.in.here.com/job/hls_routing/job/psv/job/test/job/team-routing/job/server/job/psv-test-acceptance-hlp-json-trafficdb-brf-linux-x86-gcc7.2/
    # COMMAND 2: ./bin/with-ld-preloads test-routing-acceptance --driver=server.hlp.json --include=server.hlpANDTRAFFIC --uri=urn:nokia.com:routing:atdd:target:fastcgi --log=NONE --map-config=./map_config/map_format8_brf.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    # JOB 3: https://hls.cci.in.here.com/job/hls_routing/job/psv/job/test/job/team-routing/job/server/job/psv-test-acceptance-hlp-xml-trafficdb-brf-linux-x86-gcc7.2/
    # COMMAND 3: ./bin/with-ld-preloads test-routing-acceptance --driver=server.hlp.xml --include=server.hlpANDTRAFFIC --uri=urn:nokia.com:routing:atdd:target:fastcgi --log=NONE --map-config=./map_config/map_format8_brf.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    # JOB 4: https://hls.cci.in.here.com/job/hls_routing/job/psv/job/test/job/team-routing/job/server/job/psv-test-acceptance-hlp-json-notraffic-brf-linux-x86-gcc7.2/
    # COMMAND 4: ./bin/test-routing-acceptance --driver=server.hlp.xml --exclude=TRAFFIC --include=server.hlp --log=NONE --map-config=./map_config/map_format8_brf.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    # JOB 5: https://hls.cci.in.here.com/job/hls_routing/job/psv/job/test/job/team-routing/job/server/job/psv-test-acceptance-hlp-xml-notraffic-brf-linux-x86-gcc7.2/
    # COMMAND 5: ./bin/test-routing-acceptance --driver=server.hlp.json --exclude=TRAFFIC --include=server.hlp --log=NONE --map-config=./map_config/map_format8_brf.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    # JOB 6 (NON-BLOCKING): https://hls.cci.in.here.com/job/hls_routing/job/psv/job/test/job/team-routing/job/brfc2/job/psv-test-acceptance-hlp-json-notraffic-hmc-brf-linux-x86-gcc7.2/
    # COMMAND 6: ./bin/test-routing-acceptance --driver=server.hlp.json --exclude=TRAFFIC --exclude=ESTIMATED-PT --include=server.hlp --log=NONE --map-config=./map_config/map/ols/routing/int.config --output xunit.xml --report=NONE ./share/here/routing/spec/international
    cd ./test_routing_component
    if [[ ${MAP_FORMAT} == "HLS_BRF" ]]; then
        MAP_CFG_FILE=map-config/map_format8_brf.config
    else
        # MAP_CFG_FILE=map-config/map/ols/routing/int.config
        MAP_CFG_FILE=map-config/map/ols/routing/hmc_plus_japan.config
    fi
    # DRIVER, FORMAT and INCLUDE should be specified in upstream job script
    if [[ ${DRIVER} == *"hlp"* ]] && [[ ${INCLUDE} == "TRAFFIC" ]]; then
        INCLUDE="${DRIVER}AND${INCLUDE} --uri=urn:nokia.com:routing:atdd:target:fastcgi"
        EXCLUDE=""
    else
        INCLUDE="${DRIVER}"
        EXCLUDE="--exclude=TRAFFIC"
    fi
    if [[ ${MAP_FORMAT} == "HLS_BRF2" ]]; then
        EXCLUDE="${EXCLUDE} --exclude=ESTIMATED-PT"
    fi
    if [[ ${FORMAT} == "xml" ]] || [[ ${FORMAT} == "json" ]]; then
        DRIVER="${DRIVER}.${FORMAT}"
    fi
    PYTHONPATH=lib/python LD_PRELOAD=libSegFault.so \
    python3 ./bin/test-routing-acceptance --driver=${DRIVER} \
        --log=NONE --map-config=/workspace/${MAP_CFG_FILE} \
        --output ../xunit.xml --include=${INCLUDE} ${EXCLUDE} --report=NONE \
        --map-path-prefix ${BRF_MAP_PATH} ./share/here/routing/spec/international;
    cd ..
    rebot --nostatusrc --outputdir outputs --xunit xunit/xunit.xml \
        --log NONE --report html/report.html xunit.xml;
    cp xunit.xml outputs/xunit/initial_xunit.xml
elif [[ ${MAP_FORMAT} == "F8" ]]; then
    # JOB: https://mos.cci.in.here.com/job/team-routing/job/client/job/test-acceptance-f8-base-diskcache/
    # COMMAND: installdir/map_config/copy_on_write_maps_wrapper.sh installdir/bin/with-ld-preloads test-routing-acceptance --driver=client:f8 --include=client:f8 --map-config=installdir/map_config/map_format8.config --xunit=xunit.xml installdir/share/here/routing/spec/international
    MAP_CFG_FILE=map-config/map_format8.config
    DRIVER="client:f8"
    PYTHONPATH=installdir/lib/python LD_LIBRARY_PATH=installdir/lib \
      installdir/bin/with-ld-preloads test-routing-acceptance --driver=${DRIVER} \
        --include=${DRIVER} --log=NONE--map-config=/workspace/${MAP_CFG_FILE} \
        --output xunit.xml --report=index --map-path-prefix ${MAP_PATH_PREFIX} \
        installdir/share/here/routing/spec/international/
elif [[ ${MAP_FORMAT} == "NDS_SPARTA" ]]; then
    # TODO: Move the following two commands to the top of file
    REGION=$(get_region ${LDM_REGION_DVN})
    MARKET=$(get_market ${REGION})
    # JOB: https://psv-corenav.cci.in.here.com/job/sparta/job/psv/job/test/job/team-routing/job/client/job/psv-acceptance-nds-eu-linux-x86-gcc5.4/
    # COMMAND: bin/with-ld-preloads test-routing-acceptance --driver=client:nds.eu --include=client:nds.eu --exclude=SPARTA:CRASH --exclude=SPARTA:FAIL-NDS2.5 --log=NONE --map-config=map_config/map/sparta/mapdb/eu.config --output xunit.xml --report=NONE share/here/routing/spec/international
    MAP_CFG_FILE=map_config/map/sparta/mapdb/${MARKET}.config
    DRIVER="client:nds.${MARKET}"
    PYTHONPATH=lib/python LD_LIBRARY_PATH=lib LD_PRELOAD=libSegFault.so \
      bin/with-ld-preloads test-routing-acceptance --driver=${DRIVER} \
      --exclude=SPARTA:CRASH --exclude=SPARTA:FAIL-NDS2.5 --include=${DRIVER} \
      --log=NONE --map-config=/workspace/${MAP_CFG_FILE} --output xunit.xml \
      --report=index --map-path-prefix ${MAP_PATH_PREFIX} \
      share/here/routing/spec/international/
else
    echo "ERROR: Undetermined/unsupported MAP_FORMAT=${MAP_FORMAT}"
    exit 1
fi
