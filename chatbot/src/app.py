import logging
import sys
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
rag_system_site_packages = os.getenv("RAG_SYSTEM_SITE_PACKAGES")
if rag_system_site_packages and rag_system_site_packages not in sys.path:
    sys.path.append(rag_system_site_packages)

from src.config import settings
from src.services.sentiment_cache import sentiment_cache
from src.routes.health import router as health_router
from src.routes.chat import router as chat_router
from src.routes.sentiment import router as sentiment_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    sentiment_cache.load(settings.sentiment_data_path)
    yield


app = FastAPI(
    title="CryptoPulse Chatbot API",
    description="Cryptocurrency sentiment and knowledge chatbot.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(sentiment_router)
