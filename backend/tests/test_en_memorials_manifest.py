"""Контракт: демо-набор EN в репозитории — ровно 35 имён в en_memorials_manifest."""

from en_memorials_manifest import EXPECTED_EN_COUNT, EXPECTED_EN_NAMES


def test_expected_en_count_is_35():
    assert EXPECTED_EN_COUNT == 35
    assert len(EXPECTED_EN_NAMES) == 35
