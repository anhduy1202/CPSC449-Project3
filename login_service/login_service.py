from fastapi import FastAPI
from login_service.routes import router 

app = FastAPI()

app.include_router(router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
