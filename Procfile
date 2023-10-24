# login_primary:        ./bin/litefs mount -config enrollment_service/database/var/primary.yml
# login_secondary:      ./bin/litefs mount -config enrollment_service/database/var/secondary.yml
# enrollment_primary:   ./bin/litefs mount -config login_service/database/var/primary.yml
# enrollment_secondary: ./bin/litefs mount -config login_service/database/var/secondary.yml


enrollment_service_1: uvicorn enrollment_service.enrollment_service:app --host 0.0.0.0 --port $PORT --reload
login_service: uvicorn login_service.login_service:app --host 0.0.0.0 --port $PORT --reload
worker: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT
enrollment_service_2: uvicorn enrollment_service.enrollment_service:app --host 0.0.0.0 --port $PORT --reload
enrollment_service_3: uvicorn enrollment_service.enrollment_service:app --host 0.0.0.0 --port $PORT --reload