# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Copy-law guard for teaching text that lives outside Python.

The frontend glossary (``frontend/src/lib/glossary.ts``) and the curated roles
JSON carry user-facing teaching copy that the insights/flags/digest suites never
see. The frontend has no test framework of its own, so this Python suite reads
those files as text and holds them to the same house rules: no advice phrasing,
never the digest-breaking word "median", and never a URL (which would break the
email if the copy ever reaches it).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_FRONTEND_LIB = _REPO / "frontend" / "src" / "lib"
_GLOSSARY_TS = _FRONTEND_LIB / "glossary.ts"
_ROLES_JSON = _REPO / "backend" / "app" / "data" / "watchlist_roles.json"
_PAGE_LESSONS_TS = _FRONTEND_LIB / "pageLessons.ts"
_WEATHER_COPY_TS = _FRONTEND_LIB / "weatherCopy.ts"
_STUDY_COPY_TS = _FRONTEND_LIB / "studyCopy.ts"

# Union of the insights and flags forbidden lists — the strictest bar.
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)


def _files():
    return [
        p for p in (_GLOSSARY_TS, _ROLES_JSON, _PAGE_LESSONS_TS, _WEATHER_COPY_TS,
                    _STUDY_COPY_TS)
        if p.exists()
    ]


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.name)
def test_no_advice_phrasing(path: Path):
    text = path.read_text(encoding="utf-8")
    match = FORBIDDEN.search(text)
    assert match is None, f"advice phrasing in {path.name}: {match.group(0)!r}"


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.name)
def test_never_says_median(path: Path):
    """'median' anywhere in copy that could reach the digest breaks its budget."""
    assert "median" not in path.read_text(encoding="utf-8").lower(), path.name


@pytest.mark.parametrize("path", _files(), ids=lambda p: p.name)
def test_no_urls(path: Path):
    assert "http" not in path.read_text(encoding="utf-8").lower(), path.name


def test_glossary_file_exists_and_covers_every_entry_with_an_analogy():
    """The TS field is required at compile time; this asserts it at rest too."""
    assert _GLOSSARY_TS.exists(), "frontend glossary.ts missing"
    text = _GLOSSARY_TS.read_text(encoding="utf-8")
    # `analogy:` appears once per entry plus once in the interface definition.
    n_entries = len(re.findall(r"\bterm:\s*[\"']", text))
    n_analogies = len(re.findall(r"\banalogy:\s*", text))
    assert n_entries >= 40, f"expected the full glossary, found {n_entries} entries"
    assert n_analogies >= n_entries, "some glossary entries are missing an analogy"
