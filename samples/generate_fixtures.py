"""One-off generator for the sample PO PDFs and catalog used in manual testing.

Run from the project root with the backend venv:
    backend/.venv/Scripts/python.exe samples/generate_fixtures.py

The fixtures are deliberately imperfect: two unit-of-measure mismatches, two
descriptions that have no catalog SKU, and one fuzzy near-match, so the
readiness report has something real to surface.
"""

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SAMPLES_DIR = Path(__file__).parent

CATALOG_HEADER = ["sku", "description", "unit_of_measure", "list_price"]
CATALOG_ROWS = [
    ["HB-375-200-Z", "Hex Bolt 3/8-16 x 2 Zinc Cr+3", "Box", "42.50"],
    ["HB-500-300-Z", "Hex Bolt 1/2-13 x 3 Zinc Cr+3", "Box", "68.00"],
    ["NUT-375-ZN", "Hex Nut 3/8-16 Zinc", "Pcs", "0.18"],
    ["WR-R1882-ZN", "Flat Washer 3/8 Zinc", "Pcs", "0.06"],
    ["BRG-6203-2RS", "Ball Bearing 6203-2RS Sealed", "Pcs", "3.85"],
    ["VLV-BV-075-BR", "Ball Valve 3/4 Brass FIP", "Ea", "14.20"],
    ["GLV-1042", "Globe Valve 1 1/4 Bronze 125#", "Ea", "96.40"],
    ["GLV-1062", "Globe Valve 1 1/2 Bronze 150#", "Ea", "132.75"],
    ["TYW-114-316", "Ty-Wrap Cable Tie 11in 316SS", "Pcs", "0.42"],
    ["SAF-GLV-C", "Safety Glasses Clear Anti-Fog", "Ea", "2.10"],
]

PO_LINES_ACME = [
    ["20", "Box", "Hex Bolt 3/8-16 x 2 Zinc", "42.50", "850.00"],
    ["500", "Pcs", "Hex Nut 3/8-16 Zinc", "0.18", "90.00"],
    ["6", "Carton", "Ball Valve 3/4 Brass FIP", "14.20", "85.20"],
]

PO_LINES_PREMIUM = [
    ["100", "Ea", "Safety Glasses Clear Anti-Fog", "2.10", "210.00"],
    ["5", "Box", "Globe Valve 1 1/4 Bronze 125#", "96.40", "482.00"],
    ["24", "Ea", "Stainless Steel Cable Ties 11 inch", "0.55", "13.20"],
    ["200", "Box", "M8 x 40 Socket Head Cap Screw Black", "11.90", "2380.00"],
]


def write_catalog(path: Path) -> None:
    """Write the product catalog CSV."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CATALOG_HEADER)
        writer.writerows(CATALOG_ROWS)


def build_po_pdf(path: Path, buyer: str, po_number: str, vendor: str, po_date: str, lines: list[list[str]]) -> None:
    """Render one purchase order as a simple tabular PDF."""
    styles = getSampleStyleSheet()
    table_data = [["Qty", "Unit", "Description", "Unit Price", "Line Total"]] + lines
    table = Table(table_data, colWidths=[50, 60, 220, 80, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story = [
        Paragraph(buyer, styles["Title"]),
        Paragraph(f"Purchase Order {po_number}", styles["Heading2"]),
        Paragraph(f"Vendor: {vendor}<br/>Date: {po_date}", styles["Normal"]),
        Spacer(1, 12),
        table,
        Spacer(1, 12),
        Paragraph("Payment terms: Net 30. Ship complete to warehouse dock B.", styles["Normal"]),
    ]
    SimpleDocTemplate(str(path), pagesize=LETTER, title=po_number).build(story)


def main() -> None:
    """Generate the catalog CSV and both sample PO PDFs."""
    SAMPLES_DIR.mkdir(exist_ok=True)
    write_catalog(SAMPLES_DIR / "catalog.csv")
    build_po_pdf(
        SAMPLES_DIR / "po-acme-4102.pdf",
        buyer="ACME INDUSTRIAL SUPPLY CO.",
        po_number="PO-4102",
        vendor="Zinc Fastener Works",
        po_date="2026-09-21",
        lines=PO_LINES_ACME,
    )
    build_po_pdf(
        SAMPLES_DIR / "po-premium-0088.pdf",
        buyer="PREMIUM FASTENERS AND TOOLS",
        po_number="PO-0088",
        vendor="Great Lakes Valve Distribution",
        po_date="2026-09-24",
        lines=PO_LINES_PREMIUM,
    )
    print(f"wrote {len(CATALOG_ROWS)} catalog rows and 2 sample POs to {SAMPLES_DIR}")


if __name__ == "__main__":
    main()
