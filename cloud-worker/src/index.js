/**
 * Advo Cloud — Cloudflare Worker
 *
 * This is the entire paid backend for Advo. Two independent ways to pay
 * feed the same credit system, plus the two endpoints Advo itself calls:
 *   1. Receives Lemon Squeezy's "license_key_created" webhook and credits the
 *      new key with research credits (Lemon Squeezy handles checkout, tax/VAT,
 *      key generation, and emailing the key to the buyer — none of that is
 *      built here).
 *   1b. Optionally, /stellar/quote + /stellar/order/:id do the equivalent
 *      job for paying with Stellar (XLM) instead — see the "Stellar (XLM)
 *      payments" section below for how that works. Both paths write the
 *      same shape of record to ADVO_LICENSES, so everything past "a valid
 *      license key with credits exists" is shared.
 *   2. Answers /verify so the app can show "you have N credits left" without
 *      spending one.
 *   3. Answers /research: checks the license key has credits, calls Anthropic
 *      on the SERVER using a key only this Worker holds, decrements one
 *      credit, and returns the result. This is the actual paywall — it works
 *      because the check happens here, not in client-side code the user could
 *      edit.
 *
 * Required secrets (set with `wrangler secret put NAME`):
 *   ANTHROPIC_API_KEY            your own Anthropic API key — never sent to clients
 *   ANTHROPIC_MODEL               a current model string, e.g. from
 *                                  docs.claude.com/en/docs/about-claude/models
 *   LEMONSQUEEZY_WEBHOOK_SECRET  the signing secret you set when creating the
 *                                  webhook in the Lemon Squeezy dashboard —
 *                                  only needed if you're using that path
 *
 * Public config (set in wrangler.toml under [vars], not secrets):
 *   STELLAR_ADDRESS   your "G..." receiving address — only needed if you're
 *                      using the Stellar payment path (leave blank to keep
 *                      it disabled)
 *   STELLAR_NETWORK   "testnet" (default) or "public"
 *
 * Required KV namespace binding (see wrangler.toml): ADVO_LICENSES
 *
 * CREDIT_PACKS below maps a Lemon Squeezy product_id -> credits granted.
 * Update the IDs after you create your products (see ../SETUP.md).
 * STELLAR_PACKS (further down) does the equivalent for the Stellar path.
 */

const CREDIT_PACKS = {
  // "123456": 25,   // <-- replace with your real product_id -> credit amount
  // "123457": 100,
};

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json", ...CORS_HEADERS }
  });
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return mismatch === 0;
}

async function hmacHex(secret, message) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function verifyLemonSqueezySignature(request, secret) {
  const signature = request.headers.get("X-Signature") || "";
  const rawBody = await request.clone().text();
  const digest = await hmacHex(secret, rawBody);
  return timingSafeEqual(digest, signature);
}

async function handleWebhook(request, env) {
  if (!(await verifyLemonSqueezySignature(request, env.LEMONSQUEEZY_WEBHOOK_SECRET))) {
    return json({ error: "invalid signature" }, 401);
  }

  const payload = await request.json();
  const eventName = payload.meta && payload.meta.event_name;

  // order_created always fires alongside license_key_created — nothing to do
  // with it here since the license key event carries everything we need.
  if (eventName !== "license_key_created") {
    return json({ ok: true, ignored: eventName || "unknown event" });
  }

  const attrs = payload.data.attributes;
  const key = attrs.key;
  const productId = String(attrs.product_id);
  const email = attrs.user_email;
  const credits = CREDIT_PACKS[productId];

  if (!key) return json({ error: "webhook payload missing license key" }, 400);
  if (!credits) {
    // Product not in CREDIT_PACKS yet — don't fail the webhook (Lemon Squeezy
    // will retry and keep failing), just log it as ignored so you notice in
    // the Cloudflare dashboard and can add the product_id to CREDIT_PACKS.
    return json({ ok: true, ignored: `product_id ${productId} not in CREDIT_PACKS` });
  }

  const existing = await env.ADVO_LICENSES.get(key, "json");
  const newBalance = (existing ? existing.credits : 0) + credits;
  await env.ADVO_LICENSES.put(key, JSON.stringify({ credits: newBalance, email }));

  return json({ ok: true, key, creditsGranted: credits, newBalance });
}

async function handleVerify(request, env) {
  const { licenseKey } = await request.json();
  if (!licenseKey) return json({ error: "licenseKey required" }, 400);
  const record = await env.ADVO_LICENSES.get(licenseKey, "json");
  if (!record) return json({ valid: false, credits: 0 });
  return json({ valid: true, credits: record.credits, email: record.email });
}

async function handleResearch(request, env) {
  const { licenseKey, prompt } = await request.json();
  if (!licenseKey || !prompt) return json({ error: "licenseKey and prompt are required" }, 400);

  const record = await env.ADVO_LICENSES.get(licenseKey, "json");
  if (!record || record.credits <= 0) {
    return json({ error: "No credits remaining on this license key." }, 402);
  }
  if (!env.ANTHROPIC_MODEL) {
    return json({ error: "Server misconfigured: ANTHROPIC_MODEL secret is not set." }, 500);
  }

  const anthropicRes = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: env.ANTHROPIC_MODEL,
      max_tokens: 3000,
      messages: [{ role: "user", content: prompt }],
      tools: [{ type: "web_search_20250305", name: "web_search", max_uses: 6 }]
    })
  });

  if (!anthropicRes.ok) {
    const errText = await anthropicRes.text().catch(() => "");
    return json({ error: `Research call failed (HTTP ${anthropicRes.status}). ${errText.slice(0, 300)}` }, 502);
  }

  const data = await anthropicRes.json();
  const textBlocks = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n");
  if (!textBlocks) return json({ error: "Model response had no usable text." }, 502);

  record.credits -= 1;
  await env.ADVO_LICENSES.put(licenseKey, JSON.stringify(record));

  return json({ text: textBlocks, creditsRemaining: record.credits });
}

// ---------- Stellar (XLM) payments — an alternative to Lemon Squeezy ----------
// Same end result as the Lemon Squeezy path (a license key with credits
// lands in ADVO_LICENSES), but built by hand since there's no hosted
// checkout page for Stellar the way Lemon Squeezy provides for cards. Flow:
//
//   1. POST /stellar/quote  — client asks for a price. We lock in a
//      USD->XLM rate, hand back a receiving address + exact amount + a
//      short one-time memo, and store a "pending" order in KV.
//   2. The buyer sends that exact amount of XLM to that address with that
//      memo, from their own wallet. This Worker only ever reads a public
//      address — it never touches a private key, so there's no custody
//      risk on this end at all.
//   3. GET /stellar/order/:id — polled by the client every few seconds.
//      Each call asks Horizon (Stellar's own public API) whether a
//      payment matching the memo has landed yet. Once it has, this mints
//      a license key in the exact same shape the Lemon Squeezy webhook
//      writes, so /verify and /research above needed zero changes to
//      accept a Stellar-paid key.
//
// Required vars (set in wrangler.toml under [vars] — these are public,
// not secrets: a receiving address is meant to be shared, same as a mailing
// address):
//   STELLAR_ADDRESS   the "G..." public address that receives payments
//   STELLAR_NETWORK   "testnet" (default — safe to test with, no real
//                      money) or "public" (real mainnet XLM)
//
// STELLAR_PACKS maps a pack id -> {usd, credits}, priced in USD upfront
// since (unlike Lemon Squeezy) there's no external product to look an ID
// up against — update these to whatever pack sizes/prices you want to sell.
const STELLAR_PACKS = {
  pack25: { usd: 9, credits: 25 },
  pack100: { usd: 29, credits: 100 }
};

const STELLAR_ORDER_TTL_MS = 30 * 60 * 1000; // 30 minutes to pay before the quoted price expires
const STELLAR_AMOUNT_TOLERANCE = 0.98; // accept payment >= 98% of the quoted amount (covers XLM price drift between quote and payment)
const STELLAR_MEMO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no 0/O/1/I — avoids memo transcription mistakes

function stellarHorizonBase(env) {
  return env.STELLAR_NETWORK === "public"
    ? "https://horizon.stellar.org"
    : "https://horizon-testnet.stellar.org";
}

function randomCode(length, alphabet) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  let out = "";
  for (let i = 0; i < length; i++) out += alphabet[bytes[i] % alphabet.length];
  return out;
}

// Stellar text memos are capped at 28 bytes — 10 characters from a 33-char
// alphabet (33^10 possibilities) is short enough to type or copy by hand
// while still being effectively collision-proof between orders.
function generateOrderMemo() {
  return randomCode(10, STELLAR_MEMO_ALPHABET);
}

function generateLicenseKey() {
  return `advo_${randomCode(24, "abcdefghijklmnopqrstuvwxyz0123456789")}`;
}

async function getXlmUsdPrice() {
  const res = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd");
  if (!res.ok) throw new Error(`Price lookup failed (HTTP ${res.status}).`);
  const data = await res.json();
  const price = data && data.stellar && data.stellar.usd;
  if (!price || typeof price !== "number") throw new Error("Price lookup returned no usable XLM/USD rate.");
  return price;
}

async function handleStellarQuote(request, env) {
  if (!env.STELLAR_ADDRESS) {
    return json({ error: "Server misconfigured: STELLAR_ADDRESS is not set." }, 500);
  }
  const { packId } = await request.json();
  const pack = STELLAR_PACKS[packId];
  if (!pack) return json({ error: `Unknown pack id "${packId}".` }, 400);

  let xlmPrice;
  try {
    xlmPrice = await getXlmUsdPrice();
  } catch (err) {
    return json({ error: `Couldn't get a live XLM price right now: ${err.message} Try again in a moment.` }, 502);
  }

  // 7 decimal places is Stellar's own precision limit for its native asset.
  const xlmAmount = Number((pack.usd / xlmPrice).toFixed(7));
  const orderId = randomCode(16, "abcdefghijklmnopqrstuvwxyz0123456789");
  const memo = generateOrderMemo();
  const now = Date.now();
  const order = {
    packId,
    usd: pack.usd,
    credits: pack.credits,
    xlmAmount,
    xlmPriceAtQuote: xlmPrice,
    memo,
    status: "pending",
    createdAt: now,
    expiresAt: now + STELLAR_ORDER_TTL_MS
  };
  await env.ADVO_LICENSES.put(`order:${orderId}`, JSON.stringify(order), {
    // Kept around an hour past expiry so a payment that lands late (or
    // needs reconciling by hand) can still be looked up, not just silently
    // dropped the instant the quote window closes.
    expirationTtl: Math.ceil(STELLAR_ORDER_TTL_MS / 1000) + 3600
  });

  return json({
    orderId,
    address: env.STELLAR_ADDRESS,
    network: env.STELLAR_NETWORK === "public" ? "public" : "testnet",
    xlmAmount,
    memo,
    credits: pack.credits,
    usd: pack.usd,
    expiresAt: order.expiresAt
  });
}

// Looks at recent payments Horizon has recorded for our receiving address
// and checks whether any of them carry the memo we're looking for at at
// least the tolerated amount. Payment *operations* don't carry the memo
// themselves (it lives on the transaction, one level up), so each
// candidate needs one extra lookup — fine at indie-scale traffic, and it
// avoids depending on a full Stellar SDK for something this small.
async function checkHorizonForPayment(env, memo, minAmount) {
  const base = stellarHorizonBase(env);
  const res = await fetch(
    `${base}/accounts/${env.STELLAR_ADDRESS}/payments?order=desc&limit=50&include_failed=false`
  );
  if (!res.ok) {
    if (res.status === 404) return null; // account not found/unfunded yet on this network
    throw new Error(`Horizon payments lookup failed (HTTP ${res.status}).`);
  }
  const data = await res.json();
  const records = (data._embedded && data._embedded.records) || [];

  for (const rec of records) {
    if (rec.type !== "payment") continue;
    if (rec.asset_type !== "native") continue; // XLM only — ignore custom tokens sent by mistake
    if (rec.to !== env.STELLAR_ADDRESS) continue;

    let memoOnTx;
    try {
      const txRes = await fetch(`${base}/transactions/${rec.transaction_hash}`);
      if (!txRes.ok) continue;
      const tx = await txRes.json();
      memoOnTx = tx.memo;
    } catch (e) {
      continue; // a single bad lookup shouldn't fail the whole scan
    }

    if (memoOnTx !== memo) continue;

    const amount = Number(rec.amount);
    return { found: true, amount, underpaid: amount < minAmount, txHash: rec.transaction_hash };
  }
  return null;
}

// Note on concurrency: this reads the order from KV, decides, then writes
// back — not a single atomic operation. At indie-scale traffic (one buyer
// polling their own order every few seconds) the odds of two overlapping
// requests both landing on the same order right as payment confirms are
// vanishingly small, and the worst case is one wasted extra license key
// minted for the same paid order — not a lost payment or free credits. A
// Durable Object would close that gap entirely if this ever needs it.
async function handleStellarOrderStatus(env, orderId) {
  const key = `order:${orderId}`;
  const order = await env.ADVO_LICENSES.get(key, "json");
  if (!order) return json({ error: "Order not found or expired." }, 404);

  if (order.status === "paid") {
    return json({ status: "paid", licenseKey: order.licenseKey, credits: order.credits });
  }
  if (order.status === "underpaid") {
    return json({ status: "underpaid", received: order.receivedAmount, expected: order.xlmAmount });
  }

  if (Date.now() > order.expiresAt) {
    order.status = "expired";
    await env.ADVO_LICENSES.put(key, JSON.stringify(order));
    return json({ status: "expired" });
  }

  let match;
  try {
    match = await checkHorizonForPayment(env, order.memo, order.xlmAmount * STELLAR_AMOUNT_TOLERANCE);
  } catch (err) {
    // Horizon hiccup — tell the client to keep polling rather than treat a
    // failed lookup as confirmation that no payment has arrived.
    return json({ status: "pending", note: `Temporary lookup issue, still watching: ${err.message}` });
  }

  if (!match) return json({ status: "pending" });

  if (match.underpaid) {
    order.status = "underpaid";
    order.receivedAmount = match.amount;
    order.txHash = match.txHash;
    await env.ADVO_LICENSES.put(key, JSON.stringify(order));
    return json({ status: "underpaid", received: match.amount, expected: order.xlmAmount });
  }

  // Payment matched and covers the tolerated amount — mint the key using
  // the exact same record shape the Lemon Squeezy webhook writes.
  const licenseKey = generateLicenseKey();
  const existing = await env.ADVO_LICENSES.get(licenseKey, "json");
  const newBalance = (existing ? existing.credits : 0) + order.credits;
  await env.ADVO_LICENSES.put(licenseKey, JSON.stringify({ credits: newBalance, source: "stellar" }));

  order.status = "paid";
  order.licenseKey = licenseKey;
  order.txHash = match.txHash;
  await env.ADVO_LICENSES.put(key, JSON.stringify(order));

  return json({ status: "paid", licenseKey, credits: order.credits });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS_HEADERS });

    const url = new URL(request.url);
    try {
      if (url.pathname === "/webhook/lemonsqueezy" && request.method === "POST") {
        return await handleWebhook(request, env);
      }
      if (url.pathname === "/verify" && request.method === "POST") {
        return await handleVerify(request, env);
      }
      if (url.pathname === "/research" && request.method === "POST") {
        return await handleResearch(request, env);
      }
      if (url.pathname === "/stellar/quote" && request.method === "POST") {
        return await handleStellarQuote(request, env);
      }
      if (url.pathname.startsWith("/stellar/order/") && request.method === "GET") {
        const orderId = url.pathname.slice("/stellar/order/".length);
        return await handleStellarOrderStatus(env, orderId);
      }
      return json({ error: "not found" }, 404);
    } catch (err) {
      return json({ error: "Server error: " + err.message }, 500);
    }
  }
};
