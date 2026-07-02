from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.config import settings
from app.core.security import hash_password
from app.db.models import Base, User
from app.db.session import engine, SessionLocal
from app.services.storage import ensure_bucket


async def seed_admin() -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@local"))
        if result.scalar_one_or_none():
            return
        db.add(
            User(
                email="admin@local",
                full_name="System Administrator",
                hashed_password=hash_password("admin123!"),
                role="admin",
            )
        )
        await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ensure_bucket()
    await seed_admin()
    yield


app = FastAPI(title="Enterprise RAG", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
