"""HTTP layer: request parsing, delegation to services, and error mapping."""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.config import get_settings
from app.models.schemas import ReadinessReport
from app.services.analyzer import analyze_readiness
from app.utils.file_handler import cleanup_dir, create_session_dir, save_upload

logger = logging.getLogger(__name__)
router = APIRouter()

PDF_EXTENSIONS = {"pdf"}
CSV_EXTENSIONS = {"csv"}


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.post("/api/analyze", response_model=ReadinessReport)
async def analyze_purchase_orders(
    pdfs: Annotated[list[UploadFile], File(description="Purchase order PDF files")],
    catalog: Annotated[UploadFile, File(description="Product catalog CSV file")],
) -> ReadinessReport:
    """Analyze uploaded purchase orders against the catalog and return the report."""
    settings = get_settings()
    session_dir = await asyncio.to_thread(create_session_dir, settings.upload_dir)
    try:
        pdf_paths = [
            await save_upload(upload, session_dir, PDF_EXTENSIONS, settings.max_file_size_bytes)
            for upload in pdfs
        ]
        catalog_path = await save_upload(
            catalog, session_dir, CSV_EXTENSIONS, settings.max_file_size_bytes
        )
        return await analyze_readiness(pdf_paths, catalog_path, settings.match_threshold)
    finally:
        await asyncio.to_thread(cleanup_dir, session_dir)
