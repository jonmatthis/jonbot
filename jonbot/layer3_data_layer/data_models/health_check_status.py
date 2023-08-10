from typing import Literal

from pydantic import BaseModel
from sqlalchemy import literal


class HealthCheckResponse(BaseModel):
    status: str = Literal["alive"]

