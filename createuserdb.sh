#!/bin/sh

if test -f ./share/user_schema.sql; then
	echo "Create User Database"
	mkdir -p ./var/primary/fuse/
	sqlite3 ./var/primary/fuse/database.db < ./share/user_schema.sql
fi