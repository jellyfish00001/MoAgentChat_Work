from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from flows.domain.qv_dms.workbook import (
    CONTRACT,
    NS,
    CoverValues,
    DmsInputError,
    accounting_row,
    code,
    compare_golden,
    cover_xml,
    period,
)
from flows.graphs.qv_dms_pipeline.graph import graph

FIXTURES = Path(__file__).resolve().parents[2] / "testdata" / "qv_dms" / "faa29_sprint2"


def make_workbook(path: Path) -> None:
    book = Workbook()
    cover = book.active
    cover.title = "Cover"
    cover["B2"] = date(2026, 1, 31)
    for col, pc in ((5, "TEST-PC"), (6, "OTHER-PC"), (7, "Total")):
        cover.cell(6, col, pc)
    labels = {
        8: "Sampling Amount",
        9: "Sampling Ratio",
        23: "Sub-total",
        24: "Vendor paid",
        27: "Material scrap",
        28: "Other",
        29: "Sub-total",
        30: "Adjust to 65011201-Manual",
        31: "Adjust to 65011210-Manual",
        34: "Preivous QV Auto reverse",
        35: "Current QV Auto reservation",
        36: "Sub-total",
        78: "Sub-total",
        79: "Total",
    }
    for row, label in labels.items():
        cover.cell(row, 4, label)
    cover["A81"] = "Total QV Return"
    for row in range(10, 23):
        cover.cell(row, 2, row - 9)
    for row, key in enumerate(["918", "924", "938&944", *range(1000, 1038)], 37):
        cover.cell(row, 2, key)
    for col in (5, 6):
        letter = get_column_letter(col)
        cover.cell(8, col, f"=SUM({letter}10:{letter}20)")
        cover.cell(9, col, f"=IF({letter}$8=0,0,{letter}$8/({letter}$23-{letter}$21))")
        for row, formula in {
            23: f"SUM({letter}10:{letter}22)",
            29: f"SUM({letter}24:{letter}28)",
            36: f"SUM({letter}30:{letter}35)",
            78: f"SUM({letter}37:{letter}77)",
            79: f"SUM({letter}23,{letter}29,{letter}36,{letter}78)",
            81: f"{letter}79+{letter}80",
        }.items():
            cover.cell(row, col, "=" + formula)
    for row in range(8, 82):
        if row != 9:
            cover.cell(row, 7, f"=SUM(E{row}:F{row})")
    cover["E38"] = 10
    for name, fields in CONTRACT.items():
        sheet = book.create_sheet(name)
        for col, title in fields.items():
            sheet.cell(1, col, title)
    for row, pc, value, reason in (
        (2, "TEST-PC", 12.5, "01.Bom change"),
        (3, "OTHER-PC", 5, "10.替代料"),
    ):
        sheet = book["材料分析"]
        for col, item in ((14, pc), (54, value), (56, reason)):
            sheet.cell(row, col, item)
    for row, pc, value, moh in ((2, "TEST-PC", 30, 2), (3, "OTHER-PC", 8, 1)):
        for col, item in ((77, pc), (18, value), (71, moh)):
            book["生產工單"].cell(row, col, item)
    for col, item in ((4, "TEST-PC"), (17, 3), (18, "短装材料扣款")):
        book["會計調整"].cell(2, col, item)
    for row, value, remark in (
        (2, 4, "202601 QV/PV/STD Change Adjustment"),
        (3, -2, "202512 QV/PV/STD Change Reserve"),
    ):
        for col, item in ((77, "TEST-PC"), (18, value), (89, remark)):
            book["65011201"].cell(row, col, item)
    for row, value, key in ((2, 2, " 918.0 "), (3, 2, 924), (4, 4, 938), (5, 6, 944)):
        for col, item in ((19, "TEST-PC"), (11, value), (15, key)):
            book["庫存調整單"].cell(row, col, item)
    book.save(path)


def test_period_codes_and_first_match() -> None:
    assert period("202601") == ("202601", "202512")
    assert code(" 918.0 ") == "918"
    assert code("9.18") == "918"
    assert accounting_row("VENDOR PAID QV offset with", {"918": 54})[0] == 24
    assert accounting_row("短装材料扣款", {"918": 54})[0] == 54
    assert accounting_row(None, {"918": 54})[0] == 28
    with pytest.raises(DmsInputError):
        period("202613")


def test_formula_evaluator_rejects_arbitrary_expressions() -> None:
    evaluator = CoverValues({"E10": 1, "E11": 2, "E23": "=SUM(E10:E11)", "E8": "=E23+1"})
    assert evaluator.get("E8") == Decimal(4)
    evaluator.values["E8"] = "=__import__('os')"
    with pytest.raises(DmsInputError):
        evaluator.get("E8")


def test_dynamic_pcs_accumulation_and_formula_caches(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "outputs")})
    assert result["status"] == "success"
    assert result["cover_summary"]["warning_count"] == 0
    book = load_workbook(result["output_xlsx"], read_only=True, data_only=True)
    try:
        cover = book["Cover"]
        assert cover["E8"].value == 12.5
        assert cover["E22"].value == 15.5
        assert cover["F22"].value == 2
        assert cover["E23"].value == 30
        assert cover["G23"].value == 38
        assert cover["G9"].value == 0.5
        assert cover["E37"].value == 5  # accounting 3 + inventory 2
        assert cover["E38"].value == 12  # existing 10 + inventory 2
        assert cover["E39"].value == 10  # 938 + 944
        assert cover["E35"].value == 4  # Adjustment included, not silently excluded
        assert cover["E34"].value == -2  # year rollover
        assert cover["E79"].value == 59
        assert len(list(book["金額追溯明細"].values)) == 14
    finally:
        book.close()
    assert_preserved(source, Path(result["output_xlsx"]))


def test_source_formula_cached_values_are_used(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    replacement = tmp_path / "cached.xlsx"
    with ZipFile(source) as original, ZipFile(replacement, "w") as changed:
        for entry in original.infolist():
            data = original.read(entry)
            if entry.filename in ("xl/worksheets/sheet3.xml", "xl/worksheets/sheet6.xml"):
                root = ET.fromstring(data)
                coord = "BS2" if entry.filename.endswith("sheet3.xml") else "K2"
                cell = next(c for c in root.iter(f"{{{NS}}}c") if c.attrib["r"] == coord)
                formula = ET.Element(f"{{{NS}}}f")
                formula.text = "1+1"
                cell.insert(0, formula)
                data = ET.tostring(root)
            changed.writestr(entry, data)
    replacement.replace(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "out")})
    assert result["status"] == "success"
    assert result["cover_summary"]["warning_count"] == 0
    assert result["cover_summary"]["cover_values"]["E21"] == "2"
    assert result["cover_summary"]["cover_values"]["E37"] == "5"
    assert_preserved(source, Path(result["output_xlsx"]))


def assert_preserved(source: Path, output: Path) -> None:
    with ZipFile(source) as before, ZipFile(output) as after:
        sheet_path, before_cover = cover_xml(before)
        _, after_cover = cover_xml(after)
        changed = {
            sheet_path,
            "xl/workbook.xml",
            "xl/_rels/workbook.xml.rels",
            "[Content_Types].xml",
        }
        for name in before.namelist():
            if name not in changed:
                assert before.read(name) == after.read(name), name
        original_cells = {
            c.attrib["r"]: c for row in before_cover.find(f"{{{NS}}}sheetData") for c in row
        }
        output_cells = {
            c.attrib["r"]: c for row in after_cover.find(f"{{{NS}}}sheetData") for c in row
        }
        for coord, cell in original_cells.items():
            updated = output_cells[coord]
            assert cell.attrib.get("s") == updated.attrib.get("s"), coord
            original_formula, new_formula = cell.find(f"{{{NS}}}f"), updated.find(f"{{{NS}}}f")
            if original_formula is not None:
                assert ET.tostring(original_formula) == ET.tostring(new_formula), coord
            if not re_target(coord):
                assert ET.tostring(cell) == ET.tostring(updated), coord
        for child in before_cover:
            if child.tag != f"{{{NS}}}sheetData":
                assert ET.tostring(child) == ET.tostring(after_cover.find(child.tag)), child.tag


def re_target(coord: str) -> bool:
    from openpyxl.utils.cell import coordinate_to_tuple

    row, col = coordinate_to_tuple(coord)
    return 8 <= row <= 81 and col >= 5


def test_unclassified_and_invalid_rows_are_traced(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    book = load_workbook(source)
    for row, pc, value, reason in (
        (4, "", 3, "01.Bom change"),
        (5, "MISSING", 5, "01.Bom change"),
        (6, "TEST-PC", "invalid", "01.Bom change"),
        (7, "TEST-PC", 6, "99.Unmapped"),
        (8, "TEST-PC", 0, "Material QV=0"),
    ):
        for col, item in ((14, pc), (54, value), (56, reason)):
            book["材料分析"].cell(row, col, item)
    book.save(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "out")})
    assert result["status"] == "warning"
    assert result["cover_summary"]["warning_count"] == 4
    assert result["stages"][0]["ignored_count"] == 1
    output = load_workbook(result["output_xlsx"], read_only=True, data_only=True)
    try:
        assert output["Cover"]["E10"].value == 12.5
        statuses = [r[11] for r in output["金額追溯明細"].iter_rows(min_row=2, values_only=True)]
        assert statuses.count("unclassified") == 4
        assert statuses.count("ignored") == 1
    finally:
        output.close()


@pytest.mark.parametrize("missing", [("會計調整",), ("材料分析", "65011201")])
def test_missing_sheets_hard_stop(tmp_path: Path, missing: tuple[str, ...]) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    book = load_workbook(source)
    for name in missing:
        del book[name]
    book.save(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "out")})
    assert result["status"] == "failed"
    assert all(name in result["messages"][-1].content for name in missing)
    assert result["output_xlsx"] == ""
    assert not (tmp_path / "out").exists()


def test_malformed_header_hard_stop(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    book = load_workbook(source)
    book["材料分析"]["N1"] = "wrong"
    book.save(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "out")})
    assert result["status"] == "failed"
    assert "N1" in result["error"]
    assert result["output_xlsx"] == ""


def test_total_formula_cannot_silently_omit_a_profit_center(tmp_path: Path) -> None:
    source = tmp_path / "input.xlsx"
    make_workbook(source)
    book = load_workbook(source)
    book["Cover"]["G23"] = "=E23"
    book.save(source)
    result = graph.invoke({"input_xlsx": str(source), "output_dir": str(tmp_path / "out")})
    assert result["status"] == "failed"
    assert "G23" in result["error"]
    assert result["output_xlsx"] == ""
    assert not list((tmp_path / "out").rglob("*.xlsx"))


@pytest.fixture(scope="module")
def po_results(tmp_path_factory):
    root = tmp_path_factory.mktemp("faa29")
    results = {}
    for name in ("輸入檔", "異常檔案-情境二", "異常檔案-情境三"):
        results[name] = graph.invoke(
            {
                "input_xlsx": str(FIXTURES / f"202610 {name}.xlsx"),
                "output_dir": str(root / name),
            }
        )
    return results


def test_po_normal_golden_discrepancies(po_results) -> None:
    result = po_results["輸入檔"]
    assert result["status"] == "golden_mismatch"
    comparison = compare_golden(Path(result["output_xlsx"]), FIXTURES / "202610 標準答案.xlsx", 8)
    diffs = {d["cell"]: Decimal(d["difference"]) for d in comparison["differences"]}
    assert set(diffs) == {
        "E16",
        "H16",
        "E19",
        "H19",
        "E35",
        "H35",
        "E36",
        "H36",
        "E79",
        "H79",
        "E81",
        "H81",
    }
    assert diffs["E16"].quantize(Decimal(".01")) == Decimal("-1907.90")
    assert diffs["E19"].quantize(Decimal(".01")) == Decimal("1907.90")
    assert diffs["E35"].quantize(Decimal(".01")) == Decimal("-476953.86")
    assert result["cover_summary"]["source_rows"] == 115057
    assert result["cover_summary"]["warning_count"] == 0
    assert_preserved(FIXTURES / "202610 輸入檔.xlsx", Path(result["output_xlsx"]))


def test_po_missing_sheet(po_results) -> None:
    result = po_results["異常檔案-情境二"]
    assert result["status"] == "failed"
    assert "會計調整" in result["error"]
    assert result["output_xlsx"] == ""
    assert result["download_url"] == ""
    assert result["stages"] == []


def test_po_blank_pcs(po_results) -> None:
    result = po_results["異常檔案-情境三"]
    assert result["status"] == "warning"
    assert result["cover_summary"]["warning_count"] == 26188
    output = load_workbook(result["output_xlsx"], read_only=True, data_only=True)
    try:
        assert output["Cover"]["E8"].value == 0
        assert output["Cover"]["E10"].value == 0
        assert output["Cover"]["E23"].value == pytest.approx(666947.99)
        trace = output["金額追溯明細"]
        counts = {"unclassified": 0, "included": 0, "derived": 0}
        for record in trace.iter_rows(min_row=2, values_only=True):
            counts[record[11]] += 1
        assert counts["unclassified"] == 26188
        assert counts["included"] == 88869
        assert counts["derived"] == 3
    finally:
        output.close()
    assert_preserved(FIXTURES / "202610 異常檔案-情境三.xlsx", Path(result["output_xlsx"]))
