"""FDA Engine CLI entry point."""
from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(name="fda-engine", help="FDA Medical Device Registration Automation")
console = Console()


@app.callback()
def main():
    """FDA Engine - Automated 510(k) document generation and verification."""
    pass


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload"),
):
    """Start the FDA Engine API server."""
    import uvicorn
    console.print(f"[green]Starting FDA Engine on {host}:{port}[/green]")
    uvicorn.run(
        "fda_engine.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def init(
    folder: str = typer.Argument(..., help="Path to folder with technical documents"),
    template: str = typer.Option("510k", "--template", "-t"),
):
    """Initialize workspace from a technical documents folder."""
    import asyncio
    from pathlib import Path

    from fda_engine.core.config import FDAConfig
    from fda_engine.core.engine import FDAEngine
    from fda_engine.ingestion.workspace import index_workspace

    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.exists():
        console.print(f"[red]Folder not found: {folder_path}[/red]")
        raise typer.Exit(1)

    config = FDAConfig()
    config.fda_template = template

    async def _init():
        engine = FDAEngine(config)
        await engine.initialize()
        count = await index_workspace(folder_path, config)
        params = await engine.extract_parameters(
            "\n\n".join(
                f.read_text(encoding="utf-8", errors="ignore")
                for f in folder_path.rglob("*.md")
            )
        )
        console.print(f"[green]Indexed {count} documents[/green]")
        console.print(f"[green]Extracted {len(params)} parameters[/green]")
        for k, v in params.items():
            console.print(f"  {k}: {v.get('value', 'N/A')}")

    asyncio.run(_init())


@app.command()
def tree():
    """Display the FDA document tree."""
    from fda_engine.templates.fda_tree import build_510k_tree

    root = build_510k_tree()
    _print_tree(root, "")


def _print_node(node, prefix: str, is_last: bool = True):
    """Print a single tree node."""
    connector = "\\-- " if is_last else "|-- "
    status = "[x]" if not node.required else "[o]"
    console.print(f"{prefix}{connector}{status} {node.title} ({node.node_id})")


def _print_tree(node, prefix: str):
    """Print the document tree."""
    console.print(f"{prefix}[{node.node_id}] {node.title}")
    for i, child in enumerate(node.children):
        is_last = i == len(node.children) - 1
        child_prefix = prefix + ("    " if is_last else "|   ")
        _print_node(child, child_prefix, is_last)
        if child.children:
            _print_tree(child, child_prefix)


if __name__ == "__main__":
    app()
