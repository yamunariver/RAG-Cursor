#!/usr/bin/env python3
"""Create knowledge bases that mirror the knowledge/ folder layout."""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Base, KnowledgeBase, User
from app.db.session import SessionLocal, engine
from app.services.qdrant_client import ensure_collection

KNOWLEDGE_ROOT = Path("/data/knowledge")
FALLBACK_ROOT = Path(__file__).resolve().parents[1] / "knowledge"


async def main() -> None:
    root = KNOWLEDGE_ROOT if KNOWLEDGE_ROOT.exists() else FALLBACK_ROOT
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        admin = await db.execute(select(User).where(User.email == "admin@local"))
        if admin.scalar_one_or_none() is None:
            db.add(
                User(
                    email="admin@local",
                    full_name="System Administrator",
                    hashed_password=hash_password("admin123!"),
                    role="admin",
                )
            )
            await db.commit()

        for folder in sorted(p for p in root.iterdir() if p.is_dir()):
            slug = folder.name.lower().replace(" ", "-")
            collection = f"kb_{slug.replace('-', '_')}"
            existing = await db.execute(select(KnowledgeBase).where(KnowledgeBase.slug == slug))
            if existing.scalar_one_or_none():
                continue

            ensure_collection(collection)
            db.add(
                KnowledgeBase(
                    id=uuid.uuid4(),
                    name=folder.name,
                    slug=slug,
                    department=folder.name,
                    description=f"Documents from knowledge/{folder.name}",
                    qdrant_collection=collection,
                )
            )
        await db.commit()
        print(f"Knowledge bases synced from {root}")


if __name__ == "__main__":
    asyncio.run(main())
