import argparse
from collections.abc import Sequence

from pipeline.source_registry import load_source_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Land to Homes data pipeline")
    parser.add_argument("command", choices=("ingest", "score", "sources"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "sources":
        registry = load_source_registry()
        print(
            f"source registry {registry.version}: {len(registry.sources)} sources, "
            f"reviewed {registry.reviewed_at}"
        )
    else:
        print(f"{args.command}: scaffold ready; source adapters are the next milestone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
