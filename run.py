from fastapi import FastAPI
from src.endpoints.hello.route import hello_router
from src.endpoints.docker.route import docker_router
import uvicorn

app = FastAPI()

app.include_router(hello_router)
app.include_router(docker_router)


if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=3943, reload=True)
