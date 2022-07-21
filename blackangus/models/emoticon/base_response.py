import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class ResponseResultModel:
    success: bool
    message: str
    error: Optional[str] = None
