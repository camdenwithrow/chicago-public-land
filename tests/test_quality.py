from pipeline.quality import count_change


def test_major_row_count_changes_are_flagged() -> None:
    assert count_change(110, 100) == (0.1, False)
    assert count_change(70, 100) == (-0.3, True)
    assert count_change(10, None) == (None, False)
