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

# class ProcessRequest(BaseModel):
#     sigmaV0: float = Field(..., gt=0)
#     rows: List[RowIn]

class Point(BaseModel):
    x: float
    y: float

class LineSegment(BaseModel):
    start: Point
    end: Point
    slope: float
    intercept: float

class ProcessResponse(BaseModel):
    """
    Data needed to render in frontend.
    """
    loding_curve_points: List[Point]
    segment1: LineSegment
    segment2: LineSegment
    sigma_p: float
    e_p: float
    ccIdx: Optional[float]
    crIdx: Optional[float]
    warnings: List[str]

# App setup
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

# Utility functions
def _to_float(value: object) -> Optional[float]:
    """
    Coerce a value to finite float, or returning None if not.
    Reject None, bool, string, inf, and nan.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v if np.isfinite(v) else None
    if isinstance(value, str):
        try:
            v = float(value)
            return v if np.isfinite(v) else None
        except ValueError:
            return None
    return None

# Processing functions

# def _find_unloading_and_reloading_indices(stress: Sequence[float]) -> Tuple[List[int], List[int]]:
#     idx_unloading_init: List[int] = []
#     idx_reloading_init: List[int] = []
#     for i in range(1, len(stress) - 1):
#         if stress[i] > stress[i - 1] and stress[i] > stress[i + 1]:
#             idx_unloading_init.append(i)
#         if stress[i] < stress[i - 1] and stress[i] < stress[i + 1]:
#             idx_reloading_init.append(i)
#     return idx_unloading_init, idx_reloading_init