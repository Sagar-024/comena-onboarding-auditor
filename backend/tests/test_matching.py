"""Tests for the attribute matcher and the pack-size conversion table.

These lock in the behaviour measured on the frozen eval set. They do NOT tune:
every threshold and weight is asserted as-is, so a change that alters accuracy
fails loudly here instead of silently.

Run from the project root with the backend venv:

    backend/.venv/Scripts/python.exe -m pytest backend/tests -q
"""

import csv
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.services.attribute_extractor import (  # noqa: E402
    canonicalize,
    extract_attributes,
)
from app.services.attribute_matcher import (  # noqa: E402
    AMBIGUITY_MARGIN,
    MATCH_THRESHOLD,
    match_description,
)
from app.utils.pack_conversion import (  # noqa: E402
    PackConversionError,
    convert_quantity,
    pack_factor,
    pack_size_mismatch,
)

EVAL_DIR = Path(__file__).resolve().parents[2] / "eval"
CATALOG_CSV = EVAL_DIR / "frozen_catalog.csv"
EVAL_CSV = EVAL_DIR / "frozen_eval_set.csv"


def _catalog() -> list[dict[str, str]]:
    """Load the frozen catalog."""
    with CATALOG_CSV.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _eval_rows() -> list[dict[str, str]]:
    """Load the frozen labelled set."""
    with EVAL_CSV.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# --- attribute extraction ---------------------------------------------------


@pytest.mark.parametrize(
    ("text", "key", "expected"),
    [
        ("3/8 x 2 hex bolt zinc plated", "family", "hex_bolt"),
        ("3/8 x 2 hex bolt zinc plated", "diameter", "3/8"),
        ("3/8 x 2 hex bolt zinc plated", "finish", "Zinc"),
        ("hex bolt 3/8-16 x 2in zinc CR+3", "thread_pitch", "16"),
        ("ball bearing 6203 2RS sealed", "family", "ball_bearing"),
        ("M10 stainless flat washer", "diameter", "m10"),
        ("3/4 galvanized emt connector", "finish", "Galvanized"),
        ("1 inch brass ball valve fip", "diameter", "1"),
    ],
)
def test_extracts_expected_attributes(text: str, key: str, expected: str) -> None:
    """Key attributes survive extraction from messy distributor wording."""
    assert extract_attributes(text).get(key) == expected, f"{key} wrong for {text!r}"


def test_bearing_designation_is_captured() -> None:
    """A 4-digit bearing code is a product identity, not a length."""
    assert extract_attributes("6204-2RS sealed ball bearing")["bearing"] == "6204-2RS"


def test_mixed_fraction_length_becomes_decimal() -> None:
    """'3-1/2' normalises to 3.5 so it can equal a catalog value of 3.5."""
    assert extract_attributes("5/8-11 x 3-1/2 stainless hex bolt")["length"] == "3.5"


def test_rating_is_not_mistaken_for_a_length() -> None:
    """600V wire gauge and 125# pressure must never be read as lengths."""
    assert "length" not in extract_attributes("thhn wire 12-3 black 600v")

# --- matching ---------------------------------------------------------------


def test_empty_catalog_returns_no_match() -> None:
    """An empty catalog must not raise and must not invent a SKU."""
    sku, score, _runner, conflicts = match_description("3/8 x 2 hex bolt", [])
    assert sku is None
    assert score == 0.0
    # An empty catalog is not a "conflict" -- there was nothing to conflict with.
    assert conflicts == []


def test_exact_attribute_match_is_found() -> None:
    """The canonical query resolves to its SKU regardless of word order."""
    sku, *_ = match_description("3/8 x 2 hex bolt zinc plated", _catalog())
    assert sku == "HB-375-200-Z"


def test_conflicting_length_is_never_forced() -> None:
    """2 inch and 3 inch bolts are different products."""
    two_inch, *_ = match_description("1/2-13 x 2 hex bolt zinc", _catalog())
    three_inch, *_ = match_description("1/2-13 x 3 hex bolt zinc", _catalog())
    assert two_inch == "HB-500-200-Z"
    assert three_inch == "HB-500-300-Z"


def test_conflicting_material_is_never_forced() -> None:
    """Zinc and stainless are different products."""
    zinc, *_ = match_description("3/8 hex nut zinc", _catalog())
    stainless, *_ = match_description("5/8-11 stainless hex nut 316", _catalog())
    assert zinc == "NUT-375-ZN"
    assert stainless == "NUT-625-SS"


def test_absent_item_returns_no_match() -> None:
    """An item with no catalog counterpart is never forced onto the nearest SKU."""
    sku, *_ = match_description("M8 hex bolt zinc plated", _catalog())
    assert sku is None


def test_bearing_codes_do_not_cross_match() -> None:
    """6203, 6204 and 6205 are distinct bearings."""
    assert match_description("6204-2RS ball bearing sealed", _catalog())[0] == "BRG-6204-2RS"
    assert match_description("6205-2RS ball bearing sealed", _catalog())[0] == "BRG-6205-2RS"


def test_no_wrong_sku_is_ever_returned_across_the_frozen_set() -> None:
    """The safety property: never auto-match to the wrong product."""
    catalog = _catalog()
    for row in _eval_rows():
        sku, *_ = match_description(row["text"], catalog)
        if sku is not None:
            assert sku == row["expected_sku"], f"wrong SKU for {row['text']!r}"


def test_thresholds_match_the_documented_values() -> None:
    """Guard the two tuned constants so a silent change is visible."""
    assert MATCH_THRESHOLD == 60.0
    assert AMBIGUITY_MARGIN == 8.0


# --- pack conversion --------------------------------------------------------


@pytest.mark.parametrize(
    ("quantity", "from_unit", "to_unit", "expected"),
    [
        (1, "dz", "ea", 12),
        (2, "dozen", "ea", 24),
        (1, "ctn", "ea", 10),
        (1, "carton", "ea", 10),
        (1, "pallet", "ea", 1000),
        (12, "ea", "dz", 1),
        (120, "ea", "dz", 10),
        (1, "roll", "ft", 100),
    ],
)
def test_converts_between_packs_and_pieces(
    quantity: float, from_unit: str, to_unit: str, expected: float
) -> None:
    """Pack factors are real quantities, not synonym equivalence."""
    assert convert_quantity(quantity, from_unit, to_unit) == expected


def test_same_unit_never_reports_a_mismatch() -> None:
    """Identical units cannot be a pack-size conflict."""
    assert pack_size_mismatch("ea", "ea", 1) is False
    assert pack_size_mismatch("Carton", "carton", 10) is False


def test_different_pack_sizes_report_a_mismatch() -> None:
    """A carton of 10 against catalog stock kept in eaches is a real conflict."""
    assert pack_size_mismatch("ctn", "ea", 1) is True
    assert pack_size_mismatch("dz", "ea", 1) is True


@pytest.mark.skip(
    reason="Obsolete: 'case'/'cs' are customer-defined and now refuse conversion; "
    "covered by test_customer_defined_units_are_never_guessed."
)
def test_case_converts_to_48_pieces() -> None:
    """Superseded by the customer-defined-unit rule; kept for history."""
    assert convert_quantity(1, "case", "ea") == 48


def test_customer_defined_units_are_never_guessed() -> None:
    """A 'box' has no universal size, so it must raise rather than assume."""
    with pytest.raises(PackConversionError):
        pack_factor("box")
    with pytest.raises(PackConversionError):
        pack_factor("case")


def test_pieces_and_feet_are_not_interchangeable() -> None:
    """Converting between different kinds of quantity must fail loudly."""
    with pytest.raises(PackConversionError):
        convert_quantity(1, "roll", "ea")


def test_unknown_unit_raises() -> None:
    """An unrecognised unit has no defined factor."""
    with pytest.raises(PackConversionError):
        convert_quantity(1, "parsec", "ea")


def test_empty_unit_is_not_treated_as_a_mismatch() -> None:
    """No unit stated means no evidence of conflict."""
    assert pack_size_mismatch("", "ea", 1) is False

    assert extract_attributes("globe valve 1-1/4 bronze 125#")["pressure"] == "125"


def test_canonicalize_normalises_case_and_number_format() -> None:
    """'Zinc'/'zinc' and '2.0'/'2' must compare equal."""
    assert canonicalize({"finish": "Zinc", "length": "2.0"}) == canonicalize(
        {"finish": "zinc", "length": "2"}
    )


def test_extract_empty_string_yields_nothing() -> None:
    """Empty input is safe and produces no attributes."""
    assert extract_attributes("") == {}
