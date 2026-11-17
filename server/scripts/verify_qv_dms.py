"""Run the three PO FAA-29 fixtures through the compiled LangGraph."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER))
# 本機驗證不得將 PO 明細送至外部 tracing。
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from flows.config.settings import get_settings  # noqa: E402
from flows.graphs.qv_dms_pipeline.graph import graph  # noqa: E402


def main() -> None:
    fixtures = SERVER / "testdata" / "qv_dms" / "faa29_sprint2"
    results = {}
    for label in ("輸入檔", "異常檔案-情境二", "異常檔案-情境三"):
        result = graph.invoke({"input_xlsx": str(fixtures / f"202610 {label}.xlsx")})
        results[label] = {
            "status": result["status"],
            "message": result["messages"][-1].content,
            "output_xlsx": result.get("output_xlsx", ""),
            "download_url": result.get("download_url", ""),
            "summary": result.get("cover_summary", {}),
        }
        print(
            json.dumps(
                {
                    "case": label,
                    "status": result["status"],
                    "warning_count": result.get("cover_summary", {}).get("warning_count", 0),
                    "output_xlsx": result.get("output_xlsx", ""),
                    "golden_comparison": result.get("golden_comparison", {}),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    destination = get_settings().outputs_dir() / "qv_dms" / "faa29-verification.json"
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Verification report: {destination}")
    expected = {
        "輸入檔": "golden_mismatch",
        "異常檔案-情境二": "failed",
        "異常檔案-情境三": "warning",
    }
    if any(results[name]["status"] != status for name, status in expected.items()):
        raise SystemExit("Unexpected scenario status; inspect verification report")


if __name__ == "__main__":
    main()
