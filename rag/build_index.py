"""RAG index builder: embeds underwriting policy docs and builds the FAISS index."""

import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT_DIR / "rag" / "policy.md"
INDEX_DIR = ROOT_DIR / "rag" / "index"
INDEX_PATH = INDEX_DIR / "policy.faiss"
CHUNKS_PATH = INDEX_DIR / "chunks.json"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def chunk_policy(text: str) -> list[str]:
    """Split the policy doc into one chunk per top-level (##) section, keeping the
    heading attached to its body so retrieval returns whole, meaningful sections."""
    sections = re.split(r"\n(?=## )", text.strip())
    return [section.strip() for section in sections if section.strip()]


def build_index():
    import faiss
    from sentence_transformers import SentenceTransformer

    text = POLICY_PATH.read_text(encoding="utf-8")
    chunks = chunk_policy(text)

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(chunks, convert_to_numpy=True).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    CHUNKS_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    return index, chunks


if __name__ == "__main__":
    _, built_chunks = build_index()
    print(f"Indexed {len(built_chunks)} policy sections into {INDEX_PATH}")
