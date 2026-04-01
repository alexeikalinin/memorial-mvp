"""Контракт: демо-набор EN в репозитории — ровно EXPECTED_EN_COUNT имён в en_memorials_manifest."""

from en_memorials_manifest import EXPECTED_EN_COUNT, EXPECTED_EN_NAMES


def test_expected_en_count_matches_manifest():
    assert EXPECTED_EN_COUNT == len(EXPECTED_EN_NAMES)
