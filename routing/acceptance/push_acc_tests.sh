#!/usr/bin/env bash
set -xe

# Set mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
set_env_var_if_not_set BOT_NAME "rmp-bot"
set_env_var_if_not_set BOT_EMAIL "${BOT_NAME}@here.com"
set_env_var_if_not_set TESTS_GERRIT_PROJECT mos/routing/main
set_env_var_if_not_set TESTS_GERRIT_BRANCH master
export GIT_COMMITTER_NAME="${BOT_NAME}"
export GIT_COMMITTER_EMAIL="${BOT_EMAIL}"

function push_review() {
    COMMIT_MESSAGE=$1

    cd main/tools/test/share/spec && check_if_to_commit=$(git status)
    if [[ ${check_if_to_commit} != *"nothing to commit"* ]]; then
        gitdir=$(git rev-parse --git-dir); scp -p -P 29418 ${BOT_NAME}@gerrit.it.here.com:hooks/commit-msg ${gitdir}/hooks/
        git add lib international
        git commit -m "${COMMIT_MESSAGE}" --author "${BOT_NAME} <${BOT_EMAIL}>"
        git push origin HEAD:refs/for/${TESTS_GERRIT_BRANCH} -o reviewer=ext-andrii.smirnov@here.com \
                                                             -o reviewer=ext-mykhailo.sakhnik@here.com
    else
        echo "There is nothing to commit"
    fi
}

####################################################################

COMMIT_MESSAGE="MITF-generated acceptance tests for BRF2/gemini"
push_review "ROUTING-14380: ${COMMIT_MESSAGE}"
