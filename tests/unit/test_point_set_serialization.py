"""Unit tests covering the PointSet binary serialization helpers."""

from __future__ import annotations

import struct

import pytest
# CORRECTION: Ajout de 'as serializer' pour correspondre aux appels dans le code
from src.triangulator import exceptions, serialization as serializer


@pytest.mark.serialization
def test_point_set_to_bytes_matches_reference_payload(
    square_points,
    point_set_bytes_factory,
) -> None:
    """Ensure the encoder produces the exact expected payload byte-for-byte."""

    expected = point_set_bytes_factory(square_points)
    result = serializer.point_set_to_bytes(square_points)

    assert result == expected


@pytest.mark.serialization
def test_bytes_to_point_set_decodes_reference_payload(
    square_points,
    point_set_bytes_factory,
) -> None:
    """Ensure the decoder reads the reference payload back into Python data."""

    payload = point_set_bytes_factory(square_points)
    decoded = serializer.bytes_to_point_set(payload)

    assert decoded == square_points


@pytest.mark.serialization
def test_point_set_roundtrip_preserves_order_and_values(
    pentagon_points,
) -> None:
    """Serializing then deserializing must be lossless."""

    payload = serializer.point_set_to_bytes(pentagon_points)
    decoded = serializer.bytes_to_point_set(payload)

    assert decoded == pytest.approx(pentagon_points)  # type: ignore[arg-type]


@pytest.mark.serialization
def test_point_set_serialization_supports_empty_payload() -> None:
    """The binary format supports empty point sets."""

    payload = serializer.point_set_to_bytes([])
    assert payload == struct.pack(">I", 0)
    decoded = serializer.bytes_to_point_set(payload)
    assert decoded == []


@pytest.mark.serialization
def test_point_set_deserialization_detects_truncated_payload(
    square_points,
    point_set_bytes_factory,
) -> None:
    """When coordinates are missing the decoder must raise a specific error."""

    payload = point_set_bytes_factory(square_points)[:-2]

    with pytest.raises(exceptions.SerializationError):
        serializer.bytes_to_point_set(payload)


@pytest.mark.serialization
def test_point_set_serialization_large_dataset_length(
    dense_point_set_factory,
) -> None:
    """Ensure the payload length scales exactly with the number of points."""

    dataset = dense_point_set_factory(1_000)
    payload = serializer.point_set_to_bytes(dataset)

    assert len(payload) == 4 + len(dataset) * 8


@pytest.mark.serialization
def test_point_set_serialization_extreme_coordinates() -> None:
    """Ensure serialization handles extreme coordinate values correctly."""

    extreme_points = [
        (1e10, 1e10),  # Very large coordinates
        (-1e10, -1e10),  # Very large negative coordinates
        (1e-10, 1e-10),  # Very small coordinates
        (-1e-10, -1e-10),  # Very small negative coordinates
        (float('inf'), 0.0),  # Infinity
        (0.0, float('-inf')),  # Negative infinity
    ]

    # Should not raise any errors
    payload = serializer.point_set_to_bytes(extreme_points)
    decoded = serializer.bytes_to_point_set(payload)

    # For non-finite values, check they are preserved or handled
    assert len(decoded) == len(extreme_points)


@pytest.mark.serialization
def test_point_set_serialization_nan_values() -> None:
    """NaN values should be handled gracefully or rejected."""

    nan_points = [(float('nan'), 1.0), (0.0, float('nan'))]

    # Either should reject or handle consistently
    try:
        payload = serializer.point_set_to_bytes(nan_points)
        decoded = serializer.bytes_to_point_set(payload)
        # If it succeeds, verify behavior is consistent
        assert len(decoded) == len(nan_points)
    except (exceptions.SerializationError, struct.error):
        # NaN rejection is also acceptable
        pass