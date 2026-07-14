"""MCP tool: FAISS-backed retrieval of underwriting policy documents for grounded reasoning."""

import json
import sys
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

# Lets this module resolve the top-level `rag` package regardless of the caller's
# working directory, same shim pattern used in mcp_server/server.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.build_index import CHUNKS_PATH, EMBEDDING_MODEL_NAME, INDEX_PATH, build_index

if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
    build_index()

_INDEX = faiss.read_index(str(INDEX_PATH))
_CHUNKS = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
_EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)


def policy_lookup(query: str, k: int = 3) -> list[str]:
    query_embedding = _EMBEDDING_MODEL.encode([query], convert_to_numpy=True).astype("float32")
    _, indices = _INDEX.search(query_embedding, k)
    return [_CHUNKS[i] for i in indices[0] if i != -1]


if __name__ == "__main__":
    sample_queries = [
        "what is the maximum DTI ratio",
        "what happens if an applicant has late payments",
        "what documentation is required",
    ]
    for sample_query in sample_queries:
        print(f"Query: {sample_query}")
        for chunk in policy_lookup(sample_query):
            print(f"  - {chunk.splitlines()[0]}")
        print()
