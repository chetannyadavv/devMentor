import asyncio

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis_listener import listen_for_updates
from app.routers.auth import router as auth_router
from app.routers.problems import router as problems_router
from app.routers.submissions import router as submissions_router
from app.routers.ws import router as ws_router

app = FastAPI(title="DevMentor API")

# The frontend dev server runs on a different origin (localhost:5173)
# than the api (localhost:8000) -- browsers enforce CORS for this, tools
# like curl never did, which is why this was never needed until now.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(submissions_router)
app.include_router(ws_router)


@app.on_event("startup")
async def start_redis_listener():
    # IMPORTANT: asyncio.create_task() alone doesn't keep the task
    # alive -- the event loop only holds a weak reference. Without
    # storing this somewhere real, the task can be (and was) garbage
    # collected almost immediately after startup.
    app.state.redis_listener_task = asyncio.create_task(listen_for_updates())


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    # Deliberately not just "the process is up" -- actually round-trips
    # to Postgres, so this endpoint is a real signal the api container
    # can reach the database, not just that uvicorn started.
    result = await db.execute(text("SELECT 1"))
    db_ok = result.scalar() == 1
    return {"status": "ok", "database_connected": db_ok}
