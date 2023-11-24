# CPSC 449 Project 3
> Titan Online API Endpoints with Krakend (JWT, Load Balancer, API Gateway), DynamoDB, Redis 


## Installation
run `sh ./bin/install.sh`.

## How to run
- Make sure you have the `dynamodb_local_latest/` folder at the root of the directory to run DynamoDB local, [Download it here](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)
- [Download DynamoDB NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.settingup.html)
- Import [`TitanOnline.json`](./TitanOnline.json) to NoSQL Workbench to seed the data to DynamoDB Local
- run `sh run.sh` to start the services
- run `sh ./bin/create-user-db.sh` to create user database

## Serivce directories
- enrollment_service: Contains all endpoints related to enrollment service (show class, enroll student,...)
- login_service: Contains endpoints related to register, login user for jwt   

## Service endpoint
- `http://localhost:5000/`: Enrollment endpoints
- `http://localhost:5400/`: User enpoints (register/login)
- `http://localhost:5500/`: DynamoDB Local
- `http://localhost:5400/api/login`: Verify user creds