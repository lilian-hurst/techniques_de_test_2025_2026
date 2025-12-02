"""Performance-oriented tests measuring serialization and triangulation costs."""

from __future__ import annotations

import time

import pytest

from src.triangulator import serialization, algorithm


@pytest.mark.performance
@pytest.mark.parametrize("size", [10, 100, 1_000, 10_000])
def test_point_set_serialization_scaling(dense_point_set_factory, size) -> None:
    """Measure how long serialization takes as the dataset grows."""

    points = dense_point_set_factory(size)
    start = time.perf_counter()
    payload = serialization.point_set_to_bytes(points)
    duration = time.perf_counter() - start

    assert len(payload) == 4 + size * 8
    # Guardrail: keep serialization under 250 ms per 10k points (very lenient).
    allowed = 0.25 * max(1, size / 10_000)
    assert duration < allowed


@pytest.mark.performance
@pytest.mark.parametrize("size", [10, 30, 60])
def test_triangulation_scaling(dense_point_set_factory, size) -> None:
    """Measure triangulation responsiveness on increasingly large inputs."""

    points = dense_point_set_factory(size)
    start = time.perf_counter()
    try:
        triangles = algorithm.triangulate(points)
    except Exception as exc:  # pragma: no cover - protects against not implemented yet
        pytest.fail(f"Triangulation raised unexpectedly: {exc}")
    duration = time.perf_counter() - start

    assert len(triangles) in (0, max(0, size - 2))
    allowed = 0.1 * max(1, size / 10)  # up to 1s for 100 points
    assert duration < allowed


@pytest.mark.performance
@pytest.mark.parametrize("size", [10_000, 50_000])
def test_point_set_serialization_very_large_datasets(dense_point_set_factory, size) -> None:
    """Measure serialization performance with very large datasets."""

    points = dense_point_set_factory(size)
    start = time.perf_counter()
    payload = serialization.point_set_to_bytes(points)
    duration = time.perf_counter() - start

    assert len(payload) == 4 + size * 8
    # More lenient threshold for very large datasets
    allowed = 1.0 * max(1, size / 10_000)  # Up to 1 second for 10k points
    assert duration < allowed




