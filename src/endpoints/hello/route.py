from fastapi import APIRouter

hello_router = APIRouter()


@hello_router.get("/")
def hello():
    return {"message": "Hello, World!"}
