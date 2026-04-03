"""
Ingest Material Design 3 and Material Web docs into ChromaDB.
Uses Playwright (headless Chromium) to render JS-heavy pages.
"""

import asyncio
import hashlib
import re

import chromadb
from playwright.async_api import async_playwright
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "material_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

URLS = [
    "https://material-web.dev/components/button/",
    "https://material-web.dev/components/checkbox/",
    "https://material-web.dev/components/card/",
    "https://material-web.dev/components/fab/",
    "https://material-web.dev/components/icon-button/",
    "https://material-web.dev/components/list/",
    "https://material-web.dev/components/menu/",
    "https://material-web.dev/components/dialog/",
    "https://material-web.dev/components/chip/",
    "https://material-web.dev/components/select/",
    "https://material-web.dev/components/slider/",
    "https://material-web.dev/components/switch/",
    "https://material-web.dev/components/text-field/",
    "https://material-web.dev/components/navigation-drawer/",
    "https://m3.material.io/components/all-buttons",
    "https://m3.material.io/components/cards/overview",
    "https://m3.material.io/components/cards/guidelines",
    "https://m3.material.io/components/cards/specs",
    "https://m3.material.io/components/dialogs/overview",
    "https://m3.material.io/components/navigation-drawer/overview",
    "https://m3.material.io/foundations/layout/understanding-layout",
    "https://m3.material.io/styles/color/overview",
    "https://m3.material.io/styles/typography/overview",
]

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

# ---------------------------------------------------------------------------
# ID helper
# ---------------------------------------------------------------------------

def make_id(url: str, index: int) -> str:
    prefix = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{prefix}_{index}"

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def ingest() -> None:
    print("=" * 60)
    print("Material RAG — ingestion pipeline (Playwright)")
    print("=" * 60)

    print(f"\n[1/3] Initialising ChromaDB at {CHROMA_DIR} ...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"      Collection '{COLLECTION_NAME}' ready.")

    print(f"\n[2/3] Loading embedding model '{EMBEDDING_MODEL}' ...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("      Model loaded.")

    print(f"\n[3/3] Scraping {len(URLS)} URL(s) with Playwright ...\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, url in enumerate(URLS, 1):
            print(f"  [{i}/{len(URLS)}] {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=30_000)
            except Exception as e:
                print(f"    [WARN] goto failed: {e}")
                continue

            await asyncio.sleep(3)

            try:
                text = await page.inner_text("body")
            except Exception as e:
                print(f"    [WARN] inner_text failed: {e}")
                continue

            # Collapse whitespace
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            if not text:
                print("    [SKIP] No text extracted.")
                continue

            chunks = chunk_text(text)
            print(f"    → {len(chunks)} chunks  ({len(text)} chars)")

            embeddings = model.encode(chunks, show_progress_bar=False).tolist()

            # Derive section from URL path
            parts = [p for p in url.replace("https://", "").split("/") if p]
            section = parts[1] if len(parts) > 1 else parts[0]
            title = parts[-1].replace("-", " ").title() if parts else url

            collection.upsert(
                ids=[make_id(url, j) for j in range(len(chunks))],
                documents=chunks,
                embeddings=embeddings,
                metadatas=[
                    {"url": url, "title": title, "section": section, "chunk_index": j}
                    for j in range(len(chunks))
                ],
            )

        await browser.close()

    total = collection.count()
    print(f"\n{'=' * 60}")
    print(f"Done. Total chunks in ChromaDB: {total}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(ingest())
