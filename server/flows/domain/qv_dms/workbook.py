"""Single-workbook DMS rules and lossless OOXML backfill; no LLM."""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import coordinate_to_tuple

SHEETS = ("材料分析", "生產工單", "會計調整", "65011201", "庫存調整單")
CONTRACT = {
    "材料分析": {14: "Profit Center", 54: "QV in Material(LC)", 56: "Reason"},
    "生產工單": {
        77: "PROFIT_CENTER_NEW",
        18: "QV Amt (LC Currency)",
        71: "QV in MOH (LC)",
    },
    "會計調整": {4: "Profit Center", 17: "Amount in Local Currency", 18: "Text"},
    "65011201": {77: "PROFIT_CENTER_NEW", 18: "QV Amt (LC Currency)", 89: "Remark"},
    "庫存調整單": {19: "Right Profit center", 11: "Amount-2", 15: "Reason Code"},
}
PC_COL = dict(zip(SHEETS, (14, 77, 4, 77, 19), strict=True))
AMOUNT_COL = dict(zip(SHEETS, (54, 18, 17, 18, 11), strict=True))
CLASS_COL = dict(zip(SHEETS, (56, 0, 18, 89, 15), strict=True))
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CENT = Decimal("0.01")
TRACE_HEADERS = (
    "來源檔",
    "來源Sheet",
    "來源列號",
    "原始Profit Center",
    "標準化Profit Center",
    "原始分類",
    "判定條件",
    "來源金額欄",
    "來源金額",
    "MOH金額",
    "Cover目標",
    "狀態",
    "異常原因",
    "回填前值",
    "本步加總",
    "回填後值",
)


class DmsInputError(ValueError):
    """A user-visible workbook contract or calculation error."""


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def code(value: Any) -> str:
    compact = re.sub(r"\s+", "", text(value))
    if re.fullmatch(r"\d+(?:\.0+)?", compact):
        return str(int(Decimal(compact)))
    return compact.replace(".", "")


def amount(value: Any, *, blank_zero: bool = False) -> Decimal:
    if blank_zero and value is None:
        return Decimal(0)
    if value is None or isinstance(value, bool):
        raise DmsInputError(f"無效金額：{value!r}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise DmsInputError(f"無效金額：{value!r}") from exc
    if not result.is_finite():
        raise DmsInputError(f"無效金額：{value!r}")
    return result


def period(value: Any) -> tuple[str, str]:
    if isinstance(value, (date, datetime)):
        current = value.strftime("%Y%m")
    else:
        current = text(value)
    try:
        parsed = datetime.strptime(current, "%Y%m")
    except ValueError as exc:
        raise DmsInputError("Cover B2 必須為報表日期或 YYYYMM") from exc
    if len(current) != 6:
        raise DmsInputError("Cover B2 必須為報表日期或 YYYYMM")
    previous = (
        date(parsed.year - 1, 12, 1)
        if parsed.month == 1
        else date(parsed.year, parsed.month - 1, 1)
    )
    return current, previous.strftime("%Y%m")


def inspect_workbook(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.suffix.lower() != ".xlsx":
        raise DmsInputError(f"找不到指定 Excel 活頁簿：{path.name}")
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise DmsInputError("Excel 活頁簿壓縮內容損毀")
    book = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        missing = [name for name in ("Cover", *SHEETS) if name not in book.sheetnames]
        if missing:
            raise DmsInputError(f"檔案缺少必要工作表 [{', '.join(missing)}]，請重新上傳。")
        for name, fields in CONTRACT.items():
            header = next(
                book[name].iter_rows(min_row=1, max_row=1, max_col=max(fields), values_only=True)
            )
            for col, expected in fields.items():
                if text(header[col - 1]) != expected:
                    raise DmsInputError(f"{name} {get_column_letter(col)}1 必須為 {expected}")
        cover = book["Cover"]
        current, previous = period(cover["B2"].value)
        headers = next(
            cover.iter_rows(min_row=6, max_row=6, max_col=cover.max_column, values_only=True)
        )
        pcs: dict[str, int] = {}
        total_col = None
        for col, value in enumerate(headers[4:], 5):
            label = text(value)
            if label.casefold() == "total":
                total_col = col
                continue
            if not label:
                continue
            if label in pcs:
                raise DmsInputError(f"Cover 第 6 列 Profit Center 重複：{label}")
            pcs[label] = col
        if not pcs or total_col is None:
            raise DmsInputError("Cover 第 6 列缺 Profit Center 或 Total 欄")
        for row in range(10, 23):
            if code(cover.cell(row, 2).value) != str(row - 9):
                raise DmsInputError(f"Cover B{row} Reason Code 應為 {row - 9}")
        expected_labels = {
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
        for row, expected in expected_labels.items():
            actual = text(cover.cell(row, 4).value).casefold().replace("preivous", "previous")
            normalized = expected.casefold().replace("preivous", "previous")
            if actual != normalized:
                raise DmsInputError(f"Cover D{row} 應為 {expected}")
        if text(cover["A81"].value) != "Total QV Return":
            raise DmsInputError("Cover A81 應為 Total QV Return")
        inventory_rows: dict[str, int] = {}
        for row in range(37, 78):
            key = code(cover.cell(row, 2).value)
            if not key or key in inventory_rows:
                raise DmsInputError(f"Cover 庫存 Reason Code 缺少或重複：B{row}")
            inventory_rows[key] = row
        if not {"918", "938&944"} <= inventory_rows.keys():
            raise DmsInputError("Cover 缺少庫存分類 918 或 938&944")
        # 舊追溯不覆蓋，避免遺失前次稽核內容。
        if "金額追溯明細" in book.sheetnames:
            raise DmsInputError("請使用尚未回填的輸入檔；已有金額追溯明細")
        return {
            "period": current,
            "previous_period": previous,
            "pcs": pcs,
            "total_col": total_col,
            "inventory_rows": inventory_rows,
            "sheetnames": book.sheetnames,
        }
    finally:
        book.close()


def accounting_row(value: Any, inventory_rows: dict[str, int]) -> tuple[int, str]:
    label = text(value).casefold()
    if "vendor paid" in label:
        return 24, "Text contains Vendor Paid (case-insensitive)"
    if any(word in label for word in ("不良報廢", "非生產性工時")):
        return 27, "Text contains 不良報廢 / 非生產性工時"
    if "qv offset with" in label:
        return 31, "Text contains QV offset with (case-insensitive)"
    if "短装材料扣款" in label or "短裝材料扣款" in label:
        return inventory_rows["918"], "Text contains 短装材料扣款 / 短裝材料扣款"
    return 28, "Text ELSE / blank -> Other"


def classify(name: str, value: Any, layout: dict[str, Any]) -> tuple[int | None, str]:
    label = text(value)
    if name == "材料分析":
        if "material qv=0" in label.casefold():
            return None, "Material QV=0: excluded"
        match = re.match(r"^(\d+)(?!\d)", label)
        if match and 1 <= int(match[1]) <= 11:
            return int(match[1]) + 9, f"Reason leading Code = {int(match[1])}"
        return None, "Reason Code undefined / blank"
    if name == "生產工單":
        return 21, "BS -> Code 12; R total - rows 10:20 - row 21 -> Code 13"
    if name == "會計調整":
        return accounting_row(value, layout["inventory_rows"])
    if name == "65011201":
        if "qv offset with" in label.casefold():
            return 30, "Remark contains QV offset with (manual first)"
        match = re.match(r"^(\d{6})", label)
        if match and match[1] == layout["period"]:
            return 35, f"Remark YYYYMM = current_period {layout['period']}"
        if match and match[1] == layout["previous_period"]:
            return 34, f"Remark YYYYMM = previous_period {layout['previous_period']}"
        return None, "Remark period undefined / outside current and previous / blank"
    key = code(value)
    if key in ("938", "944"):
        key = "938&944"
    return layout["inventory_rows"].get(key), f"Reason Code exact match = {key}"


def aggregate_sheet(
    source: Path, name: str, layout: dict[str, Any], trace_path: Path
) -> dict[str, Any]:
    buckets: dict[str, Decimal] = defaultdict(Decimal)
    totals: dict[str, Decimal] = defaultdict(Decimal)
    count = warning_count = ignored_count = 0
    book = load_workbook(source, read_only=True, data_only=True, keep_links=False)
    try:
        with trace_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            for row_num, row in enumerate(
                book[name].iter_rows(min_row=2, max_col=max(CONTRACT[name]), values_only=True), 2
            ):
                if all(value is None for value in row):
                    continue
                count += 1
                raw_pc = row[PC_COL[name] - 1]
                pc = text(raw_pc)
                raw_class = row[CLASS_COL[name] - 1] if CLASS_COL[name] else ""
                raw_amount = row[AMOUNT_COL[name] - 1]
                raw_moh = row[70] if name == "生產工單" else ""
                target_row, rule = classify(name, raw_class, layout)
                issues = []
                if pc not in layout["pcs"]:
                    issues.append("Profit Center 空白" if not pc else f"Profit Center 未定義：{pc}")
                ignored = name == "材料分析" and "excluded" in rule
                if target_row is None and not ignored:
                    issues.append(rule)
                value = moh = Decimal(0)
                try:
                    value = amount(raw_amount)
                    if name == "生產工單":
                        moh = amount(raw_moh)
                except DmsInputError as exc:
                    issues.append(str(exc))
                target = ""
                if issues:
                    warning_count += 1
                    status = "unclassified"
                elif ignored:
                    ignored_count += 1
                    status = "ignored"
                else:
                    status = "included"
                    target = f"{get_column_letter(layout['pcs'][pc])}{target_row}"
                    buckets[target] += moh if name == "生產工單" else value
                    totals[pc] += value
                writer.writerow(
                    [
                        source.name,
                        name,
                        row_num,
                        raw_pc,
                        pc,
                        raw_class,
                        rule,
                        CONTRACT[name][AMOUNT_COL[name]],
                        raw_amount,
                        raw_moh,
                        target,
                        status,
                        "; ".join(issues),
                    ]
                )
    finally:
        book.close()
    return {
        "sheet": name,
        "buckets": {k: str(v) for k, v in buckets.items()},
        "totals": {k: str(v) for k, v in totals.items()},
        "row_count": count,
        "warning_count": warning_count,
        "ignored_count": ignored_count,
        "trace_path": str(trace_path),
    }


class CoverValues:
    """Evaluate only the arithmetic/SUM/IF grammar actually used by Cover."""

    def __init__(self, values: dict[str, Any]):
        self.values = values
        self.active: set[str] = set()

    def get(self, coord: str) -> Decimal:
        if coord in self.active:
            raise DmsInputError(f"Cover 公式循環：{coord}")
        value = self.values.get(coord)
        if not isinstance(value, str) or not value.startswith("="):
            return amount(value, blank_zero=True)
        self.active.add(coord)
        try:
            expression = value[1:].replace("$", "")
            expression = re.sub(r"([A-Z]+\d+):([A-Z]+\d+)", r'RANGE("\1","\2")', expression)
            # 避開 RANGE 的字串參數，僅轉換裸儲存格引用。
            expression = re.sub(r'(?<!["\w])([A-Z]+\d+)(?!["\w])', r'CELL("\1")', expression)
            expression = re.sub(r"(?<![<>=!])=(?!=)", "==", expression)
            result = self.evaluate(ast.parse(expression, mode="eval").body)
            if not isinstance(result, Decimal):
                raise DmsInputError(f"Cover 公式非數值：{coord}")
            return result
        except (SyntaxError, ZeroDivisionError, InvalidOperation) as exc:
            raise DmsInputError(f"Cover 公式無法計算：{coord}: {value}") from exc
        finally:
            self.active.remove(coord)

    def evaluate(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self.evaluate(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left, right = self.evaluate(node.left), self.evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = self.evaluate(node.left), self.evaluate(node.comparators[0])
            if isinstance(node.ops[0], ast.Eq):
                return left == right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id.upper()
            if name == "CELL" and len(node.args) == 1:
                return self.get(self.evaluate(node.args[0]))
            if name == "RANGE" and len(node.args) == 2:
                from openpyxl.utils.cell import range_boundaries

                start, end = (self.evaluate(n) for n in node.args)
                c1, r1, c2, r2 = range_boundaries(f"{start}:{end}")
                return [
                    self.get(f"{get_column_letter(c)}{r}")
                    for r in range(r1, r2 + 1)
                    for c in range(c1, c2 + 1)
                ]
            if name == "IF" and len(node.args) == 3:
                return self.evaluate(node.args[1] if self.evaluate(node.args[0]) else node.args[2])
            if name == "SUM":
                values = [self.evaluate(n) for n in node.args]
                return sum(
                    (sum(v, Decimal(0)) if isinstance(v, list) else v for v in values),
                    Decimal(0),
                )
        raise DmsInputError(f"Cover 使用未支援公式語法：{ast.dump(node)}")


def cover_xml(archive: ZipFile) -> tuple[str, ET.Element]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    cover = next(s for s in workbook.find(f"{{{NS}}}sheets") if s.attrib["name"] == "Cover")
    rel_id = cover.attrib[f"{{{DOC_REL_NS}}}id"]
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    target = next(r.attrib["Target"] for r in rels if r.attrib["Id"] == rel_id)
    path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
    return path, ET.fromstring(archive.read(path))


def finalize_workbook(
    source: Path, destination: Path, layout: dict[str, Any], stages: list[dict[str, Any]]
) -> dict[str, Any]:
    book = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    try:
        values = {
            cell.coordinate: cell.value
            for row in book["Cover"].iter_rows()
            for cell in row
            if cell.value is not None
        }
    finally:
        book.close()
    evaluator = CoverValues(values)
    updates: dict[str, Decimal] = {}
    history: dict[tuple[str, str], tuple[Decimal, Decimal, Decimal]] = {}
    checks: list[dict[str, Any]] = []

    def write(coord: str, value: Decimal) -> None:
        existing = values.get(coord)
        if isinstance(existing, str) and existing.startswith("="):
            if evaluator.get(coord) != value:
                raise DmsInputError(f"Cover {coord} 原公式與回填規則不符，不可覆蓋公式")
        else:
            values[coord] = value
        updates[coord] = value

    def check(label: str, expected: Decimal, actual: Decimal) -> None:
        difference = actual - expected
        checks.append({"check": label, "difference": str(difference)})
        if difference != 0:
            raise DmsInputError(f"金額驗證失敗：{label} 差異 {difference}")

    for stage in stages:
        name = stage["sheet"]
        buckets = {k: amount(v) for k, v in stage["buckets"].items()}
        rows = {
            "材料分析": list(range(10, 21)),
            "生產工單": [21],
            "會計調整": [24, 27, 28, 31, layout["inventory_rows"]["918"]],
            "65011201": [30, 34, 35],
            "庫存調整單": list(layout["inventory_rows"].values()),
        }[name]
        for pc, col in layout["pcs"].items():
            letter = get_column_letter(col)
            for row in rows:
                coord = f"{letter}{row}"
                before = evaluator.get(coord)
                delta = buckets.get(coord, Decimal(0))
                after = before + delta if name == "庫存調整單" else delta
                write(coord, after)
                history[(name, coord)] = (before, delta, after)
            expected = amount(stage["totals"].get(pc, "0"))
            if name == "生產工單":
                sampled = sum((evaluator.get(f"{letter}{r}") for r in range(10, 21)), Decimal(0))
                write(f"{letter}22", expected - sampled - evaluator.get(f"{letter}21"))
                write(f"{letter}23", expected)
                check(f"{pc} MO Sub-total", expected, evaluator.get(f"{letter}23"))
            else:
                actual = sum((buckets.get(f"{letter}{r}", Decimal(0)) for r in rows), Decimal(0))
                check(f"{pc} {name} eligible total", expected, actual)

    for pc, col in layout["pcs"].items():
        letter = get_column_letter(col)
        sampling = sum((evaluator.get(f"{letter}{r}") for r in range(10, 21)), Decimal(0))
        write(f"{letter}8", sampling)
        denominator = evaluator.get(f"{letter}23") - evaluator.get(f"{letter}21")
        if denominator == 0 and sampling != 0:
            raise DmsInputError(f"{pc} Sampling Ratio 分母為 0，原公式無法產生有效比率")
        write(f"{letter}9", sampling / denominator if denominator else Decimal(0))
        for row, detail in (
            (23, range(10, 23)),
            (29, range(24, 29)),
            (36, range(30, 36)),
            (78, range(37, 78)),
            (79, (23, 29, 36, 78)),
            (81, (79, 80)),
        ):
            write(
                f"{letter}{row}", sum((evaluator.get(f"{letter}{r}") for r in detail), Decimal(0))
            )

    total_letter = get_column_letter(layout["total_col"])
    for row in (8, *range(10, 82)):
        write(
            f"{total_letter}{row}",
            sum(
                (evaluator.get(f"{get_column_letter(col)}{row}") for col in layout["pcs"].values()),
                Decimal(0),
            ),
        )
    total_sampling = evaluator.get(f"{total_letter}8")
    total_denominator = evaluator.get(f"{total_letter}23") - evaluator.get(f"{total_letter}21")
    if total_denominator == 0 and total_sampling != 0:
        raise DmsInputError("Total Sampling Ratio 分母為 0，原公式無法產生有效比率")
    write(
        f"{total_letter}9",
        total_sampling / total_denominator if total_denominator else Decimal(0),
    )

    # 只更新 Cover 的公式快取；公式文字、樣式和其他 Sheet 的 ZIP 項目保持原樣。
    with ZipFile(source) as original:
        xml_path, root = cover_xml(original)
        sheet_data = root.find(f"{{{NS}}}sheetData")
        cells = {c.attrib["r"]: c for row in sheet_data for c in row}
        for coord, cell in cells.items():
            row_num, col_num = coordinate_to_tuple(coord)
            if (
                cell.find(f"{{{NS}}}f") is not None
                and 8 <= row_num <= 81
                and col_num in {*layout["pcs"].values(), layout["total_col"]}
            ):
                updates[coord] = evaluator.get(coord)
        for coord, value in updates.items():
            if coord not in cells:
                row_num = int(re.search(r"\d+$", coord)[0])
                row = next((r for r in sheet_data if int(r.attrib["r"]) == row_num), None)
                if row is None:
                    row = ET.SubElement(sheet_data, f"{{{NS}}}row", {"r": str(row_num)})
                cell = ET.SubElement(row, f"{{{NS}}}c", {"r": coord})
                cells[coord] = cell
            cell = cells[coord]
            cell.attrib.pop("t", None)
            for child in list(cell):
                if child.tag in (f"{{{NS}}}v", f"{{{NS}}}is"):
                    cell.remove(child)
            ET.SubElement(cell, f"{{{NS}}}v").text = str(value)
        # XML 的儲存格按欄位順序寫回，避免 Excel repair。
        for row in sheet_data:
            row[:] = sorted(row, key=lambda c: coordinate_to_tuple(c.attrib["r"])[1])
        with TemporaryDirectory(dir=destination.parent) as temporary:
            trace_book = Workbook(write_only=True)
            trace = trace_book.create_sheet("金額追溯明細")
            trace.append(TRACE_HEADERS)

            def append_trace(record: list[str]) -> None:
                safe = []
                for value in record:
                    cell = WriteOnlyCell(trace, value=value)
                    cell.data_type = "s"
                    safe.append(cell)
                trace.append(safe)

            for stage in stages:
                with Path(stage["trace_path"]).open(encoding="utf-8", newline="") as stream:
                    for record in csv.reader(stream):
                        change = history.get((stage["sheet"], record[10]))
                        record.extend([str(v) for v in change] if change else ["", "", ""])
                        append_trace(record)
            for pc, col in layout["pcs"].items():
                letter = get_column_letter(col)
                append_trace(
                    [
                        source.name,
                        "生產工單（倒減計算）",
                        "",
                        pc,
                        pc,
                        "",
                        "R total - Cover rows 10:20 - Cover row 21",
                        "QV Amt (LC Currency)",
                        stages[1]["totals"].get(pc, "0"),
                        "",
                        f"{letter}22",
                        "derived",
                        "",
                        "",
                        "",
                        str(evaluator.get(f"{letter}22")),
                    ]
                )
            trace_path = Path(temporary) / "trace.xlsx"
            trace_book.save(trace_path)
            with ZipFile(trace_path) as trace_archive:
                trace_data = trace_archive.read("xl/worksheets/sheet1.xml")
            workbook_root = ET.fromstring(original.read("xl/workbook.xml"))
            rels_root = ET.fromstring(original.read("xl/_rels/workbook.xml.rels"))
            types_root = ET.fromstring(original.read("[Content_Types].xml"))
            sheets = workbook_root.find(f"{{{NS}}}sheets")
            sheet_id = max(int(s.attrib["sheetId"]) for s in sheets) + 1
            used = {r.attrib["Id"] for r in rels_root}
            rel_id = f"rIdDmsTrace{sheet_id}"
            while rel_id in used:
                rel_id += "_"
            trace_part = f"xl/worksheets/dmsTrace{sheet_id}.xml"
            ET.SubElement(
                sheets,
                f"{{{NS}}}sheet",
                {
                    "name": "金額追溯明細",
                    "sheetId": str(sheet_id),
                    f"{{{DOC_REL_NS}}}id": rel_id,
                },
            )
            ET.SubElement(
                rels_root,
                f"{{{REL_NS}}}Relationship",
                {
                    "Id": rel_id,
                    "Type": f"{DOC_REL_NS}/worksheet",
                    "Target": trace_part.removeprefix("xl/"),
                },
            )
            type_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
            ET.SubElement(
                types_root,
                f"{{{type_ns}}}Override",
                {
                    "PartName": f"/{trace_part}",
                    "ContentType": (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
                    ),
                },
            )
            # 保留根節點的 mc:Ignorable 與所有原始 namespace 宣告，只替換資料區塊。
            cover_data = re.sub(
                rb"<sheetData(?:\s[^>]*)?>.*?</sheetData>",
                lambda _: ET.tostring(sheet_data, encoding="utf-8"),
                original.read(xml_path),
                count=1,
                flags=re.DOTALL,
            )
            new_sheet = list(sheets)[-1]
            new_rel = list(rels_root)[-1]
            new_type = list(types_root)[-1]

            def append_xml(part: str, closing: bytes, element: ET.Element) -> bytes:
                raw = original.read(part)
                return raw.replace(closing, ET.tostring(element, encoding="utf-8") + closing, 1)

            replacements = {
                xml_path: cover_data,
                "xl/workbook.xml": append_xml("xl/workbook.xml", b"</sheets>", new_sheet),
                "xl/_rels/workbook.xml.rels": append_xml(
                    "xl/_rels/workbook.xml.rels", b"</Relationships>", new_rel
                ),
                "[Content_Types].xml": append_xml("[Content_Types].xml", b"</Types>", new_type),
            }
            pending = Path(temporary) / "result.xlsx"
            with ZipFile(pending, "w") as output:
                for entry in original.infolist():
                    output.writestr(entry, replacements.get(entry.filename, original.read(entry)))
                output.writestr(trace_part, trace_data, compress_type=ZIP_DEFLATED)
            pending.replace(destination)
    return {
        "validation_ok": True,
        "checks": checks,
        "warning_count": sum(s["warning_count"] for s in stages),
        "source_rows": sum(s["row_count"] for s in stages),
        "steps_done": [*SHEETS, "Cover totals / trace / validation"],
        "cover_values": {coord: str(value) for coord, value in updates.items()},
    }


def compare_golden(output: Path, golden: Path, total_col: int) -> dict[str, Any]:
    differences = []
    result_book = load_workbook(output, read_only=True, data_only=True, keep_links=False)
    golden_book = load_workbook(golden, read_only=True, data_only=True, keep_links=False)
    try:
        actual_rows = result_book["Cover"].iter_rows(
            min_row=8, max_row=81, min_col=5, max_col=total_col, values_only=True
        )
        expected_rows = golden_book["Cover"].iter_rows(
            min_row=8, max_row=81, min_col=5, max_col=total_col, values_only=True
        )
        for row_num, (actual, expected) in enumerate(
            zip(actual_rows, expected_rows, strict=True), 8
        ):
            for col, (a, e) in enumerate(zip(actual, expected, strict=True), 5):
                a_value, e_value = amount(a, blank_zero=True), amount(e, blank_zero=True)
                delta = a_value - e_value
                mismatch = (
                    abs(delta) > Decimal("0.000000000001")
                    if row_num == 9
                    else (a_value.quantize(CENT) != e_value.quantize(CENT))
                )
                if mismatch:
                    differences.append(
                        {
                            "cell": f"{get_column_letter(col)}{row_num}",
                            "actual": str(a_value),
                            "expected": str(e_value),
                            "difference": str(delta),
                        }
                    )
    finally:
        result_book.close()
        golden_book.close()
    return {"passed": not differences, "differences": differences}


def save_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
