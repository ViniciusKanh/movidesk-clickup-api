import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import admin, health, webhooks
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Movidesk ClickUp API",
    description="API para criar tarefas no ClickUp a partir de tickets elegiveis do Movidesk.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(admin.router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
