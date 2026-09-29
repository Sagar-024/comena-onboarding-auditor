"""Readiness analysis: pipeline orchestration and report computation."""

import asyncio
import logging
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from app.exceptions import LLMParsingError
from app.models.schemas import (
    CatalogEntry,
    CatalogGap,
    ExtractedDocument,
    MatchedLineItem,
    ReadinessReport,
    UnitMismatch,
)
from app.services.llm_parser import parse_document
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.sku_matcher import load_catalog, match_line_items
from app.utils.units import normalize_unit

logger = logging.getLogger(__name__)


async def analyze_readiness(
    pdf_paths: Sequence[Path],
    catalog_path: Path,
    threshold: int,
) -> ReadinessReport:
    """Run the full pipeline over the PDFs plus catalog and return the readiness report."""
    catalog = await asyncio.to_thread(load_catalog, catalog_path)
    documents = await _extract_documents(pdf_paths)
    report = analyze(documents, catalog, threshold)
    logger.info(
        "analysis complete: %d/%d line items matched (score %.1f)",
        report.matched_items,
        report.total_line_items,
        report.overall_score,
    )
    return report


def analyze(
    documents: list[ExtractedDocument],
    catalog: list[CatalogEntry],
    threshold: int,
) -> ReadinessReport:
    """Compute the readiness report from extracted documents and a loaded catalog."""
    all_items = [item for document in documents for item in document.line_items]
    matched_items = match_line_items(all_items, catalog, threshold)
    total = len(matched_items)
    matched_count = sum(1 for item in matched_items if item.match_method == "fuzzy")
    match_rate = matched_count / total if total else 0.0
    unit_mismatches = _find_unit_mismatches(matched_items)
    unmatched = [item for item in matched_items if item.matched_sku is None]
    return ReadinessReport(
        documents_processed=len(documents),
        total_line_items=total,
        matched_items=matched_count,
        match_rate=round(match_rate, 4),
        overall_score=round(match_rate * 100, 1),
        unmatched_descriptions=sorted({item.description for item in unmatched}),
        catalog_gaps=_collect_catalog_gaps(unmatched),
        unit_mismatches=unit_mismatches,
        erp_mapping_flags=_build_erp_flags(unmatched, unit_mismatches, total),
        recommendations=_build_recommendations(match_rate, unmatched, unit_mismatches),
    )


async def _extract_documents(pdf_paths: Sequence[Path]) -> list[ExtractedDocument]:
    """Extract and LLM-parse every PDF concurrently, preserving input order."""
    return list(await asyncio.gather(*(_extract_document(path) for path in pdf_paths)))


async def _extract_document(path: Path) -> ExtractedDocument:
    """Extract text from one PDF and structure it through the LLM."""
    text = await asyncio.to_thread(extract_text_from_pdf, path)
    payload = await parse_document(text)
    return _validated_document(payload, path.name)


def _validated_document(payload: dict, filename: str) -> ExtractedDocument:
    """Attach the source filename and enforce the document schema."""
    try:
        return ExtractedDocument.model_validate({**payload, "filename": filename})
    except ValidationError as exc:
        raise LLMParsingError(f"LLM output for '{filename}' failed schema validation: {exc}") from exc


def _find_unit_mismatches(items: list[MatchedLineItem]) -> list[UnitMismatch]:
    """Flag matched lines whose PO unit differs from the catalog unit."""
    return [
        UnitMismatch(
            sku=item.matched_sku or "",
            description=item.description,
            po_unit=item.unit,
            catalog_unit=item.catalog_unit or "",
        )
        for item in items
        if item.matched_sku
        and item.unit
        and item.catalog_unit
        and normalize_unit(item.unit) != normalize_unit(item.catalog_unit)
    ]


def _collect_catalog_gaps(unmatched: list[MatchedLineItem]) -> list[CatalogGap]:
    """Group unmatched descriptions with their nearest catalog candidate."""
    gaps: dict[str, CatalogGap] = {}
    for item in unmatched:
        gaps.setdefault(
            item.description,
            CatalogGap(
                description=item.description,
                best_candidate_sku=item.best_candidate_sku,
                best_candidate_score=item.best_candidate_score,
            ),
        )
    return list(gaps.values())


def _build_erp_flags(
    unmatched: list[MatchedLineItem],
    mismatches: list[UnitMismatch],
    total: int,
) -> list[str]:
    """Summarize the concrete blockers an ERP integration would hit."""
    flags: list[str] = []
    if unmatched and total:
        flags.append(
            f"{len(unmatched)} of {total} line items have no catalog SKU "
            "and would require manual ERP entry."
        )
    if mismatches:
        flags.append(
            f"{len(mismatches)} line items use a different unit of measure than the catalog; "
            "ERP unit conversion rules must be configured."
        )
    return flags


def _build_recommendations(
    match_rate: float,
    unmatched: list[MatchedLineItem],
    mismatches: list[UnitMismatch],
) -> list[str]:
    """Turn the match statistics into next actions for the onboarding team."""
    recommendations: list[str] = []
    if match_rate >= 0.9:
        recommendations.append("Match rate is high; this catalog is ready for automated order entry.")
    elif match_rate >= 0.7:
        recommendations.append("Review the unmatched descriptions and add catalog aliases before go-live.")
    else:
        recommendations.append(
            "Match rate is below 70%; enrich the catalog with the customer's product "
            "names and internal SKUs before deployment."
        )
    if unmatched:
        distinct = len({item.description for item in unmatched})
        recommendations.append(f"Add or alias {distinct} unmatched descriptions in the catalog.")
    if mismatches:
        recommendations.append("Set up unit-of-measure conversions in the ERP for the flagged SKUs.")
    return recommendations
