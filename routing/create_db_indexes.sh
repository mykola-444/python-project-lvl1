#!/usr/bin/env bash
set -xe

LDM_DB_PATH=$1; REGION=$2

source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var LDM_DB_PATH
exit_if_no_env_var REGION

if [[ ! -f ${LDM_DB_PATH}/${REGION}_common.db3 ]]; then
    ln -s ${LDM_DB_PATH}/${REGION}.db3 ${LDM_DB_PATH}/${REGION}_common.db3
fi

for db_file in "${LDM_DB_PATH}"/*.db3; do
    if [[ "${db_file}" =~ "_common.db3" ]]; then
        sqlite3 ${LDM_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_LINK_FN ON LDM_LINK(FROM_NODE_ID)" || true
        sqlite3 ${LDM_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_FN_TN ON LDM_LINK(FROM_NODE_ID, TO_NODE_ID)" || true
        sqlite3 ${LDM_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_X_Y_PID ON LDM_JUNCTION(X, Y, PARTITION_ID)" || true
        sqlite3 ${LDM_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_LINKNAMEID_LINKID ON LDM_LINK_TO_NAME(LINK_NAME_ID, LINK_ID)" || true
        sqlite3 ${LDM_DB_PATH}/${REGION}_common.db3 "CREATE INDEX IF NOT EXISTS IDX_LDM_LINK_ID_EXT ON LDMV_LINK_ATTRIBUTE_EXTENDED(LINK_ID)" || true
    elif [[ ! "${db_file}" =~ "-language_mappings.db3" ]]; then
        sqlite3 ${db_file} "CREATE INDEX IF NOT EXISTS IDX_LI ON LDM_TRUCK_RESTRICTION(LINK_ID)" || true
    else
        continue
    fi
done
