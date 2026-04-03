# material-rag

RAG service para documentación de Material Design 3 y Material Web. Corre local, expone una API REST y un servidor MCP para que Claude Code consulte la documentación automáticamente al generar componentes UI.

---

## Qué hace

Indexa la documentación oficial de Material Design 3 y Material Web en una base de datos vectorial (ChromaDB) y la expone de dos formas:

- **API REST** — para consultas manuales desde el browser o cualquier cliente HTTP
- **MCP Server** — para que Claude Code consulte la documentación automáticamente al generar componentes

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Vector DB | ChromaDB (persistente en disco) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| Scraping | Playwright (headless Chromium) |
| API | FastAPI + Uvicorn |
| MCP | Python MCP SDK |

---

## Estructura

```
material-rag/
├── ingest.py        # Pipeline de scraping + embeddings → ChromaDB
├── server.py        # FastAPI REST API (puerto 8000)
├── mcp_server.py    # MCP Server para Claude Code
├── config.py        # Configuración centralizada
└── chroma_db/       # Base de datos vectorial (generada por ingest.py)
```

---

## Setup

### Requisitos

- Python 3.10+
- pip

### Instalación

```bash
# Clonar el repo
git clone https://github.com/AugustoFiorella/material-rag.git
cd material-rag

# Crear entorno virtual
python -m venv entorno-rag
entorno-rag\Scripts\activate   # Windows
# source entorno-rag/bin/activate  # Mac/Linux

# Instalar dependencias
pip install chromadb sentence-transformers fastapi uvicorn playwright requests beautifulsoup4 mcp

# Instalar browser para Playwright
python -m playwright install chromium
```

### Uso

**Paso 1 — Indexar la documentación** (una sola vez, o cuando querés actualizar)

```bash
python ingest.py
```

Esto scrapea las URLs configuradas, genera embeddings y persiste todo en `./chroma_db`.

**Paso 2 — Levantar el servidor REST**

```bash
python server.py
```

El servidor queda corriendo en `http://localhost:8000`. Docs interactivas en `http://localhost:8000/docs`.

**Paso 3 — Registrar el MCP en Claude Code** (una sola vez)

```bash
claude mcp add material-rag "C:\Python314\python.exe" "D:\ruta\al\repo\mcp_server.py" --scope user
```

Reemplazá los paths con los de tu máquina. Verificá con:

```bash
claude mcp list
```

---

## API REST

### GET /health

```bash
curl http://localhost:8000/health
# {"status": "ok", "chunks": 382}
```

### GET /query

```bash
curl "http://localhost:8000/query?q=card+elevated+filled+outlined&n=5"
```

### POST /query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"q": "button variants", "n": 5}'
```

Respuesta:

```json
[
  {
    "text": "...",
    "url": "https://m3.material.io/components/cards/guidelines",
    "title": "Guidelines",
    "section": "components",
    "score": 0.82
  }
]
```

---

## MCP — uso en Claude Code

Una vez registrado, Claude Code consulta la documentación automáticamente. También podés forzar una consulta:

```
Usá query_material_docs para buscar "navigation drawer behavior"
```

La tool `query_material_docs` devuelve los chunks más relevantes de la documentación indexada con su URL de origen y score de similitud.

---

## Documentación indexada

| Fuente | Secciones |
|--------|-----------|
| material-web.dev | button, checkbox, fab, icon-button, list, menu, dialog, chip, select, slider, switch, text-field |
| m3.material.io | cards (overview/guidelines/specs), all-buttons, dialogs, navigation-drawer, layout, typography |

Para agregar más URLs, editá la lista `URLS` en `ingest.py` y volvé a correr el pipeline.

---

## Notas

- El servidor REST debe estar corriendo para que el MCP funcione — el MCP server hace HTTP POST a `localhost:8000`.
- El scraping usa Playwright para páginas que renderizan con JavaScript.
- Los embeddings se calculan localmente, sin llamadas a APIs externas.
- ChromaDB persiste en `./chroma_db` — no hace falta re-indexar entre reinicios del servidor.
