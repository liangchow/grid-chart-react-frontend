from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RowIn(BaseModel):
    pressure: Optional[float] = None
    void_ratio: Optional[float] = None


class ProcessRequest(BaseModel):
    sigmaV: float = Field(..., gt=0)
    rows: List[RowIn]


class ProcessResponse(BaseModel):
    compressionIdx: Optional[float]
    recompressionIdx: Optional[float]
    warnings: List[str]

