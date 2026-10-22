"""QV DMS input inventory — pure rules (MVP skeleton)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "Cover.xlsx",
    "生產工單.xlsx",
    "會計調整.xlsx",
    "65011201.xlsx",
    "庫存調整單.xlsx",
    "材料分析-previous.xlsx",
]

OPTIONAL_OR_OFTEN_MISSING = [
    "材料分析.xlsx",  # 當期：規格需要，示範包可能缺
]


@dataclass
class QvInventory:
    data_dir: str
    present: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    pipeline_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inventory_qv_dms(data_dir: Path) -> QvInventory:
    present: list[str] = []
    missing_req: list[str] = []
    missing_opt: list[str] = []

    for name in REQUIRED_FILES:
        path = data_dir / name
        if path.is_file():
            present.append(name)
        else:
            missing_req.append(name)

    for name in OPTIONAL_OR_OFTEN_MISSING:
        path = data_dir / name
        if path.is_file():
            present.append(name)
        else:
            missing_opt.append(name)

    steps = [
        "1. 材料分析 → Pivot → 回填 Cover PCL500（需當期材料分析.xlsx）",
        "2. 生產工單 → 报工差异／未分析",
        "3. 會計調整關鍵字回填",
        "4. 65011201 QV Reserve",
        "5. 庫存調整 Reason Code",
        "6. 格式 + Email/Teams",
        "7. 樞紐儀表板 HTML",
        "8. 當期／上期 Material Analysis（LLM 敘事）",
        "9. 兩期 Pivot-Comprise",
        "10. HTML 簡報 + 交互選單",
    ]
    return QvInventory(
        data_dir=str(data_dir),
        present=present,
        missing_required=missing_req,
        missing_optional=missing_opt,
        pipeline_steps=steps,
    )
