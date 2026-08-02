#!/usr/bin/env python3
"""肩部超音波課程的醫療內容閘門。

這個稽核不判斷醫療內容是否正確；它確認每個單元都具備可供醫師審閱的
教學目標、標準切面、陷阱、評量與來源，並防止第一階段混入介入操作。
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSE = Path(os.environ.get("COURSE") or ROOT / "course").resolve()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_clock(value: object) -> int | None:
    """將 MM:SS 或 HH:MM:SS 轉為秒；不接受超出 59 的秒／小時格式分鐘。"""
    clock = str(value or "")
    if re.fullmatch(r"(?:\d{1,2}:\d{2}|\d+:\d{2}:\d{2})", clock) is None:
        return None
    parts = clock.split(":")
    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds if seconds < 60 else None
    hours, minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds if minutes < 60 and seconds < 60 else None


SEGMENT_SPLIT_RE = re.compile(r"[、;,]")
SEGMENT_RE = re.compile(
    r"((?:\d{1,2}:)?\d{1,2}:\d{2})\s*[–-]\s*((?:\d{1,2}:)?\d{1,2}:\d{2})"
)


def format_clock(seconds: int) -> str:
    """秒轉回 MM:SS 或 H:MM:SS，只用於錯誤訊息。"""
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def parse_segment_ranges(text: str) -> list[tuple[int, int]] | None:
    """解析一或多段診斷區間；格式錯、單段非遞增、或段間重疊時回 None。

    多段以 、 ; , 分隔。允許段與段之間留空隙——介入內容就落在空隙裡——
    但要求整體嚴格遞增且不重疊，避免打錯字造成錯誤框定。
    """
    parts = [part.strip() for part in SEGMENT_SPLIT_RE.split(text)]
    if not parts or any(not part for part in parts):
        return None
    segments: list[tuple[int, int]] = []
    for part in parts:
        match = SEGMENT_RE.fullmatch(part)
        if match is None:
            return None
        start = parse_clock(match.group(1))
        end = parse_clock(match.group(2))
        if start is None or end is None or start >= end:
            return None
        if segments and start <= segments[-1][1]:
            return None
        segments.append((start, end))
    return segments


def main() -> int:
    cfg = load(COURSE / "course.config.json")
    source_names = {chapter["source"] for chapter in cfg["chapters"]}
    sources = [load(COURSE / "data" / f"{name}.json") for name in source_names]
    medical = cfg.get("medical", {})
    status_order = medical.get("reviewStatuses", [])
    allowed_status = set(status_order)
    allowed_tiers = {
        tier.get("id")
        for tier in cfg.get("learningTiers", [])
        if isinstance(tier, dict) and tier.get("id")
    }
    allowed_curation = {"provisional", "pending-date-verification", "approved"}
    cutoff = date.fromisoformat(medical["contentCutoff"])

    references: dict[str, dict] = {}
    chapters: list[dict] = []
    for source in sources:
        references.update(source.get("reference_catalog", {}))
        chapters.extend(source.get("chapters", []))

    errors: list[str] = []
    warnings: list[str] = []
    unit_ids: set[str] = set()
    video_ids: set[str] = set()
    classic_count = 0
    review_counts: dict[str, int] = {}

    def err(where: str, message: str) -> None:
        errors.append(f"{where}: {message}")

    for chapter in chapters:
        chapter_code = chapter.get("chapter", "?")
        for unit in chapter.get("units", []):
            where = f"{chapter_code}/{unit.get('id', '?')}"
            unit_id = unit.get("id")
            if not unit_id:
                err(where, "缺少單元 id")
            elif unit_id in unit_ids:
                err(where, "單元 id 重複")
            else:
                unit_ids.add(unit_id)

            required_lists = {"objectives": 2, "key_points": 2, "pitfalls": 2}
            for field, minimum in required_lists.items():
                value = unit.get(field)
                if not isinstance(value, list) or len(value) < minimum:
                    err(where, f"{field} 至少需要 {minimum} 項")

            if len(str(unit.get("summary", "")).strip()) < 20:
                err(where, "summary 太短，無法供醫療審閱")
            if len(str(unit.get("assessment", "")).strip()) < 50:
                err(where, "assessment 少於 50 字")
            if unit.get("review_status") not in allowed_status:
                err(where, f"review_status 不在允許清單：{unit.get('review_status')!r}")
            else:
                status = unit["review_status"]
                review_counts[status] = review_counts.get(status, 0) + 1
            if unit.get("type") != "orientation" and not unit.get("required_views"):
                err(where, "非導論單元必須列出 required_views")

            for reference_id in unit.get("reference_ids", []):
                if reference_id not in references:
                    err(where, f"找不到 reference_id {reference_id}")

            if medical.get("scope") == "diagnostic-only" and unit.get("type") == "intervention":
                err(where, "第一階段不得包含 intervention 類型")

            for video in unit.get("drills", []):
                video_where = f"{where}/{video.get('name', '?')}"
                match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", video.get("url", ""))
                if not match:
                    err(video_where, "不是可辨識的 YouTube 連結")
                else:
                    video_ids.add(match.group(1))

                for field in (
                    "source_authority",
                    "curation_status",
                    "last_verified_at",
                    "why",
                    "scope_note",
                ):
                    if not video.get(field):
                        err(video_where, f"缺少 {field}")

                tier = video.get("learning_tier")
                if tier not in allowed_tiers:
                    err(video_where, f"learning_tier 不在允許清單：{tier!r}")
                if tier == "core" and not (video.get("presenter") or video.get("presenter_note")):
                    err(video_where, "核心影片必須標示 presenter 或 presenter_note")

                status = video.get("curation_status")
                if status not in allowed_curation:
                    err(video_where, f"curation_status 不在允許清單：{status!r}")

                if (
                    video.get("source_authority") == "medical-device-education"
                    and not video.get("disclosure")
                ):
                    err(video_where, "醫療器材教育來源必須提供 disclosure")

                upload = video.get("upload_date")
                if not upload:
                    if status == "pending-date-verification":
                        warnings.append(f"{video_where}: YouTube 上架日期仍待確認")
                    else:
                        err(video_where, "缺少 upload_date 時必須標記 pending-date-verification")
                upload_date = None
                try:
                    if upload:
                        upload_date = date.fromisoformat(upload)
                except (TypeError, ValueError):
                    err(video_where, f"upload_date 日期格式錯誤：{upload!r}")

                if "original_content_date" not in video:
                    err(video_where, "缺少 original_content_date 欄位；未知時請明確填 null")
                original = video.get("original_content_date")
                original_date = None
                try:
                    if original:
                        original_date = date.fromisoformat(original)
                except (TypeError, ValueError):
                    err(video_where, f"original_content_date 日期格式錯誤：{original!r}")
                if original is None and not video.get("date_note"):
                    err(video_where, "original_content_date 為 null 時必須提供 date_note")
                if original_date and upload_date and original_date > upload_date:
                    err(video_where, "original_content_date 不得晚於 upload_date")

                verified = video.get("last_verified_at")
                try:
                    if verified:
                        verified_date = date.fromisoformat(verified)
                        if verified_date > date.today():
                            err(video_where, "last_verified_at 不得晚於今天")
                except (TypeError, ValueError):
                    err(video_where, f"last_verified_at 日期格式錯誤：{verified!r}")

                if "contains_intervention" not in video:
                    err(video_where, "缺少 contains_intervention 布林欄位")
                elif not isinstance(video.get("contains_intervention"), bool):
                    err(video_where, "contains_intervention 必須是 true 或 false")

                if video.get("contains_intervention") is True:
                    intervention_start = parse_clock(video.get("intervention_start_timestamp"))
                    if intervention_start is None:
                        err(
                            video_where,
                            "含介入內容時 intervention_start_timestamp 必須是合法 MM:SS 或 HH:MM:SS",
                        )

                    range_text = str(video.get("diagnostic_segment_range") or "").strip()
                    segments = parse_segment_ranges(range_text)
                    if segments is None:
                        err(
                            video_where,
                            "含介入內容時 diagnostic_segment_range 必須是遞增的合法時間範圍"
                            "（多段以 、 或 ; 分隔，段間不得重疊）",
                        )
                    elif intervention_start is not None:
                        for seg_start, seg_end in segments:
                            if seg_start <= intervention_start <= seg_end:
                                err(
                                    video_where,
                                    "診斷段落不得涵蓋介入起點："
                                    f"{format_clock(seg_start)}–{format_clock(seg_end)}"
                                    f" 含 {video.get('intervention_start_timestamp')}",
                                )
                                break

                    duration = parse_clock(video.get("duration"))
                    if duration is None:
                        err(video_where, "含介入內容時必須提供合法 duration")
                    elif intervention_start is not None and intervention_start >= duration:
                        err(video_where, "介入起點必須早於影片結束")

                    if not video.get("presenter"):
                        err(video_where, "含介入內容的影片必須標示 presenter")
                    if not video.get("qualification_evidence_url"):
                        err(video_where, "含介入內容的影片必須提供 qualification_evidence_url")

                content_date = original_date or upload_date
                if not content_date:
                    if status != "pending-date-verification":
                        warnings.append(f"{video_where}: 原始內容與上架日期仍待確認")
                    continue

                if content_date < cutoff:
                    classic_count += 1
                    if not video.get("classic_exception"):
                        err(video_where, f"早於近五年門檻 {cutoff}，但未標示經典例外")
                    if medical.get("classicExceptionsRequireReason") and not video.get(
                        "classic_exception_reason"
                    ):
                        err(video_where, "經典例外缺少 classic_exception_reason")

                intervention_markers = (
                    "inject",
                    "needle",
                    "aspiration",
                    "intervention",
                    "介入",
                    "穿刺",
                    "抽吸",
                )
                title = f"{video.get('name', '')} {video.get('title', '')}".lower()
                if medical.get("scope") == "diagnostic-only" and any(
                    marker in title for marker in intervention_markers
                ) and video.get("contains_intervention") is not True:
                    err(video_where, "診斷階段選片疑似含介入操作")

    if medical.get("primaryAudience") != "physicians":
        errors.append("設定檔：primaryAudience 必須是 physicians")
    if not medical.get("interventionalContentDeferred"):
        errors.append("設定檔：第一階段必須將介入注射標記為 deferred")
    if medical.get("allowIndexing") and review_counts.get("approved", 0) != len(unit_ids):
        errors.append("設定檔：仍有未 approved 單元時不得啟用搜尋引擎索引")

    print("\n醫療內容閘門")
    print(f"  {'✓' if not errors else '✗'} {len(unit_ids)} 個單元 · {len(video_ids)} 支影片")
    print(f"  ✓ {len(references)} 筆參考來源 · {classic_count} 支經典例外")
    print(
        "  ✓ 審閱狀態："
        + " · ".join(f"{status} {review_counts.get(status, 0)}" for status in status_order)
        + (" · 可索引" if medical.get("allowIndexing") else " · noindex")
    )
    if warnings:
        print(f"  ⚠ {len(warnings)} 項非阻斷警告（目前主要為內容或上架日期待確認）")
        for warning in warnings:
            print(f"      · {warning}")
    if errors:
        print(f"  ✗ {len(errors)} 項錯誤")
        for error in errors:
            print(f"      · {error}")
    else:
        print("  ✓ 診斷限定、審閱狀態與經典影片例外規則通過")

    print(
        "\n注意：結構稽核通過不等於醫療核准；所有未 approved 單元仍需具資格醫師簽核。"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
