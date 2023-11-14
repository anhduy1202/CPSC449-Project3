
enrollment_service: uvicorn enrollment_service.enrollment_service:app --port $PORT --reload
login_service_primary: ./bin/litefs mount -config etc/primary.yml
login_secondary: ./bin/litefs mount -config etc/secondary.yml
login_tertiary: ./bin/litefs mount -config etc/tertiary.yml
# login_service: uvicorn login_service.login_service:app --host 0.0.0.0 --port $PORT --reload
worker: echo ./etc/krakend.json | krakend run --config etc/krakend.json --port $PORT
dynamodb: java -Djava.library.path=./dynamodb_local_latest/DynamoDBLocal_lib -jar ./dynamodb_local_latest/DynamoDBLocal.jar -sharedDb --port $PORT

#use the below command to run foreman with 3 instances for enrollment service 
#foreman start -m enrollment_service=3,login_service_primary=1,login_secondary=1,login_tertiary=1,worker=1