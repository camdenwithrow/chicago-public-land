from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class OwnershipScope(StrEnum):
    FEDERAL_EXCLUDED = "federal_excluded"
    NONFEDERAL_PUBLIC = "nonfederal_public"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class OwnershipClassification:
    scope: OwnershipScope
    rule: str


FEDERAL_OWNER_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("united_states", re.compile(r"\bUNITED STATES(?: OF AMERICA)?\b")),
    (
        "us_agency",
        re.compile(
            r"\bU\.?\s*S\.?\s+(?:GOVERNMENT|POSTAL SERVICE|DEPARTMENT|DEPT|ARMY|NAVY|AIR FORCE)\b"
        ),
    ),
    ("federal_government", re.compile(r"\bFEDERAL GOVERNMENT\b")),
    ("gsa", re.compile(r"\bGENERAL SERVICES ADMINISTRATION\b")),
    ("veterans_affairs", re.compile(r"\bDEPARTMENT OF VETERANS AFFAIRS\b")),
)

NONFEDERAL_PUBLIC_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("state_of_illinois", re.compile(r"\bSTATE OF ILLINOIS\b")),
    ("cook_county", re.compile(r"\bCOOK COUNTY\b")),
    ("city_of_chicago", re.compile(r"\bCITY OF CHICAGO\b")),
    (
        "named_public_agency",
        re.compile(
            r"\b(?:CHICAGO TRANSIT AUTHORITY|CHICAGO HOUSING AUTHORITY|"
            r"CHICAGO PUBLIC SCHOOLS|CHICAGO PARK DISTRICT)\b"
        ),
    ),
)


def normalize_owner_name(owner_name: str) -> str:
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", owner_name.upper()).split())


def classify_owner_scope(owner_name: str) -> OwnershipClassification:
    normalized = normalize_owner_name(owner_name)
    for rule, pattern in FEDERAL_OWNER_RULES:
        if pattern.search(normalized):
            return OwnershipClassification(OwnershipScope.FEDERAL_EXCLUDED, rule)
    for rule, pattern in NONFEDERAL_PUBLIC_RULES:
        if pattern.search(normalized):
            return OwnershipClassification(OwnershipScope.NONFEDERAL_PUBLIC, rule)
    return OwnershipClassification(OwnershipScope.REVIEW_REQUIRED, "no_explicit_match")
