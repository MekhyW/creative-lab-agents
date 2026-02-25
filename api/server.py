import asyncio
import json
import os
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHROMA_PATH    = os.getenv("CHROMA_PATH", "./chroma_db")
VAULT_PATH     = os.getenv("VAULT_PATH", "./my_vault")
MODELS_CONFIG  = os.path.join("config", "models.yaml")

app = FastAPI(title="Creative Lab Agents GUI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],)

_services_ready = False
_llm_service    = None
_memory_service = None
_trend_service  = None


def _init_services():
    global _services_ready, _llm_service, _memory_service, _trend_service
    if _services_ready:
        return True
    if not OPENAI_API_KEY:
        return False
    try:
        from services.llm import LLMService
        from services.memory_service import MemoryService
        from services.trend_service import TrendService
        model_map       = LLMService.load_config_from_yaml(MODELS_CONFIG)
        _llm_service    = LLMService(api_key=OPENAI_API_KEY, model_map=model_map)
        _memory_service = MemoryService(persist_directory=CHROMA_PATH, embedding_api_key=OPENAI_API_KEY)
        _trend_service  = TrendService(_llm_service)
        _services_ready = True
        return True
    except Exception as e:
        print(f"[server] service init failed: {e}")
        return False


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_generator(gen: AsyncGenerator) -> AsyncGenerator[str, None]:
    async for msg in gen:
        yield msg
    yield sse_event("done", {"message": "Stream complete"})


class IngestRequest(BaseModel):
    vault_path: str  = VAULT_PATH
    chroma_path: str = CHROMA_PATH

class ScoutRequest(BaseModel):
    theme:       str       = ""
    constraints: list[str] = []


@app.get("/api/status")
async def get_status():
    """Return environment/config health info."""
    return {
        "api_key_present":  bool(OPENAI_API_KEY),
        "vault_path":        VAULT_PATH,
        "chroma_path":       CHROMA_PATH,
        "models_config":     MODELS_CONFIG,
        "services_ready":    _services_ready,
    }


@app.get("/api/trends/raw")
async def get_raw_trends():
    """Return the mock raw trends (no LLM call)."""
    from services.trend_service import TrendService
    mock = TrendService(llm_service=None)
    trends = await mock.fetch_raw_trends()
    return {"trends": trends}


@app.post("/api/vault/ingest")
async def vault_ingest(req: IngestRequest):
    """
    Trigger vault ingest and stream log lines back via SSE.
    """
    async def generate() -> AsyncGenerator[str, None]:
        yield sse_event("log", {"message": f"Scanning vault at: {req.vault_path}"})
        await asyncio.sleep(0.05)
        try:
            import os as _os
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_community.document_loaders import TextLoader
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import Chroma
            if not OPENAI_API_KEY:
                yield sse_event("error", {"message": "OPENAI_API_KEY not set — cannot embed documents."})
                return
            documents = []
            for root, dirs, files in _os.walk(req.vault_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = _os.path.join(root, file)
                        try:
                            loader = TextLoader(file_path, encoding="utf-8")
                            docs   = loader.load()
                            documents.extend(docs)
                            yield sse_event("log", {"message": f"   ✓ Loaded: {_os.path.basename(file_path)}"})
                            await asyncio.sleep(0.02)
                        except Exception as e:
                            yield sse_event("warning", {"message": f"   ⚠ Skipped {file}: {e}"})
            if not documents:
                yield sse_event("warning", {"message": "No markdown files found in that path."})
                return
            yield sse_event("log", {"message": f"Found {len(documents)} file(s). Chunking…"})
            await asyncio.sleep(0.05)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100, separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", " "])
            chunks = splitter.split_documents(documents)
            yield sse_event("log", {"message": f"Split into {len(chunks)} chunks. Embedding…"})
            await asyncio.sleep(0.05)
            embeddings   = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vectorstore  = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=req.chroma_path)
            vectorstore.persist()
            yield sse_event("success", {"message": f"Vault indexed to {req.chroma_path}"})
        except Exception as e:
            yield sse_event("error", {"message": f"Ingest failed: {e}"})
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/scout")
async def scout_trends(req: ScoutRequest):
    """
    Trigger trend scouting and stream progress + results via SSE.
    Uses the mock TrendService (real LLM analysis requires API key).
    """
    async def generate() -> AsyncGenerator[str, None]:
        yield sse_event("log", {"message": "🔍 Starting trend scout…"})
        await asyncio.sleep(0.1)

        try:
            from services.trend_service import TrendService

            # Always fetch mock raw trends (no LLM required)
            mock_trend = TrendService(llm_service=None)
            raw = await mock_trend.fetch_raw_trends(theme=req.theme or None)

            yield sse_event("log", {"message": f"Retrieved {len(raw)} raw trend signals (mock data)"})
            await asyncio.sleep(0.1)

            if OPENAI_API_KEY and _services_ready and _trend_service:
                # Real LLM analysis
                yield sse_event("log", {"message": "Analyzing trends with LLM…"})
                identity_summary = req.theme or "A creative content creator."
                analyzed = await _trend_service.analyze_trends(identity_summary, raw)
                # Normalize: handle both list and dict responses
                if isinstance(analyzed, dict):
                    analyzed = analyzed.get("trends", list(analyzed.values())[0] if analyzed else [])
                for trend in analyzed:
                    yield sse_event("trend", {"trend": trend})
                    await asyncio.sleep(0.15)
                yield sse_event("log", {"message": f"Analysis complete — {len(analyzed)} trends scored."})
            else:
                # Mock-only path — emit raw trends directly
                if not OPENAI_API_KEY:
                    yield sse_event("warning", {"message": "No API key — showing mock trends without LLM scoring."})
                for t in raw:
                    trend_out = {
                        "topic":     t.get("topic", "Unknown"),
                        "score":     t.get("relevance", t.get("score", "N/A")),
                        "rationale": "Mock data — LLM analysis not available.",
                    }
                    yield sse_event("trend", {"trend": trend_out})
                    await asyncio.sleep(0.2)
                yield sse_event("log", {"message": f"Returned {len(raw)} mock trends."})

        except Exception as e:
            yield sse_event("error", {"message": f"Scout failed: {e}"})

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Serve GUI static files ─────────────────────────────────────────────────────
# Must be mounted LAST so API routes take priority.
gui_dir = os.path.join(os.path.dirname(__file__), "..", "gui")
if os.path.isdir(gui_dir):
    app.mount("/", StaticFiles(directory=gui_dir, html=True), name="gui")
