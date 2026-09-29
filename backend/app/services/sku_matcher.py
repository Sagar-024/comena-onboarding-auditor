"""Catalog loading and fuzzy SKU matching."""

import logging
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from app.exceptions import CatalogValidationError
from app.models.schemas import CatalogEntry, LineItem, MatchedLineItem

logger = logging.getLogger(__name__)

_SKU_COLUMNS = ("sku", "item_code", "item_no", "item_number", "part_number", "part_no", "product_code", "code", "material")
_DESCRIPTION_COLUMNS = (
    "description",
    "item_description",
    "product_description",
    "product_name",
    "name",
    "desc",
    "item_desc",
)
_UNIT_COLUMNS = ("unit_of_measure", "unit", "uom", "u_m", "units", "um", "unit_measure")


def load_catalog(csv_path: Path | str) -> list[CatalogEntry]:
    """Load and normalize the catalog CSV, raising CatalogValidationError when unusable."""
    try:
        frame = pd.read_csv(csv_path, dtype=str)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        raise CatalogValidationError(f"could not read catalog CSV: {exc}") from exc

    frame.columns = [_normalize_column(column) for column in frame.columns]
    frame = frame.fillna("")
    sku_column = _find_column(frame, _SKU_COLUMNS, "SKU")
    description_column = _find_column(frame, _DESCRIPTION_COLUMNS, "description")
    unit_column = _find_column(frame, _UNIT_COLUMNS, "unit", required=False)

    entries = [
        CatalogEntry(
            sku=row[sku_column].strip(),
            description=row[description_column].strip(),
            unit_of_measure=row[unit_column].strip() if unit_column else "",
        )
        for row in frame.to_dict("records")
        if row.get(sku_column) and row.get(description_column)
    ]
    if not entries:
        raise CatalogValidationError("catalog CSV has no rows with both SKU and description")
    logger.info("loaded %d catalog entries from %s", len(entries), Path(csv_path).name)
    return entries


def match_line_items(
    items: list[LineItem],
    catalog: list[CatalogEntry],
    threshold: int,
) -> list[MatchedLineItem]:
    """Fuzzy match every line item against catalog descriptions at the given threshold."""
    matched = [MatchedLineItem(**item.model_dump()) for item in items]
    if not matched or not catalog:
        return matched

    descriptions = [entry.description for entry in catalog]
    for item in matched:
        result = process.extractOne(item.description, descriptions, scorer=fuzz.token_sort_ratio)
        if result is None:
            continue
        _, score, index = result
        entry = catalog[index]
        item.match_score = round(float(score), 1)
        if score >= threshold:
            item.matched_sku = entry.sku
            item.match_method = "fuzzy"
            item.catalog_unit = entry.unit_of_measure
        else:
            item.best_candidate_sku = entry.sku
            item.best_candidate_score = round(float(score), 1)
    return matched


def _normalize_column(column: str) -> str:
    """Collapse a header to its snake_case form so aliases match reliably."""
    return re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")


def _find_column(
    frame: pd.DataFrame,
    candidates: tuple[str, ...],
    label: str,
    *,
    required: bool = True,
) -> str | None:
    """Locate a catalog column by exact snake_case match against known aliases."""
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    if required:
        looked_for = ", ".join(candidates)
        raise CatalogValidationError(f"catalog CSV is missing a {label} column (looked for: {looked_for})")
    return None
