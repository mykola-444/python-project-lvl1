#!/usr/bin/env bash
set -xe

# Check mandatory variables
source map-integration-testing/ci/routing/common_functions.sh
set -a

mkdir -p /home/gemini/share/here/routing/
mv build/share/here/routing/spec /home/gemini/share/here/routing/spec_orig

yum install -y patch

# Patch gemini source code:
cd build
patch -p0 <<'EOF'
--- lib64/here/python3/here/routing/drivers/server/ols/json/response.py 2020-04-30 10:25:14.000000000 +0300
+++ lib64/here/python3/here/routing/drivers/server/ols/json/response.py.patched 2020-04-30 14:13:39.000000000 +0300
@@ -11,9 +11,9 @@
     def create(cls, response):
         raw = response.json()
         # Enable to log response
-        # import logging
-        # import json
-        # logging.info(json.dumps(raw, indent=4))
+        import logging
+        import json
+        logging.info(json.dumps(raw, indent=4))
         # if response results in notice with 200 status code
         if len(raw.get('routes', [])) == 0 and raw.get('notices') is not None:
             return Catalog.get_response_class('Error')(convert_ols_error(raw['notices'][0]))
EOF
cd ..

export LD_LIBRARY_PATH=$(pwd)/build/lib64/here
build/bin/trafficdb --cfg /workspace/trafficdb.cfg -p
sleep 5
build/bin/gemini --brf ${BRF} --l10n build/share/here/routing/l10n --developer \
    --enable-traffic --traffic_packages_path build/share/here/traffic &
sleep 5

# 2019-11-28T18:00:05.453370+00:00 - INFO - Started server: 0.0.0.0:8080
build/bin/test-routing-acceptance --driver server.ols.json --include server.ols \
    --uri http://localhost:8080 /workspace/robot_specs \
    --no-map-config --http-header "x-sentry-businessfeatures=ols-pc1-route-invoke"
rebot --nostatusrc --outputdir outputs --xunit xunit/xunit.xml \
    --log NONE --report html/report.html output.xml
cp output.xml outputs/xunit/initial_xunit.xml
