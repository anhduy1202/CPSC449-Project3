#!/bin/bash

DB_LOCATION="./enrollment_service/database/database.db"

if test -f $DB_LOCATION; then
	echo "Error: Enrollment service database already exists."
	exit 1
fi

python3 ./enrollment_service/database/populate.py

if test -f $DB_LOCATION; then
	echo "Enrollment service database has been created."
fi