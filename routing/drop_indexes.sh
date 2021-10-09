#!/usr/bin/env bash
set -xe

DB=$1
INDEXES="$(echo "SELECT name FROM sqlite_master WHERE type == 'index'" | sqlite3 $DB)"
for i in $INDEXES; do
echo "DROP INDEX '$i';" | sqlite3 $DB
done

# echo "VACUUM;" | sqlite3 $DB
