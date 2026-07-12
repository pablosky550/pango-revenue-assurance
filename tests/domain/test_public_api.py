from __future__ import annotations

import domain


def test_public_api_all_is_unique_and_complete():
    assert len(domain.__all__) == len(set(domain.__all__))
    for name in domain.__all__:
        assert hasattr(domain, name), name


def test_internal_helpers_are_not_public():
    forbidden = {
        "_parse_enum",
        "_freeze_metadata",
        "_normalise_score",
        "MetadataInputValue",
        "DiagnosticInputValue",
    }
    assert forbidden.isdisjoint(domain.__all__)


def test_representative_package_level_imports():
    assert domain.Money is not None
    assert domain.PaymentTransaction is not None
    assert domain.ReconciliationResult is not None
    assert domain.IdentityGraph is not None
