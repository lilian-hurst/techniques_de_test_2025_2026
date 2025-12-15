class TriangulatorError(Exception):
    """Base exception for the triangulator service."""
    pass

class PointSetNotFoundError(TriangulatorError):
    """Raised when a point set ID does not exist remotely (HTTP 404)."""
    pass

class InvalidPointSetIdError(TriangulatorError):
    """Raised when the point set ID format is invalid or rejected (HTTP 400)."""
    pass

class PointSetManagerUnavailableError(TriangulatorError):
    """Raised when the upstream service cannot be reached, times out, or returns 5xx."""
    pass

class SerializationError(TriangulatorError):
    """Raised when binary data is malformed, truncated, or fails validation."""
    pass

class InvalidPointSetError(TriangulatorError):
    """Raised when points are not suitable for triangulation (e.g. colinear, duplicates, insufficient count)."""
    pass

class TriangulationError(TriangulatorError):
    """Raised when the algorithm fails to triangulate for internal reasons."""
    pass
