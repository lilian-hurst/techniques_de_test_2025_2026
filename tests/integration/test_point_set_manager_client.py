"""Integration tests for the PointSetManager HTTP client."""

from __future__ import annotations

import struct
import uuid
from unittest.mock import Mock

import pytest

from src.triangulator import exceptions
from src.triangulator.clients import HttpResponse, PointSetManagerClient


@pytest.fixture
def point_set_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def client(point_set_id) -> tuple[PointSetManagerClient, Mock]:
    session = Mock()
    tri_client = PointSetManagerClient(
        base_url="https://point-set-manager",
        timeout=2.0,
        session=session,
    )
    return tri_client, session


@pytest.mark.integration
def test_fetch_point_set_happy_path(point_set_id, client) -> None:
    """
    SCÉNARIO : Tout se passe bien (Code 200).
    POURQUOI : Vérifier que le client ne modifie pas les données binaires reçues.
    COMMENT : On mock une réponse HTTP 200 avec un payload binaire simple.
    """

    tri_client, session = client
    payload = b"\x00\x00\x00\x00"
    session.get.return_value = HttpResponse(status_code=200, content=payload)

    result = tri_client.fetch_point_set(point_set_id)

    assert result == payload
    session.get.assert_called_once_with(
        f"https://point-set-manager/pointset/{point_set_id}",
        timeout=2.0,
    )


@pytest.mark.integration
def test_fetch_point_set_not_found(point_set_id, client) -> None:
    """
    SCÉNARIO : Le service distant ne trouve pas l'ID (404).
    POURQUOI : Traduire une erreur technique HTTP en erreur métier (PointSetNotFoundError).
    """

    tri_client, session = client
    session.get.return_value = HttpResponse(status_code=404, content=b"")

    with pytest.raises(exceptions.PointSetNotFoundError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_invalid_id(point_set_id, client) -> None:
    """A 400 from the upstream service must become InvalidPointSetIdError."""

    tri_client, session = client
    session.get.return_value = HttpResponse(status_code=400, content=b"")

    with pytest.raises(exceptions.InvalidPointSetIdError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_unavailable(point_set_id, client) -> None:
    """A 503 must propagate as PointSetManagerUnavailableError."""

    tri_client, session = client
    session.get.return_value = HttpResponse(status_code=503, content=b"")

    with pytest.raises(exceptions.PointSetManagerUnavailableError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_network_failure(point_set_id, client) -> None:
    """
    SCÉNARIO : Le réseau coupe ou timeout.
    POURQUOI : L'application ne doit pas crasher mais signaler l'indisponibilité.
    COMMENT : On utilise side_effect=TimeoutError pour simuler une exception levée par la librairie 'requests'.
    """
    tri_client, session = client
    session.get.side_effect = TimeoutError("boom")

    with pytest.raises(exceptions.PointSetManagerUnavailableError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_unexpected_status_code(point_set_id, client) -> None:
    """Unexpected HTTP status codes should be handled gracefully."""

    tri_client, session = client
    session.get.return_value = HttpResponse(status_code=418, content=b"I'm a teapot")

    with pytest.raises(exceptions.PointSetManagerUnavailableError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_malformed_response(point_set_id, client) -> None:
    """
    SCÉNARIO : Le service répond 200 OK, mais envoie des données corrompues.
    POURQUOI : Sécurité et Robustesse. On ne veut pas passer des déchets à l'algorithme.
    COMMENT : Le client appelle 'bytes_to_point_set' pour valider dès la réception.
    """

    tri_client, session = client
    # Invalid payload - too short
    session.get.return_value = HttpResponse(status_code=200, content=b"\x00\x00\x00")

    with pytest.raises(exceptions.SerializationError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_corrupted_payload(point_set_id, client) -> None:
    """Payload with invalid point count should be detected."""

    tri_client, session = client
    # Claims 1000 points but provides only 2
    corrupted_payload = struct.pack(">I", 1000) + struct.pack(">ff", 1.0, 2.0)
    session.get.return_value = HttpResponse(status_code=200, content=corrupted_payload)

    with pytest.raises(exceptions.SerializationError):
        tri_client.fetch_point_set(point_set_id)


@pytest.mark.integration
def test_fetch_point_set_generic_exception(point_set_id, client) -> None:
    """
    SCÉNARIO : Erreur inconnue (ni réseau, ni HTTP).
    POURQUOI : Coverage défensif. S'assurer que le 'try/except Exception' capture tout.
    NOTE : C'est un test un peu artificiel pour garantir qu'on ne laisse rien passer.
    """
    tri_client, session = client
    # Simulate an unexpected error (not a network timeout, but something else)
    session.get.side_effect = Exception("Something weird happened")

    with pytest.raises(exceptions.PointSetManagerUnavailableError) as exc:
        tri_client.fetch_point_set(point_set_id)

    assert "Network error: Something weird happened" in str(exc.value)


@pytest.mark.integration
def test_fetch_point_set_handles_generic_exception(point_set_id, client) -> None:
    """Couvre clients.py lignes 31-32: Catch Exception générique."""
    tri_client, session = client
    # Simule un crash inattendu de la librairie
    session.get.side_effect = Exception("Unknown library error")

    with pytest.raises(exceptions.PointSetManagerUnavailableError) as exc:
        tri_client.fetch_point_set(point_set_id)

    assert "Network error" in str(exc.value)


