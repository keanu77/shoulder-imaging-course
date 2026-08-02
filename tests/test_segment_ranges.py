"""驗證多區間稽核的安全性質：能通過好資料，也仍能擋住壞資料。"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src" / "build"))
from audit_medical import parse_clock, parse_segment_ranges


def covers(text: str, intervention: str) -> bool:
    """模擬稽核的判定：任一診斷區間涵蓋介入起點就是違規。"""
    segments = parse_segment_ranges(text)
    if segments is None:
        return True  # 格式不合法一樣視為擋下
    iv = parse_clock(intervention)
    return any(s <= iv <= e for s, e in segments)


PARSE_OK = [
    ("02:33–19:08", 1),
    ("02:33–19:08、19:20–35:54", 2),
    ("00:00–08:54; 09:35–11:23; 11:49–20:57", 3),
    ("1:05:00–1:08:43", 1),
]

PARSE_REJECT = [
    ("", "空字串"),
    ("19:08–02:33", "單段倒退"),
    ("02:33", "缺結束時間"),
    ("19:20–35:54、02:33–19:08", "段落順序顛倒"),
    ("02:33–19:30、19:20–35:54", "段落重疊"),
    ("02:33–19:08、19:08–35:54", "段落相接（端點重疊）"),
    ("02:33–19:99", "秒數非法"),
    ("abc–def", "非時間格式"),
]

# (診斷區間, 介入起點, 是否應被擋下)
SAFETY = [
    ("02:33–19:08", "19:09", False, "介入在單段之後——放行"),
    ("02:33–19:08、19:20–35:54", "19:09", False, "介入落在兩段之間的空隙——放行"),
    ("02:33–35:54", "19:09", True, "單段涵蓋介入起點——必須擋"),
    (
        "02:33–19:08、19:00–35:54",
        "19:09",
        True,
        "第二段回頭涵蓋介入起點（且重疊）——必須擋",
    ),
    ("02:33–19:09", "19:09", True, "區間終點正好等於介入起點——必須擋"),
    ("19:09–35:54", "19:09", True, "區間起點正好等於介入起點——必須擋"),
    ("00:00–06:00、06:30–19:08、19:20–35:54", "19:09", False, "三段皆避開——放行"),
    (
        "00:00–06:00、06:30–19:20、19:30–35:54",
        "19:09",
        True,
        "中段涵蓋介入起點——必須擋",
    ),
]


def main() -> int:
    failures = []

    for text, expected_count in PARSE_OK:
        result = parse_segment_ranges(text)
        if result is None or len(result) != expected_count:
            failures.append(f"解析應成功但失敗：{text!r} → {result!r}")

    for text, why in PARSE_REJECT:
        if parse_segment_ranges(text) is not None:
            failures.append(f"解析應拒絕但通過：{text!r}（{why}）")

    for text, iv, should_block, why in SAFETY:
        blocked = covers(text, iv)
        if blocked != should_block:
            verb = "應擋下但放行" if should_block else "應放行但擋下"
            failures.append(f"安全性質{verb}：{text!r} + 介入 {iv}（{why}）")

    total = len(PARSE_OK) + len(PARSE_REJECT) + len(SAFETY)
    if failures:
        print(f"❌ {len(failures)}/{total} 項失敗：")
        for failure in failures:
            print("   -", failure)
        return 1
    print(
        f"✅ 全部 {total} 項通過（解析 {len(PARSE_OK)} 正例 / {len(PARSE_REJECT)} 反例、"
        f"安全性質 {len(SAFETY)} 項）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
