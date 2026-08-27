import argparse
import asyncio
import logging
from collections.abc import Sequence

from pipeline.config import PipelineSettings
from pipeline.ingest import ingest_city_owned_land
from pipeline.source_registry import load_source_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Land to Homes data pipeline")
    parser.add_argument("command", choices=("ingest", "score", "sources"))
    parser.add_argument(
        "--source", choices=("chicago_city_owned_land",), default="chicago_city_owned_land"
    )
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--page-size", type=int, default=10_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "sources":
        registry = load_source_registry()
        print(
            f"source registry {registry.version}: {len(registry.sources)} sources, "
            f"reviewed {registry.reviewed_at}"
        )
    elif args.command == "ingest":
        outcome = asyncio.run(
            ingest_city_owned_land(
                PipelineSettings(), publish=not args.no_publish, page_size=args.page_size
            )
        )
        print(
            f"ingest: run={outcome.run_id} rows={outcome.rows_written} "
            f"published={outcome.published}"
        )
    else:
        print("score: scaffold ready; scoring is a later milestone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
