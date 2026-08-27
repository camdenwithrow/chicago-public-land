import pytest

from pipeline.ownership import OwnershipScope, classify_owner_scope, normalize_owner_name


@pytest.mark.parametrize(
    "owner_name",
    [
        "United States of America",
        "U.S. Postal Service",
        "Federal Government",
        "General Services Administration",
        "Department of Veterans Affairs",
    ],
)
def test_federal_owners_are_explicitly_excluded(owner_name: str) -> None:
    assert classify_owner_scope(owner_name).scope is OwnershipScope.FEDERAL_EXCLUDED


@pytest.mark.parametrize(
    "owner_name",
    ["City of Chicago", "Cook County", "State of Illinois", "Chicago Transit Authority"],
)
def test_named_nonfederal_public_owners_are_in_scope(owner_name: str) -> None:
    assert classify_owner_scope(owner_name).scope is OwnershipScope.NONFEDERAL_PUBLIC


def test_ambiguous_owner_requires_review() -> None:
    assert (
        classify_owner_scope("First Federal Savings Bank").scope is OwnershipScope.REVIEW_REQUIRED
    )


def test_owner_normalization_is_stable() -> None:
    assert normalize_owner_name("  City-of Chicago, Dept.  ") == "CITY OF CHICAGO DEPT"
