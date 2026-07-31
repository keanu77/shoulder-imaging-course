#!/usr/bin/env python3
"""把 data/ 下各章 JSON 合併成 public/course.json，並驗證配額與連結。"""

from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSE = Path(os.environ.get("COURSE") or ROOT / "course").resolve()
DATA = COURSE / "data"
WEB = ROOT / "src" / "web"
DIST = Path(os.environ.get("DIST") or ROOT / "dist").resolve()
OUT = DIST / "course.json"

CFG = json.loads((COURSE / "course.config.json").read_text())

# 章節、配額、別名全部由課程設定決定，框架本身不認識任何主題
CHAPTERS = [(c["code"], c["title"], c["icon"], c["source"]) for c in CFG["chapters"]]
QUOTA = {c["code"]: (c["units"], c.get("drills", 0)) for c in CFG["chapters"]}
EVIDENCE_ALIAS = CFG.get("evidenceAlias", {})

# 課程可以自帶詞彙模組（肌群、動作類別之類）；沒有就退化成無分面、無分類
sys.path.insert(0, str(COURSE))


def _load_taxonomy(key: str):
    name = (CFG.get("taxonomy") or {}).get(key)
    return importlib.import_module(name) if name else None


facets = _load_taxonomy("facets")
categories = _load_taxonomy("categories")

YT = re.compile(
    r"^https://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}(?:&\S*)?$|^https://youtu\.be/[\w-]{11}"
)


def parse_duration(s: str | None) -> int:
    """'12:34' / '1:02:33' -> 秒。無法解析回 0。"""
    if not s:
        return 0
    parts = s.strip().split(":")
    if not all(p.isdigit() for p in parts):
        return 0
    secs = 0
    for p in parts:
        secs = secs * 60 + int(p)
    return secs


def fmt_clock(total: int) -> str:
    """秒數 -> '8:38' / '1:02:33'"""
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url or "")
    return m.group(1) if m else None


HAN = re.compile(r"[一-鿿]")


def detect_lang(text: str | None) -> str:
    return "zh" if HAN.search(text or "") else "en"


def collect_alt_lessons() -> dict:
    """unit_id -> 其他語言的主課影片清單。"""
    out: dict[str, list] = defaultdict(list)
    for path in sorted(DATA.glob("alt-lessons-*.json")):
        blob = load_json(path)
        for les in (blob or {}).get("lessons", []):
            if isinstance(les, dict) and les.get("unit") and les.get("url"):
                out[les["unit"]].append(les)
    return out


def collect_drill_evidence() -> dict:
    """合併各 agent 產出的動作類別文獻。"""
    out = {}
    for path in sorted(DATA.glob("drill-evidence-*.json")):
        blob = load_json(path)
        for cat in (blob or {}).get("categories", []):
            if isinstance(cat, dict) and cat.get("id"):
                out[cat["id"]] = cat
    return out


def fmt_duration(total: int) -> str:
    h, rem = divmod(total, 3600)
    m = rem // 60
    return f"{h} 小時 {m} 分" if h else f"{m} 分"


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"  ✗ {path.name} JSON 解析失敗：{e}", file=sys.stderr)
        return None


def collect_evidence() -> dict:
    """把 oe-*.json 攤平成 unit_id -> evidence dict。"""
    ev = {}
    for path in sorted(DATA.glob("oe-*.json")):
        blob = load_json(path)
        if not blob:
            continue
        for cond in blob.get("conditions", []):
            # agent 分批寫入時檔內可能殘留佔位字串，跳過非物件節點
            if isinstance(cond, dict) and cond.get("unit"):
                ev[cond["unit"]] = cond
    return ev


def sync_web() -> None:
    """把框架的前端骨架複製到產物目錄，course/assets 可覆寫同名檔。"""
    DIST.mkdir(parents=True, exist_ok=True)
    for src in WEB.rglob("*"):
        if src.is_dir() or src.name == "og.html":
            continue
        dst = DIST / src.relative_to(WEB)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # 課程可放自己的 favicon、覆寫樣式等
    assets = COURSE / "assets"
    if assets.is_dir():
        for src in assets.rglob("*"):
            if src.is_dir():
                continue
            dst = DIST / src.relative_to(assets)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main() -> int:
    evidence = collect_evidence()
    chapters, problems = [], []
    unit_total = drill_total = 0
    seconds = 0
    kinds = Counter()
    learning_tiers = Counter()
    missing_urls, bad_urls, seen_urls = [], [], Counter()
    within_unit = Counter()  # (unit_id, url) -> 次數，同單元重複才是真問題

    vmeta = load_json(DATA / "video-meta.json") or {}
    drill_ev = collect_drill_evidence()
    alt_lessons = collect_alt_lessons()
    multilang = [0]
    meta_hits, meta_miss = [0], []
    seconds_all = [0]  # 含多語言版本的總長度
    alt_count = [0]
    cat_counts, uncategorised = Counter(), []
    muscle_units: dict[str, set] = defaultdict(set)
    muscle_count: Counter = Counter()
    reference_catalog: dict[str, dict] = {}
    source_stance: list[dict] = []
    lesson_video_count = 0

    # 各章 JSON 可能一檔含多章（ch0-3），先把所有來源讀進來
    sources = {}
    for _, _, _, src in CHAPTERS:
        if src not in sources:
            sources[src] = load_json(DATA / f"{src}.json")
            blob = sources[src]
            if isinstance(blob, dict):
                reference_catalog.update(blob.get("reference_catalog") or {})
                source_stance.extend(blob.get("stance") or [])

    for code, title, ic, src in CHAPTERS:
        blob = sources.get(src)
        if not blob:
            problems.append(f"{code}: 找不到來源檔 data/{src}.json")
            continue

        # 一個檔可能是單章 {chapter, units} 或多章 {chapters: [...]}
        if blob.get("chapters"):
            node = next((c for c in blob["chapters"] if c.get("chapter") == code), None)
        elif blob.get("chapter") == code:
            node = blob
        else:
            node = None

        if not node:
            problems.append(f"{code}: 來源檔 data/{src}.json 中找不到這一章")
            continue

        units = node.get("units", [])
        want_units, want_drills = QUOTA[code]
        got_drills = sum(len(u.get("drills") or []) for u in units)

        if len(units) != want_units:
            problems.append(f"{code}: 單元數 {len(units)}，應為 {want_units}")
        if got_drills != want_drills:
            problems.append(f"{code}: 精選影片 {got_drills} 支，應為 {want_drills}")

        for u in units:
            u.setdefault("id", f"{code.lower()}-u{units.index(u) + 1}")
            ref_ids = u.get("reference_ids") or []
            u["references"] = [reference_catalog[r] for r in ref_ids if r in reference_catalog]
            ev_key = EVIDENCE_ALIAS.get(u["id"], u["id"])
            if ev_key in evidence:
                u["evidence"] = evidence[ev_key]

            # 單元層級的肌群：緊繃 + 無力兩側都算涉及
            u["facets"] = facets.extract(*(u.get("tight") or []), *(u.get("weak") or [])) if facets else []

            # 主課可以有多語言版本，第一支為預設
            if u.get("lesson"):
                lesson_video_count += 1
                u["lesson"].setdefault("lang", detect_lang(u["lesson"].get("title")))
                u["lessons"] = [u["lesson"], *alt_lessons.get(u["id"], [])]
                for les in u["lessons"][1:]:
                    les.setdefault("lang", detect_lang(les.get("title")))
                if len(u["lessons"]) > 1:
                    multilang[0] += 1

            # 替代語言版本要驗證與補 metadata，但不計入總時長（同一堂課不重複算）
            primary = {id(x) for x in [u.get("lesson"), *(u.get("drills") or [])] if x}
            vids = list(u.get("lessons") or [u.get("lesson")]) + list(u.get("drills") or [])
            for v in vids:
                if not v:
                    continue
                counts_toward_total = id(v) in primary
                url = v.get("url")
                if not url:
                    missing_urls.append(
                        f"{u['id']} / {v.get('name') or v.get('title') or '主課影片'}"
                    )
                    continue
                if not YT.match(url):
                    bad_urls.append(f"{u['id']}: {url}")
                seen_urls[url] += 1
                within_unit[(u["id"], url)] += 1

                # 時長與頻道以 YouTube 實際 metadata 為準，策展資料僅作後備
                info = vmeta.get(video_id(url) or "")
                if info and info.get("status") == "OK":
                    v["duration"] = fmt_clock(info["seconds"])
                    v["channel"] = info["channel"]
                    v["views"] = info["views"]
                    secs = info["seconds"]
                    meta_hits[0] += 1
                else:
                    secs = parse_duration(v.get("duration"))
                    meta_miss.append(url)
                seconds_all[0] += secs
                if counts_toward_total:
                    seconds += secs
                else:
                    alt_count[0] += 1

            for d in u.get("drills") or []:
                kinds[d.get("kind")] += 1
                learning_tiers[d.get("learning_tier")] += 1
                d["facets"] = facets.extract(d.get("target"), d.get("name")) if facets else []
                cid = categories.classify(d) if categories else None
                if cid:
                    d["cat"] = cid
                    cat_counts[cid] += 1
                    if cid in drill_ev:
                        d["catName"] = categories.NAMES[cid]
                else:
                    uncategorised.append(d.get("name"))

                for m in d["facets"]:
                    muscle_units[m].add(u["id"])
                    muscle_count[m] += 1
            for m in u["facets"]:
                muscle_units[m].add(u["id"])
                muscle_count[m] += 1

        unit_total += len(units)
        drill_total += got_drills
        chapters.append({"code": code, "title": title, "icon": ic, "units": units})

    dupes = {u: n for u, n in seen_urls.items() if n > 1}

    # concept-* 不屬於任何章節，抽出來當首頁的立場聲明
    stance = source_stance or [
        evidence[k] for k in ("concept-1", "concept-2", "concept-3") if k in evidence
    ]

    # 肌群索引：依部位分組，數量少的不進篩選器（避免上百個一次性標籤）
    muscle_index = [
        {
            "name": m,
            "group": facets.GROUP_OF.get(m, "其他") if facets else "其他",
            "count": muscle_count[m],
            "units": sorted(muscle_units[m]),
        }
        for m in sorted(muscle_count, key=lambda x: -muscle_count[x])
        if muscle_count[m] >= 2
    ]
    group_order = [*(facets.GROUPS if facets else []), "其他"]
    muscle_index.sort(key=lambda x: (group_order.index(x["group"]), -x["count"]))

    ui_keys = (
        "site", "hero", "ui", "kinds", "learningTiers", "grades", "languages",
        "nav", "stance", "landing", "footer",
        "discussions", "counter",
    )
    course = {
        "config": {k: CFG[k] for k in ui_keys if k in CFG},
        "stance": stance,
        "facets": muscle_index,
        "drillEvidence": drill_ev,
        "referenceCatalog": reference_catalog,
        "meta": {
            # 課程單元與第三方影片分開計數；書面單元不假裝成影片欄位。
            "units": unit_total,
            "lesson_units": unit_total,
            "drill_units": drill_total,
            "drill_tier_counts": {
                tier["id"]: learning_tiers[tier["id"]]
                for tier in CFG.get("learningTiers", [])
            },
            # 影片：有連結的主課 + 輔助影片 + 多語言替代版本
            "alt_lessons": alt_count[0],
            "video_slots": lesson_video_count + drill_total + alt_count[0],
            "video_unique": len(seen_urls),
            # 時長分兩個：跑完課程一輪 vs 把每個語言版本都看過
            "duration": fmt_duration(seconds),
            "duration_seconds": seconds,
            "duration_all": fmt_duration(seconds_all[0]),
            "duration_all_seconds": seconds_all[0],
            "problem_units": sum(
                1
                for c in chapters
                for u in c["units"]
                if u.get("type") == (CFG.get("ui", {}).get("problemType") or "posture")
            ),
            "evidence_checked": len(evidence),
        },
        "chapters": chapters,
    }

    sync_web()
    OUT.write_text(json.dumps(course, ensure_ascii=False, indent=1))

    try:
        out_label = OUT.relative_to(ROOT)
    except ValueError:
        out_label = OUT
    print(f"→ {out_label}  ({OUT.stat().st_size / 1024:.0f} KB)")
    print(f"   教學單元 {unit_total} · 精選影片 {drill_total}")
    print("   " + " / ".join(f"{k['label']} {kinds[k['id']]}" for k in CFG["kinds"]))
    print(
        "   "
        + " / ".join(
            f"{tier['label']} {learning_tiers[tier['id']]}"
            for tier in CFG.get("learningTiers", [])
        )
    )
    print(
        f"   影片 {lesson_video_count + drill_total + alt_count[0]} 個欄位"
        f"（含 {alt_count[0]} 支多語言版本）· 去重後 {len(seen_urls)} 支"
    )
    print(
        f"   課程時長 {fmt_duration(seconds)}"
        f" · 全部語言版本 {fmt_duration(seconds_all[0])}"
        f" · 實證查核 {len(evidence)} 題"
    )
    print(
        f"   YouTube metadata {meta_hits[0]}/{meta_hits[0] + len(meta_miss)} 命中"
        f" · 肌群索引 {len(muscle_index)} 項"
        f" · 動作類別 {len(cat_counts)} 類（文獻 {len(drill_ev)} 類）"
    )
    if uncategorised:
        print(
            f"   ⚠ 未分類動作 {len(uncategorised)}：{'、'.join(x for x in uncategorised[:5] if x)}"
        )

    if missing_urls:
        print(f"\n⚠ 缺影片連結 {len(missing_urls)} 支：")
        for m in missing_urls[:15]:
            print(f"   · {m}")
        if len(missing_urls) > 15:
            print(f"   … 另有 {len(missing_urls) - 15} 支")
    if bad_urls:
        print(f"\n✗ URL 格式不正確 {len(bad_urls)} 支：")
        for b in bad_urls[:10]:
            print(f"   · {b}")
    same_unit_dupes = {k: n for k, n in within_unit.items() if n > 1}
    if same_unit_dupes:
        print(f"\n✗ 同一單元內重複的影片 {len(same_unit_dupes)} 筆：")
        for (uid, url), n in same_unit_dupes.items():
            print(f"   · {uid} 用了 {n} 次 {url}")
        problems.append(f"同單元重複影片 {len(same_unit_dupes)} 筆")
    if dupes:
        print(f"\n· 跨單元共用的影片 {len(dupes)} 支（規格允許的少量重疊）")
    if problems:
        print(f"\n✗ 配額不符 {len(problems)} 項：")
        for p in problems:
            print(f"   · {p}")
        return 1

    print("\n✓ 配額全數符合\n")

    # 結構化資料的數字必須跟著課程走，所以綁在建置流程裡
    import seo

    return seo.main()


if __name__ == "__main__":
    sys.exit(main())
