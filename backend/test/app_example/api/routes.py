from __future__ import annotations

import anyio
from fastapi import APIRouter

from app.models import ProcessRequest, ProcessResponse
from app.services.processing import process_rows


router = APIRouter()


@router.post("/api/process", response_model=ProcessResponse)
async def process(request: ProcessRequest) -> ProcessResponse:
    result = await anyio.to_thread.run_sync(
        process_rows,
        sigma_v=request.sigmaV,
        rows=((r.pressure, r.void_ratio) for r in request.rows),
    )
    return ProcessResponse(
        compressionIdx=result.compression_idx,
        recompressionIdx=result.recompression_idx,
        warnings=result.warnings,
    )

