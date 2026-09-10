# 部署與版本核對

現況整理：2026-09-10。原始碼可見性不決定 Cloudflare 網站能否公開瀏覽。

| 設定 | 現況 |
| --- | --- |
| GitHub | keanu77/shoulder-imaging-course（PUBLIC） |
| 正式分支 | main |
| Cloudflare Pages 專案 | shoulder-imaging-course |
| 建置根目錄 | repo 根目錄 |
| 建置指令 | `python3 src/build/build.py` |
| 輸出目錄 | dist |
| 正式網址 | https://shoulder-imaging.sportsmedicine.tw/ |

既有正式站由 Git integration 部署。第三方改作須新建自己的 Pages 專案；不要更改原站專案、DNS 或綁定。環境變數及秘密只放本機未追蹤設定或 Cloudflare，不提交有效憑證。

## 發布流程

1. 執行 README 與 DEVELOPMENT 的建置、品質及必要瀏覽器檢查。
2. 核對變更範圍、來源與審閱狀態；文件整備不等於新增教材批准。
3. 依 repo 的分支保護規則提交／合併，確認 GitHub Actions 通過。
4. 查 Cloudflare 的正式 deployment SHA 是否等於欲發布的 commit。
5. 使用 UTC 本機建置，核對正式頁面、主要程式及資料與 dist 的 SHA-256；不能只看 HTTP 200。若僅更新文件，網站功能內容應維持相同，版本標記可能更新。
6. 若修改介面，實測手機、鍵盤、主題與課程／投稿入口；不自行送出真實測試信。

repo 公開、網站索引與醫療審閱相互獨立。目前主頁、肩部與膝部 repo 公開，其餘五部位 repo 維持私有；搜尋索引設定不變。
