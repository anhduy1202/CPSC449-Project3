#!/bin/sh

rm -rf var/
mkdir var
mkdir var/primary
mkdir var/primary/fuse
mkdir var/primary/dat

sh bin/create-user-db.sh

foreman start -m enrollment_service=3,login_service_primary=1,login_secondary=1,login_tertiary=1,worker=1,dynamodb=1,enrollment_notification_service=1