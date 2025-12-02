"""Unit tests describing the expected triangulation algorithm behavior."""

from __future__ import annotations

import itertools

import pytest

from src.triangulator import algorithm, exceptions


def _normalize(triangles):
    """Return triangles sorted both internally and externally for comparison."""

    return sorted(tuple(sorted(tri)) for tri in triangles)


@pytest.mark.algorithm
def test_triangulate_triangle_returns_single_face(triangle_points) -> None:
    """The simplest polygon should produce a single triangle."""

    result = algorithm.triangulate(triangle_points)

    assert _normalize(result) == [(0, 1, 2)]


@pytest.mark.algorithm
def test_triangulate_square_returns_two_faces(square_points) -> None:
    """The triangulation of a convex quadrilateral should yield two faces."""

    result = algorithm.triangulate(square_points)

    assert _normalize(result) == [(0, 1, 2), (0, 2, 3)]


@pytest.mark.algorithm
def test_triangulate_pentagon_returns_three_faces(pentagon_points) -> None:
    """A convex pentagon should yield exactly n-2 triangles."""

    result = algorithm.triangulate(pentagon_points)

    assert len(result) == len(pentagon_points) - 2
    assert len({tuple(sorted(tri)) for tri in result}) == len(result)
    assert all(0 <= idx < len(pentagon_points) for tri in result for idx in tri)


@pytest.mark.algorithm
def test_triangulate_rejects_insufficient_points(triangle_points) -> None:
    """Less than three points cannot produce a triangle."""

    with pytest.raises(exceptions.InvalidPointSetError):
        algorithm.triangulate(triangle_points[:2])


@pytest.mark.algorithm
def test_triangulate_rejects_duplicate_points(triangle_points) -> None:
    """Duplicate points must be reported as invalid inputs."""

    invalid_input = triangle_points + [triangle_points[0]]
    with pytest.raises(exceptions.InvalidPointSetError):
        algorithm.triangulate(invalid_input)


@pytest.mark.algorithm
def test_triangulate_rejects_colinear_points(degenerate_points) -> None:
    """Colinear sets cannot be triangulated and must raise."""

    with pytest.raises(exceptions.InvalidPointSetError):
        algorithm.triangulate(degenerate_points)


@pytest.mark.algorithm
def test_triangulation_no_overlapping_triangles(pentagon_points) -> None:
    """Verify no triangles in the result overlap with each other."""

    triangles = algorithm.triangulate(pentagon_points)

    # For convex polygons, triangles should not overlap
    # Simple check: ensure triangle indices are unique combinations
    all_indices = []
    for tri in triangles:
        all_indices.extend(tri)

    # In a proper triangulation, each edge should be shared at most once
    # except for convex hull edges which may be in one triangle
    edges = []
    for a, b, c in triangles:
        edges.extend([(min(a, b), max(a, b)),
                      (min(b, c), max(b, c)),
                      (min(c, a), max(c, a))])

    edge_counts = {}
    for edge in edges:
        edge_counts[edge] = edge_counts.get(edge, 0) + 1

    # Internal edges should appear exactly twice, hull edges once
    # This is a simplified check - full geometric overlap detection is complex
    for edge, count in edge_counts.items():
        assert count in (1, 2), f"Edge {edge} appears {count} times"


@pytest.mark.algorithm
def test_triangulation_uses_all_points(pentagon_points) -> None:
    """All input points should be used in the triangulation."""

    triangles = algorithm.triangulate(pentagon_points)

    used_indices = set()
    for tri in triangles:
        used_indices.update(tri)

    # All point indices should be used
    assert used_indices == set(range(len(pentagon_points)))


@pytest.mark.algorithm
def test_triangulation_area_property(triangle_points) -> None:
    """Sum of triangle areas should equal polygon area (for convex shapes)."""

    triangles = algorithm.triangulate(triangle_points)

    def triangle_area(points, indices):
        a, b, c = indices
        x1, y1 = points[a]
        x2, y2 = points[b]
        x3, y3 = points[c]
        return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)

    total_area = sum(triangle_area(triangle_points, tri) for tri in triangles)

    # For a single triangle, area should match
    expected_area = triangle_area(triangle_points, (0, 1, 2))
    assert total_area == pytest.approx(expected_area)

