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
 * Required Durable Object binding (see wrangler.toml): LICENSE_GATE — see
 *   the LicenseGate class below for what it's for. `wrangler deploy` sets
 *   this up automatically from wrangler.toml's [[durable_objects.bindings]]
 *   and [[migrations]] entries; no separate manual step needed.
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

// Shared rate-limit tuning, used by both /research and /verify (see
// LicenseGate.rateLimit below). /research spends real money per call, so
// its limit is deliberately tighter than /verify's, which is a free read.
// Both are keyed per license key, not per IP — this stops the specific
// abuse pattern of hammering ONE (real, paid-for) key with concurrent or
// rapid-fire requests. It does not stop someone probing with many
// different/garbage license keys, each of which gets its own fresh
// rate-limit bucket — that's a different threat (general endpoint abuse,
// not credit-race exploitation) and would need IP- or Cloudflare-level
// rate limiting to close, which is out of scope for this fix.
const RATE_WINDOW_MS = 60 * 1000;
const RESEARCH_RATE_LIMIT = 10;
const VERIFY_RATE_LIMIT = 30;

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

// ---------- LicenseGate Durable Object ----------
// One Durable Object class, reused to close two structurally identical
// races found in a 2026-08-20 security audit: /research's credit
// check-then-decrement, and the Stellar order's pending->paid claim. Both
// were plain KV read-modify-write sequences (get, decide, put) with no
// atomicity — two concurrent requests for the SAME key could both read
// the same starting state, both decide "yes", and both write, the second
// silently clobbering the first's effect. For /research specifically that
// meant concurrent requests on one license key could each slip past the
// credit check and each trigger a real, billed Anthropic call before any
// single decrement landed — direct, repeatable cost exposure with no
// payment or exploit sophistication required.
//
// A Durable Object closes this for free, with no manual locking: Cloudflare
// guarantees a single DO instance handles one request at a time, in order,
// so concurrent requests routed to the same instance are simply queued and
// run one after another — there's nothing left to interleave. This class
// doesn't hold its own copy of license/order data; every op below still
// reads and writes the SAME ADVO_LICENSES KV entries as before (`env` is
// shared with the parent Worker script automatically), so no data
// migration happened and nothing about where data lives changed — this is
// purely a serialization gate in front of the existing storage.
//
// Callers get an instance via callGate(env, idSeed, op, args) below.
// idSeed is a string; env.LICENSE_GATE.idFromName(idSeed) means every
// call that uses the SAME idSeed — from any request, at any time — is
// routed to the same DO instance and serialized against each other.
// Convention used throughout this file: idSeed is either a raw license
// key (for credit ops), `order:<orderId>` (for Stellar order ops), or
// `webhook:<eventId>` (for webhook-delivery dedup, which never touches KV
// at all — see claimOnce).
const LICENSE_GATE_OPS = new Set(["getRecord", "addCredits", "decrementCredits", "claimOnce", "rateLimit"]);

export class LicenseGate {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }

  async fetch(request) {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid JSON body" }, 400);
    }
    if (!LICENSE_GATE_OPS.has(body.op)) {
      return json({ error: `unknown op "${body.op}"` }, 400);
    }
    try {
      return await this[body.op](body);
    } catch (err) {
      console.error("LicenseGate op failed:", body.op, err.message);
      return json({ error: "LicenseGate internal error: " + err.message }, 500);
    }
  }

  async getRecord({ kvKey }) {
    const record = await this.env.ADVO_LICENSES.get(kvKey, "json");
    return json({ record: record || null });
  }

  async addCredits({ kvKey, amount, merge }) {
    const record = (await this.env.ADVO_LICENSES.get(kvKey, "json")) || { credits: 0 };
    record.credits = (record.credits || 0) + (amount || 0);
    Object.assign(record, merge || {});
    await this.env.ADVO_LICENSES.put(kvKey, JSON.stringify(record));
    return json({ ok: true, record });
  }

  async decrementCredits({ kvKey, amount }) {
    const record = await this.env.ADVO_LICENSES.get(kvKey, "json");
    if (!record || record.credits < amount) {
      return json({ ok: false, record: record || null });
    }
    record.credits -= amount;
    await this.env.ADVO_LICENSES.put(kvKey, JSON.stringify(record));
    return json({ ok: true, record });
  }

  // First caller wins, permanently, for this DO instance (i.e. for this
  // idSeed) — every later call just sees ok:false. `kvKey`/`merge` are
  // optional: if given, the winning call also writes `merge` into that KV
  // record's fields as part of the same atomic step (used for the Stellar
  // paid-claim, which needs to both claim-once AND record the result).
  // Webhook dedup uses this with no kvKey at all, since there's nothing to
  // write to KV for "have I seen this event id before."
  async claimOnce({ kvKey, merge }) {
    const alreadyClaimed = await this.state.storage.get("claimed");
    if (alreadyClaimed) {
      const record = kvKey ? await this.env.ADVO_LICENSES.get(kvKey, "json") : null;
      return json({ ok: false, record });
    }
    await this.state.storage.put("claimed", true);
    let record = null;
    if (kvKey) {
      record = (await this.env.ADVO_LICENSES.get(kvKey, "json")) || {};
      Object.assign(record, merge || {});
      await this.env.ADVO_LICENSES.put(kvKey, JSON.stringify(record));
    }
    return json({ ok: true, record });
  }

  // Sliding-window limiter, local to this DO instance's own storage (not
  // KV) — old timestamps outside the window are dropped every call, so
  // this never grows unbounded.
  async rateLimit({ limit, windowMs }) {
    const now = Date.now();
    const timestamps = ((await this.state.storage.get("rl")) || []).filter((t) => now - t < windowMs);
    if (timestamps.length >= limit) {
      return json({ ok: false, retryAfterMs: windowMs - (now - timestamps[0]) });
    }
    timestamps.push(now);
    await this.state.storage.put("rl", timestamps);
    return json({ ok: true });
  }
}

async function callGate(env, idSeed, op, args = {}) {
  const id = env.LICENSE_GATE.idFromName(idSeed);
  const stub = env.LICENSE_GATE.get(id);
  const res = await stub.fetch("https://license-gate/op", {
    method: "POST",
    body: JSON.stringify({ op, ...args })
  });
  return res.json();
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
  // Lemon Squeezy's own resource id for this delivery — used to dedupe a
  // retried webhook. Lemon Squeezy retries on transient failure, and
  // without this a retried delivery would silently double-credit the same
  // purchase every time it landed.
  const webhookEventId = payload.data && payload.data.id;

  if (!key) return json({ error: "webhook payload missing license key" }, 400);
  if (!credits) {
    // Product not in CREDIT_PACKS yet — don't fail the webhook (Lemon Squeezy
    // will retry and keep failing), just log it as ignored so you notice in
    // the Cloudflare dashboard and can add the product_id to CREDIT_PACKS.
    return json({ ok: true, ignored: `product_id ${productId} not in CREDIT_PACKS` });
  }

  if (webhookEventId) {
    const claim = await callGate(env, `webhook:${webhookEventId}`, "claimOnce", {});
    if (!claim.ok) {
      return json({ ok: true, deduped: true, key });
    }
  } else {
    // No usable id to dedupe against — proceed and credit anyway rather
    // than silently drop a real purchase; log it so it's visible.
    console.error("Lemon Squeezy webhook payload missing data.id — cannot dedupe this delivery.");
  }

  const result = await callGate(env, key, "addCredits", { kvKey: key, amount: credits, merge: { email } });

  return json({ ok: true, key, creditsGranted: credits, newBalance: result.record.credits });
}

async function handleVerify(request, env) {
  const { licenseKey } = await request.json();
  if (!licenseKey) return json({ error: "licenseKey required" }, 400);

  const limited = await callGate(env, licenseKey, "rateLimit", { limit: VERIFY_RATE_LIMIT, windowMs: RATE_WINDOW_MS });
  if (!limited.ok) return json({ error: "Too many requests. Try again in a moment." }, 429);

  const { record } = await callGate(env, licenseKey, "getRecord", { kvKey: licenseKey });
  if (!record) return json({ valid: false, credits: 0 });
  return json({ valid: true, credits: record.credits, email: record.email });
}

async function handleResearch(request, env) {
  const { licenseKey, prompt } = await request.json();
  if (!licenseKey || !prompt) return json({ error: "licenseKey and prompt are required" }, 400);
  if (!env.ANTHROPIC_MODEL) {
    return json({ error: "Server misconfigured: ANTHROPIC_MODEL secret is not set." }, 500);
  }

  const limited = await callGate(env, licenseKey, "rateLimit", { limit: RESEARCH_RATE_LIMIT, windowMs: RATE_WINDOW_MS });
  if (!limited.ok) return json({ error: "Too many requests. Try again in a moment." }, 429);

  // Atomic check-and-decrement happens BEFORE the (expensive, real-money)
  // Anthropic call below, not after — this is the actual fix for the
  // credit race. No request can reach the Anthropic call at all unless it
  // just atomically won a real credit, via the LicenseGate DO instance for
  // this exact license key (see LicenseGate.decrementCredits above), so
  // concurrent requests on one key can no longer each slip through and
  // each trigger a billed call before any single decrement lands.
  const decrement = await callGate(env, licenseKey, "decrementCredits", { kvKey: licenseKey, amount: 1 });
  if (!decrement.ok) {
    return json({ error: "No credits remaining on this license key." }, 402);
  }

  let anthropicRes;
  try {
    anthropicRes = await fetch("https://api.anthropic.com/v1/messages", {
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
  } catch (err) {
    // Network-level failure reaching Anthropic at all (not an HTTP error
    // response, an actual thrown exception) — refund the credit we already
    // atomically took, same as every other failure path below.
    await callGate(env, licenseKey, "addCredits", { kvKey: licenseKey, amount: 1 });
    console.error("Anthropic call threw:", err.message);
    return json({ error: "Research call failed. Your credit was not spent — try again." }, 502);
  }

  if (!anthropicRes.ok) {
    const errText = await anthropicRes.text().catch(() => "");
    console.error(`Anthropic call failed HTTP ${anthropicRes.status}:`, errText.slice(0, 500));
    await callGate(env, licenseKey, "addCredits", { kvKey: licenseKey, amount: 1 });
    return json({ error: "Research call failed. Your credit was not spent — try again." }, 502);
  }

  const data = await anthropicRes.json();
  const textBlocks = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n");
  if (!textBlocks) {
    await callGate(env, licenseKey, "addCredits", { kvKey: licenseKey, amount: 1 });
    console.error("Anthropic response had no usable text block:", JSON.stringify(data).slice(0, 500));
    return json({ error: "Research call returned no usable result. Your credit was not spent — try again." }, 502);
  }

  return json({ text: textBlocks, creditsRemaining: decrement.record.credits });
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
    console.error("XLM price lookup failed:", err.message);
    return json({ error: "Couldn't get a live XLM price right now. Try again in a moment." }, 502);
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
    console.error("Horizon payment lookup failed:", err.message);
    return json({ status: "pending", note: "Temporary lookup issue, still watching." });
  }

  if (!match) return json({ status: "pending" });

  if (match.underpaid) {
    order.status = "underpaid";
    order.receivedAmount = match.amount;
    order.txHash = match.txHash;
    await env.ADVO_LICENSES.put(key, JSON.stringify(order));
    return json({ status: "underpaid", received: match.amount, expected: order.xlmAmount });
  }

  // Payment matched and covers the tolerated amount — this used to be the
  // race: multiple polls arriving around the same moment could each see
  // "payment found, not yet claimed" and each mint + grant a separate
  // license key for the SAME payment (real free credits, not just a
  // wasted key). claimOnce is serialized per order id by the LicenseGate
  // Durable Object (see above), so only the first poll to reach this point
  // actually mints and writes; every other concurrent poll gets back the
  // SAME already-minted key instead of minting its own.
  const licenseKey = generateLicenseKey();
  const claim = await callGate(env, key, "claimOnce", {
    kvKey: key,
    merge: { status: "paid", licenseKey, txHash: match.txHash }
  });

  if (!claim.ok) {
    // Someone else's poll already claimed this order first — return
    // their result, not the (unused, never-credited) key generated above.
    const finalOrder = claim.record || order;
    return json({ status: finalOrder.status, licenseKey: finalOrder.licenseKey, credits: finalOrder.credits });
  }

  await callGate(env, licenseKey, "addCredits", { kvKey: licenseKey, amount: order.credits, merge: { source: "stellar" } });

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
      // Generic message to the client -- the real detail goes to the
      // Cloudflare dashboard's Worker logs (wrangler tail / Logs tab),
      // where only you can see it, instead of being echoed back to
      // whoever's request triggered it.
      console.error("Unhandled error:", err.message, err.stack);
      return json({ error: "Server error. Please try again." }, 500);
    }
  }
};
