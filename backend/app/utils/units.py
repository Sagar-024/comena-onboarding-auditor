"""Unit-of-measure normalization for PO and catalog comparisons."""

from typing import Final

_ALIASES: Final[dict[str, str]] = {
    "ea": "each",
    "each": "each",
    "eaches": "each",
    "pc": "each",
    "pcs": "each",
    "piece": "each",
    "pieces": "each",
    "box": "box",
    "boxes": "box",
    "bx": "box",
    "carton": "carton",
    "cartons": "carton",
    "ctn": "carton",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
}


def normalize_unit(unit: str) -> str:
    """Map a unit of measure to its canonical form; unknown units pass through lowercased."""
    key = unit.strip().lower().rstrip(".")
    return _ALIASES.get(key, key)
