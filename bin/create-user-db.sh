#!/bin/bash

SCHEMA="./share/user_schema.sql"
DB_LOCATION="./var/primary/fuse/database.db"
FUSE_DIRECTORY="./var/primary/fuse/"

if test -f $DB_LOCATION; then
	echo "Error: User database already exists."
	exit 1
fi

if ! test -f $SCHEMA; then
	echo "Error - File Not Found: ${SCHEMA}"
	exit 1
fi

if ! test -d $FUSE_DIRECTORY; then
	echo "Error - Directory Not Found: ${FUSE_DIRECTORY}"
	exit 1
fi

sqlite3 $DB_LOCATION < $SCHEMA

if test -f $DB_LOCATION; then
	echo "User database has been created."
fi