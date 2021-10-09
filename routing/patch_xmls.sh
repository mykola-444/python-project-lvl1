#!/bin/bash -ex

source map-integration-testing/ci/routing/common_functions.sh

function verify_env_vars {
    exit_if_no_env_var PATH_TO_XMLS
    exit_if_no_env_var TOPIC
}

if [[ ${TOPIC} == "FORMAT8_HLS_ROUTING_MAP_VERSION"* ]] || \
   [[ ${TOPIC} == *"NDS"*"SPARTA_"*"_MAP_VERSION"* ]]; then
    # Do the following change:
    #-        <route_options route_type="FASTEST" routing_mode="CAR">
    #-            <avoid_seasonal_closures/>
    #-        </route_options>
    #+        <route_options route_type="FASTEST" routing_mode="CAR">
    #+            <seasonal_closure_mode value="CLOSED"/>
    #+        </route_options>
    #
    # or
    #+        <route_options route_type="FASTEST" routing_mode="CAR">
    #+            <seasonal_closure_mode value="TIME_AWARE"/>
    #+        </route_options>
    find ${PATH_TO_XMLS} -type f \
                         -name "seasonal_closure_is_avoided_in_non_time_aware_mode_with_option_specified*.xml" \
                         -exec sed -i 's/avoid_seasonal_closures/seasonal_closure_mode value="CLOSED"/' {} +
    # There are issues with time_aware tests cases: see ROUTING-11594
    #
    #find $PATH_TO_XMLS -type f -name "seasonal_closure_is_avoided_with_option_specified_outside_restricted_time*.xml" -exec sed -i 's/avoid_seasonal_closures/seasonal_closure_mode value="TIME_AWARE"/' {} +
    #find $PATH_TO_XMLS -type f -name "seasonal_closure_is_avoided_with_option_specified_within_restricted_time*.xml" -exec sed -i 's/avoid_seasonal_closures/seasonal_closure_mode value="TIME_AWARE"/' {} +
    # so we are just removing them for hls
    find ${PATH_TO_XMLS} -type f \
                         -name "seasonal_closure_is_avoided_with_option_specified_outside_restricted_time*.xml" \
                         -exec rm {} +
    find ${PATH_TO_XMLS} -type f \
                         -name "seasonal_closure_is_avoided_with_option_specified_within_restricted_time*.xml" \
                         -exec rm {} +
fi

if [[ ${TOPIC} == "FORMAT8_HLS_ROUTING_MAP_VERSION"* ]]; then
    # There are issues with time_aware tests cases: see MITF-872
    # Do the following change:
    #-        <route_info error_code="NGEO_ERROR_ROUTE_VIOLATES_OPTIONS" violated_option="VIOLATED_BLOCKED_ROADS"/>
    #+        <route_info error_code="NGEO_ERROR_ROUTE_VIOLATES_OPTIONS" violated_option="VIOLATED_TIME_DEPENDENT_RESTRICTION"/>
    find ${PATH_TO_XMLS} -type f \
                         -name "tta_detail_blocked_road_is_set_when_road_is_blocked_by_time_restriction*.xml" \
                         -exec sed -i 's/VIOLATED_BLOCKED_ROADS/VIOLATED_TIME_DEPENDENT_RESTRICTION/' {} +
    find ${PATH_TO_XMLS} -type f \
                         -name "tta_detail_respects_timezone_and_daylight_saving_time_positive*.xml" \
                         -exec sed -i 's/VIOLATED_BLOCKED_ROADS/VIOLATED_TIME_DEPENDENT_RESTRICTION/' {} +
fi
