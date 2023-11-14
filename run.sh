#!/bin/sh

foreman start -m enrollment_service=3,login_service_primary=1,login_secondary=1,login_tertiary=1,worker=1,dynamodb=1