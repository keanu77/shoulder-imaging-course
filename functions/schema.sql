-- 累計瀏覽次數。只有一列，k 固定是 'total'。
-- 建表：make counter（或 npx wrangler d1 execute <DB> --file functions/schema.sql --remote）
CREATE TABLE IF NOT EXISTS hits (
  k TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO hits (k, n) VALUES ('total', 0);
