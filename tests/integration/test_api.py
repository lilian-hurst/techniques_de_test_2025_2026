"""Integration tests describing the Triangulator HTTP API behavior."""
from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest

from src.triangulator import app as triangulator_app
from src.triangulator import exceptions


def _build_app(point_payload: bytes, result_payload: bytes):
    client = Mock()
    client.fetch_point_set.return_value = point_payload
    service = Mock()
    service.triangulate.return_value = result_payload
    app = triangulator_app.create_app(
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
    """
        SCÉNARIO : Appel GET valide sur /triangulation/{uuid}.
        POURQUOI : Vérifier le "Happy Path" de bout en bout (Controller -> Client -> Service).
        VÉRIFICATIONS : Status 200, Content-Type binaire, Appels aux services mocks.
        """
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
    """
        SCÉNARIO : L'ID passé dans l'URL n'est pas un UUID valide.
        POURQUOI : Validation d'entrée (Input Sanitization) avant d'appeler la logique métier.
        """
    app, client, service = _build_app(b"", b"")
    test_client = app.test_client()
    response = test_client.get("/triangulation/not-a-uuid")
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    payload = response.get_json()
    assert payload["code"] == "INVALID_POINT_SET_ID"
    client.fetch_point_set.assert_not_called()

@pytest.mark.integration
def test_triangulation_endpoint_handles_missing_point_set(
    point_set_bytes_factory,
    triangle_points,
) -> None:
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
    """
        SCÉNARIO : Le service de données externe est en panne (Exception levée par le mock).
        POURQUOI : Vérifier le mapping d'erreur : Exception interne -> HTTP 502 Bad Gateway.
        """
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
    large_points = dense_point_set_factory(5000)
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
    app, client, service = _build_app(b"", b"")
    test_client = app.test_client()
    invalid_uuids = [
        "not-a-uuid",
        "12345678-1234-1234-1234-123456789",
        "12345678-1234-1234-1234-1234567890123", # Fixed: Added extra digit to make it 37 chars (too long)
        "gggggggg-1234-1234-1234-123456789012",
        "12345678123412341234123456789012",
    ]
    for invalid_uuid in invalid_uuids:
        response = test_client.get(f"/triangulation/{invalid_uuid}")
        assert response.status_code == 400
        payload = response.get_json()
        assert payload["code"] == "INVALID_POINT_SET_ID"



@pytest.mark.integration
def test_triangulation_endpoint_rejects_non_canonical_uuid() -> None:
    """
    Covers app.py: Strict UUID check (rejects uppercase if logic requires lowercase).
    """
    app, _, _ = _build_app(b"", b"")
    test_client = app.test_client()

    # Python's uuid.UUID accepts this, but our app enforces strict comparison
    canonical = str(uuid.uuid4())
    non_canonical = canonical.upper()

    response = test_client.get(f"/triangulation/{non_canonical}")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "INVALID_POINT_SET_ID"


@pytest.mark.integration
def test_triangulation_endpoint_without_client_configured() -> None:
    """
    SCÉNARIO : Erreur de configuration (oubli d'injection du client).
    POURQUOI : Coverage de la ligne `if not point_set_client:` dans app.py.
    """
    # Create app explicitly without a client
    app = triangulator_app.create_app(point_set_client=None)
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 502
    payload = response.get_json()
    assert payload["code"] == "POINT_SET_MANAGER_UNAVAILABLE"


@pytest.mark.integration
def test_triangulation_endpoint_maps_invalid_point_set_error_to_500(
        point_set_bytes_factory,
        square_points
) -> None:
    """
    Covers app.py: Catching InvalidPointSetError and re-raising/mapping it.
    """
    point_payload = point_set_bytes_factory(square_points)

    client = Mock()
    client.fetch_point_set.return_value = point_payload

    service = Mock()
    # Simulate a domain logic error (e.g. colinear points) from the service
    service.triangulate.side_effect = exceptions.InvalidPointSetError("Logic error")

    app = triangulator_app.create_app(point_set_client=client, triangulation_service=service)
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    response = test_client.get(f"/triangulation/{point_set_id}")

    # The integration test contract expects 500 for algorithm failures
    assert response.status_code == 500
    payload = response.get_json()
    assert payload["code"] == "TRIANGULATION_FAILED"
    assert "Logic error" in payload["message"]




@pytest.mark.integration
def test_triangulation_endpoint_handles_list_return_from_service(
        square_points,
        point_set_bytes_factory,
) -> None:
    """Couvre app.py lignes 51-52: branche else quand le service renvoie une liste."""
    # 1. Préparation des données
    point_payload = point_set_bytes_factory(square_points)
    mock_triangles = [(0, 1, 2), (0, 2, 3)]

    # 2. Configuration des Mocks
    client = Mock()
    client.fetch_point_set.return_value = point_payload
    service = Mock()
    # Le service renvoie une liste Python brute, forçant app.py à la sérialiser
    service.triangulate.return_value = mock_triangles

    # 3. Création de l'application
    app = triangulator_app.create_app(point_set_client=client, triangulation_service=service)
    test_client = app.test_client()
    point_set_id = str(uuid.uuid4())

    # 4. Exécution et Vérification
    response = test_client.get(f"/triangulation/{point_set_id}")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/octet-stream"
    assert len(response.data) > 0


@pytest.mark.integration
def test_triangulation_endpoint_maps_domain_error_to_500(
        point_set_bytes_factory,
        square_points
) -> None:
    """Couvre app.py ligne 46: Catch InvalidPointSetError -> 500."""
    point_payload = point_set_bytes_factory(square_points)

    client = Mock()
    client.fetch_point_set.return_value = point_payload
    service = Mock()
    # Force une erreur métier spécifique
    service.triangulate.side_effect = exceptions.InvalidPointSetError("Colinear points")

    app = triangulator_app.create_app(point_set_client=client, triangulation_service=service)
    test_client = app.test_client()

    response = test_client.get(f"/triangulation/{str(uuid.uuid4())}")

    assert response.status_code == 500
    assert response.get_json()["code"] == "TRIANGULATION_FAILED"
