from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

import numpy as np
from scipy.interpolate import CubicSpline


# Define model
class RowIn(BaseModel):
    pressure: Optional[float] = None
    void_ratio: Optional[float] = None


class ProcessRequest(BaseModel):
    sigmaV0: float = Field(..., gt=0)
    rows: List[RowIn]


class Indices(BaseModel):
    ccIdx: Optional[float]
    crIdx: Optional[float]
    warnings: List[str]


app = FastAPI(debug=True)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define utility functions

def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
        if np.isfinite(v):
            return v
        return None
    return None

def _find_unloading_and_reloading_indices(stress: Sequence[float]) -> Tuple[List[int], List[int]]:
    idx_unloading_init: List[int] = []
    idx_reloading_init: List[int] = []
    for i in range(1, len(stress) - 1):
        if stress[i] > stress[i - 1] and stress[i] > stress[i + 1]:
            idx_unloading_init.append(i)
        if stress[i] < stress[i - 1] and stress[i] < stress[i + 1]:
            idx_reloading_init.append(i)
    return idx_unloading_init, idx_reloading_init