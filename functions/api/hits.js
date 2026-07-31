/**
 * 累計瀏覽次數。GET 讀取，POST 遞增後回傳。
 *
 * 為什麼是 D1 而不是 KV 或 Durable Object：
 * - KV 免費方案每天只有 1,000 次寫入，而且**同一個 key 每秒最多寫 1 次**，
 *   訪客一多就會撞 429。計數器是最不適合 KV 的用法。
 * - Durable Object 是計數器的教科書解，但 **Pages 專案不能自己託管 DO class**，
 *   必須另外部署一個 Worker 再綁定，對「clone 下來就能跑」的框架來說設定成本太高。
 * - D1 直接綁 Pages Functions，全程 CLI 就能建好，免費方案每天 100,000 列寫入。
 *
 * 沒有綁 D1（例如本機預覽）時回 503，前端會安靜地不顯示徽章，不會壞掉。
 */

const NO_STORE = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store, max-age=0",
};

// 爬蟲會把數字灌得很難看。擋不完，但擋掉最大宗的那幾種成本極低。
const BOT = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|headless|lighthouse|monitor|preview|curl|wget|python-requests/i;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: NO_STORE });
}

async function read(db) {
  const row = await db.prepare("SELECT n FROM hits WHERE k = 'total'").first();
  return row?.n ?? 0;
}

export async function onRequestGet({ env }) {
  if (!env.HITS) return json({ error: "no-d1" }, 503);
  try {
    return json({ hits: await read(env.HITS) });
  } catch {
    return json({ error: "query-failed" }, 503);
  }
}

export async function onRequestPost({ env, request }) {
  if (!env.HITS) return json({ error: "no-d1" }, 503);

  // 機器人只給讀，不計入
  if (BOT.test(request.headers.get("user-agent") || "")) {
    try {
      return json({ hits: await read(env.HITS), counted: false });
    } catch {
      return json({ error: "query-failed" }, 503);
    }
  }

  try {
    // 單一語句完成遞增，不需要交易，也沒有 read-modify-write 的競態
    const row = await env.HITS.prepare(
      `INSERT INTO hits (k, n) VALUES ('total', 1)
       ON CONFLICT(k) DO UPDATE SET n = n + 1
       RETURNING n`,
    ).first();
    return json({ hits: row?.n ?? 0, counted: true });
  } catch {
    return json({ error: "write-failed" }, 503);
  }
}
