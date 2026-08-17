"""
LUX — Main Entry Point

Starts the LUX application: either the web server (default)
or the CLI interface (with --cli flag).

Usage:
    python -m app.main              # Start web server
    python -m app.main --cli        # Start CLI interface
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import config


def setup_logging() -> None:
    """Configure structured logging."""
    level = getattr(logging, config.log_level.upper(), logging.INFO)

    handlers = [logging.StreamHandler(sys.stdout)]

    # File logging
    config.ensure_directories()
    try:
        file_handler = logging.FileHandler(config.log_path, encoding="utf-8")
        handlers.append(file_handler)
    except Exception:
        pass

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def run_server() -> None:
    """Start the FastAPI web server."""
    import uvicorn

    print()
    print("  +========================================+")
    print("  |         LUX - Local AI Assistant        |")
    print("  |     Powered by Microsoft Foundry Local  |")
    print("  +========================================+")
    print()

    uvicorn.run(
        "api.server:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
        reload=False,
    )


def run_cli() -> None:
    """Start the interactive CLI interface."""
    from core.agent import LuxAgent

    print()
    print("  +========================================+")
    print("  |         LUX - CLI Interface             |")
    print("  |     Powered by Microsoft Foundry Local  |")
    print("  +========================================+")
    print()

    agent = LuxAgent(config)
    print("Initializing LUX (loading models)...")
    timings = agent.initialize()

    stats = agent.get_knowledge_base_stats()
    print(f"\nKnowledge Base: {stats['documents']} documents, {stats['chunks']} chunks")
    print(f"Chat Model: {config.chat_model}")
    print(f"Embedding Model: {config.embedding_model}")
    print(f"Debug Mode: {'ON' if config.debug else 'OFF'}")
    print(f"\nInitialization: {timings.get('total', '?')}s")
    print("\nType your questions below. Type 'quit' to exit.\n")
    print("-" * 50)

    conversation_id = agent.create_conversation("CLI Session")

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!")
            break

        response = agent.handle(user_input, conversation_id)

        print(f"\n  LUX: {response.answer}")

        # Show sources if available
        if response.sources:
            print("\n  Sources:")
            for s in response.sources:
                entry = f"    - {s.get('filename', '?')}"
                if 'page' in s:
                    entry += f" — page {s['page']}"
                if 'score' in s:
                    entry += f" ({s['score']:.0%})"
                print(entry)

        # Show debug info
        if config.debug and response.debug:
            print("\n  [DEBUG]")
            debug = response.debug
            if 'query_type' in debug:
                print(f"    Query Type: {debug['query_type']}")
            if 'raw_results' in debug:
                print(f"    Results: {debug.get('raw_results', 0)} found → {debug.get('filtered_results', 0)} used")
            if 'generation_time' in debug:
                print(f"    Generation: {debug['generation_time']}s")
            if 'total_time' in debug:
                print(f"    Total: {debug['total_time']}s")

        print(f"\n  [{response.generation_time:.1f}s | {response.query_type}]")
        print("-" * 50)


def main() -> None:
    parser = argparse.ArgumentParser(description="LUX — Local AI Knowledge Assistant")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", type=str, default=None, help="Server host")
    parser.add_argument("--port", type=int, default=None, help="Server port")
    args = parser.parse_args()

    if args.debug:
        config.debug = True
        config.log_level = "DEBUG"

    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port

    setup_logging()

    if args.cli:
        run_cli()
    else:
        run_server()


if __name__ == "__main__":
    main()
