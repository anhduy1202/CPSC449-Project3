enrollment_service: uvicorn enrollment_service.enrollment_service:app --host 0.0.0.0 --port $PORT --reload
login_service: uvicorn login_service.login_service:app --host 0.0.0.0 --port $PORT --reload
worker: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT 