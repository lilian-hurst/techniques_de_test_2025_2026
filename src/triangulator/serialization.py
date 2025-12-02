from typing import Sequence, Tuple, List

Point = Tuple[float, float]
Triangle = Tuple[int, int, int]

def point_set_to_bytes(points: Sequence[Point]) -> bytes:
    # TODO: Implement serialization logic
    return b""

def bytes_to_point_set(data: bytes) -> List[Point]:
    # TODO: Implement deserialization logic
    return []

def triangles_to_bytes(points: Sequence[Point], triangles: Sequence[Triangle]) -> bytes:
    # TODO: Implement serialization logic
    return b""

def bytes_to_triangles(data: bytes) -> Tuple[List[Point], List[Triangle]]:
    # TODO: Implement deserialization logic
    return [], []