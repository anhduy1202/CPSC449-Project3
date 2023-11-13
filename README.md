# CPSC 449 Project 3


## Installation
run `sh ./bin/install.sh`.

## How to run
- run `sh run.sh` to start the services
- run `sh ./bin/create-user-db.sh` to create user database
- run `sh ./bin/create-enrollment-db.sh` to create enrollment service database

## Serivce directories
- enrollment_service:  class, department, dropped, enrollment, instructor, student
- login_service: users   

## Service endpoint
- `http://localhost:5000/`: Enrollment endpoints
- `http://localhost:5400/`: User enpoints (register/login)
- `http://localhost:5400/api/login`: Verify user creds