"""
MCP Server that exposes the Material Design RAG to Claude Code.
Runs as a stdio server — add it to Claude Code's MCP config.
"""

import json
import urllib.request
import urllib.error

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

RAG_URL = "http://localhost:8000/query"

app = Server("material-rag")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_material_docs",
            description=(
                "Consulta documentación de Material Design 3 y Material Web. "
                "Usar antes de generar cualquier componente UI para obtener guías "
                "de uso, props, variantes y patrones de UX correctos."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pregunta o término a buscar en la documentación",
                    },
                    "n": {
                        "type": "integer",
                        "description": "Cantidad de resultados a devolver (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    if name != "query_material_docs":
        raise ValueError(f"Unknown tool: {name}")

    query = arguments["query"]
    n = arguments.get("n", 5)

    payload = json.dumps({"q": query, "n": n}).encode()
    req = urllib.request.Request(
        RAG_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: no se pudo conectar al RAG server en {RAG_URL}.\n{e}",
            )
        ]

    if not results:
        return [
            types.TextContent(
                type="text",
                text="No se encontraron resultados para la consulta.",
            )
        ]

    lines = [f"## Resultados para: {query}\n"]
    for i, chunk in enumerate(results, 1):
        lines.append(
            f"### [{i}] {chunk['title']} — {chunk['section']}  (score: {chunk['score']})"
        )
        lines.append(f"Fuente: {chunk['url']}")
        lines.append("")
        lines.append(chunk["text"])
        lines.append("")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
