set -xe

source ci/routing/common_functions.sh
exit_if_no_env_var TARGET_REGION  # int OR japan

source ci/routing/docker_acc.cfg
docker pull ${NAGINI_IMAGE}

echo "Executing OLP adapter"

# Since olp-pysdk docker image does not contain bldadmin user we have to change permissions:
mkdir -p ${HOME}/here/artifacts/
chmod -R a+rw ${HOME}/here/artifacts/

if [[  ${TARGET_REGION} == "int" ]]; then
    HRN="hrn:here:data:::rib-2"
    PARTITIONS=23592960
    # 23598595,23258631,23598603,23602189,23606531,23602200,23606534
elif [[  ${TARGET_REGION} == "japan" ]]; then
    # HRN="hrn:here:data:::here-map-content-japan-2"
    HRN="hrn:here:data::olp-here:hmc-world-services-2"
    # PARTITIONS=23592960
    # 24545080,24545081,24545084,24543412,24368148,24545062,24543711
else
    echo "Specified TARGET_REGION is invalid: ${TARGET_REGION}"
fi

# Use 'python3 ./get_japan_part_ids.py' to generate partitions file that cover the whole Japan
if [[ -f ${PARTITIONS_FILE} ]]; then
    unset PARTITIONS
    # cat ${PARTITIONS_FILE}
fi

docker run \
    -p 8888:8888 -p 25333:25333 -e JUPYTER=YES \
    -v ${HOME}/here/map-integration-testing/config/olp_creds/:/root/.here/ \
    --env=PARTITIONS=${PARTITIONS} --ulimit nofile=98304:98304 --env=HRN=${HRN} --volume=${HOME}/here/:/workspace \
    --env=PARTITIONS_FILE=${PARTITIONS_FILE} --workdir=/workspace ${NAGINI_IMAGE} \
    map-integration-testing/ci/routing/acceptance/run_olp_adapter.sh

mkdir -p ${HOME}/tmp/out_folder_${TARGET_REGION}
tar -C ${HOME}/tmp/out_folder_${TARGET_REGION} -zxvf ${HOME}/here/artifacts/hmc_based_sqlite.tgz
