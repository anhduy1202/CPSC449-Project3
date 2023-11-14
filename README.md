# CPSC 449 Project 3


## Installation
run `sh ./bin/install.sh`.

## How to run
- Make sure you have the `dynamodb_local_latest/` folder at the root of the directory to run DynamoDB local, [Download it here](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)
- run `sh run.sh` to start the services
- run `sh ./bin/create-user-db.sh` to create user database
- run `sh ./bin/create-enrollment-db.sh` to create enrollment service database

## Serivce directories
- enrollment_service:  class, department, dropped, enrollment, instructor, student
- login_service: users   

## Service endpoint
- `http://localhost:5000/`: Enrollment endpoints
- `http://localhost:5400/`: User enpoints (register/login)
- `http://localhost:5500/`: DynamoDB Local
- `http://localhost:5400/api/login`: Verify user creds