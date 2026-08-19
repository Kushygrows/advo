# Advo Cloud — setup guide

Advo Cloud is the optional paid Sync backend: a buyer purchases a one-time
credit pack, gets a license key by email, pastes it into Advo, and Sync runs
live web search on your server instead of theirs. This is the only part of
Advo that isn't free and offline — everything else in the app still works
with zero setup and zero cost.

You need two accounts, both free to create:

- **[Lemon Squeezy](https://www.lemonsqueezy.com)** — handles checkout, tax/VAT,
  and emailing license keys to buyers. You never touch payment details.
- **[Cloudflare](https://dash.cloudflare.com/sign-up)** — hosts the Worker
  (the small server in `src/index.js`) on its free tier.

Total setup time is about 20 minutes. Nothing here requires you to write code
beyond pasting a few IDs into two files.

---

## 1. Create your Lemon Squeezy products

1. Sign up and create a store at [lemonsqueezy.com](https://www.lemonsqueezy.com).
2. Go to **Products → New Product**.
3. Set the product type to **License Keys**. This matters — it's what makes
   Lemon Squeezy auto-generate a key and email it to the buyer with zero
   custom code.
4. Create one product per credit pack size you want to sell. A reasonable
   starting point: a single "25 Sync credits" pack around $9. You can add
   more sizes later.
5. For each product, leave **Activation limit** unset or generous (this
   Worker tracks credits itself in a separate database — it does not rely on
   Lemon Squeezy's activation-limit field).
6. Publish the product(s) and copy each **Buy Link** — you'll need one of
   these for `ADVO_CLOUD_BUY_URL` in `advo.html`.
7. Open each product's page in the dashboard and note its **Product ID**
   (visible in the URL or the product details) — you'll map these to credit
   amounts in step 4 below.

## 2. Create the webhook

1. In Lemon Squeezy, go to **Settings → Webhooks → Add webhook**.
2. **Callback URL**: you'll fill this in after step 3, once you know your
   Worker's URL — it'll look like
   `https://advo-cloud.YOUR-SUBDOMAIN.workers.dev/webhook/lemonsqueezy`.
3. **Signing secret**: generate a long random string yourself (e.g.
   `openssl rand -hex 32`) and paste it in here. You'll set the same value as
   a Worker secret in step 3 — this is how the Worker verifies a webhook
   really came from Lemon Squeezy and not an impersonator.
4. **Events to subscribe to**: check `license_key_created`. Nothing else is
   required — this Worker's `handleWebhook` ignores every other event type on
   purpose (see the comment in `src/index.js`).
5. Save it. You can come back and update the callback URL later if needed.

## 3. Deploy the Cloudflare Worker

You'll need [Node.js](https://nodejs.org) 18+ installed.

```bash
cd cloud-worker
npm install
npx wrangler login          # opens a browser to connect your Cloudflare account

# Create the KV namespace that stores license keys and credit balances
npx wrangler kv namespace create ADVO_LICENSES
```

The last command prints an `id`. Open `wrangler.toml` and paste it in, replacing
`REPLACE_WITH_YOUR_KV_NAMESPACE_ID`:

```toml
kv_namespaces = [
  { binding = "ADVO_LICENSES", id = "paste-the-real-id-here" }
]
```

Now set the three secrets (each command prompts you to paste a value —
nothing is echoed to your terminal history):

```bash
npx wrangler secret put ANTHROPIC_API_KEY
# paste your own Anthropic API key — get one at console.anthropic.com

npx wrangler secret put ANTHROPIC_MODEL
# paste a current model string — see docs.claude.com/en/docs/about-claude/models

npx wrangler secret put LEMONSQUEEZY_WEBHOOK_SECRET
# paste the SAME signing secret you set in step 2
```

Deploy:

```bash
npx wrangler deploy
```

This prints your live Worker URL, e.g. `https://advo-cloud.yoursubdomain.workers.dev`.

Go back to Lemon Squeezy's webhook settings (step 2) and set the callback URL
to `<that URL>/webhook/lemonsqueezy`.

## 4. Map products to credit amounts

Open `src/index.js` and fill in `CREDIT_PACKS` with the real product IDs from
step 1:

```js
const CREDIT_PACKS = {
  "123456": 25,    // your "25 Sync credits" product ID -> credits granted
  "123457": 100,   // add more packs as you create them
};
```

Redeploy so the change takes effect:

```bash
npx wrangler deploy
```

Until a product ID is added here, a purchase of that product will not error
out (see the code comment on why) but also won't grant credits — so do this
before announcing the product is for sale.

## 5. Point the app at your Worker

Open `advo.html` (the top-level one, not the copy in this repo — keep both in
sync) and find these two lines near `let aiState`:

```js
const ADVO_CLOUD_ENDPOINT = "https://advo-cloud.YOUR-SUBDOMAIN.workers.dev";
const ADVO_CLOUD_BUY_URL = "https://YOUR-STORE.lemonsqueezy.com/buy/YOUR-PRODUCT-ID";
```

Replace both with your real Worker URL (from step 3) and your real Buy Link
(from step 1). Save, and every copy of `advo.html` you distribute from then on
will point at your live Advo Cloud backend.

## 6. Test end to end

1. Buy your own product using Lemon Squeezy's test mode (toggle it on in the
   dashboard before going live) to confirm the email arrives with a key.
2. Paste that key into Advo's "Advo Cloud" panel and click **Use this key** —
   it should show your credit balance.
3. Run a Sync — it should return a live fact bank and the credit count should
   drop by one.
4. Check the Cloudflare dashboard (**Workers & Pages → advo-cloud → Logs**)
   if anything doesn't behave as expected.

Turn off test mode in Lemon Squeezy once everything checks out, and you're live.

## Option B: Stellar (XLM) instead of — or alongside — Lemon Squeezy

This path skips Lemon Squeezy (and its 5% + $0.50 fee) entirely: a buyer
sends XLM straight to a wallet address you control, this Worker watches for
it using Stellar's own free public API, and mints a license key itself the
moment payment lands — no card processor, no third party in the middle. It's
more setup than Option A and you take on two jobs Lemon Squeezy normally
does for you (see the caveats at the end), but the fees are a fraction of a
percent instead of 5%+.

You can turn on both payment paths at once, just one, or neither — each is
independent, and `advo.html` only shows the buttons for whichever one(s) are
actually configured on your Worker.

### 1. Get a Stellar wallet and its public address

You need a wallet you control the private key for — this Worker never
touches your private key, only your public address (safe to share, like an
email address).

- **[Freighter](https://www.freighter.app)** — a free browser extension from
  the Stellar Development Foundation, the most common choice.
- **[Lobstr](https://lobstr.co)** — a free mobile/web wallet, also popular.

Either way, once it's set up you'll have a public address starting with
`G` (56 characters).

### 2. Test on testnet first — no real money involved

Set `STELLAR_NETWORK = "testnet"` in `wrangler.toml` (it's already the
default). Testnet is a separate, free practice version of the Stellar
network — testnet XLM has no real value, so you can run the entire flow
end to end without risking anything.

Fund your testnet account for free using Stellar's **Friendbot**: go to
`https://friendbot.stellar.org?addr=YOUR_PUBLIC_ADDRESS` in a browser (or
most wallets have a "fund with testnet Friendbot" button when switched to
testnet mode). This deposits 10,000 test XLM instantly.

### 3. Point the Worker at your address

Open `cloud-worker/wrangler.toml` and fill in your address:

```toml
[vars]
STELLAR_ADDRESS = "GABC...YOUR-REAL-ADDRESS-HERE"
STELLAR_NETWORK = "testnet"
```

Deploy:

```bash
cd cloud-worker
npx wrangler deploy
```

### 4. (Optional) Adjust pack sizes/prices

Open `src/index.js` and edit `STELLAR_PACKS` near the top of the Stellar
section if you want different pack sizes or prices than the defaults
(25 credits for $9, 100 credits for $29). Redeploy after changing it.

### 5. Test end to end

1. Open `advo.html`, go to **Settings → Manage API keys / connections…**
   (or the Sync panel's Advo Cloud section directly), and click
   **💫 Buy with Stellar**.
2. Pick a pack. Advo shows you an exact XLM amount, an address, and a short
   memo code — all three matter; the memo is how the Worker matches your
   payment to your order, so it must be included exactly.
3. From your wallet (switched to testnet), send that exact amount to that
   address with that memo.
4. Within a few seconds, Advo's polling should pick it up and show your new
   license key.

### 6. Go live

Fund a **real** account (mainnet) — you'll need at least ~1 XLM in it just
to keep the account active on the network (Stellar's own minimum-balance
requirement, separate from anything a buyer sends you) — then flip:

```toml
STELLAR_NETWORK = "public"
```

Redeploy, and you're live.

### What you're taking on that Lemon Squeezy normally handles

- **No automatic email.** Lemon Squeezy emails the buyer their key
  automatically. This path shows the key directly on the success screen in
  Advo instead — make sure that's communicated clearly (it already is, in
  the UI), since there's no email fallback if someone closes the tab too
  fast. (The order is still on record in KV if you need to look one up by
  hand and relay the key yourself.)
- **No tax/VAT handling.** Lemon Squeezy is a merchant-of-record and
  handles this for you. Selling directly via a wallet address means that
  responsibility is yours.
- **No refund mechanism.** There's no built-in way to reverse a Stellar
  payment (that's inherent to how any blockchain works, not something
  specific to this code) — if you need to refund someone, that's a manual
  process on your end.

## What this Worker does and doesn't do

- It never sees your Anthropic account beyond making the API call — your key
  stays a server-side secret, never sent to any client.
- It stores only: license key, credit balance, and the email Lemon Squeezy
  attaches to the key. No fact banks, drafts, or other app content ever
  reaches it — `/research` only ever receives the subject line a user typed.
- A failed upstream Anthropic call does not consume a credit (see the test
  suite this was verified against, or read `handleResearch` in `src/index.js`
  — the credit is decremented only after a successful response).
- Credits are tracked here, independent of Lemon Squeezy's own
  `activation_limit` concept, so a buyer can use their key from as many
  devices as they like — the limit is credits, not device activations.
- The Stellar path never sees or holds a private key — only your public
  address, which is meant to be shared. There's no custody of funds by this
  Worker at any point; XLM goes straight from the buyer's wallet to yours.
- Order-matching (`/stellar/order/:id`) reads an order's status from KV then
  writes back — not a single atomic step. At indie-scale traffic this is a
  non-issue; the realistic worst case is one wasted extra license key for an
  order that was already paid, never a lost payment or free credits.
