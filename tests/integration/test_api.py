"""Integration tests describing the Triangulator HTTP API behavior."""

from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest

from src import triangulator

from src.triangulator import exceptions, app


def _build_app(point_payload: bytes, result_payload: bytes):
    client = Mock()
    client.fetch_point_set.return_value = point_payload

    service = Mock()
    service.triangulate.return_value = result_payload

    app = triangulator.app.create_app(
        point_set_client=client,
        triangulation_service=service,
    )
    return app, client, service


@pytest.mark.integration
def test_triangulation_endpoint_success(
    square_points,
    point_set_bytes_factory,
    triangles_bytes_factory,
) -> None:
    """Happy path returns binary payload with correct headers."""

    point_payload = point_set_bytes_factory(square_points)
    triangles = [(0, 1, 2), (0, 2, 3)]
    result_payload = triangles_bytes_factory(square_points, triangles)
    app, client, service = _build_app(point_payload, result_payload)
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/octet-stream"
    assert response.data == result_payload
    client.fetch_point_set.assert_called_once_with(point_set_id)
    service.triangulate.assert_called_once_with(point_payload)


@pytest.mark.integration
def test_triangulation_endpoint_rejects_invalid_uuid() -> None:
    """The server must validate the UUID format before calling dependencies."""

    app, client, service = _build_app(b"", b"")
    test_client = app.test_client()

    response = test_client.get("/triangulation/not-a-uuid")

    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    payload = response.get_json()
    assert payload["code"] == "INVALID_POINT_SET_ID"
    assert "not a valid uuid" in payload["message"].lower()
    client.fetch_point_set.assert_not_called()
    service.triangulate.assert_not_called()


@pytest.mark.integration
def test_triangulation_endpoint_handles_missing_point_set(
    point_set_bytes_factory,
    triangle_points,
) -> None:
    """The endpoint must surface upstream 404 errors as HTTP 404."""

    point_payload = point_set_bytes_factory(triangle_points)
    app, client, _ = _build_app(point_payload, b"")
    client.fetch_point_set.side_effect = exceptions.PointSetNotFoundError()
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["code"] == "POINT_SET_NOT_FOUND"


@pytest.mark.integration
def test_triangulation_endpoint_handles_point_set_manager_failure(
    point_set_bytes_factory,
    triangle_points,
) -> None:
    """Upstream availability issues must translate to HTTP 502."""

    point_payload = point_set_bytes_factory(triangle_points)
    app, client, _ = _build_app(point_payload, b"")
    client.fetch_point_set.side_effect = exceptions.PointSetManagerUnavailableError()
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 502
    payload = response.get_json()
    assert payload["code"] == "POINT_SET_MANAGER_UNAVAILABLE"


@pytest.mark.integration
def test_triangulation_endpoint_handles_triangulation_failure(
    point_set_bytes_factory,
    triangle_points,
) -> None:
    """Algorithm failures must map to HTTP 500."""

    point_payload = point_set_bytes_factory(triangle_points)
    app, _, service = _build_app(point_payload, b"")
    service.triangulate.side_effect = exceptions.TriangulationError("degenerate polygon")
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["code"] == "TRIANGULATION_FAILED"


@pytest.mark.integration
def test_triangulation_endpoint_rejects_unsupported_methods() -> None:
    """Methods other than GET must return HTTP 405."""

    app, _, _ = _build_app(b"", b"")
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.post(f"/triangulation/{point_set_id}")

    assert response.status_code == 405


@pytest.mark.integration
def test_triangulation_endpoint_large_point_set(
        dense_point_set_factory,
        point_set_bytes_factory,
        triangles_bytes_factory,
) -> None:
    """API should handle reasonably large point sets without timing out."""

    large_points = dense_point_set_factory(5000)  # Large but reasonable
    point_payload = point_set_bytes_factory(large_points)
    triangles = [(i, i + 1, i + 2) for i in range(len(large_points) - 2)]
    result_payload = triangles_bytes_factory(large_points, triangles)

    app, client, service = _build_app(point_payload, result_payload)
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 200
    assert len(response.data) == len(result_payload)


@pytest.mark.integration
def test_triangulation_endpoint_handles_malformed_uuid() -> None:
    """Various malformed UUID formats should be rejected."""

    app, client, service = _build_app(b"", b"")
    test_client = app.test_client()

    invalid_uuids = [
        "not-a-uuid",
        "12345678-1234-1234-1234-123456789",  # Too short
        "12345678-1234-1234-1234-123456789012",  # Too long
        "gggggggg-1234-1234-1234-123456789012",  # Invalid chars
        "12345678123412341234123456789012",  # No dashes
    ]

    for invalid_uuid in invalid_uuids:
        response = test_client.get(f"/triangulation/{invalid_uuid}")
        assert response.status_code == 400
        payload = response.get_json()
        assert payload["code"] == "INVALID_POINT_SET_ID"

