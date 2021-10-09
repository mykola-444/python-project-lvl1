#!/bin/bash -ex

mkdir -p /workspace/out_folder/
export PYTHONPATH=$PYTHONPATH:./map-integration-testing/

if [[ ! -z ${PARTITIONS} ]] && [[ -z ${PARTITIONS_FILE} ]]; then
    echo ${PARTITIONS} > /workspace/part_data.txt
    python ./map-integration-testing/adapters/olp/run.py --partition_file /workspace/part_data.txt \
        --schema ./map-integration-testing/adapters/olp/sqlite/scripts/schema.json \
        --output /workspace/out_folder --hrn=${HRN} --version=${HMC_VERSION} --proc_number=${PROC_NUMBER} --chunk_size=${MAX_CHUNK_SIZE}

elif [[ -z ${PARTITIONS} ]] && [[ ! -z ${PARTITIONS_FILE} ]]; then
    cp ${PARTITIONS_FILE} /workspace/part_data.txt
    if [[ -z ${EXISTS} ]]; then
        python ./map-integration-testing/adapters/olp/run.py --partition_file ${PARTITIONS_FILE} \
            --schema ./map-integration-testing/adapters/olp/sqlite/scripts/schema.json \
            --output /workspace/out_folder --hrn=${HRN} --skip_indexes --proc_number=${PROC_NUMBER} --chunk_size=${MAX_CHUNK_SIZE}
        python3 ./map-integration-testing/adapters/olp/sqlite/create_indices.py /workspace/out_folder/HMC_common.db3
        python3 ./map-integration-testing/adapters/olp/sqlite/create_indices.py /workspace/out_folder/HMC-ADDITIONAL.db3
    else
        START_VERSION=$(</workspace/out_folder/version.txt)
        python ./map-integration-testing/adapters/olp/utils/last_updated_partitions.py --output /workspace/tmp_partition_ids.txt --hrn ${HRN} --versions ${START_VERSION}..${HMC_VERSION} --max_number 900000
        if [ -s /workspace/tmp_partition_ids.txt ]; then
            python ./map-integration-testing/adapters/olp/utils/partitions_intersection.py --base /workspace/part_data.txt --extension /workspace/tmp_partition_ids.txt --output /workspace/final.txt
            if [ -s /workspace/final.txt ]
            then
                python ./map-integration-testing/adapters/olp/run.py --partition_file /workspace/final.txt \
                    --schema ./map-integration-testing/adapters/olp/sqlite/scripts/schema.json \
                    --output /workspace/out_folder1 --hrn=${HRN} --skip_indexes  --proc_number=${PROC_NUMBER} --chunk_size=${MAX_CHUNK_SIZE}

                aws s3 cp ${BUCKET}/${DB_NAME}/HMC_common.db3 /workspace/out_folder/HMC_common.db3 --no-progress
                python ./map-integration-testing/ci/routing/acceptance/merge.py -m /workspace/out_folder/HMC_common.db3 -n /workspace/out_folder1/HMC_common.db3 -p /workspace/final.txt
                sqlite3 /workspace/out_folder/HMC_common.db3 'VACUUM;'
                aws s3 cp /workspace/out_folder/HMC_common.db3 ${BUCKET}/${DB_NAME}/HMC_common.db3 --no-progress
                # python3 ./map-integration-testing/adapters/olp/sqlite/create_indices.py /workspace/out_folder/HMC_common.db3
                rm /workspace/out_folder/HMC_common.db3 /workspace/out_folder1/HMC_common.db3
                aws s3 cp ${BUCKET}/${DB_NAME}/HMC-ADDITIONAL.db3 /workspace/out_folder/HMC-ADDITIONAL.db3 --no-progress
                python ./map-integration-testing/ci/routing/acceptance/merge.py -m /workspace/out_folder/HMC-ADDITIONAL.db3 -n /workspace/out_folder1/HMC-ADDITIONAL.db3 -p /workspace/final.txt
                sqlite3 /workspace/out_folder/HMC-ADDITIONAL.db3 'VACUUM;'
                aws s3 cp /workspace/out_folder/HMC-ADDITIONAL.db3 ${BUCKET}/${DB_NAME}/HMC-ADDITIONAL.db3 --no-progress
                rm /workspace/out_folder/HMC-ADDITIONAL.db3 /workspace/out_folder1/HMC-ADDITIONAL.db3
            fi
        fi
    fi
else
    echo "Specified combination of PARTITIONS and PARTITIONS_FILE parameters is not acceptable"
    exit 1
fi

ls -lah /workspace/out_folder/
