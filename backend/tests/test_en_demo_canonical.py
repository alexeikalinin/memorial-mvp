"""Регрессия канонических проверок EN-демо (без БД)."""
from verify_en_demo_graph import CANONICAL_PARENT_CHECKS, CANONICAL_SPOUSE_PAIRS


def test_canonical_parent_checks_cover_three_families():
    assert len(CANONICAL_PARENT_CHECKS) >= 8
    names = {c for c, _ in CANONICAL_PARENT_CHECKS}
    assert "Emily Chang" in names and "Antonio Rossi" in names


def test_canonical_spouse_pairs_nonempty():
    assert len(CANONICAL_SPOUSE_PAIRS) >= 3
    for a, b in CANONICAL_SPOUSE_PAIRS:
        assert a != b
