from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HttpCheckParams:
    url: str
    method: str = "GET"
    expected_status_code: int = 200
    expected_keyword: Optional[str] = None
    timeout_seconds: float = 10.0

@dataclass(frozen=True)
class CheckResult:
    status_code: int
    response_time_ms: int
    is_success: bool
    error_message: str = ""