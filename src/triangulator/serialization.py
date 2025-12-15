import struct
from collections.abc import Sequence

from . import exceptions  # Relative import

Point = tuple[float, float]
Triangle = tuple[int, int, int]

HEADER_FORMAT = ">I"
POINT_FORMAT = ">ff"
TRIANGLE_INDICES_FORMAT = ">III"

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
POINT_SIZE = struct.calcsize(POINT_FORMAT)
TRIANGLE_SIZE = struct.calcsize(TRIANGLE_INDICES_FORMAT)


def point_set_to_bytes(points: Sequence[Point]) -> bytes:
    try:
        payload = bytearray()
        payload.extend(struct.pack(HEADER_FORMAT, len(points)))
        for x, y in points:
            payload.extend(struct.pack(POINT_FORMAT, x, y))
        return bytes(payload)
    except struct.error as e:
        raise exceptions.SerializationError(f"Failed to serialize points: {e}") from e


def bytes_to_point_set(data: bytes) -> list[Point]:
    if len(data) < HEADER_SIZE:
        raise exceptions.SerializationError("Payload too short to contain header")

    try:
        count = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])[0]
        expected_size = HEADER_SIZE + (count * POINT_SIZE)

        if len(data) < expected_size:
            raise exceptions.SerializationError("Payload smaller than expected")

        points = []
        offset = HEADER_SIZE
        for _ in range(count):
            x, y = struct.unpack(POINT_FORMAT, data[offset: offset + POINT_SIZE])
            points.append((x, y))
            offset += POINT_SIZE
        return points
    except struct.error as e:
        raise exceptions.SerializationError(f"Failed to deserialize points: {e}") from e


def triangles_to_bytes(points: Sequence[Point], triangles: Sequence[Triangle]) -> bytes:
    try:
        # On réutilise la sérialisation des points
        payload = bytearray(point_set_to_bytes(points))

        max_index = len(points) - 1

        # C'est ici que le TypeError se produit si on passe des strings
        # car on ne peut pas comparer str > int
        for tri in triangles:
            if any(idx > max_index or idx < 0 for idx in tri):
                raise exceptions.SerializationError("Triangle index out of bounds")

        payload.extend(struct.pack(HEADER_FORMAT, len(triangles)))
        for a, b, c in triangles:
            payload.extend(struct.pack(TRIANGLE_INDICES_FORMAT, a, b, c))

        return bytes(payload)

    # CORRECTION ICI : On capture TypeError et ValueError en plus de struct.error
    except (struct.error, TypeError, ValueError) as e:
        raise exceptions.SerializationError(f"Failed to serialize triangles: {e}") from e


def bytes_to_triangles(data: bytes) -> tuple[list[Point], list[Triangle]]:
    if len(data) < HEADER_SIZE:
        raise exceptions.SerializationError("Payload too short")

    try:
        point_count = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])[0]
        points_end_offset = HEADER_SIZE + (point_count * POINT_SIZE)

        if len(data) < points_end_offset:
            raise exceptions.SerializationError("Payload too short for points")

        points_data = data[:points_end_offset]
        points = bytes_to_point_set(points_data)

        if len(data) < points_end_offset + HEADER_SIZE:
            raise exceptions.SerializationError("Missing triangle count header")

        triangle_count = struct.unpack(
            HEADER_FORMAT,
            data[points_end_offset: points_end_offset + HEADER_SIZE]
        )[0]

        expected_total_size = points_end_offset + HEADER_SIZE + (triangle_count * TRIANGLE_SIZE)
        if len(data) != expected_total_size:
            raise exceptions.SerializationError("Payload size mismatch for triangles section")

        triangles = []
        offset = points_end_offset + HEADER_SIZE
        for _ in range(triangle_count):
            a, b, c = struct.unpack(TRIANGLE_INDICES_FORMAT, data[offset: offset + TRIANGLE_SIZE])
            triangles.append((a, b, c))
            offset += TRIANGLE_SIZE

        return points, triangles

    except struct.error as e:
        raise exceptions.SerializationError(f"Failed to deserialize payload: {e}") from e
