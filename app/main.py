from fastapi import FastAPI, status, HTTPException, Depends
from app.routers import auth, analyze
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.include_router(auth.router)

app.include_router(analyze.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: None):
    if user is None:
        raise HTTPException(401, detail=" No user")
    return {user}

