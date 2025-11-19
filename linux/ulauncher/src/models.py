from __future__ import annotations

from pydantic import BaseModel, Field

class FrequencyEntry(BaseModel):
    count: int = 0
    last_accessed: str | None = None

class FrequencyData(BaseModel):
    entries: dict[str, FrequencyEntry] = Field(default_factory=dict)
