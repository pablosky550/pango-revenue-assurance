from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain import (
    CorrelationId,
    DuplicateRecordError,
    ExternalReference,
    IdentityGraph,
    InvalidIdentifierError,
    LineageEdge,
    PaymentId,
    ReferenceCollection,
    ReferenceConfidence,
    ReferenceProvenance,
    ReferenceRelationship,
    ReferenceType,
    RefundId,
    SettlementId,
    SourceSystem,
)


def make_reference(
    value: str,
    *,
    source=SourceSystem.PAYPAL,
    reference_type=ReferenceType.PROCESSOR_TRANSACTION_ID,
    primary=False,
):
    return ExternalReference(
        source_system=source,
        reference_type=reference_type,
        value=value,
        is_primary=primary,
        provenance=ReferenceProvenance.API,
        confidence=ReferenceConfidence.VERIFIED,
    )


def test_identifier_preserves_case_and_leading_zeroes():
    assert str(PaymentId(" 00AbC-1 ")) == "00AbC-1"


@pytest.mark.parametrize("invalid", ["", "   ", None, 123, "A\nB"])
def test_invalid_identifier_is_rejected(invalid):
    with pytest.raises(Exception):
        PaymentId(invalid)


def test_parse_rejects_different_identifier_type():
    with pytest.raises(InvalidIdentifierError):
        PaymentId.parse(RefundId("REF_1"))


def test_identifier_equality_is_typed():
    assert PaymentId("1") == PaymentId("1")
    assert PaymentId("1") != RefundId("1")


def test_external_reference_from_identifier():
    ref = ExternalReference.from_identifier(
        PaymentId("PAY_1"),
        SourceSystem.PANGO_BACKEND,
        is_primary=True,
    )
    assert ref.reference_type is ReferenceType.INTERNAL_PAYMENT_ID
    assert ref.to_identifier(PaymentId) == PaymentId("PAY_1")


def test_external_reference_wrong_conversion():
    ref = make_reference("TX_1")
    with pytest.raises(InvalidIdentifierError):
        ref.to_identifier(PaymentId)


def test_external_reference_requires_aware_timestamp():
    with pytest.raises(Exception):
        ExternalReference(
            source_system=SourceSystem.PAYPAL,
            reference_type=ReferenceType.PROCESSOR_TRANSACTION_ID,
            value="TX_1",
            observed_at=datetime(2026, 1, 1),
        )


def test_reference_collection_detects_duplicate():
    ref = make_reference("TX_1")
    with pytest.raises(DuplicateRecordError):
        ReferenceCollection([ref, ref])


def test_reference_collection_enforces_one_primary_per_namespace():
    with pytest.raises(DuplicateRecordError):
        ReferenceCollection([
            make_reference("TX_1", primary=True),
            make_reference("TX_2", primary=True),
        ])


def test_reference_collection_is_deterministic_and_indexed():
    refs = ReferenceCollection([
        make_reference("TX_2"),
        make_reference("TX_1"),
    ])
    assert [ref.value for ref in refs] == ["TX_1", "TX_2"]
    assert refs.get(
        SourceSystem.PAYPAL,
        ReferenceType.PROCESSOR_TRANSACTION_ID,
        "TX_1",
    ).value == "TX_1"


def test_find_and_require_one():
    ref = make_reference("TX_1")
    refs = ReferenceCollection([ref])
    assert refs.find(source_system=SourceSystem.PAYPAL) == (ref,)
    assert refs.require_one(value="TX_1") == ref


def test_require_one_missing():
    with pytest.raises(Exception):
        ReferenceCollection.empty().require_one(value="missing")


def test_collection_add_is_immutable():
    first = ReferenceCollection.empty()
    second = first.add(make_reference("TX_1"))
    assert len(first) == 0
    assert len(second) == 1


def test_correlation_id_roundtrip():
    correlation = CorrelationId.new()
    assert CorrelationId.parse(str(correlation)) == CorrelationId(
        correlation.value
    )
    assert correlation.created_at is not None


def test_correlation_id_rejects_invalid_uuid():
    with pytest.raises(InvalidIdentifierError):
        CorrelationId.parse("invalid")


def test_lineage_edge_rejects_self_reference():
    ref = make_reference("TX_1")
    with pytest.raises(InvalidIdentifierError):
        LineageEdge(
            source=ref,
            target=ref,
            relationship=ReferenceRelationship.MATCHED_TO,
        )


def test_identity_graph_navigation():
    payment = ExternalReference.from_identifier(
        PaymentId("PAY_1"),
        SourceSystem.PANGO_BACKEND,
    )
    settlement = ExternalReference.from_identifier(
        SettlementId("SET_1"),
        SourceSystem.PAYPAL,
    )
    edge = LineageEdge(
        source=payment,
        target=settlement,
        relationship=ReferenceRelationship.SETTLED_BY,
    )
    graph = IdentityGraph([payment, settlement], [edge])
    assert graph.outgoing(payment) == (edge,)
    assert graph.incoming(settlement) == (edge,)
    assert graph.neighbours(payment) == (settlement,)


def test_identity_graph_detects_duplicate_edges():
    payment = ExternalReference.from_identifier(
        PaymentId("PAY_1"),
        SourceSystem.PANGO_BACKEND,
    )
    settlement = ExternalReference.from_identifier(
        SettlementId("SET_1"),
        SourceSystem.PAYPAL,
    )
    edge = LineageEdge(
        source=payment,
        target=settlement,
        relationship=ReferenceRelationship.SETTLED_BY,
    )
    with pytest.raises(DuplicateRecordError):
        IdentityGraph([payment, settlement], [edge, edge])


def test_reference_is_immutable():
    ref = make_reference("TX_1")
    with pytest.raises(FrozenInstanceError):
        ref.value = "TX_2"
