# login_primary:        ./bin/litefs mount -config enrollment_service/database/var/primary.yml
# login_secondary:      ./bin/litefs mount -config enrollment_service/database/var/secondary.yml
# enrollment_primary:   ./bin/litefs mount -config login_service/database/var/primary.yml
# enrollment_secondary: ./bin/litefs mount -config login_service/database/var/secondary.yml


enrollment_service: uvicorn enrollment_service.enrollment_service:app --host 0.0.0.0 --port $PORT --reload
login_service: uvicorn login_service.login_service:app --host 0.0.0.0 --port $PORT --reload
worker: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT


#use the below command to run foreman with 3 instances for enrollment service 
#foreman start -m enrollment_service=3,login_service=1,worker=1