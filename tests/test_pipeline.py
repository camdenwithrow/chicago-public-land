from pipeline.__main__ import build_parser, main


def test_pipeline_commands_are_registered() -> None:
    assert build_parser().parse_args(["ingest"]).command == "ingest"
    assert main(["score"]) == 0
    assert main(["sources"]) == 0
