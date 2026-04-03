from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"

# ChromaDB
COLLECTION_NAME = "material_docs"

# Embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking
CHUNK_SIZE = 500      # tokens (approx chars / 4)
CHUNK_OVERLAP = 50

# URLs to scrape (seed pages)
SEED_URLS = [
    "https://material-web.dev/components/",
    "https://m3.material.io/components",
    "https://m3.material.io/foundations",
    "https://m3.material.io/styles",
]

# Domain allowlist for link following (one level deep)
ALLOWED_DOMAINS = [
    "material-web.dev",
    "m3.material.io",
]

# HTTP request settings
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; material-rag-ingest/1.0; "
        "+https://github.com/local/material-rag)"
    )
}
