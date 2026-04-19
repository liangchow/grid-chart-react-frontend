from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


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

def remove_loginf_rows(loading_data: NDArray) -> NDArray:
    mask = np.isinfinite(loading_data["log_p"])
    return loading_data[mask]
   
# Processing functions

_LOADING_DTYPE = np.type([
    ("idx", np.intp),
    ("p", np.float64),
    ("log_p", np.float64),
    ("e", np.float64),
])

def loading_curve(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray:
    """
    Remove unloading-reloading cycles
    """
    loading_data: list[Tuple[int, float, float, float]] = []
    max_p = -np.inf

    for i, (p, e) in enumerate(zip(x,y)):
        if p > max_p:
            loading_data.append((i, p, np.log10(p), e))
            max_p = p
    if not loading_data:
        return np.array([], dtype=_LOADING_DTYPE)
    return np.array(loading_data, dtype=_LOADING_DTYPE)


def fit_error(x: NDArray[np.float64], y: NDArray[np.float64]) -> float:
    coeffs = np.polyfit(x, y, deg=1)
    y_pred = np.polyval(coeffs, x)
    return float(np.sum(y - y_pred)**2)

def bilinear(log_x: NDArray[np.float64], y: NDArray[np.float64]) -> Tuple[float, float, NDArray, NDArray]:
    """
    Bilinear fit to find yield point
    
    Params:
    x: 1-d array of np.log10(pressure)
    y: 1-d array of void ratio

    Returns:
    sigma_p, e_p

    """
    n = len(log_x)
    best k = None
    best_err = np.inf

    # Minimum of 2 points are needed
    for k in range(2, n-1):
        err = _fit_error(log_x[:k], y[:k]) + _fit_error(log_x[k:], y[k:])
        if err < best_err:
            best_err = err
            best_k = k

    coeff1 = np.polyfit(log_x[:best_k], y[:best_k], deg=1)
    coeff2 = np.polyfit(log_x[best_k:], y[best_k:], deg=1)

    dslope = (coeff1[0] - coeff2[0])
    if np.isclose(dslope, 0, atol=1e-10):
        raise ValueError("The two regression lines are parallel. Cannot determine intersection (yield) point.")
    
    log_p_init = (coeff1[1] - coeff2[1]) / dslope
    e_p = float(np.polyval(coeff1, log_p_init))

    sigma_p = float(10**log_p_init) # Return to original unit

    return sigma_p, e_p, 

# def _find_unloading_and_reloading_indices(stress: Sequence[float]) -> Tuple[List[int], List[int]]:
#     idx_unloading_init: List[int] = []
#     idx_reloading_init: List[int] = []
#     for i in range(1, len(stress) - 1):
#         if stress[i] > stress[i - 1] and stress[i] > stress[i + 1]:
#             idx_unloading_init.append(i)
#         if stress[i] < stress[i - 1] and stress[i] < stress[i + 1]:
#             idx_reloading_init.append(i)
#     return idx_unloading_init, idx_reloading_init