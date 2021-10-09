if [ -z $(eval echo \${MITF_PATH}) ]; then
    echo "MITF_PATH is not set"
    exit 1
fi

keywords=$1
test_cases=$2
index=$3
current=$(pwd)
cd $test_cases
git checkout $test_cases
cd $current
find $keywords -name "*_$index.robot" -print0 | while read -d $'\0' file
do
    python3 ${MITF_PATH}/ci/routing/acceptance/acceptance_tests_updater_prod.py --lib $file  --sources $test_cases
done



