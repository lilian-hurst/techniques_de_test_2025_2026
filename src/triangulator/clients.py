from dataclasses import dataclass
from typing import Any

@dataclass
class HttpResponse:
    """Simple wrapper used in tests."""
    status_code: int
    content: bytes

class PointSetManagerClient:
    def __init__(self, base_url: str, timeout: float = 5.0, session: Any = None):
        self.base_url = base_url
        self.timeout = timeout
        self.session = session

    def fetch_point_set(self, point_set_id: str) -> bytes:
        # TODO: Implement HTTP call to PointSetManager
        return b""