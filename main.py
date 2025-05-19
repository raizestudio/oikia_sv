#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pythonjsonlogger import jsonlogger

import signals  # noqa
from config import Settings
from routers import core, users
from utils.db import Database

settings = Settings()
logger = logging.getLogger("uvicorn")
logger_auth = logging.getLogger("auth")

for folder in settings.required_dirs:
    os.makedirs(folder, exist_ok=True)

logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

log_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(Path(settings.log_file_path) / settings.log_file_name, maxBytes=settings.log_file_max_bytes, backupCount=settings.log_backup_count)
file_handler_auth = logging.handlers.RotatingFileHandler(Path(settings.log_file_path) / "auth.log", maxBytes=settings.log_file_max_bytes, backupCount=settings.log_backup_count)

formatter_str = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
log_handler.setFormatter(formatter_str)
file_handler.setFormatter(formatter)
file_handler_auth.setFormatter(formatter)
# ogging.getLogger("uvicorn.error").disabled = True
# logging.getLogger("uvicorn.access").disabled = True
logger.addHandler(log_handler)
logger.addHandler(file_handler)
logger_auth.addHandler(log_handler)
logger_auth.addHandler(file_handler_auth)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.include_router(core.router, tags=["Core"])
app.include_router(users.router, prefix="/users", tags=["Users"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

Database.init(app)


origins = [
    "http://localhost",
    "http://localhost:3000",
    f"http://{settings.app_api_host}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})
