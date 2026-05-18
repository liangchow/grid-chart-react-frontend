import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


# Define models
class RowIn(BaseModel):
    pressure: Optional[float] = None
    void_ratio: Optional[float] = None

class ProcessRequest(BaseModel):
    sigmaV0: float = Field(..., gt=0)
    rows: List[RowIn]

class Point(BaseModel):
    x: float  # pressure (linear scale)
    y: float  # void ratio

class ProcessResponse(BaseModel):
    """
    Data needed to render the bilinear fit in the frontend Chart.
    segment1 / segment2: arrays of {x, y} points (pressure, void ratio) for each fit line.
    intersection: the yield point where the two lines meet (preconsolidation pressure).
    """
    segment1: List[Point]
    segment2: List[Point]
    intersection: Point
    warnings: List[str]
    compressionIdx: Optional[float] = None
    recompressionIdx: Optional[float] = None

# App setup
app = FastAPI(debug=True)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

# App functions

@app.get("/test", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your test page."}

@app.post("/process", tags=["process"])
async def process(request: ProcessRequest) -> ProcessResponse:
    warnings: List[str] = []

    # 1. Extract finite, positive-pressure rows
    pairs = [
        (r.pressure, r.void_ratio)
        for r in request.rows
        if r.pressure is not None
        and r.void_ratio is not None
        and np.isfinite(r.pressure)
        and np.isfinite(r.void_ratio)
        and r.pressure > 0
    ]

    if len(pairs) < 4:
        raise HTTPException(
            status_code=422,
            detail="At least 4 valid data points (positive pressure, finite void ratio) are required."
        )

    x = np.array([p[0] for p in pairs], dtype=np.float64)
    y = np.array([p[1] for p in pairs], dtype=np.float64)

    # Step 1: isolate the loading curve (strip unloading-reloading cycles)
    lc = loading_curve(x, y)

    if len(lc) < 4:
        raise HTTPException(
            status_code=422,
            detail="Not enough monotonically increasing pressure points to fit a loading curve."
        )

    # Step 2: bilinear fit in log(P) – void ratio space
    try:
        fit = bilinear(lc["log_p"], lc["e"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # seg1/seg2 x-values are log10(pressure); convert back to pressure for the Chart
    def to_points(log_p_arr: NDArray, e_arr: NDArray) -> List[Point]:
        return [Point(x=float(10 ** lp), y=float(e)) for lp, e in zip(log_p_arr, e_arr)]

    segment1 = to_points(fit["seg1"]["x"], fit["seg1"]["y_fit"])
    segment2 = to_points(fit["seg2"]["x"], fit["seg2"]["y_fit"])
    intersection = Point(x=float(10 ** fit["x_int"]), y=float(fit["y_int"]))

    return ProcessResponse(
        segment1=segment1,
        segment2=segment2,
        intersection=intersection,
        warnings=warnings,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
