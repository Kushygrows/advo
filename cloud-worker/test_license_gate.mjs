// Unit tests for the LicenseGate Durable Object class in src/index.js,
// run with plain `node` (no wrangler/Cloudflare account needed) since
// LicenseGate only touches `crypto` (available in Node) and the
// env.ADVO_LICENSES / state.storage interfaces mocked below.
//
// This exists because the actual deployment target (a real Cloudflare
// Worker + Durable Object + KV namespace) can't be exercised in an
// offline sandbox -- this is the closest thing to a real test of the
// concurrency fix short of deploying to a live/staging Worker. Test 4
// specifically proves the fix works by re-running the OLD racy pattern
// (direct KV read-modify-write, no DO) against the same concurrent load
// and showing it overspends, then showing the new DO-gated path doesn't.
//
// Usage: node cloud-worker/test_license_gate.mjs

import assert from "node:assert/strict";
import { LicenseGate } from "./src/index.js";

// ---- Mock KV namespace: same get(key, "json")/put(key, jsonString) shape
// as Cloudflare's real KV binding, backed by an in-memory Map. ----
function makeMockKV() {
  const store = new Map();
  return {
    async get(key, type) {
      const raw = store.get(key);
      if (raw === undefined) return null;
      return type === "json" ? JSON.parse(raw) : raw;
    },
    async put(key, value) {
      store.set(key, value);
    },
    _dump: () => Object.fromEntries(store)
  };
}

// ---- Mock Durable Object state.storage: same get/put shape as the real
// DO storage API, one Map per DO instance. ----
function makeMockDOStorage() {
  const store = new Map();
  return {
    async get(key) {
      return store.has(key) ? store.get(key) : undefined;
    },
    async put(key, value) {
      store.set(key, value);
    }
  };
}

// Mimics env.LICENSE_GATE.idFromName(id) + .get(id) -- one LicenseGate
// instance per distinct idSeed, persisting across calls within a test
// (matches real DO behavior: same idFromName -> same instance -> same
// storage), backed by the SAME shared mock KV every instance reads/writes.
//
// IMPORTANT: this also queues concurrent .fetch() calls to the SAME
// instance so only one runs at a time, start to finish -- this is not
// something LicenseGate's own code provides (and doesn't need to; nothing
// in the class implements a lock). It's Cloudflare's own documented
// Durable Object guarantee: a single DO instance processes requests one
// at a time, run-to-completion, so two requests to the same instance can
// never interleave. That guarantee is what actually closes the race in
// production. A first version of this test skipped modeling it and
// wrongly showed the fix doing nothing (5/5 concurrent requests still
// overspent) -- caught by test4's own explicit "did serialization actually
// happen" assertion, not by inspection. This queue exists specifically so
// the test can't silently give a false pass again.
function makeGateFactory(kv) {
  const instances = new Map();
  return function getGate(idSeed) {
    if (!instances.has(idSeed)) {
      const env = { ADVO_LICENSES: kv };
      const state = { storage: makeMockDOStorage() };
      const real = new LicenseGate(state, env);
      let queue = Promise.resolve();
      const queued = {
        fetch(request) {
          const result = queue.then(() => real.fetch(request));
          // Swallow the rejection on the queue chain itself (the caller
          // still sees it via `result`) so one failed call doesn't wedge
          // every later call queued behind it.
          queue = result.catch(() => {});
          return result;
        }
      };
      instances.set(idSeed, queued);
    }
    return instances.get(idSeed);
  };
}

async function callGate(gate, op, args = {}) {
  const req = new Request("https://license-gate/op", {
    method: "POST",
    body: JSON.stringify({ op, ...args })
  });
  const res = await gate.fetch(req);
  return res.json();
}

let passed = 0;
function ok(label) {
  passed++;
  console.log(`  PASS: ${label}`);
}

async function test1_decrementBasics() {
  console.log("Test 1: decrementCredits basics");
  const kv = makeMockKV();
  const getGate = makeGateFactory(kv);
  await kv.put("lic_a", JSON.stringify({ credits: 2 }));
  const gate = getGate("lic_a");

  const r1 = await callGate(gate, "decrementCredits", { kvKey: "lic_a", amount: 1 });
  assert.equal(r1.ok, true);
  assert.equal(r1.record.credits, 1);
  ok("first decrement succeeds, credits 2 -> 1");

  const r2 = await callGate(gate, "decrementCredits", { kvKey: "lic_a", amount: 1 });
  assert.equal(r2.ok, true);
  assert.equal(r2.record.credits, 0);
  ok("second decrement succeeds, credits 1 -> 0");

  const r3 = await callGate(gate, "decrementCredits", { kvKey: "lic_a", amount: 1 });
  assert.equal(r3.ok, false);
  ok("third decrement correctly refused at 0 credits");
}

async function test2_addCreditsAndRefund() {
  console.log("Test 2: addCredits (webhook grant + refund pattern)");
  const kv = makeMockKV();
  const getGate = makeGateFactory(kv);
  const gate = getGate("lic_b");

  const grant = await callGate(gate, "addCredits", { kvKey: "lic_b", amount: 25, merge: { email: "a@example.com" } });
  assert.equal(grant.record.credits, 25);
  assert.equal(grant.record.email, "a@example.com");
  ok("addCredits grants credits and merges extra fields");

  const spend = await callGate(gate, "decrementCredits", { kvKey: "lic_b", amount: 1 });
  assert.equal(spend.record.credits, 24);
  const refund = await callGate(gate, "addCredits", { kvKey: "lic_b", amount: 1 });
  assert.equal(refund.record.credits, 25);
  ok("refund-after-failed-call restores the exact credit spent");
}

async function test3_claimOnce() {
  console.log("Test 3: claimOnce (webhook dedup + Stellar paid-claim)");
  const kv = makeMockKV();
  const getGate = makeGateFactory(kv);

  // webhook-dedup style: no kvKey, just a one-time flag
  const webhookGate = getGate("webhook:evt_123");
  const first = await callGate(webhookGate, "claimOnce", {});
  assert.equal(first.ok, true);
  const second = await callGate(webhookGate, "claimOnce", {});
  assert.equal(second.ok, false);
  ok("claimOnce: first call wins, second call (same delivery retried) is a no-op");

  // Stellar-style: kvKey + merge, both written atomically with the claim
  const orderGate = getGate("order:xyz");
  await kv.put("order:xyz", JSON.stringify({ status: "pending", credits: 25 }));
  const claim1 = await callGate(orderGate, "claimOnce", { kvKey: "order:xyz", merge: { status: "paid", licenseKey: "advo_AAA" } });
  assert.equal(claim1.ok, true);
  assert.equal(claim1.record.licenseKey, "advo_AAA");
  const claim2 = await callGate(orderGate, "claimOnce", { kvKey: "order:xyz", merge: { status: "paid", licenseKey: "advo_BBB" } });
  assert.equal(claim2.ok, false);
  // The loser gets back the WINNER's record, not its own unused attempt --
  // this is what stops a concurrent poll from minting a second real key.
  assert.equal(claim2.record.licenseKey, "advo_AAA");
  ok("claimOnce: losing caller sees the winner's record, not its own discarded attempt");
}

async function test4_concurrencyRaceProof() {
  console.log("Test 4: concurrency proof -- old pattern overspends, DO-gated pattern doesn't");

  // Simulates the ORIGINAL bug: raw KV get-then-put with an artificial
  // delay between them (standing in for the real-world delay of an actual
  // Anthropic API call), no serialization at all. This is what
  // handleResearch did before the fix.
  async function legacyRacyDecrement(kv, key, amount, delayMs) {
    const record = await kv.get(key, "json");
    await new Promise((r) => setTimeout(r, delayMs)); // stands in for the Anthropic call
    if (!record || record.credits < amount) return { ok: false };
    record.credits -= amount;
    await kv.put(key, JSON.stringify(record));
    return { ok: true };
  }

  const kvOld = makeMockKV();
  await kvOld.put("lic_race", JSON.stringify({ credits: 1 }));
  // Fire 5 concurrent requests against a key that only has 1 real credit.
  const legacyResults = await Promise.all(
    Array.from({ length: 5 }, () => legacyRacyDecrement(kvOld, "lic_race", 1, 5))
  );
  const legacySuccesses = legacyResults.filter((r) => r.ok).length;
  console.log(`    legacy pattern: ${legacySuccesses}/5 concurrent requests succeeded on 1 real credit`);
  assert.ok(legacySuccesses > 1, "sanity check: the OLD pattern should overspend under this exact test, proving the test actually exercises the race");
  ok(`legacy pattern reproduces the bug: ${legacySuccesses} requests wrongly succeeded on 1 credit`);

  // Same scenario, through the DO-gated path this fix introduces.
  const kvNew = makeMockKV();
  const getGate = makeGateFactory(kvNew);
  await kvNew.put("lic_race", JSON.stringify({ credits: 1 }));
  const gate = getGate("lic_race");
  async function gatedDecrementWithDelay(delayMs) {
    const result = await callGate(gate, "decrementCredits", { kvKey: "lic_race", amount: 1 });
    await new Promise((r) => setTimeout(r, delayMs)); // stands in for the Anthropic call, AFTER the atomic decrement
    return result;
  }
  const gatedResults = await Promise.all(Array.from({ length: 5 }, () => gatedDecrementWithDelay(5)));
  const gatedSuccesses = gatedResults.filter((r) => r.ok).length;
  console.log(`    DO-gated pattern: ${gatedSuccesses}/5 concurrent requests succeeded on 1 real credit`);
  assert.equal(gatedSuccesses, 1, "exactly one of the 5 concurrent requests should win the 1 available credit");
  const finalRecord = await kvNew.get("lic_race", "json");
  assert.equal(finalRecord.credits, 0);
  ok("DO-gated pattern: exactly 1/5 concurrent requests succeeded, credits end at exactly 0 -- race closed");
}

async function test5_rateLimit() {
  console.log("Test 5: rateLimit sliding window");
  const kv = makeMockKV();
  const getGate = makeGateFactory(kv);
  const gate = getGate("lic_rl");

  for (let i = 0; i < 3; i++) {
    const r = await callGate(gate, "rateLimit", { limit: 3, windowMs: 60000 });
    assert.equal(r.ok, true);
  }
  const blocked = await callGate(gate, "rateLimit", { limit: 3, windowMs: 60000 });
  assert.equal(blocked.ok, false);
  assert.ok(blocked.retryAfterMs > 0);
  ok("rate limit: 4th request within the window is correctly blocked with a retryAfterMs");
}

async function main() {
  await test1_decrementBasics();
  await test2_addCreditsAndRefund();
  await test3_claimOnce();
  await test4_concurrencyRaceProof();
  await test5_rateLimit();
  console.log(`\nALL LICENSE_GATE TESTS PASSED (${passed} assertions)`);
}

main().catch((err) => {
  console.error("LICENSE_GATE TEST FAILED:", err);
  process.exit(1);
});
