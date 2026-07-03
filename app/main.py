from fastapi import FastAPI, status, HTTPException, Depends
import app.routers.auth as auth
app = FastAPI()
app.include_router(auth.router)


@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: None):
    if user is None:
        raise HTTPException(401, detail=" No user")
    return {user}

