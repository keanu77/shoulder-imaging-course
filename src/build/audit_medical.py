#!/usr/bin/env python3
"""區域肌肉骨骼超音波課程的醫療內容閘門。

這個稽核不判斷醫療內容是否正確；它確認每個單元都具備可供醫師審閱的
教學目標、標準切面、陷阱、評量與來源，並防止未框限的介入內容混入診斷課程。
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
    parts = str(value or "").split(":")
    if len(parts) not in {2, 3} or not all(part.isdigit() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds if seconds < 60 else None
    hours, minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds if minutes < 60 and seconds < 60 else None


# 半形與全形分隔符都接受，讓同一套引擎能解析不同課程既有的合法多段範圍。
# 全形逗號目前沒有資料在用，但與全形分號屬於同一類格式漂移，支援成本為零。
SEGMENT_SPLIT_RE = re.compile(r"[、，；;,]")
SEGMENT_RE = re.compile(
    r"((?:\d{1,2}:)?\d{1,2}:\d{2})\s*[–-]\s*((?:\d{1,2}:)?\d{1,2}:\d{2})"
)
AI_CRAWLER_AGENTS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended")


def format_clock(seconds: int) -> str:
    """秒轉回 MM:SS 或 H:MM:SS，只用於錯誤訊息。"""
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def check_ai_crawler_gate(dist_dir: Path, allow_indexing: bool) -> list[str]:
    """簽核前 robots.txt 必須明確封鎖常見 AI 檢索器。"""
    if allow_indexing:
        return []
    robots_path = dist_dir / "robots.txt"
    if not robots_path.exists():
        return []
    rules: dict[str, str] = {}
    agent = None
    for raw in robots_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
        elif agent and line.lower().startswith(("allow:", "disallow:")):
            rules.setdefault(agent, line)
    messages: list[str] = []
    for name in AI_CRAWLER_AGENTS:
        rule = rules.get(name)
        if rule is None:
            messages.append(f"robots.txt 未涵蓋 AI 檢索器 {name}：簽核前必須明確封鎖")
        elif not rule.lower().replace(" ", "").startswith("disallow:/"):
            messages.append(
                f"allowIndexing=false 時 {name} 必須是 Disallow: /，實際為「{rule}」"
            )
    return messages


def parse_segment_ranges(text: str) -> list[tuple[int, int]] | None:
    """解析一或多段診斷區間；格式錯、單段非遞增、或段間重疊時回 None。

    多段以 、 ; , 分隔。允許段與段之間留空隙——介入內容就落在空隙裡——
    但要求整體嚴格遞增且不重疊，避免打錯字造成錯誤框定。
    """
    parts = [part.strip() for part in SEGMENT_SPLIT_RE.split(text) if part.strip()]
    if not parts:
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


def check_segment_framing(
    segments: list[tuple[int, int]],
    intervention_start: int | None,
    duration: int | None,
) -> list[str]:
    """在區間本身已解析成功之後，檢查它是否真的框住了介入內容。

    回傳錯誤訊息清單（空清單代表通過）。抽成獨立函式是為了讓
    tests/test_segment_ranges.py 直接呼叫到**稽核真正跑的那份邏輯**，
    而不是在測試裡複製一份規則——複製的那份不會因為 main() 忘了呼叫而失敗。
    """
    messages: list[str] = []

    if intervention_start is not None:
        for seg_start, seg_end in segments:
            if seg_start <= intervention_start <= seg_end:
                messages.append(
                    "診斷段落不得涵蓋介入起點："
                    f"{format_clock(seg_start)}–{format_clock(seg_end)}"
                    f" 含 {format_clock(intervention_start)}"
                )
                break

    # 終點打錯（例如多一位數）會把觀看範圍延伸到影片結束之後，
    # 實務上等於沒有框限。
    if duration is not None and any(seg_end > duration for _, seg_end in segments):
        messages.append("診斷段落不得超出影片長度")

    # 這裡刻意「不」要求至少一段在介入起點前結束。肘部的稽核有這條，但
    # 2026-08-03 拿肩部真實資料一驗就是誤報：有兩支影片的介入落在最開頭
    # （02:12、04:56），診斷段落從其後開始（02:30、05:06）——播放器從第一段
    # 起點播，學員根本不會經過介入畫面，框限是正確的。那條規則只在「介入落在
    # 中段空隙」這種形狀下恆真，而肘部唯一一支介入影片正好是那個形狀。
    # 要加回來之前，先確認它在六站的資料上都不誤報。

    return messages


def check_segments(video: dict, entry: dict, allowed_status: set[str]) -> list[str]:
    """檢查一支影片的逐段筆記。回傳錯誤訊息清單，空清單代表通過。

    逐段筆記會在播放器上變成一鍵跳播的入口，所以最重要的一條是：只要影片有框限
    診斷範圍，每一段都必須完整落在框限內。否則學員按下時間碼就會被直接送進注射
    示範——那正是 contains_intervention 這套機制要擋的事。
    """
    errors: list[str] = []

    status = entry.get("review_status")
    if status not in allowed_status:
        errors.append(f"review_status 不在允許清單：{status!r}")

    segments = entry.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments 必須是非空陣列")
        return errors

    duration = parse_clock(video.get("duration"))
    # 呼叫 parser 前先正規化空值，與 main() 的資料流保持一致。
    range_text = str(video.get("diagnostic_segment_range") or "").strip()
    diagnostic_ranges = parse_segment_ranges(range_text) if range_text else None
    if video.get("contains_intervention") is True and diagnostic_ranges is None:
        errors.append("含介入影片缺少可解析的 diagnostic_segment_range，無法框限逐段筆記")

    previous_end: int | None = None
    for index, segment in enumerate(segments, start=1):
        where = f"第 {index} 段"
        start = parse_clock(segment.get("start"))
        end = parse_clock(segment.get("end"))
        if start is None or end is None:
            errors.append(f"{where}：start／end 必須是合法 MM:SS 或 HH:MM:SS")
            continue
        if start >= end:
            errors.append(f"{where}：start 必須早於 end")
            continue
        if previous_end is not None and start <= previous_end:
            errors.append(f"{where}：段落必須嚴格遞增且不重疊")
        previous_end = end

        if duration is not None and end > duration:
            errors.append(f"{where}：段落結束時間超出影片長度")

        if diagnostic_ranges is not None and not any(
            r_start <= start and end <= r_end for r_start, r_end in diagnostic_ranges
        ):
            errors.append(f"{where}：段落未完整落在診斷段落範圍內，不得作為跳播入口")

        for field, minimum in (("title", 4), ("summary", 10)):
            if len(str(segment.get(field, "")).strip()) < minimum:
                errors.append(f"{where}：{field} 太短或缺漏")
        detail = segment.get("detail")
        if not isinstance(detail, list) or not detail:
            errors.append(f"{where}：detail 必須是非空陣列")

    return errors


def audit_segments(
    path: Path, videos_by_url: dict[str, dict], allowed_status: set[str]
) -> tuple[list[str], int, dict[str, int]]:
    """稽核整份 segments.json，回傳（錯誤清單、段落總數、各審閱狀態計數）。"""
    errors: list[str] = []
    counts: dict[str, int] = {}
    total = 0
    if not path.exists():
        return errors, total, counts

    blob = load(path)
    seen_urls: set[str] = set()
    for entry in blob.get("videos", []):
        url = entry.get("video_url")
        where = f"segments/{url or '?'}"
        if not url:
            errors.append(f"{where}: 缺少 video_url")
            continue
        if url in seen_urls:
            errors.append(f"{where}: video_url 重複")
            continue
        seen_urls.add(url)

        video = videos_by_url.get(url)
        if video is None:
            errors.append(f"{where}: video_url 不對應課程中任何一支影片")
            continue

        for message in check_segments(video, entry, allowed_status):
            errors.append(f"{where}: {message}")

        status = entry.get("review_status")
        counts[status] = counts.get(status, 0) + 1
        total += len(entry.get("segments") or [])

    return errors, total, counts


def check_questions(catalog_ids: set[str], allowed_status: set[str]) -> list[str]:
    """知識檢核題組的結構稽核：題數、選項解析、正解數、引用存在性、id 穩定性。"""
    path = ROOT / "course" / "data" / "questions.json"
    if not path.exists():
        return []
    blob = json.loads(path.read_text())
    errors: list[str] = []
    seen_ids: set[str] = set()
    for uid, entry in (blob.get("units") or {}).items():
        where = f"questions/{uid}"
        if entry.get("review_status") not in allowed_status:
            errors.append(f"{where}: review_status 不在允許清單：{entry.get('review_status')!r}")
        qs = entry.get("questions") or []
        if not 3 <= len(qs) <= 5:
            errors.append(f"{where}: 題數 {len(qs)}，應為 3–5")
        for q in qs:
            qid = q.get("id") or ""
            qwhere = f"{where}/{qid or '(no id)'}"
            if not qid.startswith(uid + "-q"):
                errors.append(f"{qwhere}: id 必須以 {uid}-q 開頭")
            if qid in seen_ids:
                errors.append(f"{qwhere}: id 重複")
            seen_ids.add(qid)
            if q.get("type") not in {"single", "multi"}:
                errors.append(f"{qwhere}: type 必須是 single|multi")
            if not (q.get("stem") or "").strip():
                errors.append(f"{qwhere}: 缺 stem")
            opts = q.get("options") or []
            if len(opts) < 3:
                errors.append(f"{qwhere}: 選項至少 3 個")
            correct = [o for o in opts if o.get("correct")]
            if q.get("type") == "single" and len(correct) != 1:
                errors.append(f"{qwhere}: single 題必須恰好 1 個正解")
            if q.get("type") == "multi" and len(correct) < 1:
                errors.append(f"{qwhere}: multi 題至少 1 個正解")
            for i, o in enumerate(opts):
                if not (o.get("rationale") or "").strip():
                    errors.append(f"{qwhere}: 選項 {i+1} 缺 rationale（不論對錯都要有解析）")
            refs = q.get("reference_ids") or []
            if not refs:
                errors.append(f"{qwhere}: 缺 reference_ids")
            for r in refs:
                if r not in catalog_ids:
                    errors.append(f"{qwhere}: 引用 {r} 不存在於 reference_catalog")
    return errors


def main() -> int:
    cfg = load(COURSE / "course.config.json")
    brief_path = COURSE / "brief.json"
    brief = load(brief_path) if brief_path.exists() else None
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
    errors.extend(
        check_ai_crawler_gate(ROOT / "dist", bool(medical.get("allowIndexing", False)))
    )
    unit_ids: set[str] = set()
    video_ids: set[str] = set()
    videos_by_url: dict[str, dict] = {}
    classic_count = 0
    review_counts: dict[str, int] = {}

    serialized = json.dumps({"brief": brief, "config": cfg, "sources": sources}, ensure_ascii=False)
    if "TODO" in serialized or "__" in serialized:
        errors.append("模板：course brief/config/data 仍有 TODO 或未替換 token，不得發布")

    # 新引擎支援具名 brief 治理；舊世代課程若沒有 brief，仍由 config 與逐項
    # review_status 閘門治理。只要 brief 存在，就完整執行新世代的欄位檢查。
    if brief is not None:
        if brief.get("audience") != medical.get("primaryAudience"):
            errors.append("需求：brief audience 與 medical.primaryAudience 不一致")
        if brief.get("scope") != medical.get("scope"):
            errors.append("需求：brief scope 與 medical.scope 不一致")
        if bool(brief.get("indexing")) != bool(medical.get("allowIndexing")):
            errors.append("需求：brief indexing 與 medical.allowIndexing 不一致")
        repo_settings = brief.get("repository_settings") or {}
        if repo_settings.get("visibility") not in {"public", "private"}:
            errors.append("需求：repository visibility 必須明確為 public 或 private")
        if not repo_settings.get("default_branch"):
            errors.append("需求：缺少 repository default branch")
        if not brief.get("content_owner"):
            errors.append("需求：缺少 content owner")
        reviewer = brief.get("medical_reviewer") or {}
        for field in ("name", "qualification", "scope"):
            if not reviewer.get(field):
                errors.append(f"需求：medical reviewer 缺少 {field}")

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
            if unit.get("type") != "orientation" and not unit.get("reference_ids"):
                err(where, "非導論單元至少需要一筆 reference_id")

            if medical.get("scope") == "diagnostic-only" and unit.get("type") == "intervention":
                err(where, "第一階段不得包含 intervention 類型")

            lesson = unit.get("lesson")
            for video in [*([lesson] if lesson else []), *unit.get("drills", [])]:
                if video.get("url"):
                    videos_by_url[video["url"]] = video

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

                if video.get("source_authority") == "medical-device-education" and not video.get(
                    "disclosure"
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
                    duration = parse_clock(video.get("duration"))
                    if segments is None:
                        err(
                            video_where,
                            "含介入內容時 diagnostic_segment_range 必須是遞增的合法時間範圍"
                            "（多段以 、；; 或 , 分隔，段間不得重疊）",
                        )
                    else:
                        for message in check_segment_framing(
                            segments, intervention_start, duration
                        ):
                            err(video_where, message)

                    if duration is None:
                        err(video_where, "含介入內容時必須提供合法 duration")
                    elif intervention_start is not None and intervention_start >= duration:
                        err(video_where, "介入起點必須早於影片結束")

                    if not video.get("presenter"):
                        err(video_where, "含介入內容的影片必須標示 presenter")
                    if not video.get("qualification_evidence_url"):
                        err(video_where, "含介入內容的影片必須提供 qualification_evidence_url")
                elif video.get("contains_intervention") is False:
                    # 沒有介入卻留著介入時間戳，是殘留髒資料：它會讓人以為這支
                    # 影片已經框限過，稽核卻因為 contains_intervention=false 而
                    # 完全不看那個值。
                    #
                    # 但 diagnostic_segment_range 不在此列。診斷影片用
                    # 00:00–<完整片長> 記錄「整支都是診斷內容」是既有慣例
                    # （肩部 9 支這樣寫，每一支的終點都精確等於 duration）。
                    # 肘部的稽核要求兩個欄位都為 null，照搬過來會逼人刪掉有意義
                    # 的資料——2026-08-03 實測確認。
                    if str(video.get("intervention_start_timestamp") or "").strip():
                        err(
                            video_where,
                            "不含介入內容時 intervention_start_timestamp 必須為 null 或留白",
                        )

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
                    err(
                        video_where,
                        "片名疑似含介入內容，必須標記 contains_intervention=true 並框限診斷段落",
                    )

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

    segment_errors, segment_total, segment_counts = audit_segments(
        COURSE / "data" / "segments.json", videos_by_url, allowed_status
    )
    errors.extend(segment_errors)

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
    if segment_counts:
        print(
            f"  ✓ 逐段筆記：{sum(segment_counts.values())} 支影片 · {segment_total} 段 · "
            + " · ".join(f"{status} {count}" for status, count in sorted(segment_counts.items()))
            + "（只有 approved 會進入 course.json）"
        )
    if warnings:
        print(f"  ⚠ {len(warnings)} 項非阻斷警告（目前主要為內容或上架日期待確認）")
        for warning in warnings:
            print(f"      · {warning}")
    q_errors = check_questions(set(references), allowed_status)
    errors.extend(q_errors)
    qpath = ROOT / "course" / "data" / "questions.json"
    if qpath.exists():
        qblob = json.loads(qpath.read_text())
        qunits = qblob.get("units") or {}
        qa = sum(1 for e in qunits.values() if e.get("review_status") == "approved")
        qtotal = sum(len(e.get("questions") or []) for e in qunits.values())
        print(f"  {'✓' if not q_errors else '✗'} 知識檢核：{len(qunits)} 個題組 · {qtotal} 題 · approved {qa}（只有 approved 會進入 course.json）")

    if errors:
        print(f"  ✗ {len(errors)} 項錯誤")
        for error in errors:
            print(f"      · {error}")
    else:
        print("  ✓ 診斷限定、審閱狀態與經典影片例外規則通過")

    print("\n注意：結構稽核通過不等於醫療核准。approved 代表通過策展審閱（範圍框限、來源與資格查證、文獻對應），\n不代表策展人對第三方影片的臨床內容背書；未 approved 的內容不會進入 course.json。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
