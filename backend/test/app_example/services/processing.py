from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from scipy.interpolate import CubicSpline


@dataclass(frozen=True)
class ProcessResult:
    compression_idx: Optional[float]
    recompression_idx: Optional[float]
    warnings: List[str]


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


def _compute_compression_idx_cubic_spline(stress: np.ndarray, void_ratio: np.ndarray) -> Optional[float]:
    if len(stress) < 3:
        return None

    stress_pos_mask = stress > 0
    if not np.any(stress_pos_mask):
        return None

    stress_pos = stress[stress_pos_mask]
    void_ratio_pos = void_ratio[stress_pos_mask]
    if len(stress_pos) < 2:
        return None

    sigma_log = np.log10(stress_pos)
    if len(np.unique(sigma_log)) < 2:
        return None

    cs = CubicSpline(x=sigma_log, y=void_ratio_pos)
    sigma_cs = np.linspace(float(sigma_log[0]), float(sigma_log[-1]), 500)
    slopes = cs(sigma_cs, 1)
    idx = int(np.argmin(slopes))
    return float(abs(slopes[idx]))


def _compute_recompression_idx_opt1(stress: np.ndarray, void_ratio: np.ndarray, brk_idx_1: int, brk_idx_2: int) -> Optional[float]:
    sigma = np.array([stress[brk_idx_1], stress[brk_idx_2]], dtype=float)
    e = np.array([void_ratio[brk_idx_1], void_ratio[brk_idx_2]], dtype=float)
    if np.any(sigma <= 0) or np.any(~np.isfinite(sigma)) or np.any(~np.isfinite(e)):
        return None
    sigma_log = np.log10(sigma)
    if len(np.unique(sigma_log)) < 2:
        return None
    intercept, slope = np.polynomial.polynomial.polyfit(sigma_log, e, deg=1)
    _ = intercept
    return float(abs(slope))


def process_rows(
    *,
    sigma_v: float,
    rows: Iterable[Tuple[object, object]],
) -> ProcessResult:
    warnings: List[str] = []

    pressures: List[float] = []
    void_ratios: List[float] = []
    dropped = 0
    for pressure_raw, void_ratio_raw in rows:
        pressure = _to_float(pressure_raw)
        void_ratio = _to_float(void_ratio_raw)
        if pressure is None or void_ratio is None:
            dropped += 1
            continue
        pressures.append(pressure)
        void_ratios.append(void_ratio)

    if dropped > 0:
        warnings.append(f"Dropped {dropped} row(s) with null or non-finite values.")

    if sigma_v <= 0 or not np.isfinite(sigma_v):
        return ProcessResult(compression_idx=None, recompression_idx=None, warnings=warnings + ["sigmaV must be a positive finite number."])

    if len(pressures) < 3:
        return ProcessResult(
            compression_idx=None,
            recompression_idx=None,
            warnings=warnings + ["Need at least 3 valid rows to compute indices."],
        )

    stress = np.asarray(pressures, dtype=float)
    e = np.asarray(void_ratios, dtype=float)

    if np.any(~np.isfinite(stress)) or np.any(~np.isfinite(e)):
        return ProcessResult(compression_idx=None, recompression_idx=None, warnings=warnings + ["Input contains non-finite numbers."])

    compression_idx = _compute_compression_idx_cubic_spline(stress, e)
    if compression_idx is None:
        warnings.append("compressionIdx could not be computed (need at least two distinct positive pressures).")

    idx_unloading_init, idx_reloading_init = _find_unloading_and_reloading_indices(stress.tolist())
    if len(idx_unloading_init) == 0 or len(idx_reloading_init) == 0:
        return ProcessResult(
            compression_idx=compression_idx,
            recompression_idx=None,
            warnings=warnings + ["No unloading/reloading stage detected; recompressionIdx (opt=1) not computed."],
        )

    use_stage = 0
    brk_idx_1 = idx_unloading_init[use_stage]
    brk_idx_2 = idx_reloading_init[use_stage]
    if brk_idx_2 <= brk_idx_1:
        return ProcessResult(
            compression_idx=compression_idx,
            recompression_idx=None,
            warnings=warnings + ["Unloading/reloading break indices were not valid; recompressionIdx not computed."],
        )

    recompression_idx = _compute_recompression_idx_opt1(stress, e, brk_idx_1, brk_idx_2)
    if recompression_idx is None:
        warnings.append("recompressionIdx could not be computed (requires two distinct positive pressures in unloading stage).")

    return ProcessResult(
        compression_idx=compression_idx,
        recompression_idx=recompression_idx,
        warnings=warnings,
    )

