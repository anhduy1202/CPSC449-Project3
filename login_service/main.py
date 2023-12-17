from fastapi import FastAPI
from login_service.routes import router

app = FastAPI()

app.include_router(router)
