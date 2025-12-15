"""Unit tests for the Triangles binary serialization helpers."""

from __future__ import annotations

import struct
from unittest.mock import patch

import pytest

from src.triangulator import exceptions
from src.triangulator import serialization as serializer


def _to_float32(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Helper to simulate float32 precision loss."""
    cleaned = []
    for x, y in points:
        fx = struct.unpack('>f', struct.pack('>f', x))[0]
        fy = struct.unpack('>f', struct.pack('>f', y))[0]
        cleaned.append((fx, fy))
    return cleaned


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

    # Compare exact float32 values
    assert decoded_points == _to_float32(square_points)
    assert decoded_triangles == triangles


@pytest.mark.serialization
def test_triangles_roundtrip_is_lossless(
    pentagon_points,
) -> None:
    """Roundtrip conversion must preserve all values."""
    triangles = [(0, 1, 2), (0, 2, 3), (0, 3, 4)]
    payload = serializer.triangles_to_bytes(pentagon_points, triangles)
    decoded_points, decoded_triangles = serializer.bytes_to_triangles(payload)

    # Compare exact float32 values
    assert decoded_points == _to_float32(pentagon_points)
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
    """
    SCÉNARIO : Un triangle pointe vers le point #5 alors qu'il n'y a que 3 points.
    POURQUOI : Intégrité des données. Empêcher de créer des références invalides (segfault potentiel).
    """
    invalid_triangles = [(0, 1, 5)]

    with pytest.raises(exceptions.SerializationError):
        serializer.triangles_to_bytes(square_points, invalid_triangles)


@pytest.mark.serialization
def test_triangles_to_bytes_rejects_negative_indices(
        square_points,
) -> None:
    """Covers serialization.py: Explicit check for negative indices."""
    # -1 is valid in Python list slicing but invalid in our binary format logic
    invalid_triangles = [(0, 1, -1)]

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.triangles_to_bytes(square_points, invalid_triangles)
    assert "Triangle index out of bounds" in str(exc.value)


@pytest.mark.serialization
def test_triangles_to_bytes_handles_struct_error(
        square_points,
) -> None:
    """Covers serialization.py: Exception handling when struct.pack fails for triangles."""
    # Invalid types for indices
    invalid_triangles = [("a", "b", "c")]

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.triangles_to_bytes(square_points, invalid_triangles)  # type: ignore
    assert "Failed to serialize triangles" in str(exc.value)


@pytest.mark.serialization
def test_bytes_to_triangles_handles_struct_error_during_unpack() -> None:
    """
    SCÉNARIO : Simulation d'une erreur interne de la librairie 'struct'.
    POURQUOI : 100% Coverage.
    COMMENT : On utilise 'patch' pour remplacer la fonction standard 'struct.unpack'
             par une version qui plante artificiellement.
    """
    # Create a payload that looks valid in size
    dummy_payload = b"\x00\x00\x00\x00" * 20

    # Force struct.unpack to fail even if size checks pass
    with patch("struct.unpack", side_effect=struct.error("Boom")):
        with pytest.raises(exceptions.SerializationError) as exc:
            serializer.bytes_to_triangles(dummy_payload)
        assert "Failed to deserialize payload" in str(exc.value)


@pytest.mark.serialization
def test_triangles_to_bytes_catch_type_error(square_points) -> None:
    """Couvre serialization.py ligne 77: Catch TypeError/ValueError lors du pack."""
    # Indices invalides (string au lieu de int)
    bad_triangles = [("a", "b", "c")]

    with pytest.raises(exceptions.SerializationError):
        serializer.triangles_to_bytes(square_points, bad_triangles)  # type: ignore


@pytest.mark.serialization
def test_bytes_to_triangles_truncated_in_points_section(
        square_points,
        point_set_bytes_factory
) -> None:
    """Couvre serialization.py ligne 84: Troncature dans la zone des points."""
    payload = point_set_bytes_factory(square_points)
    # On coupe juste avant la fin des points
    truncated = payload[:-1]

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.bytes_to_triangles(truncated)
    assert "Payload too short for points" in str(exc.value)


@pytest.mark.serialization
def test_bytes_to_triangles_missing_triangle_header(
        square_points,
        point_set_bytes_factory
) -> None:
    """Couvre serialization.py ligne 90: Manque le header des triangles."""
    # Payload contient juste les points, rien après
    payload = point_set_bytes_factory(square_points)

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.bytes_to_triangles(payload)
    assert "Missing triangle count header" in str(exc.value)


def test_bytes_to_point_set_internal_struct_error(square_points, point_set_bytes_factory):
    """
    Force une struct.error à l'intérieur du bloc try de bytes_to_point_set.
    """
    # On crée un payload valide pour passer les checks de taille (len(data) < expected_size)
    valid_payload = point_set_bytes_factory(square_points)

    # On patche struct.unpack pour qu'il lève une erreur arbitrairement
    # Cela simule une corruption de données subtile ou un problème système
    with patch('struct.unpack', side_effect=struct.error("Erreur simulée")):
        with pytest.raises(exceptions.SerializationError) as exc:
            serializer.bytes_to_point_set(valid_payload)

    # On vérifie que c'est bien notre message formaté qui est levé
    assert "Failed to deserialize points" in str(exc.value)


# --- TEST 2 : Couvre "Payload too short" ---
# Fichier: src/triangulator/serialization.py
# Cas: Le payload est plus petit que la taille d'un header (4 octets)

def test_bytes_to_triangles_too_short_header():
    """
    Passe un payload trop court (< 4 octets) à bytes_to_triangles.
    Doit activer le tout premier check de la fonction.
    """
    short_payload = b"\x00\x00"  # 2 octets, insuffisant pour lire le nombre de points

    with pytest.raises(exceptions.SerializationError) as exc:
        serializer.bytes_to_triangles(short_payload)

    assert "Payload too short" in str(exc.value)
