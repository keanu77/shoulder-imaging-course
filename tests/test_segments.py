"""驗證逐段筆記閘門：好資料要放行，壞資料要擋下。

測試直接呼叫 audit_medical.check_segments——也就是稽核真正跑的那個函式，
不是另外複寫一份判斷邏輯。稽核改了而測試沒跟上時，這裡才會紅。

最重要的一條是「跳播不得落在框限外」：逐段筆記在播放器上是一鍵跳播的入口，
若允許段落落在 diagnostic_segment_range 之外，學員按下時間碼就會被直接送進
注射示範，等於繞過 contains_intervention 這整套機制。
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src" / "build"))

from audit_medical import check_segments

STATUSES = {"draft", "medical-review", "approved"}

# 範例形狀：片長 14:22，介入自 06:30 起，框限 00:00–06:29 與 06:44–14:22
INTERVENTION_VIDEO = {
    "duration": "14:22",
    "contains_intervention": True,
    "intervention_start_timestamp": "06:30",
    "diagnostic_segment_range": "00:00–06:29；06:44–14:22",
}

# 無介入、也沒有框限的一般診斷影片
PLAIN_VIDEO = {
    "duration": "12:45",
    "contains_intervention": False,
    "intervention_start_timestamp": None,
    "diagnostic_segment_range": None,
}


def seg(start, end, title="外側解剖回顧", summary="這一段在講什麼的速讀摘要。", detail=None):
    return {
        "start": start,
        "end": end,
        "title": title,
        "summary": summary,
        "detail": detail if detail is not None else ["一條實際的教學重點。"],
    }


def entry(segments, status="draft"):
    return {"review_status": status, "segments": segments}


ACCEPT = [
    (
        INTERVENTION_VIDEO,
        entry([seg("00:00", "02:33"), seg("02:37", "04:16"), seg("04:19", "06:29")]),
        "全部落在第一個診斷區間內",
    ),
    (
        INTERVENTION_VIDEO,
        entry([seg("06:44", "08:04"), seg("12:31", "14:22")]),
        "落在第二個診斷區間，且結束時間正好等於片長",
    ),
    (
        INTERVENTION_VIDEO,
        entry([seg("00:00", "06:29"), seg("06:44", "14:22")]),
        "段落端點正好貼齊框限端點",
    ),
    (PLAIN_VIDEO, entry([seg("00:00", "05:00")]), "無框限的影片不做涵蓋檢查"),
    (PLAIN_VIDEO, entry([seg("00:00", "12:45")], status="approved"), "整支影片一段，且已簽核"),
]

REJECT = [
    (
        INTERVENTION_VIDEO,
        entry([seg("06:00", "07:00")]),
        "跨越介入起點：這正是要擋的一鍵跳播進注射示範",
    ),
    (INTERVENTION_VIDEO, entry([seg("06:30", "06:43")]), "整段落在介入區間內"),
    (INTERVENTION_VIDEO, entry([seg("06:35", "08:00")]), "起點在介入區間內"),
    (
        INTERVENTION_VIDEO,
        entry([seg("00:00", "02:33"), seg("02:30", "04:16")]),
        "段落重疊",
    ),
    (
        INTERVENTION_VIDEO,
        entry([seg("02:37", "04:16"), seg("00:00", "02:33")]),
        "段落順序顛倒",
    ),
    (PLAIN_VIDEO, entry([seg("00:00", "13:00")]), "結束時間超出片長"),
    (PLAIN_VIDEO, entry([seg("05:00", "02:00")]), "start 晚於 end"),
    (PLAIN_VIDEO, entry([seg("abc", "02:00")]), "非時間格式"),
    (PLAIN_VIDEO, entry([]), "空的段落陣列"),
    (PLAIN_VIDEO, entry([seg("00:00", "05:00")], status="signed-off"), "review_status 不在允許清單"),
    (PLAIN_VIDEO, entry([seg("00:00", "05:00", title="短")]), "title 太短"),
    (PLAIN_VIDEO, entry([seg("00:00", "05:00", summary="太短")]), "summary 太短"),
    (PLAIN_VIDEO, entry([seg("00:00", "05:00", detail=[])]), "detail 為空陣列"),
    (
        {**INTERVENTION_VIDEO, "diagnostic_segment_range": None},
        entry([seg("00:00", "02:00")]),
        "含介入卻沒有可解析的框限",
    ),
]


def main() -> int:
    failures = []

    for video, data, why in ACCEPT:
        errors = check_segments(video, data, STATUSES)
        if errors:
            failures.append(f"應通過但被擋下（{why}）→ {errors}")

    for video, data, why in REJECT:
        if not check_segments(video, data, STATUSES):
            failures.append(f"應擋下但通過了（{why}）")

    total = len(ACCEPT) + len(REJECT)
    if failures:
        print(f"❌ {len(failures)}/{total} 項失敗：")
        for f in failures:
            print("   -", f)
        return 1
    print(f"✅ 全部 {total} 項通過（正例 {len(ACCEPT)} / 反例 {len(REJECT)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
