"""Run: python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000."""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import ai
from .sources import SOURCE_INFO, SourceService, interpret, utc_now

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)
VERSION = "0.1.0"
ALLOWED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:8080", "http://localhost:8080"]
DOC_FILES = {"README.md", "HELP.md", "COMMERCIAL_LICENSING.md", "THIRD_PARTY_NOTICES.md", "REI_RESEARCH_EXPLORER_PROMPT.md", "LICENSE"}


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=250)
    mode: Literal["auto", "topic", "gene", "region"] = "auto"
    sources: List[Literal["pubmed", "ensembl", "gwas"]] = Field(default_factory=lambda: ["pubmed", "ensembl", "gwas"], min_length=1, max_length=3)
    limit: int = Field(default=10, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def valid_query(cls, value: str) -> str:
        if not value.strip() or any(ord(ch) < 32 for ch in value):
            raise ValueError("Enter a nonempty query without control characters.")
        return value.strip()

    @field_validator("sources")
    @classmethod
    def unique_sources(cls, value: List[str]) -> List[str]:
        if len(set(value)) != len(value):
            raise ValueError("Select each source only once.")
        return value


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0, pool=8.0), follow_redirects=False,
                                 headers={"User-Agent": "REIResearchExplorer/0.1 (local fellowship research prototype)"},
                                 limits=httpx.Limits(max_connections=12, max_keepalive_connections=6)) as client:
        application.state.sources = SourceService(client, os.getenv("NCBI_EMAIL", ""))
        application.state.search_slots = asyncio.Semaphore(6)
        application.state.ai_slots = asyncio.Semaphore(2)
        yield


app = FastAPI(title="REI Research Explorer", version=VERSION, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], allow_credentials=False)


@app.middleware("http")
async def request_limits(request: Request, call_next):
    if request.method == "POST":
        origin = request.headers.get("origin")
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse({"detail": "Open the local application to make API requests."}, status_code=403)
        if "application/json" not in request.headers.get("content-type", "").lower():
            return JSONResponse({"detail": "API requests must use application/json."}, status_code=415)
        try:
            declared_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Invalid request length."}, status_code=400)
        if declared_length > 120000 or len(await request.body()) > 120000:
            return JSONResponse({"detail": "Request too large. Select fewer evidence records."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Do not echo input values, which may contain accidentally pasted credentials.
    errors = [{"field": ".".join(str(v) for v in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse({"detail": "Check the request fields.", "errors": errors}, status_code=422)


@app.get("/api/health")
async def health():
    return {"version": VERSION, "ai": {"configured": ai.configured(), "model": ai.model_name()}, "sources": SOURCE_INFO}


@app.post("/api/search")
async def search(request: SearchRequest):
    try:
        interpretation = interpret(request.query, request.mode)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    async with app.state.search_slots:
        responses = await asyncio.gather(*(app.state.sources.search(source, interpretation, request.limit) for source in request.sources))
    return {"query": request.query, "interpretation": interpretation,
            "records": [record for result in responses for record in result["records"]],
            "coverage": [result["coverage"] for result in responses], "retrieved_at": utc_now(), "demo": False}


@app.post("/api/ai")
async def ai_request(request: ai.AIRequest):
    async with app.state.ai_slots:
        return await ai.generate(request)


@app.post("/api/ai/check")
@app.get("/api/ai/check")
async def ai_check():
    return await ai.check_connection()


@app.get("/")
@app.get("/index.html")
async def frontend():
    path = ROOT / "index.html"
    if not path.is_file():
        raise HTTPException(404, "Frontend is not installed.")
    return FileResponse(path, media_type="text/html")


@app.get("/api/docs/{filename}")
async def docs(filename: str):
    if filename not in DOC_FILES or not (ROOT / filename).is_file():
        raise HTTPException(404, "Documentation not found.")
    return FileResponse(ROOT / filename, media_type="text/markdown; charset=utf-8")


@app.get("/licenses/{filename}")
async def license_file(filename: str):
    directory = ROOT / "licenses"
    path = (directory / filename).resolve()
    if path.parent != directory.resolve() or not filename.endswith(".txt") or not path.is_file():
        raise HTTPException(404, "License text not found.")
    return FileResponse(path, media_type="text/plain; charset=utf-8")


@app.get("/{filename}")
async def document_link(filename: str):
    # Relative documentation links resolve without exposing the project directory.
    return await docs(filename)
