from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import httpx

MODE = os.getenv("MODE", "local")  # local | api

app = FastAPI(title="Local ML API Server")

embedder = None
reranker = None

if MODE == "local":
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from sentence_transformers import SentenceTransformer, CrossEncoder
    print("🔄 正在加载向量模型 (BAAI/bge-m3) ...")
    embedder = SentenceTransformer("BAAI/bge-m3")
    print("🔄 正在加载重排模型 (BAAI/bge-reranker-v2-m3) ...")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)
    print("✅ 本地模型加载完毕！")
else:
    API_BASE = os.getenv("API_BASE", "https://api.openai.com/v1")
    API_KEY = os.getenv("API_KEY", "")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    RERANK_MODEL = os.getenv("RERANK_MODEL", "")
    print(f"✅ API 模式启动！API_BASE={API_BASE}, EMBED_MODEL={EMBED_MODEL}")

class EmbedRequest(BaseModel):
    text: str

class RerankRequest(BaseModel):
    query: str
    documents: list[str]

@app.post("/api/embeddings")
async def get_embedding(req: EmbedRequest):
    if MODE == "local":
        vector = embedder.encode(req.text).tolist()
        return {"embedding": vector}
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/embeddings",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": EMBED_MODEL, "input": req.text}
            )
            return resp.json()

@app.post("/api/rerank")
async def get_rerank(req: RerankRequest):
    if MODE == "local":
        pairs = [[req.query, doc] for doc in req.documents]
        scores = reranker.predict(pairs).tolist()
        return {"scores": scores}
    else:
        if not RERANK_MODEL:
            return {"error": "rerank model not configured", "scores": []}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/rerank",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": RERANK_MODEL, "query": req.query, "documents": req.documents}
            )
            return resp.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
