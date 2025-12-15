from dataclasses import dataclass
from typing import Any

from . import exceptions, serialization  # Relative imports


@dataclass
class HttpResponse:
    status_code: int
    content: bytes


class PointSetManagerClient:
    def __init__(self, base_url: str, timeout: float = 5.0, session: Any = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session

    def fetch_point_set(self, point_set_id: str) -> bytes:
        url = f"{self.base_url}/pointset/{point_set_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)
        except Exception as e:
            raise exceptions.PointSetManagerUnavailableError(f"Network error: {e}") from e

        if response.status_code == 200:
            try:
                serialization.bytes_to_point_set(response.content)
            except exceptions.SerializationError:
                raise
            return response.content

        elif response.status_code == 404:
            raise exceptions.PointSetNotFoundError(f"Point set {point_set_id} not found.")

        elif response.status_code == 400:
            raise exceptions.InvalidPointSetIdError(f"Invalid ID format: {point_set_id}")

        elif response.status_code == 503:
            raise exceptions.PointSetManagerUnavailableError("Service unavailable (503).")

        else:
            raise exceptions.PointSetManagerUnavailableError(
                f"Unexpected upstream status: {response.status_code}"
            )
