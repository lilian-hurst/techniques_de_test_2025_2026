class TriangulatorError(Exception):
    """Base exception for the triangulator service."""
    pass

class PointSetNotFoundError(TriangulatorError):
    """Raised when a point set ID does not exist remotely."""
    pass

class InvalidPointSetIdError(TriangulatorError):
    """Raised when the point set ID format is invalid."""
    pass

class PointSetManagerUnavailableError(TriangulatorError):
    """Raised when the upstream service cannot be reached or fails."""
    pass

class SerializationError(TriangulatorError):
    """Raised when binary data is malformed or invalid."""
    pass

class InvalidPointSetError(TriangulatorError):
    """Raised when points are not suitable for triangulation (colinear, duplicates)."""
    pass

class TriangulationError(TriangulatorError):
    """Raised when the algorithm fails to triangulate."""
    pass