"""Shared pytest fixtures for the triangulator test suite."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

Point = Tuple[float, float]
Triangle = Tuple[int, int, int]


@pytest.fixture(scope="session")
def point_set_bytes_factory() -> Callable[[Sequence[Point]], bytes]:
    """Factory that encodes point sets following the binary contract."""

    import struct

    def _encode(points: Sequence[Point]) -> bytes:
        payload = struct.pack(">I", len(points))
        for x, y in points:
            payload += struct.pack(">ff", x, y)
        return payload

    return _encode


@pytest.fixture(scope="session")
def triangles_bytes_factory(
    point_set_bytes_factory: Callable[[Sequence[Point]], bytes],
) -> Callable[[Sequence[Point], Sequence[Triangle]], bytes]:
    """Factory that encodes a triangulation payload."""

    import struct

    def _encode(points: Sequence[Point], triangles: Sequence[Triangle]) -> bytes:
        payload = point_set_bytes_factory(points)
        payload += struct.pack(">I", len(triangles))
        for a, b, c in triangles:
            payload += struct.pack(">III", a, b, c)
        return payload

    return _encode


@pytest.fixture
def triangle_points() -> list[Point]:
    """Points forming a single triangle."""

    return [(0.0, 0.0), (1.0, 0.0), (0.5, math.sqrt(3) / 2)]


@pytest.fixture
def square_points() -> list[Point]:
    """Points describing a unit square."""

    return [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ]


@pytest.fixture
def pentagon_points() -> list[Point]:
    """Regular pentagon centered on the origin."""

    points: list[Point] = []
    for idx in range(5):
        angle = math.radians(72 * idx)
        points.append((math.cos(angle), math.sin(angle)))
    return points


@pytest.fixture
def degenerate_points() -> list[Point]:
    """Colinear point set (invalid for triangulation)."""

    return [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (1.5, 0.0)]


@pytest.fixture(scope="session")
def dense_point_set_factory() -> Callable[[int], list[Point]]:
    """Factory returning deterministic point clouds of the requested size."""

    def _factory(size: int) -> list[Point]:
        if size < 0:
            raise ValueError("size must be positive")
        return [(float(i), float((i * 7) % 13)) for i in range(size)]

    return _factory

@pytest.fixture
def large_point_set() -> list[Point]:
    """Large point set for stress testing."""
    return [(float(i * 0.1), float(i * 0.1)) for i in range(10000)]

