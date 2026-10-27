"""QV DMS Cover.xlsx backfill chain (steps 1.1–1.5). No LLM."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from flows.domain.excel_io import load_excel

REASON_REPLACEMENTS = {
    "05.Rework MO-时间差": "時間差",
    "05.Rework MO-時間差": "時間差",
    "05.Rework MO-替代料": "替代料",
    "05.Rework MO-跨月退料": "跨月投料",
    "Rework MO-跨月投料": "跨月投料",
}


@dataclass
class CoverPipelineResult:
    cover: pd.DataFrame
    pivot: pd.DataFrame | None = None
    filled_count: int = 0
    unmatched_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    steps_done: list[str] = field(default_factory=list)
    validation_ok: bool | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "filled_count": self.filled_count,
            "unmatched_reasons": self.unmatched_reasons,
            "notes": self.notes,
            "steps_done": self.steps_done,
            "validation_ok": self.validation_ok,
            "cover_rows": len(self.cover),
        }


def _norm_reason(value: str) -> str:
    s = str(value or "").strip()
    s = re.sub(r"^\d+\.\s*", "", s)
    s = unicodedata.normalize("NFKC", s)
    return s.casefold().replace(" ", "")


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {str(c).strip().casefold(): c for c in df.columns}
    for name in candidates:
        key = name.casefold()
        if key in lower_map:
            return lower_map[key]
        for k, orig in lower_map.items():
            if key in k or k in key:
                return orig
    return None


def load_cover(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "Cover.xlsx"
    df = load_excel(path)
    # Prompt: first row is header — pandas already uses header=0
    return df


def build_material_pivot(material_df: pd.DataFrame) -> pd.DataFrame:
    reason_col = _find_col(material_df, ["Reason"])
    qv_col = _find_col(material_df, ["QV in Material(LC)", "QV in Material (LC)"])
    if not reason_col or not qv_col:
        raise ValueError(
            f"材料分析缺 Reason / QV 欄；have={list(material_df.columns)[:20]}"
        )
    work = material_df[[reason_col, qv_col]].copy()
    work[reason_col] = work[reason_col].astype(str).map(
        lambda x: REASON_REPLACEMENTS.get(x.strip(), x.strip())
    )
    work[reason_col] = work[reason_col].map(lambda x: re.sub(r"^\d+\.\s*", "", x).strip())
    work[qv_col] = pd.to_numeric(work[qv_col], errors="coerce").fillna(0)
    # merge same reason ignoring case / 简繁 via norm key then display first
    work["_key"] = work[reason_col].map(_norm_reason)
    grouped = work.groupby("_key", as_index=False).agg(
        {reason_col: "first", qv_col: "sum"}
    )
    grouped = grouped.rename(columns={reason_col: "Reason", qv_col: "QV in Material(LC)"})
    return grouped[["Reason", "QV in Material(LC)"]]


def match_and_fill_pcl500(
    cover: pd.DataFrame,
    pivot: pd.DataFrame,
) -> tuple[pd.DataFrame, int, list[str], bool]:
    reason_col = _find_col(cover, ["Reason Code", "Reason", "A"])
    pcl_col = _find_col(cover, ["PCL500", "D"])
    if not reason_col or not pcl_col:
        raise ValueError(f"Cover 缺 Reason Code / PCL500；have={list(cover.columns)}")

    out = cover.copy()
    _ensure_float_col(out, pcl_col)
    pivot_map = {
        _norm_reason(r): float(v)
        for r, v in zip(pivot["Reason"], pivot["QV in Material(LC)"], strict=False)
    }
    filled = 0
    unmatched: list[str] = []
    used_keys: set[str] = set()
    for idx, row in out.iterrows():
        key = _norm_reason(row[reason_col])
        if not key:
            continue
        if key in pivot_map:
            out.at[idx, pcl_col] = pivot_map[key]
            filled += 1
            used_keys.add(key)
    for k, reason in zip(
        [_norm_reason(r) for r in pivot["Reason"]],
        pivot["Reason"],
        strict=False,
    ):
        if k not in used_keys:
            unmatched.append(str(reason))

    # validate D2:D13 style — first 12 data rows often reason categories
    subset = pd.to_numeric(out[pcl_col].iloc[:12], errors="coerce").fillna(0)
    pivot_total = float(pivot["QV in Material(LC)"].sum())
    cover_total = float(subset.sum())
    ok = abs(pivot_total - cover_total) < 0.01 or filled == 0
    return out, filled, unmatched, ok


def _ensure_float_col(df: pd.DataFrame, col: str) -> None:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")


def fill_production_mo(cover: pd.DataFrame, mo_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    notes: list[str] = []
    out = cover.copy()
    reason_col = _find_col(out, ["Reason Code", "Reason"])
    pcl_col = _find_col(out, ["PCL500"])
    if not reason_col or not pcl_col:
        return out, ["Cover 缺欄，跳過生產工單回填"]
    _ensure_float_col(out, pcl_col)

    moh_col = _find_col(mo_df, ["QV in MOH (LC)", "QV in MOH(LC)"])
    amt_col = _find_col(mo_df, ["QV Amt (LC Currency)", "QV Amt (LC Currency))"])
    if moh_col is None:
        # fallback positional BS = col index 70 if enough cols
        if mo_df.shape[1] > 70:
            moh_col = mo_df.columns[70]
            notes.append(f"使用第 71 欄作為 QV in MOH: {moh_col}")
        else:
            return out, ["找不到 QV in MOH 欄"]
    if amt_col is None and mo_df.shape[1] > 17:
        amt_col = mo_df.columns[17]
        notes.append(f"使用第 18 欄作為 QV Amt: {amt_col}")

    a = float(pd.to_numeric(mo_df[moh_col], errors="coerce").fillna(0).sum())
    b = float(pd.to_numeric(mo_df[amt_col], errors="coerce").fillna(0).sum()) if amt_col else 0.0
    # fill 报工差异
    for idx, row in out.iterrows():
        if "报工" in str(row[reason_col]) or "報工" in str(row[reason_col]):
            out.at[idx, pcl_col] = a
    c = float(pd.to_numeric(out[pcl_col].iloc[:12], errors="coerce").fillna(0).sum())
    d = b - a - c
    for idx, row in out.iterrows():
        if "未分析" in str(row[reason_col]):
            out.at[idx, pcl_col] = d
    notes.append(f"报工差异 a={a}, QV Amt b={b}, D2:D13 c={c}, 未分析 d={d}")
    return out, notes


def fill_accounting(cover: pd.DataFrame, acct_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Keyword buckets into Cover rows — pragmatic Text contains match."""
    notes: list[str] = []
    out = cover.copy()
    reason_col = _find_col(out, ["Reason Code", "Reason"])
    pcl_col = _find_col(out, ["PCL500"])
    text_col = _find_col(acct_df, ["Text"])
    amt_col = _find_col(
        acct_df,
        [
            "Amount in Local Currency",
            "Amount in Doc. Curr.",
            "Amount in Doc.Curr.",
            "Amount",
        ],
    )
    if not reason_col or not pcl_col or not text_col or not amt_col:
        return out, [
            f"會計調整缺欄，跳過 (text={text_col}, amt={amt_col}, cols={list(acct_df.columns)[:12]})"
        ]
    _ensure_float_col(out, pcl_col)

    # map: if Cover reason appears in Text, accumulate
    for idx, row in out.iterrows():
        reason = str(row[reason_col]).strip()
        if not reason or reason in ("报工差异", "報工差異", "未分析"):
            continue
        mask = acct_df[text_col].astype(str).str.contains(re.escape(reason), case=False, na=False)
        if mask.any():
            total = float(pd.to_numeric(acct_df.loc[mask, amt_col], errors="coerce").fillna(0).sum())
            if total:
                out.at[idx, pcl_col] = total
                notes.append(f"會計調整「{reason}」={total}")
    return out, notes


def fill_65011201(cover: pd.DataFrame, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    notes: list[str] = []
    out = cover.copy()
    reason_col = _find_col(out, ["Reason Code", "Reason"])
    pcl_col = _find_col(out, ["PCL500"])
    amt_col = _find_col(df, ["QV Amt (LC Currency)", "QV Amt"])
    remark_col = _find_col(df, ["Remark", "Text"])
    if not reason_col or not pcl_col or not amt_col:
        return out, ["65011201 缺欄，跳過"]
    _ensure_float_col(out, pcl_col)
    for idx, row in out.iterrows():
        reason = str(row[reason_col]).strip()
        if "Reserve" not in reason and "reserve" not in reason.lower() and "迴轉" not in reason and "提列" not in reason:
            continue
        if remark_col:
            mask = df[remark_col].astype(str).str.contains("reserve|Reserve|迴轉|提列", case=False, na=False)
            total = float(pd.to_numeric(df.loc[mask, amt_col], errors="coerce").fillna(0).sum())
        else:
            total = float(pd.to_numeric(df[amt_col], errors="coerce").fillna(0).sum())
        out.at[idx, pcl_col] = total
        notes.append(f"65011201「{reason}」={total}")
    return out, notes


def fill_inventory_adj(cover: pd.DataFrame, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    notes: list[str] = []
    out = cover.copy()
    reason_col = _find_col(out, ["Reason Code", "Reason"])
    pcl_col = _find_col(out, ["PCL500"])
    code_col = _find_col(df, ["Reason Code", "Reason"])
    amt_col = _find_col(df, ["Amount-2", "Amount"])
    if not reason_col or not pcl_col or not code_col or not amt_col:
        return out, ["庫存調整缺欄，跳過"]
    _ensure_float_col(out, pcl_col)
    grouped = (
        df.assign(_amt=pd.to_numeric(df[amt_col], errors="coerce").fillna(0))
        .groupby(df[code_col].astype(str).str.strip())["_amt"]
        .sum()
    )
    for idx, row in out.iterrows():
        reason = str(row[reason_col]).strip()
        key = _norm_reason(reason)
        for gkey, val in grouped.items():
            if _norm_reason(str(gkey)) == key or key in _norm_reason(str(gkey)):
                out.at[idx, pcl_col] = float(val)
                notes.append(f"庫存調整「{reason}」={val}")
                break
    return out, notes


def run_cover_pipeline(data_dir: Path) -> CoverPipelineResult:
    cover = load_cover(data_dir)
    result = CoverPipelineResult(cover=cover)

    material_path = data_dir / "材料分析.xlsx"
    if material_path.is_file():
        mat = load_excel(material_path)
        pivot = build_material_pivot(mat)
        cover, filled, unmatched, ok = match_and_fill_pcl500(cover, pivot)
        result.cover = cover
        result.pivot = pivot
        result.filled_count = filled
        result.unmatched_reasons = unmatched
        result.validation_ok = ok
        result.steps_done.append("1.1_material_pivot")
        if not ok:
            result.notes.append("Pivot 總額與 Cover D2:D13 不一致（QV-01 匹配可能不全）")
    else:
        result.notes.append("QV-02：缺當期 材料分析.xlsx，跳過步驟 1.1")

    mo_path = data_dir / "生產工單.xlsx"
    if mo_path.is_file():
        cover, notes = fill_production_mo(result.cover, load_excel(mo_path))
        result.cover = cover
        result.notes.extend(notes)
        result.steps_done.append("1.2_production_mo")

    acct_path = data_dir / "會計調整.xlsx"
    if acct_path.is_file():
        cover, notes = fill_accounting(result.cover, load_excel(acct_path))
        result.cover = cover
        result.notes.extend(notes)
        result.steps_done.append("1.3_accounting")

    r650_path = data_dir / "65011201.xlsx"
    if r650_path.is_file():
        cover, notes = fill_65011201(result.cover, load_excel(r650_path))
        result.cover = cover
        result.notes.extend(notes)
        result.steps_done.append("1.4_65011201")

    inv_path = data_dir / "庫存調整單.xlsx"
    if inv_path.is_file():
        cover, notes = fill_inventory_adj(result.cover, load_excel(inv_path))
        result.cover = cover
        result.notes.extend(notes)
        result.steps_done.append("1.5_inventory")

    result.steps_done.append("1.6_format_skipped_keep_values")
    result.notes.append("QV-03：Email/Teams 僅產草稿，不實發")
    return result


def analyze_period_top3(material_df: pd.DataFrame, *, label: str) -> dict[str, Any]:
    reason_col = _find_col(material_df, ["Reason"])
    qv_col = _find_col(material_df, ["QV in Material(LC)"])
    group_col = _find_col(material_df, ["Component Material Group", "Material Group Des.", "Material Group"])
    mat_col = _find_col(material_df, ["Material"])
    if not reason_col or not qv_col:
        return {"label": label, "error": "缺 Reason/QV 欄"}
    df = material_df.copy()
    df[qv_col] = pd.to_numeric(df[qv_col], errors="coerce").fillna(0)
    by_reason = df.groupby(reason_col)[qv_col].sum().sort_values()
    rows = []
    for reason, total in by_reason.items():
        sub = df[df[reason_col] == reason]
        top_groups = []
        if group_col:
            top_groups = (
                sub.groupby(group_col)[qv_col].sum().sort_values().head(3).to_dict()
            )
        top_mat = None
        if mat_col and not sub.empty:
            top_mat = sub.groupby(mat_col)[qv_col].sum().sort_values().index[0]
        rows.append(
            {
                "reason": str(reason),
                "qv_total": float(total),
                "top_groups": {str(k): float(v) for k, v in top_groups.items()},
                "top_material": str(top_mat) if top_mat is not None else None,
            }
        )
    return {"label": label, "reasons": rows}


def render_qv_html(summary: dict[str, Any], narrative: dict[str, Any] | None = None) -> str:
    import html as html_mod

    narrative = narrative or {}
    title = html_mod.escape(str(narrative.get("summary") or "QV DMS Cover 整理結果"))
    notes = summary.get("notes") or []
    steps = summary.get("steps_done") or []
    note_lis = "".join(f"<li>{html_mod.escape(str(n))}</li>" for n in notes)
    step_lis = "".join(f"<li>{html_mod.escape(str(s))}</li>" for s in steps)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"/><title>QV DMS</title>
<style>body{{font-family:Segoe UI,Microsoft JhengHei,sans-serif;background:#111;color:#eee;padding:24px}}
section{{background:#1c1c1c;padding:16px;border-radius:8px;margin-bottom:16px}}</style>
</head><body>
<h1>{title}</h1>
<section><h2>已執行步驟</h2><ul>{step_lis}</ul></section>
<section><h2>備註</h2><ul>{note_lis}</ul></section>
<section><h2>下一步（LLM）</h2><pre>{html_mod.escape(str(narrative.get("next_actions") or []))}</pre></section>
</body></html>
"""
