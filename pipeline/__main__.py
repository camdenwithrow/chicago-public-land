import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Land to Homes data pipeline")
    parser.add_argument("command", choices=("ingest", "score"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"{args.command}: scaffold ready; source adapters are the next milestone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
