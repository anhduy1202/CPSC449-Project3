from fastapi import FastAPI
from enrollment_service.routes import router

app = FastAPI()

app.include_router(router)


