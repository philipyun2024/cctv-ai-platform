import asyncio

from . import models  # noqa: F401
from .database import Base, engine


async def init_db() -> None:
    """Create the MVP database tables if they do not already exist."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
