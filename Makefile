PY := uv run python
COURSE ?= course
DIST ?= dist
PORT ?= 8899
PROJECT ?= $(shell $(PY) -c "import json;print(json.load(open('$(COURSE)/course.config.json'))['site']['project'])")

export COURSE
export DIST

.DEFAULT_GOAL := help

help: ## 列出可用指令
	@grep -E '^[a-z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

build: ## 合併資料 → public/course.json，含配額驗證與 SEO 產出
	$(PY) src/build/build.py

icons: ## 重新下載 Lucide 圖示並打包成內嵌 sprite
	$(PY) src/build/build_icons.py

og: ## 用 headless Chrome 重新產生社群預覽圖
	@"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
		--headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
		--window-size=1200,630 --screenshot="$(PWD)/src/web/og.png" "$(PWD)/src/web/og.html"
	@sips -z 630 1200 src/web/og.png >/dev/null
	@cp src/web/og.png $(DIST)/og.png
	@echo "→ src/web/og.png + $(DIST)/og.png"

meta: ## 用 yt-dlp 補齊 video-meta.json（長度、觀看數、頻道、上架日期）
	$(PY) src/build/fetch_meta.py

counter: ## 建立瀏覽次數用的 D1 資料庫並寫出 wrangler 綁定（冪等，可重跑）
	$(PY) src/build/setup_counter.py

audit: ## 離線稽核設定檔、配額、影片長度與實證深度（確定性，不打網路）
	$(PY) src/build/audit.py
	$(PY) src/build/audit_medical.py

verify: ## 重驗所有影片連結與 PubMed 引用（打真實 API，會跑一陣子）
	$(PY) src/build/verify_links.py
	$(PY) src/build/verify_refs.py

serve: ## 本機預覽
	@echo "→ http://localhost:$(PORT)"
	@$(PY) -m http.server $(PORT) --directory $(DIST)

deploy: ## 正式站採 Cloudflare Git integration；避免誤建不可切換的 Direct Upload 專案
	@echo "✗ 此專案停用 Direct Upload。請依 docs/DEPLOYMENT.md 由 GitHub main 部署。"
	@exit 2

lint: ## ruff 檢查
	uv run ruff check .

fmt: ## ruff 格式化
	uv run ruff format .
	uv run ruff check --fix .

check: lint build audit ## 提交前跑這個（含離線稽核）

clean: ## 清掉建置暫存
	rm -rf .tmp .wrangler .ruff_cache dist **/__pycache__

.PHONY: help build icons og meta counter audit verify serve deploy lint fmt check clean
