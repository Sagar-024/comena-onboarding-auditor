"""Pydantic schemas for pipeline inputs and the readiness report."""

from typing import Literal

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """A single purchase order line as extracted from the document."""

    quantity: float = 0
    unit: str = ""
    description: str
    unit_price: float | None = None
    line_total: float | None = None


class MatchedLineItem(LineItem):
    """A line item enriched with catalog matching results."""

    matched_sku: str | None = None
    match_score: float = 0.0
    match_method: Literal["fuzzy", "none"] = "none"
    catalog_unit: str | None = None
    best_candidate_sku: str | None = None
    best_candidate_score: float | None = None


class ExtractedDocument(BaseModel):
    """Structured content of one purchase order document."""

    filename: str
    po_number: str | None = None
    vendor: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)


class CatalogEntry(BaseModel):
    """One product row from the customer's catalog CSV."""

    sku: str
    description: str
    unit_of_measure: str = ""


class UnitMismatch(BaseModel):
    """A matched line whose PO unit differs from the catalog unit."""

    sku: str
    description: str
    po_unit: str
    catalog_unit: str


class CatalogGap(BaseModel):
    """An unmatched description together with its nearest catalog candidate."""

    description: str
    best_candidate_sku: str | None = None
    best_candidate_score: float | None = None


class ReadinessReport(BaseModel):
    """Final onboarding readiness assessment across all uploaded documents."""

    documents_processed: int
    total_line_items: int
    matched_items: int
    match_rate: float
    overall_score: float
    unmatched_descriptions: list[str]
    catalog_gaps: list[CatalogGap]
    unit_mismatches: list[UnitMismatch]
    erp_mapping_flags: list[str]
    recommendations: list[str]
