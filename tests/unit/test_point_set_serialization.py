"""Unit tests covering the PointSet binary serialization helpers."""

from __future__ import annotations

import struct

import pytest

from src.triangulator import exceptions
from src.triangulator import serialization as serializer


def _to_float32(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Helper to simulate float32 precision loss for accurate comparison."""
    cleaned = []
    for x, y in points:
        # Round-trip through struct to force float32 truncation
        fx = struct.unpack('>f', struct.pack('>f', x))[0]
        fy = struct.unpack('>f', struct.pack('>f', y))[0]
        cleaned.append((fx, fy))
    return cleaned


@pytest.mark.serialization
def test_point_set_to_bytes_matches_reference_payload(
    square_points,
    point_set_bytes_factory,
) -> None:
    """
    SCÉNARIO : Comparaison avec une référence fixe.
    POURQUOI : Garantir que le format binaire ne change pas par accident (Non-régression).
    """
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

    # We compare against the float32 version of square_points
    assert decoded == _to_float32(square_points)


@pytest.mark.serialization
def test_point_set_roundtrip_preserves_order_and_values(
    pentagon_points,
) -> None:
    """
    SCÉNARIO : Encodage puis Décodage immédiat (Roundtrip).
    POURQUOI : Vérifier qu'on ne perd aucune donnée (lossless).
    NOTE : Utilise _to_float32 car la conversion binaire réduit la précision (double -> float).
    """
    payload = serializer.point_set_to_bytes(pentagon_points)
    decoded = serializer.bytes_to_point_set(payload)

    # The result should be EXACTLY equal to the input cast to float32
    assert decoded == _to_float32(pentagon_points)


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
    """
    SCÉNARIO : Paquet réseau coupé (manque des octets à la fin).
    POURQUOI : Éviter de lire dans la mémoire hors limites ou de planter.
    """
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
    """
    SCÉNARIO : Valeurs mathématiques limites (Infini, très grands nombres).
    POURQUOI : Vérifier la robustesse du format 'float' (IEEE 754).
    """
    extreme_points = [
        (1e10, 1e10),
        (-1e10, -1e10),
        (1e-10, 1e-10),
        (-1e-10, -1e-10),
        (float('inf'), 0.0),
        (0.0, float('-inf')),
    ]
    payload = serializer.point_set_to_bytes(extreme_points)
    decoded = serializer.bytes_to_point_set(payload)
    assert len(decoded) == len(extreme_points)


@pytest.mark.serialization
def test_point_set_serialization_nan_values() -> None:
    """NaN values should be handled gracefully or rejected."""
    nan_points = [(float('nan'), 1.0), (0.0, float('nan'))]
    try:
        payload = serializer.point_set_to_bytes(nan_points)
        decoded = serializer.bytes_to_point_set(payload)
        assert len(decoded) == len(nan_points)
    except (exceptions.SerializationError, struct.error):
        pass


@pytest.mark.serialization
def test_point_set_to_bytes_handles_struct_error() -> None:
    """
    SCÉNARIO : Erreur de type (passer des strings au lieu de floats).
    POURQUOI : Coverage. Vérifier que l'erreur 'struct.error' est bien catchée et transformée.
    NOTE : En Python typé correctement, cela ne devrait pas arriver, c'est une sécurité.
    """
    # Passing incompatible types (strings instead of floats)
    invalid_points = [("not_a_float", "zero")]

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.point_set_to_bytes(invalid_points)  # type: ignore
    assert "Failed to serialize points" in str(exc.value)


@pytest.mark.serialization
def test_bytes_to_point_set_allows_extra_data_pass_branch(
        square_points,
        point_set_bytes_factory
) -> None:
    """
    Covers serialization.py: The 'pass' branch where payload is larger than expected.
    """
    valid_payload = point_set_bytes_factory(square_points)
    # Add extra garbage bytes at the end
    extended_payload = valid_payload + b"\x00\x00\x00\x00"

    # Should not raise, just ignore extra bytes (or pass the specific size check logic)
    decoded = serializer.bytes_to_point_set(extended_payload)

    # Check that we still got the correct number of points
    assert len(decoded) == len(square_points)


@pytest.mark.serialization
def test_bytes_to_point_set_ignores_trailing_garbage(
        square_points,
        point_set_bytes_factory
) -> None:
    """Couvre serialization.py ligne 48: Payload plus grand que prévu."""
    payload = point_set_bytes_factory(square_points)
    # Ajoute du "bruit" à la fin
    garbage_payload = payload + b"\xDE\xAD\xBE\xEF"

    # Doit fonctionner sans erreur
    decoded = serializer.bytes_to_point_set(garbage_payload)
    assert len(decoded) == len(square_points)



