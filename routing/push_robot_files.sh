#!/usr/bin/env bash
set -xe

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
exit_if_no_env_var TOPIC
set_env_var_if_not_set BOT_NAME "rmp-bot"
set_env_var_if_not_set BOT_EMAIL "${BOT_NAME}@here.com"


function push_review() {
    TOPIC_NAME=$1; COMMIT_MESSAGE=$2

    REVIEWERS=("ext-andrii.smirnov@here.com"\
               "ext-mykhailo.sakhnik@here.com")

    REVIEW=$(ssh gerrit.it.here.com -p 29418 \
                                    -l ${BOT_NAME} \
                                    gerrit query --current-patch-set \
                                                 --commit-message *"MITF-generated acceptance tests for"* \
             topic:${TOPIC_NAME} \
             project:${TESTS_GERRIT_PROJECT} \
             status:open \
             owner:${BOT_NAME} \
             branch:${TESTS_GERRIT_BRANCH} \
             limit:1)

    REF_ID=$(get_ref "${REVIEW}")

    cd main

    if [[ -n ${REF_ID} ]]; then
        git fetch origin ${REF_ID} && git checkout FETCH_HEAD
        CREATE_PATCHSET=true
    elif [[ -n ${commit_ref} ]]; then
        git fetch ssh://${BOT_NAME}@gerrit.it.here.com:29418/${TESTS_GERRIT_PROJECT} ${commit_ref} &&
        git checkout FETCH_HEAD
        CREATE_PATCHSET=false
    fi

    cd tools/test/share/spec && check_if_to_commit=$(git status)
    if [[ ${check_if_to_commit} != *"nothing to commit"* ]]; then
        git add lib international

        if [[ ${CREATE_PATCHSET} == true ]]; then
            find . -name 'dev_*' > /tmp/filesToRemove.txt && cat /tmp/filesToRemove.txt | xargs git rm
            git commit --amend --no-edit
            git push origin HEAD:refs/for/${TESTS_GERRIT_BRANCH} -o topic=${TOPIC_NAME}\
                                                                 -o reviewer=ext-andrii.smirnov@here.com\
                                                                 -o reviewer=ext-mykhailo.sakhnik@here.com\
                                                                 -o label=Code-Review+1\
                                                                 -o message=This_is_the_final_patchset_after_analysis!
        else
            git commit -m "${COMMIT_MESSAGE}"
            git push origin HEAD:refs/for/${TESTS_GERRIT_BRANCH} -o topic=${TOPIC_NAME}\
                                                                 -o reviewer=ext-andrii.smirnov@here.com\
                                                                 -o reviewer=ext-mykhailo.sakhnik@here.com\
                                                                 -o label=Code-Review-1\
                                                                 -o message=This_is_the_draft_patchset_which_will_be_overwritten!
        fi
    else
        echo "There is nothing to commit"
    fi
}

####################################################################

COMMIT_MESSAGE="MITF-generated acceptance tests for ${TOPIC}"

# TODO Appropriate tickets should be created
declare -A ISSUES=( ["NDS_SPARTA"]="SPARTA-33384" \
                    ["HLS_ROUTING"]="ROUTING-14380")

case ${TOPIC} in
    "FORMAT8_HLS_ROUTING_MAP_VERSION"* )
        push_review "${TOPIC}" "${ISSUES["HLS_ROUTING"]}: ${COMMIT_MESSAGE}"
        ;;
    * )
        echo "TOPIC=${TOPIC} is not supported"
        exit 1
        ;;
esac
