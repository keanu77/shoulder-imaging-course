#!/usr/bin/env python3
"""離線品質稽核：設定檔、配額、影片長度與中繼資料、實證深度。

刻意不打任何網路——連結與 PMID 是否真實存在由 verify_links.py / verify_refs.py 負責。
這支腳本只看 course/ 底下的資料與 src/web 的產物，因此同樣的輸入永遠得到同樣的輸出，
可以放進 CI 或交給 agent 自我檢查，不會因為 API 抽風而閃爍。

門檻全部從 course.config.json 的 `audit` 區塊讀，沒寫就用 DEFAULTS，
框架本身不預設任何主題。

用法：
    python3 audit.py            # 人看的報告；有錯誤回傳 1
    python3 audit.py --strict   # 警告也視為錯誤
    python3 audit.py --json     # 機器可讀，給 agent 用
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSE = Path(os.environ.get("COURSE") or ROOT / "course").resolve()
DATA = COURSE / "data"
WEB = ROOT / "src" / "web"
DIST = Path(os.environ.get("DIST") or ROOT / "dist").resolve()
SCHEMA = Path(__file__).parent / "course.schema.json"

# 沒寫 audit 區塊時的通則門檻。單位：秒數用 "分:秒" 字串，比例用 0–1。
DEFAULTS = {
    "duration": {
        "lesson": {"min": "3:00", "max": "30:00"},
        "drill": {"min": "0:20", "max": "15:00"},
    },
    "driftSeconds": 45,
    "minViews": 1000,
    "metaCoverage": 0.95,
    "drillsPerUnit": {"min": 1, "max": 30},
    "maxSharedVideos": 60,
    "requireAssessment": [],
    "minAssessmentChars": 40,
    "minCitations": 1,
    "allowMissingUrls": 0,
}

YT = re.compile(
    r"^https://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}(?:&\S*)?$|^https://youtu\.be/[\w-]{11}"
)
SECTIONS = ("設定檔", "結構與配額", "影片", "內容深度")


# ── 小工具 ────────────────────────────────────────────────────────────────


def clock(total: int) -> str:
    h, rem = divmod(int(total), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def parse_clock(s: str | int | None) -> int:
    """'12:34' / '1:02:33' / 750 -> 秒。無法解析回 -1。"""
    if isinstance(s, int):
        return s
    if not s:
        return -1
    parts = str(s).strip().split(":")
    if not all(p.isdigit() for p in parts):
        return -1
    secs = 0
    for p in parts:
        secs = secs * 60 + int(p)
    return secs


def video_id(url: str | None) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = (
            deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
        )
    return out


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        return e


class Report:
    """收集稽核結果。錯誤 = 一定要修；警告 = 值得看一眼。"""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, list[str]]] = []
        self.stats: dict[str, object] = {}

    def _add(self, level: str, section: str, msg: str, detail: list[str] | None = None) -> None:
        self.rows.append((section, level, msg, detail or []))

    def err(self, section, msg, detail=None):
        self._add("error", section, msg, detail)

    def warn(self, section, msg, detail=None):
        self._add("warn", section, msg, detail)

    def ok(self, section, msg, detail=None):
        self._add("ok", section, msg, detail)

    def count(self, level: str) -> int:
        return sum(1 for _, lv, _, _ in self.rows if lv == level)

    def emit(self) -> None:
        mark = {"ok": "✓", "warn": "⚠", "error": "✗"}
        for section in SECTIONS:
            rows = [r for r in self.rows if r[0] == section]
            if not rows:
                continue
            print(f"\n{section}")
            for _, level, msg, detail in rows:
                print(f"  {mark[level]} {msg}")
                for d in detail[:8]:
                    print(f"      · {d[:118]}{'…' if len(d) > 118 else ''}")
                if len(detail) > 8:
                    print(f"      … 另有 {len(detail) - 8} 筆")

    def as_json(self) -> dict:
        return {
            "errors": [
                {"section": s, "message": m, "detail": d}
                for s, lv, m, d in self.rows
                if lv == "error"
            ],
            "warnings": [
                {"section": s, "message": m, "detail": d}
                for s, lv, m, d in self.rows
                if lv == "warn"
            ],
            "stats": self.stats,
        }


# ── 迷你 JSON Schema 驗證器（只支援本專案 schema 用到的關鍵字）────────────


def validate(node, schema: dict, path: str, defs: dict, out: list[str]) -> None:
    if "$ref" in schema:
        schema = defs.get(schema["$ref"].rsplit("/", 1)[-1], {})

    types = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }
    t = schema.get("type")
    if t and not isinstance(node, types[t]):
        out.append(f"{path} 應為 {t}，實際是 {type(node).__name__}")
        return
    if t == "integer" and isinstance(node, bool):
        out.append(f"{path} 應為 integer")
        return

    if (enum := schema.get("enum")) and node not in enum:
        out.append(f"{path} 只能是 {'/'.join(map(str, enum))}，實際是 {node!r}")
    if (pat := schema.get("pattern")) and isinstance(node, str) and not re.match(pat, node):
        out.append(f"{path} 不符合格式 {pat}：{node!r}")
    if (lo := schema.get("minimum")) is not None and isinstance(node, (int, float)) and node < lo:
        out.append(f"{path} 不得小於 {lo}")
    if isinstance(node, list):
        if len(node) < schema.get("minItems", 0):
            out.append(f"{path} 至少要有 {schema['minItems']} 項")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in node}) != len(
            node
        ):
            out.append(f"{path} 有重複項目")
        if item_schema := schema.get("items"):
            for i, item in enumerate(node):
                validate(item, item_schema, f"{path}[{i}]", defs, out)
    if isinstance(node, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in node:
                out.append(f"{path} 缺少必要欄位 {key}")
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props and not key.startswith("$"):
                    out.append(f"{path}.{key} 不是已知欄位（拼錯了？）")
        for key, sub in props.items():
            if key in node:
                validate(node[key], sub, f"{path}.{key}", defs, out)
        if isinstance(extra := schema.get("additionalProperties"), dict):
            for key, val in node.items():
                if key not in props:
                    validate(val, extra, f"{path}.{key}", defs, out)


# ── 設定檔 ────────────────────────────────────────────────────────────────


def sprite_icons() -> set[str]:
    m = re.search(r"ICON_NAMES = (\[.*?\]);", (WEB / "js" / "icons.js").read_text(), re.S)
    return set(json.loads(m.group(1))) if m else set()


def css_tones() -> set[str]:
    """tone 是設計語彙的一部分，定義在 tokens.css，不看其他主題性的樣式檔。"""
    return set(re.findall(r"\.Label--([a-z-]+)", (WEB / "css" / "tokens.css").read_text()))


def audit_versioned_assets(rep: Report) -> None:
    """所有未雜湊資產都要帶同一個內容指紋，不能只依賴 CDN cache header。"""
    sec = "設定檔"
    html_path = DIST / "index.html"
    if not html_path.exists():
        rep.warn(sec, "dist/index.html 尚未建置，略過前端資產版本稽核")
        return

    html = html_path.read_text()
    html_assets = re.findall(
        r'\b(?:href|src)=["\']((?:css|js)/[^"\']+\.(?:css|js)(?:\?[^"\']*)?)["\']',
        html,
    )
    versions: set[str] = set()
    missing = []
    for asset in html_assets:
        match = re.search(r"\?v=([0-9a-f]{12})$", asset)
        if match:
            versions.add(match.group(1))
        else:
            missing.append(f"index.html：{asset}")

    module_refs = 0
    module_targets: dict[Path, set[Path]] = defaultdict(set)
    for path in sorted((DIST / "js").glob("*.js")):
        source = path.read_text()
        static_assets = re.findall(
            r'(?:\bfrom\s+|\bimport\s*)["\'](\./[^"\']+\.js(?:\?[^"\']*)?)["\']',
            source,
        )
        dynamic_assets = re.findall(
            r'\bimport\s*\(\s*["\'](\./[^"\']+\.js(?:\?[^"\']*)?)["\']\s*\)',
            source,
        )
        dynamic_calls = len(re.findall(r"\bimport\s*\(", source))
        if dynamic_calls != len(dynamic_assets):
            missing.append(f"{path.name}：含無法靜態加入版本的 dynamic import")

        for asset in [*static_assets, *dynamic_assets]:
            module_refs += 1
            match = re.search(r"\?v=([0-9a-f]{12})$", asset)
            if match:
                versions.add(match.group(1))
            else:
                missing.append(f"{path.name}：{asset}")
            target = (path.parent / asset.split("?", 1)[0]).resolve()
            module_targets[path.resolve()].add(target)
            if target.parent != (DIST / "js").resolve() or not target.is_file():
                missing.append(f"{path.name}：import target 不存在 {asset}")

    app_source = (DIST / "js" / "app.js").read_text()
    course_match = re.search(r'fetch\(["\']course\.json\?v=([0-9a-f]{12})["\']\)', app_source)
    if course_match:
        versions.add(course_match.group(1))
    else:
        missing.append("app.js：course.json fetch 沒有內容指紋")

    reachable = set()
    pending = [(DIST / "js" / "app.js").resolve()]
    while pending:
        path = pending.pop()
        if path in reachable:
            continue
        reachable.add(path)
        pending.extend(module_targets.get(path, set()) - reachable)
    js_files = {path.resolve() for path in (DIST / "js").glob("*.js")}
    if orphaned := sorted(path.name for path in js_files - reachable):
        missing.extend(f"ES module graph：app.js 無法到達 {name}" for name in orphaned)

    if missing:
        rep.err(sec, f"{len(missing)} 個前端請求沒有內容指紋", missing)
    elif len(versions) != 1:
        rep.err(sec, f"前端資產用了 {len(versions)} 個不同版本：{'、'.join(sorted(versions))}")
    else:
        version = next(iter(versions))
        digest = hashlib.sha256()
        inputs = sorted(
            [*DIST.glob("css/*.css"), *DIST.glob("js/*.js"), DIST / "course.json"],
            key=lambda path: path.relative_to(DIST).as_posix(),
        )
        for path in inputs:
            content = path.read_bytes()
            if path.suffix == ".js":
                content = content.replace(f"?v={version}".encode(), b"")
            digest.update(path.relative_to(DIST).as_posix().encode())
            digest.update(b"\0")
            digest.update(content)
            digest.update(b"\0")
        expected = digest.hexdigest()[:12]
        if version != expected:
            rep.err(sec, f"前端資產版本 {version} 與內容 digest {expected} 不符")
            return
        rep.ok(
            sec,
            f"前端資產版本 {version} · HTML {len(html_assets)} 處 · "
            f"ES modules {module_refs} 處 · course.json 1 處",
        )


def audit_config(cfg: dict, rep: Report) -> None:
    sec = "設定檔"
    # 設定檔可能本身就壞掉——稽核要能報出來，不能自己爆掉，所以一律用 .get()
    chapters = [c for c in cfg.get("chapters") or [] if isinstance(c, dict)]

    schema = load_json(SCHEMA)
    if isinstance(schema, dict):
        errs: list[str] = []
        validate(cfg, schema, "config", schema.get("$defs", {}), errs)
        if errs:
            rep.err(sec, f"course.config.json 不符合 schema（{len(errs)} 項）", errs)
        else:
            rep.ok(
                sec,
                f"schema 通過 · {len(chapters)} 章 · {len(cfg.get('kinds', []))} 種項目類型",
            )
    else:
        rep.warn(sec, f"找不到 {SCHEMA.name}，略過 schema 驗證")

    # 章節碼唯一、來源檔存在
    codes = [c.get("code") for c in chapters]
    if dupe := [c for c, n in Counter(codes).items() if n > 1]:
        rep.err(sec, f"章節碼重複：{'、'.join(dupe)}")
    if missing := sorted(
        {
            c["source"]
            for c in chapters
            if c.get("source") and not (DATA / f"{c['source']}.json").exists()
        }
    ):
        rep.err(sec, f"找不到來源檔 {len(missing)} 個", [f"data/{s}.json" for s in missing])

    # nav 分組必須不多不少剛好涵蓋所有章節，否則側欄會漏掉一整章
    nav_codes = [code for grp in cfg.get("nav", []) for code in grp.get("chapters", [])]
    if cfg.get("nav"):
        if orphan := [c for c in codes if c not in nav_codes]:
            rep.err(sec, f"nav 沒有涵蓋 {'、'.join(orphan)}（側欄會看不到）")
        if ghost := [c for c in nav_codes if c not in codes]:
            rep.err(sec, f"nav 指向不存在的章節：{'、'.join(ghost)}")
        if again := [c for c, n in Counter(nav_codes).items() if n > 1]:
            rep.err(sec, f"nav 重複列出：{'、'.join(again)}")

    # 圖示必須已經打包進 sprite，否則線上是空白方塊
    icons = sprite_icons()
    used = {
        f"site.brandIcon={cfg.get('site', {}).get('brandIcon')}": cfg.get("site", {}).get(
            "brandIcon"
        ),
        **{f"{c.get('code')}={c.get('icon')}": c.get("icon") for c in chapters},
        **{
            f"stats[{i}]={s.get('icon')}": s.get("icon")
            for i, s in enumerate(cfg.get("ui", {}).get("stats", []))
        },
        **{
            f"landing.steps[{i}]={s.get('icon')}": s.get("icon")
            for i, s in enumerate(cfg.get("landing", {}).get("steps", []))
        },
    }
    if absent := sorted(label for label, name in used.items() if name and name not in icons):
        rep.err(
            sec,
            f"{len(absent)} 個圖示不在 sprite 內（把名稱加進 build_icons.py 的 ICONS 再跑 make icons）",
            absent,
        )
    else:
        rep.ok(
            sec,
            f"圖示 {len({n for n in used.values() if n})} 個全部已打包（sprite 共 {len(icons)} 個）",
        )

    # tone 必須有對應的 .Label--<tone> 樣式，否則標籤會變成沒有顏色的灰底
    tones = css_tones()
    bad_tone = [
        f"{group}[{o['id']}].tone={o['tone']}"
        for group in ("kinds", "grades")
        for o in cfg.get(group, [])
        if o.get("tone") and o["tone"] not in tones
    ]
    if bad_tone:
        rep.err(
            sec,
            f"{len(bad_tone)} 個 tone 沒有對應樣式（可用：{'、'.join(sorted(tones))}）",
            bad_tone,
        )

    # id 唯一
    for group in ("kinds", "grades"):
        ids = [o.get("id") for o in cfg.get(group, []) if isinstance(o, dict)]
        if d := [i for i, n in Counter(ids).items() if n > 1]:
            rep.err(sec, f"{group} id 重複：{'、'.join(d)}")

    # 詞彙模組可 import 且介面齊全
    sys.path.insert(0, str(COURSE))
    for key, attrs in (
        ("facets", ("extract", "GROUPS", "GROUP_OF")),
        ("categories", ("classify", "NAMES")),
    ):
        name = (cfg.get("taxonomy") or {}).get(key)
        if not name:
            continue
        try:
            mod = importlib.import_module(name)
        except Exception as e:  # 任何 import 失敗都要報出來，不能讓稽核自己爆掉
            rep.err(sec, f"taxonomy.{key} 模組 {name} 匯入失敗：{type(e).__name__}: {e}")
            continue
        if lack := [a for a in attrs if not hasattr(mod, a)]:
            rep.err(sec, f"taxonomy.{key} 模組 {name} 缺少 {'、'.join(lack)}")

    # 統計欄位要對得上 build 產出的 meta（沒建置過就跳過）
    built = load_json(DIST / "course.json")
    if isinstance(built, dict):
        fields = set(built.get("meta", {}))
        if unknown := [
            str(s.get("field"))
            for s in cfg.get("ui", {}).get("stats", [])
            if s.get("field") not in fields
        ]:
            rep.err(
                sec,
                f"ui.stats 參照不存在的統計欄位：{'、'.join(unknown)}",
                [f"可用：{'、'.join(sorted(fields))}"],
            )

    # 文案佔位符：只有這幾個會被替換，寫錯就會原樣印在頁面上
    known = {"units", "problems", "videos", "evidence"}
    stray = []
    for path, text in (
        ("hero.lede", cfg.get("hero", {}).get("lede")),
        ("landing.ctaLede", cfg.get("landing", {}).get("ctaLede")),
        ("llms.summary", cfg.get("llms", {}).get("summary")),
        ("llms.stanceIntro", cfg.get("llms", {}).get("stanceIntro")),
    ):
        for token in re.findall(r"\{(\w+)\}", text or ""):
            if token not in known:
                stray.append(f"{path} 的 {{{token}}}")
    if stray:
        rep.err(sec, f"{len(stray)} 個佔位符不會被替換（可用：{'、'.join(sorted(known))}）", stray)


# ── 資料走訪 ──────────────────────────────────────────────────────────────


def walk(cfg: dict, rep: Report) -> list[dict]:
    """把各章來源檔攤平成 [{code, unit}]，順便檢查 JSON 是否壞掉。"""
    chapters = [c for c in cfg.get("chapters") or [] if isinstance(c, dict) and c.get("source")]
    sources: dict[str, object] = {}
    for c in chapters:
        if c["source"] not in sources:
            sources[c["source"]] = load_json(DATA / f"{c['source']}.json")

    for name, blob in sources.items():
        if isinstance(blob, json.JSONDecodeError):
            rep.err("設定檔", f"data/{name}.json 不是合法 JSON：第 {blob.lineno} 行 {blob.msg}")

    out = []
    for c in chapters:
        blob = sources.get(c["source"])
        if not isinstance(blob, dict):
            continue
        if blob.get("chapters"):
            node = next((x for x in blob["chapters"] if x.get("chapter") == c["code"]), None)
        else:
            node = blob if blob.get("chapter") == c["code"] else None
        for u in (node or {}).get("units", []):
            if isinstance(u, dict):
                out.append({"code": c.get("code"), "unit": u})
    return out


def audit_structure(cfg: dict, units: list[dict], opts: dict, rep: Report) -> None:
    sec = "結構與配額"
    quota = {
        c["code"]: (c.get("units", 0), c.get("drills", 0))
        for c in cfg.get("chapters") or []
        if isinstance(c, dict) and c.get("code")
    }
    kind_ids = {k.get("id") for k in cfg.get("kinds", []) if isinstance(k, dict)}
    tier_ids = {tier.get("id") for tier in cfg.get("learningTiers", []) if isinstance(tier, dict)}
    unit_types = set(cfg.get("ui", {}).get("unitTypes", {}))

    per_chapter = defaultdict(list)
    for row in units:
        per_chapter[row["code"]].append(row["unit"])

    off = []
    for code, (want_u, want_d) in quota.items():
        got_u = len(per_chapter[code])
        got_d = sum(len(u.get("drills") or []) for u in per_chapter[code])
        if got_u != want_u:
            off.append(f"{code} 單元 {got_u}，設定為 {want_u}")
        if got_d != want_d:
            off.append(f"{code} 項目 {got_d}，設定為 {want_d}")
    total_u = len(units)
    total_d = sum(len(r["unit"].get("drills") or []) for r in units)
    if off:
        rep.err(sec, f"配額不符 {len(off)} 項", off)
    else:
        rep.ok(
            sec,
            f"{len(quota)} 章 · 主課 {total_u} · 項目 {total_d} · 合計 {total_u + total_d}，配額全數符合",
        )

    # id 唯一（進度追蹤與深連結都靠它）
    ids = [r["unit"].get("id") for r in units]
    if d := [i for i, n in Counter(ids).items() if n > 1]:
        rep.err(sec, f"單元 id 重複 {len(d)} 個", d)
    if blank := [
        f"{r['code']} 第 {i + 1} 個單元" for i, r in enumerate(units) if not r["unit"].get("id")
    ]:
        rep.err(sec, f"{len(blank)} 個單元沒有 id", blank)

    # 未定義的 kind / type 會讓標籤變成生的 id
    bad_kind = [
        f"{r['unit'].get('id')} / {d.get('name')} kind={d.get('kind')!r}"
        for r in units
        for d in r["unit"].get("drills") or []
        if d.get("kind") not in kind_ids
    ]
    if bad_kind:
        rep.err(
            sec,
            f"{len(bad_kind)} 個項目的 kind 不在 config.kinds（{'、'.join(sorted(kind_ids))}）",
            bad_kind,
        )
    bad_tier = [
        f"{r['unit'].get('id')} / {d.get('name')} learning_tier={d.get('learning_tier')!r}"
        for r in units
        for d in r["unit"].get("drills") or []
        if d.get("learning_tier") not in tier_ids
    ]
    if bad_tier:
        rep.err(
            sec,
            f"{len(bad_tier)} 個項目的 learning_tier 不在 config.learningTiers"
            f"（{'、'.join(sorted(tier_ids))}）",
            bad_tier,
        )
    bad_type = [
        f"{r['unit'].get('id')} type={r['unit'].get('type')!r}"
        for r in units
        if r["unit"].get("type") and r["unit"]["type"] not in unit_types
    ]
    if bad_type:
        rep.err(sec, f"{len(bad_type)} 個單元的 type 不在 ui.unitTypes", bad_type)

    # 項目數失衡：一個單元 2 支、隔壁 30 支，通常是策展 agent 偷懶或超載
    lo, hi = opts["drillsPerUnit"]["min"], opts["drillsPerUnit"]["max"]
    skew = [
        f"{r['unit'].get('id')} {len(r['unit'].get('drills') or [])} 支"
        for r in units
        if r["unit"].get("drills") and not (lo <= len(r["unit"]["drills"]) <= hi)
    ]
    if skew:
        rep.warn(sec, f"{len(skew)} 個單元的項目數超出 {lo}–{hi} 支", skew)

    # 同一單元裡的項目名稱重複
    same = [
        f"{r['unit'].get('id')} / {name}"
        for r in units
        for name, n in Counter(d.get("name") for d in r["unit"].get("drills") or []).items()
        if n > 1
    ]
    if same:
        rep.err(sec, f"{len(same)} 個項目在同一單元內重名", same)

    # evidenceAlias 必須指向真的存在的單元
    if ghost := [k for k in cfg.get("evidenceAlias", {}) if k not in set(ids)]:
        rep.err(sec, f"evidenceAlias 指向不存在的單元：{'、'.join(ghost)}")

    rep.stats.update(chapters=len(quota), lesson_units=total_u, drill_units=total_d)


# ── 影片 ──────────────────────────────────────────────────────────────────


def videos_of(units: list[dict]) -> list[tuple[str, str, str, dict]]:
    """yield (unit_id, 角色, 標籤, 影片 dict)。角色是 lesson / drill。"""
    out = []
    for r in units:
        u = r["unit"]
        uid = u.get("id") or "?"
        if u.get("lesson"):
            out.append((uid, "lesson", u["lesson"].get("title") or "主課", u["lesson"]))
        for d in u.get("drills") or []:
            out.append((uid, "drill", d.get("name") or "?", d))
    return out


def audit_videos(cfg: dict, units: list[dict], opts: dict, rep: Report) -> None:
    sec = "影片"
    vmeta = load_json(DATA / "video-meta.json")
    if not isinstance(vmeta, dict):
        vmeta = {}
        rep.warn(sec, "找不到 data/video-meta.json，長度與觀看數無從稽核（跑 make meta 產生）")

    nodes = videos_of(units)
    for path in sorted(DATA.glob("alt-lessons-*.json")):
        blob = load_json(path)
        for les in (blob or {}).get("lessons", []) if isinstance(blob, dict) else []:
            if isinstance(les, dict):
                nodes.append((les.get("unit", "?"), "lesson", f"{les.get('lang', '')} 版", les))

    explained, unexplained, malformed = [], [], []
    seen: Counter = Counter()
    within: Counter = Counter()
    hits = 0
    dead, drift, date_drift, missing_meta_dates, short, long_, unpopular = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    seconds = Counter()

    bounds = {
        role: (
            parse_clock(opts["duration"][role]["min"]),
            parse_clock(opts["duration"][role]["max"]),
        )
        for role in ("lesson", "drill")
    }

    for uid, role, label, v in nodes:
        url = v.get("url")
        if not url:
            # 找不到合格影片而誠實留空是允許的，但一定要在 note 說明為什麼
            note = (v.get("note") or "").strip()
            (explained if note else unexplained).append(f"{uid} / {label}：{note or '沒有 note'}")
            continue
        if not YT.match(url):
            malformed.append(f"{uid} / {label}：{url}")
            continue
        seen[url] += 1
        within[(uid, url)] += 1

        info = vmeta.get(video_id(url) or "")
        if not info:
            continue
        if info.get("status") != "OK":
            dead.append(f"{uid} / {label}：{info.get('status')} {url}")
            continue
        hits += 1
        secs = int(info.get("seconds") or 0)
        seconds[role] += secs

        lo, hi = bounds[role]
        if secs < lo:
            short.append(f"{uid} / {label} {clock(secs)}（下限 {clock(lo)}）")
        elif secs > hi:
            long_.append(f"{uid} / {label} {clock(secs)}（上限 {clock(hi)}）")

        claimed = parse_clock(v.get("duration"))
        if claimed >= 0 and abs(claimed - secs) > opts["driftSeconds"]:
            drift.append(f"{uid} / {label} 寫 {v.get('duration')}，實際 {clock(secs)}")

        if (views := info.get("views")) is not None and views < opts["minViews"]:
            unpopular.append(f"{uid} / {label} {views:,} 次觀看")

        if not info.get("upload_date"):
            missing_meta_dates.append(f"{uid} / {label}：中繼資料缺少 YouTube 上架日期")
        elif v.get("upload_date") != info["upload_date"]:
            date_drift.append(
                f"{uid} / {label} 寫 {v.get('upload_date')!r}，YouTube 為 {info['upload_date']}"
            )

    slots = len(nodes)
    filled = slots - len(explained) - len(unexplained)
    coverage = hits / filled if filled else 0
    line = (
        f"{slots} 個影片欄位 · 去重 {len(seen)} 支 · 中繼資料命中 {hits}/{filled}（{coverage:.1%}）"
    )
    if filled and coverage < opts["metaCoverage"]:
        rep.err(sec, f"{line}，低於門檻 {opts['metaCoverage']:.0%}（跑 make meta 補齊）")
    else:
        rep.ok(sec, line)

    if unexplained:
        rep.err(sec, f"{len(unexplained)} 個欄位沒有連結也沒有 note 說明原因", unexplained)
    if explained:
        level = rep.warn if len(explained) <= opts["allowMissingUrls"] else rep.err
        level(
            sec,
            f"{len(explained)} 個欄位誠實留空（容許 {opts['allowMissingUrls']} 個）",
            explained,
        )
    if malformed:
        rep.err(sec, f"{len(malformed)} 個連結不是合法的 YouTube watch 網址", malformed)
    if dead:
        rep.err(sec, f"{len(dead)} 支影片在中繼資料裡是不可用狀態", dead)
    if dupe := [f"{uid} 重複用了 {url}" for (uid, url), n in within.items() if n > 1]:
        rep.err(sec, f"{len(dupe)} 支影片在同一單元內重複", dupe)

    shared = sum(1 for n in seen.values() if n > 1)
    if shared > opts["maxSharedVideos"]:
        rep.warn(
            sec, f"跨單元共用 {shared} 支影片，超過門檻 {opts['maxSharedVideos']}（內容重疊過多？）"
        )

    if drift:
        rep.warn(sec, f"{len(drift)} 支影片的宣稱長度與實際差超過 {opts['driftSeconds']} 秒", drift)
    if date_drift:
        rep.err(sec, f"{len(date_drift)} 支影片的 upload_date 與 YouTube metadata 不符", date_drift)
    if missing_meta_dates:
        rep.err(
            sec,
            f"{len(missing_meta_dates)} 支影片的 YouTube metadata 缺少 upload_date（跑 make meta 補齊）",
            missing_meta_dates,
        )
    if short or long_:
        rep.warn(
            sec,
            f"{len(short) + len(long_)} 支影片長度超出設定區間"
            f"（主課 {opts['duration']['lesson']['min']}–{opts['duration']['lesson']['max']}、"
            f"項目 {opts['duration']['drill']['min']}–{opts['duration']['drill']['max']}）",
            short + long_,
        )
    if unpopular:
        rep.warn(
            sec,
            f"{len(unpopular)} 支影片觀看數低於 {opts['minViews']:,}（品質門檻，人工看一眼）",
            unpopular,
        )

    total = sum(seconds.values())
    rep.ok(
        sec,
        f"所有欄位合計 {clock(total)}"
        f"（主課 {clock(seconds['lesson'])} + 項目 {clock(seconds['drill'])}，含多語言版本）",
    )
    rep.stats.update(
        video_slots=slots,
        video_unique=len(seen),
        meta_coverage=round(coverage, 4),
        duration_seconds=total,
    )


# ── 內容深度 ──────────────────────────────────────────────────────────────


def audit_depth(cfg: dict, units: list[dict], opts: dict, rep: Report) -> None:
    sec = "內容深度"
    grades = {g.get("id") for g in cfg.get("grades", []) if isinstance(g, dict)}
    need = set(opts["requireAssessment"])
    min_chars = opts["minAssessmentChars"]

    thin = [
        f"{r['unit'].get('id')} / {r['unit'].get('name')}"
        f"（{len(r['unit'].get('assessment') or '')} 字）"
        for r in units
        if r["unit"].get("type") in need and len(r["unit"].get("assessment") or "") < min_chars
    ]
    if need:
        if thin:
            rep.err(sec, f"{len(thin)} 個單元缺少可操作的 assessment（至少 {min_chars} 字）", thin)
        else:
            rep.ok(
                sec,
                f"{sum(1 for r in units if r['unit'].get('type') in need)} 個 {'/'.join(sorted(need))} 單元都有 assessment",
            )

    if nowhy := [
        f"{r['unit'].get('id')}"
        for r in units
        if r["unit"].get("lesson") and not r["unit"]["lesson"].get("why")
    ]:
        rep.warn(sec, f"{len(nowhy)} 堂主課沒有寫選片理由 why", nowhy)

    # 單元層級實證
    ev_units, bad_grade = set(), []
    for path in sorted(DATA.glob("oe-*.json")):
        blob = load_json(path)
        for cond in (blob or {}).get("conditions", []) if isinstance(blob, dict) else []:
            if not isinstance(cond, dict) or not cond.get("unit"):
                continue
            ev_units.add(cond["unit"])
            if grades and cond.get("evidence_grade") not in grades:
                bad_grade.append(
                    f"{path.name} · {cond['unit']} grade={cond.get('evidence_grade')!r}"
                )

    alias = cfg.get("evidenceAlias", {})
    targeted = {
        alias.get(r["unit"].get("id"), r["unit"].get("id"))
        for r in units
        if r["unit"].get("type") in need
    }
    # minCitations=0 表示主題以 unit.reference_ids 由專用內容閘門查核，
    # 不要求舊版 oe-*.json 的逐題證據檔。
    if need and targeted and opts["minCitations"] > 0:
        covered = len(targeted & ev_units)
        gap = sorted(targeted - ev_units)
        msg = f"實證查核 {covered}/{len(targeted)} 個主題（另有 {len(ev_units - targeted)} 個非章節主題）"
        rep.warn(sec, msg + "，未查核：" + "、".join(gap), []) if gap else rep.ok(sec, msg)

    # 類別層級文獻
    cats, thin_cats, bad_pmid = {}, [], []
    for path in sorted(DATA.glob("drill-evidence-*.json")):
        blob = load_json(path)
        for cat in (blob or {}).get("categories", []) if isinstance(blob, dict) else []:
            if not isinstance(cat, dict) or not cat.get("id"):
                continue
            cats[cat["id"]] = cat
            if grades and cat.get("evidence_grade") not in grades:
                bad_grade.append(f"{path.name} · {cat['id']} grade={cat.get('evidence_grade')!r}")
            cites = cat.get("citations") or []
            if len(cites) < opts["minCitations"]:
                thin_cats.append(f"{cat['id']}（{len(cites)} 篇）")
            for c in cites:
                pmid = str(c.get("pmid") or "").strip()
                if not (pmid.isdigit() and 6 <= len(pmid) <= 9):
                    bad_pmid.append(
                        f"{cat['id']} · pmid={c.get('pmid')!r} · {(c.get('title') or '')[:40]}"
                    )

    if bad_grade:
        rep.err(
            sec,
            f"{len(bad_grade)} 筆 evidence_grade 不在 config.grades（{'、'.join(sorted(grades))}）",
            bad_grade,
        )
    if bad_pmid:
        rep.err(
            sec, f"{len(bad_pmid)} 筆 PMID 格式不合法（跑 make verify 打真實 API 才算數）", bad_pmid
        )
    if thin_cats:
        rep.warn(sec, f"{len(thin_cats)} 個類別的文獻少於 {opts['minCitations']} 篇", thin_cats)
    if cats:
        n_cites = sum(len(c.get("citations") or []) for c in cats.values())
        rep.ok(sec, f"{len(cats)} 個類別 · {n_cites} 篇引用 · {len(ev_units)} 個單元層級查核")

    rep.stats.update(evidence_units=len(ev_units), categories=len(cats))


# ── 進入點 ────────────────────────────────────────────────────────────────


def main() -> int:
    strict = "--strict" in sys.argv
    as_json = "--json" in sys.argv

    cfg = load_json(COURSE / "course.config.json")
    if not isinstance(cfg, dict):
        print(f"✗ 讀不到 {COURSE / 'course.config.json'}：{cfg}", file=sys.stderr)
        return 1
    opts = deep_merge(DEFAULTS, cfg.get("audit") or {})

    rep = Report()
    audit_config(cfg, rep)
    audit_versioned_assets(rep)
    units = walk(cfg, rep)
    audit_structure(cfg, units, opts, rep)
    audit_videos(cfg, units, opts, rep)
    audit_depth(cfg, units, opts, rep)

    errors, warnings = rep.count("error"), rep.count("warn")

    if as_json:
        print(json.dumps({**rep.as_json(), "ok": errors == 0}, ensure_ascii=False, indent=1))
    else:
        print(f"稽核 {COURSE.name}/（離線，不打網路；連結存活與 PMID 真偽請跑 make verify）")
        rep.emit()
        verdict = (
            f"\n✗ {errors} 個錯誤" if errors else ("\n⚠ 沒有錯誤" if warnings else "\n✓ 全部通過")
        )
        print(f"{verdict}、{warnings} 個警告\n" if warnings else f"{verdict}\n")

    return 1 if errors or (strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
