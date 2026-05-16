import uvicorn
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

@app.get("/test", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your test page."}

_LOADING_DTYPE = np.dtype([
    ("idx", np.intp),
    ("p", np.float64),
    ("log_p", np.float64),
    ("e", np.float64),
    ("epsilon", np.float64),
])

def loading_curve(x: NDArray[np.float64], y: NDArray[np.float64]) -> NDArray:
    """
    Remove unloading-reloading cycles
    """
    loading_data: list[Tuple[int, float, float, float]] = []
    max_p = -np.inf
    e0 = y[0]

    for i, (p, e) in enumerate(zip(x,y)):
        if p > max_p:
            log_p = np.log10(p) if p > 0 else 0.0
            epsilon = (e0-e)/(1+e0)
            loading_data.append((i, p, log_p, e, epsilon))
            max_p = p
    if not loading_data:
        return np.array([], dtype=_LOADING_DTYPE)
    return np.array(loading_data, dtype=_LOADING_DTYPE)


def _fit_error(x: NDArray[np.float64], y: NDArray[np.float64], deg: np.number = 1) -> float:
    coeffs = np.polyfit(x, y, deg)
    y_pred = np.polyval(coeffs, x)
    return float(np.sum(y - y_pred)**2)

def bilinear(x: NDArray[np.float64], y: NDArray[np.float64]) -> Tuple[float, float, float, float, float, np.number]:
    """
    General bilinear fit to find least square error
    
    Params:
    x: 1-d generic array, e.g., pressure
    y: 1-d generic array, e.g., void ratio

    Returns:
    x_int, y_int, coeffs1, coeffs2, seg1, seg2, best_k

    """
    n = len(x)
    deg = 1
    best_k = None
    best_err = np.inf

    # Minimum of 2 points are needed
    for k in range(2, n-1):
        err = _fit_error(x[:k], y[:k], deg) + _fit_error(x[k:], y[k:], deg)
        if err < best_err:
            best_err = err
            best_k = k

    coeffs1 = np.polyfit(x[:best_k], y[:best_k], deg)
    coeffs2 = np.polyfit(x[best_k:], y[best_k:], deg)

    dslope = (coeffs1[0] - coeffs2[0])
    if np.isclose(dslope, 0, atol=1e-10):
        raise ValueError("The two regression lines are parallel. Cannot determine intersection (yield) point.")
    
    x_int = (coeffs1[1] - coeffs2[1]) / dslope
    y_int = float(np.polyval(coeffs1, x_int))

    # Plotting parameters for each segment (extended to meet at intersection)
    x1 = np.append(x[:best_k], x_int)
    x2 = np.insert(x[best_k:], 0, x_int)
    seg1 = {"x": x1, "y_fit": np.polyval(coeffs1, x1)}
    seg2 = {"x": x2, "y_fit": np.polyval(coeffs2, x2)}

    return {
        "x_int": x_int, "y_int": y_int,
        "coeff1": coeffs1, "coeff2": coeffs2,
        "seg1": seg1, "seg2": seg2,
        "best_k": best_k,
    }

# def _find_unloading_and_reloading_indices(stress: Sequence[float]) -> Tuple[List[int], List[int]]:
#     idx_unloading_init: List[int] = []
#     idx_reloading_init: List[int] = []
#     for i in range(1, len(stress) - 1):
#         if stress[i] > stress[i - 1] and stress[i] > stress[i + 1]:
#             idx_unloading_init.append(i)
#         if stress[i] < stress[i - 1] and stress[i] < stress[i + 1]:
#             idx_reloading_init.append(i)
#     return idx_unloading_init, idx_reloading_init

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)