#!/usr/bin/env python3
"""CLI Utility voor RAG Archief Zoeken en Beheer (ADR-006 & ADR-008).

Gebruik vanuit de terminal of Claude Code:
  python3 scripts/rag_cli.py search "zoekterm"
  python3 scripts/rag_cli.py status
  python3 scripts/rag_cli.py reindex [--purge] [--incremental]
"""

from __future__ import annotations

import argparse
import sys
import json

from scripts.orchestrator.rag_archive import archive_vectorstore


def main() -> None:
    parser = argparse.ArgumentParser(description="Blogpost Workflow RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search subcommando
    search_parser = subparsers.add_parser("search", help="Zoek in RAG archief")
    search_parser.add_argument("query", help="Zoekterm of passage")
    search_parser.add_argument("--top-k", type=int, default=5, help="Aantal resultaten (standaard 5)")

    # Status subcommando
    subparsers.add_parser("status", help="Toon RAG index status")

    # Reindex subcommando
    reindex_parser = subparsers.add_parser("reindex", help="Herindexeer posts/ map")
    reindex_parser.add_argument("--purge", action="store_true", help="Wis bestaande index en start opnieuw")
    reindex_parser.add_argument("--incremental", action="store_true", help="Indexeer alleen nieuwe posts")

    args = parser.parse_args()

    if args.command == "search":
        results = archive_vectorstore.search(args.query, top_k=args.top_k)
        print(json.dumps({"query": args.query, "count": len(results), "results": results}, indent=2, ensure_ascii=False))

    elif args.command == "status":
        print(json.dumps(archive_vectorstore.get_status(), indent=2, ensure_ascii=False))

    elif args.command == "reindex":
        print(f"Indexering gestart (purge={args.purge}, incremental={args.incremental})...")
        count = archive_vectorstore.index_all_posts(purge=args.purge, incremental=args.incremental)
        print(f"Indexering voltooid! Totaal geïndexeerde chunks: {count}")


if __name__ == "__main__":
    main()
