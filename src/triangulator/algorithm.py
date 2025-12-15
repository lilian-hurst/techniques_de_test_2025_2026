from collections.abc import Sequence

from . import exceptions, serialization  # Relative imports

Point = tuple[float, float]
Triangle = tuple[int, int, int]


def _is_colinear(p1: Point, p2: Point, p3: Point) -> bool:
    val = p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1])
    return abs(val) < 1e-5  # slightly relaxed for float32 inputs


def triangulate(points_or_bytes: Sequence[Point] | bytes) -> list[Triangle]:
    points: Sequence[Point]
    if isinstance(points_or_bytes, bytes):
        points = serialization.bytes_to_point_set(points_or_bytes)
    else:
        points = points_or_bytes

    n = len(points)

    if n < 3:
        raise exceptions.InvalidPointSetError("At least 3 points are required.")

    if len(set(points)) != n:
        raise exceptions.InvalidPointSetError("Duplicate points detected.")

    if n >= 3:
        all_colinear = True
        p0, p1 = points[0], points[1]
        for i in range(2, n):
            if not _is_colinear(p0, p1, points[i]):
                all_colinear = False
                break
        if all_colinear:
            raise exceptions.InvalidPointSetError("Points are colinear.")

    triangles: list[Triangle] = []
    for i in range(1, n - 1):
        triangles.append((0, i, i + 1))

    return triangles
