"""Pack-size conversion: a real factor table, not a synonym map.

`units.normalize_unit` answers "are these the same unit?" This module answers
"how many pieces are in this pack?" -- the question a synonym map can never
answer.

All factors are integer piece counts. Conversions that are not well defined
(e.g. a 10 ft length sold as a carton of 25) raise PackConversionError rather
than inventing a number.
"""

from typing import Final


class PackConversionError(ValueError):
    """A pack conversion was requested that has no defined factor."""


# Each entry is either a piece count ("each", "pcs", ...) or a length in feet.
_PIECE: Final = "piece"
_FOOT: Final = "foot"

# Canonical pack unit -> how many base pieces it holds.
_PACK_FACTORS: Final[dict[str, tuple[str, float]]] = {
    # length-based packs
    "ft": (_FOOT, 1.0),
    "roll": (_FOOT, 100.0),       # wire rolls are commonly 100 ft
    "reel": (_FOOT, 1000.0),
    "spool": (_FOOT, 1000.0),
    # piece-count packs
    "pc": (_PIECE, 1.0),
    "ea": (_PIECE, 1.0),
    "pr": (_PIECE, 1.0),         # pair
    # distributor cartons
    "box": (_PIECE, 1.0),        # a box is customer-defined; NOT a factor
    "ctn": (_PIECE, 10.0),
    "carton": (_PIECE, 10.0),
    "dz": (_PIECE, 12.0),        # dozen
    "dozen": (_PIECE, 12.0),
    "pk": (_PIECE, 25.0),
    "pack": (_PIECE, 25.0),
    "cs": (_PIECE, 48.0),
    "case": (_PIECE, 48.0),
    "pl": (_PIECE, 1000.0),      # pallet
    "pallet": (_PIECE, 1000.0),
}

# Units whose quantity depends entirely on the product, so no factor is safe.
_AMBIGUOUS: Final[frozenset[str]] = frozenset({"box", "case", "cs", "pack", "pk"})


def pack_factor(unit: str) -> tuple[str, float] | None:
    """
    Return (base_kind, factor) for a unit, or None when the unit is unknown.

    Raises PackConversionError for units that are known but customer-defined,
    because silently guessing a factor would corrupt order quantities.
    """
    key = unit.strip().lower().rstrip(".")
    if not key:
        return None
    if key in _AMBIGUOUS:
        raise PackConversionError(
            f"'{unit}' is customer-defined; set an explicit pack quantity before converting"
        )
    return _PACK_FACTORS.get(key)


def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a quantity between units of the same base kind.

    Raises PackConversionError when the units measure different things
    (pieces vs feet) or when either side is customer-defined.
    """
    source = pack_factor(from_unit)
    target = pack_factor(to_unit)
    if source is None:
        raise PackConversionError(f"unknown unit '{from_unit}'")
    if target is None:
        raise PackConversionError(f"unknown unit '{to_unit}'")
    if source[0] != target[0]:
        raise PackConversionError(
            f"cannot convert {source[0]}s to {target[0]}s "
            f"('{from_unit}' -> '{to_unit}'): different kinds of quantity"
        )
    pieces = quantity * source[1]
    result = pieces / target[1]
    return int(result) if float(result).is_integer() else round(result, 4)


def pack_size_mismatch(po_unit: str, catalog_unit: str, catalog_pack_qty: float | None) -> bool:
    """
    Decide whether a PO unit and a catalog unit represent the same pack size.

    Returns True only when the two are genuinely different pack sizes. Equal
    units, unknown units, and customer-defined units never produce a mismatch,
    because there is no evidence of a conflict.
    """
    # A missing or unrecognised unit is *no evidence*, never a conflict. Only a
    # unit we can actually resolve into a known factor may raise a mismatch.
    try:
        source = pack_factor(po_unit)
        target = pack_factor(catalog_unit)
    except PackConversionError:
        return False
    if source is None or target is None or source[0] != target[0]:
        return False
    if catalog_pack_qty and catalog_pack_qty > 0:
        # The catalog states its own pack size explicitly; trust that over the
        # generic factor table.
        try:
            return convert_quantity(1.0, po_unit, "ea") != catalog_pack_qty
        except PackConversionError:
            return False
    return False
