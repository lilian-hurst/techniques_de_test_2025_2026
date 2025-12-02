"""Integration tests for the PointSetManager HTTP client."""

from __future__ import annotations

import struct
import uuid
from unittest.mock import Mock

import pytest

from src.triangulator import exceptions
from src.triangulator.clients import PointSetManagerClient, HttpResponse


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
    """A 200 response should return the binary payload as-is."""

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
    """A 404 from the upstream service must be mapped to a domain error."""

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
    """Network failures must be surfaced as PointSetManagerUnavailableError."""

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
    """Malformed binary responses should raise SerializationError."""

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

