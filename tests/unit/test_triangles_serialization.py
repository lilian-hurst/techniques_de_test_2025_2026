"""Unit tests for the Triangles binary serialization helpers."""

from __future__ import annotations

import pytest

# CORRECTION: Imports corrigés pointant vers src.triangulator
from src.triangulator import exceptions
from src.triangulator import serialization as serializer


@pytest.mark.serialization
def test_triangles_to_bytes_matches_reference_payload(
    square_points,
    triangles_bytes_factory,
) -> None:
    """Ensure the encoder matches the documented binary layout."""

    triangles = [(0, 1, 2), (0, 2, 3)]
    expected = triangles_bytes_factory(square_points, triangles)
    payload = serializer.triangles_to_bytes(square_points, triangles)

    assert payload == expected


@pytest.mark.serialization
def test_bytes_to_triangles_decodes_reference_payload(
    square_points,
    triangles_bytes_factory,
) -> None:
    """Ensure the decoder returns both the vertices and the indices."""

    triangles = [(0, 1, 2), (0, 2, 3)]
    payload = triangles_bytes_factory(square_points, triangles)

    decoded_points, decoded_triangles = serializer.bytes_to_triangles(payload)

    assert decoded_points == pytest.approx(square_points)  # type: ignore[arg-type]
    assert decoded_triangles == triangles


@pytest.mark.serialization
def test_triangles_roundtrip_is_lossless(
    pentagon_points,
) -> None:
    """Roundtrip conversion must preserve all values."""

    triangles = [(0, 1, 2), (0, 2, 3), (0, 3, 4)]
    payload = serializer.triangles_to_bytes(pentagon_points, triangles)
    decoded_points, decoded_triangles = serializer.bytes_to_triangles(payload)

    assert decoded_points == pytest.approx(pentagon_points)  # type: ignore[arg-type]
    assert decoded_triangles == triangles


@pytest.mark.serialization
def test_triangles_decoder_detects_incomplete_triangle_section(
    square_points,
    triangles_bytes_factory,
) -> None:
    """If the payload ends mid-triangle a SerializationError must be raised."""

    triangles = [(0, 1, 2), (0, 2, 3)]
    payload = triangles_bytes_factory(square_points, triangles)[:-4]

    with pytest.raises(exceptions.SerializationError):
        serializer.bytes_to_triangles(payload)


@pytest.mark.serialization
def test_triangles_encoder_rejects_invalid_indices(
    square_points,
) -> None:
    """Indices referencing missing vertices must be rejected."""

    invalid_triangles = [(0, 1, 5)]

    with pytest.raises(exceptions.SerializationError):
        serializer.triangles_to_bytes(square_points, invalid_triangles)