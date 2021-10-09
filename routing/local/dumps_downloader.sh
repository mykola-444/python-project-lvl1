#!/bin/bash -xe

declare -a dvn_list=("APAC_19145" "AU_20107" "EEU_20106" "IND_20105" "MEA_20106" "NA_20104" "SAM_20103" "TWN_20107" "WEU_20106")


for dvn in ${dvn_list[@]} ; do
    aws s3 cp --profile routing-mapdata-rd s3://mitf-artifacts/mitf/acc/${dvn}/tests.tgz ./${dvn}.tgz
    mkdir ${dvn} && tar zxf ./${dvn}.tgz -C ${dvn}
done
