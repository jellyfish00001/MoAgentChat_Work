"""Assemble dark-theme HTML dashboard from scan dict (no LLM)."""

from __future__ import annotations

import html
from typing import Any


def render_rd_dashboard(scan: dict[str, Any], *, narrative: dict[str, Any] | None = None) -> str:
    kpi = scan.get("kpi") or {}
    narrative = narrative or {}
    headline = html.escape(str(narrative.get("headline") or "Rework & Dismantle 工單風險分析報告"))
    risks = narrative.get("risks") or scan.get("notes") or []
    actions = narrative.get("actions") or []

    def cards() -> str:
        items = [
            ("工單總數", kpi.get("order_total", 0)),
            ("返工工單", f"{kpi.get('rework_count', 0)} ({kpi.get('rework_pct', 0)}%)"),
            ("拆解工單", f"{kpi.get('dismantle_count', 0)} ({kpi.get('dismantle_pct', 0)}%)"),
            ("異常工單數", kpi.get("abnormal_order_count", 0)),
            ("物料異常金額", kpi.get("material_abnormal_amount", 0)),
            ("整體合規率", f"{kpi.get('compliance_rate', 0)}%"),
        ]
        return "".join(
            f'<div class="card"><div class="label">{html.escape(str(k))}</div>'
            f'<div class="value">{html.escape(str(v))}</div></div>'
            for k, v in items
        )

    def ul(title: str, rows: list[Any], empty: str) -> str:
        if not rows:
            return f"<section><h3>{html.escape(title)}</h3><p>{html.escape(empty)}</p></section>"
        lis = "".join(f"<li><code>{html.escape(str(r))}</code></li>" for r in rows[:50])
        return f"<section><h3>{html.escape(title)}</h3><ul>{lis}</ul></section>"

    risk_lis = "".join(f"<li>{html.escape(str(r))}</li>" for r in risks)
    act_lis = "".join(f"<li>{html.escape(str(a))}</li>" for a in actions)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>{headline}</title>
<style>
body{{margin:0;font-family:Segoe UI,Microsoft JhengHei,sans-serif;background:#0f1419;color:#e7ecf3}}
header{{padding:24px 32px;border-bottom:1px solid #243044}}
h1{{margin:0 0 8px;font-size:1.4rem}}
.meta{{opacity:.7;font-size:.9rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;padding:24px 32px}}
.card{{background:#1a2332;border-radius:10px;padding:16px}}
.card .label{{font-size:.75rem;opacity:.7}}
.card .value{{font-size:1.25rem;margin-top:6px;font-weight:600}}
main{{padding:0 32px 40px;display:grid;gap:20px}}
section{{background:#1a2332;border-radius:10px;padding:16px 20px}}
h2,h3{{margin-top:0}}
code{{font-size:.8rem;word-break:break-all}}
ul{{padding-left:1.2rem}}
</style>
</head>
<body>
<header>
  <h1>{headline}</h1>
  <div class="meta">報告目的：識別返工／拆解流程、物料與成本風險（程式掃描 + 可選 LLM 研判）</div>
</header>
<div class="cards">{cards()}</div>
<main>
  <section>
    <h2>綜合研判</h2>
    <ul>{risk_lis or "<li>（無 LLM 研判；見規則 notes）</li>"}</ul>
    <h3>管理行動</h3>
    <ul>{act_lis or "<li>（待 LLM 或人工補行動）</li>"}</ul>
  </section>
  {ul("流程倒置", scan.get("inversion_orders") or [], "流程倒置：未發現。")}
  {ul("異常調帳", scan.get("missrate_anomalies") or [], "異常調賬：未發現。")}
  {ul("物料挪用", scan.get("misuse_anomalies") or [], "物料挪用：未發現。")}
  {ul("超期 KPI", scan.get("kpi_overdue") or [], "超期KPI：未發現。")}
  {ul("拆解異常", scan.get("dismantle_anomalies") or [], "拆解異常：未發現。")}
  {ul("其他／待命名", scan.get("other_anomalies") or [], "無待命名異常（RD-01）。")}
</main>
</body>
</html>
"""
