<img src="assets/advo-mark.svg" width="56" height="56" alt="Advo logomark" align="left" />

# ADVO
<sub>TRUTH · CONTEXT · EVIDENCE</sub>

<br clear="left"/>

### The fact-checked content engine for creators who'd rather be right than viral

Every fact sourced. Every claim bias-checked. Every post formatted for the platform you're posting it to — before you hit publish, not after someone quote-tweets your mistake.

Advo turns a sourced fact bank into ready-to-post content for X, Instagram, Facebook, LinkedIn, TikTok, and Threads, or into a fully timed video script with a built-in teleprompter for YouTube, Rumble, or Twitch — plus an SEO title/tag helper, a thumbnail preview, and a tone-and-bias check that flags loaded language before your audience does.

**No account. No subscription. No cloud required. One HTML file that runs entirely offline, forever, for free.**

📺 [Watch the 60-second tutorial](advo-tutorial.mp4) &nbsp;·&nbsp; ⬇ [Get Advo](../../releases)

### Why creators use it

- 🧾 **Every fact carries a source** — tier-rated (Official/Gov, Academic, Org, Secondary) so you know what you're standing on before you post it.
- ⚖️ **Bias check before you publish** — flags loaded language, absolutist claims, and one-sided framing most creator tools don't even look for.
- 🎬 **Fact bank to finished video, in one pass** — a timed Hook/Context/Record/Stakes/CTA script, teleprompter, short-form cut, and SEO title/tag helper.
- 📥 **Import your own notes** — pull straight from Notion, OneNote, Apple Notes, or Obsidian and turn them into sourced, bias-scored content chunks.
- 🔒 **Private by default** — works offline, never phones home, and can encrypt your saved drafts with a passphrase only you know.
- 💸 **Free forever, upgrade only if you want to** — the whole app is free and offline; optional AI-assisted research and note extraction are the only paid add-on.

## Download

Grab the latest build for your OS from the [Releases page](../../releases):

- **Windows** — `Advo-Setup-x.x.x.exe` (installer) or `Advo-x.x.x-portable.exe` (no install, just run it)
- **Linux** — `Advo-x.x.x.AppImage` (make it executable, then run it — no install) or the `.deb` package

No releases published yet? See [Build it yourself](#build-it-yourself) below, or just open `advo.html` directly — see [Run without installing anything](#run-without-installing-anything).

## Run without installing anything

Advo's entire app is one self-contained file, `advo.html`. It works on Windows, Linux, and Mac exactly the same way: download it and double-click it, or open it in any browser (Chrome, Firefox, Brave, Edge — anything). No install, no build step, no server. The desktop `.exe`/`AppImage` builds above just wrap this same file in a native app window with a taskbar icon — they're a convenience, not a requirement.

## Features

- **Guided or Classic view** — a top switcher toggles between a step-by-step **Guided** wizard (start a subject → review sources → choose an angle → generate & export, one screen at a time, with a tip if a step isn't ready to continue) and the original **Classic** all-in-one scrolling page with every panel visible. Same app, same fact bank, either way — your choice is remembered on this device. Picking one shows a brief one-line reminder of what it does, which fades away on its own rather than sitting there permanently.
- **A File/Edit/View/Settings menu bar** — a conventional app menu across the top for jumping straight to any panel (Import notes, Manage the fact bank, Video outline, Privacy & storage, API keys, and so on) without hunting for it on the page, plus an **Appearance** panel under Settings for text size (Small–X-Large), an accessibility-focused font (Atkinson Hyperlegible or Lexend, both designed for reading legibility — see Fonts below), and a bolder-text option. Everything reflows live and is saved on this device.
- **Atmosphere, with an off switch** — a slow-drifting ambient background glow, a shimmering top accent line, and smooth hover/press/panel-transition animations throughout, all in the same dark palette. **Settings → Motion** offers an explicit **Full motion** / **Reduced (static)** choice that turns every bit of it off instantly when picked, and automatically follows this device's OS-level "reduce motion" setting until you do.
- **Automatic mobile & touch adaptation** — detected via feature queries (touch capability, hover support), not user-agent sniffing, so it's accurate on any device. The File/Edit/View/Settings menu bar collapses into a single "☰ Menu" sheet, every interactive element grows to a comfortable tap-target minimum, hover-only effects are scoped out so nothing looks "stuck" after a tap, form inputs stay at a safe font size to avoid iOS's auto-zoom-on-focus, and the ambient background trims its cost on phone-class hardware — same design language and same fact bank either way.
- **Sourced fact bank** for any subject, with tier badges (Official/Gov, Academic, Org/Association, Secondary) and outlet-lean badges for major news sources (attributed to [AllSides Media Bias Ratings](https://www.allsides.com/media-bias/ratings))
- **Six writing angles** (data-led, story-led, question-led, comparison-led, myth-bust, news-jack) and platform-aware formatting with live character counts and readability scoring
- **Automatic character-limit fitting** — if a draft runs over a platform's limit, Advo trims it to a clean sentence/word boundary itself (never mid-word, and the source link is never cut) instead of just warning you to do it manually. For platforms with a genuine premium tier — currently X, 280 free / 25,000 with Premium — an inline toggle re-fits the draft to the higher limit; Advo doesn't fabricate a premium tier for platforms that don't actually have one.
- **Blog post, Article & School report output** — pulls every fact currently in your fact bank into one longer, sourced draft with a headline and a source list, instead of a single-fact caption. School report is built for students of any age doing a school project — every source is a real link that doubles as a starting bibliography.
- **Tone & bias check** — flags loaded language, absolutist claims, and one-sided framing in your draft, with rewrite tips
- **Video outline builder** — turns several facts into a timed Hook/Context/Record/Stakes/CTA script, with a built-in teleprompter, auto-generated video description, 30-45s short-form cut, pinned-comment correction notes, an SEO-style title/tag helper, and an offline thumbnail text preview
- **Sync** — optionally connects to a local AI model (Ollama, LM Studio), your own Anthropic API key, or a paid **Advo Cloud** license key for live research; falls back to a copy-paste AI prompt or advanced search-engine queries when none of those are available. A **Suggest subjects** button reuses the same connection to propose specific content ideas when you don't have a subject yet.
- **Smart search query builder** — an alternative to AI research, and more than a plain keyword search: Advo parses the actual text you typed for recognizable patterns (a comparison like "Tesla vs Rivian" becomes an OR search for either name, Title Case text gets exact-phrase quoting, ranking language like "best"/"top" nudges toward review pages, how-to phrasing nudges toward guides/FAQs, a year or "latest"/"recent" adds a date filter) and turns each one into a real search-operator refinement — shown as its own labeled, toggleable checkbox, never applied silently. On top of that, pick from 11 source categories (News, Government & regulatory, Academic & research, Statistics & data, Legal & court records, Company & financial, Reviews, How-to/docs, Forums, Person/biography, General) and Advo composes the rest of the query (`site:`, `filetype:`, `intitle:`, `inurl:`, exclusions, `OR` groups, `after:` date ranges). A transparent keyword heuristic suggests a category based on your subject and highlights it — it never auto-applies one; you always confirm by clicking a category. Each category has its own relevant sub-option toggles, plus global exact-phrase and date-range controls, then opens or copies the finished query for Google, DuckDuckGo, Brave, or Bing.
- **Import your notes** — pull existing notes from Notion, Microsoft OneNote, Apple Notes, or Obsidian (via file/folder picker or paste) and break them into reviewable, source-tagged fact-bank chunks. A free, offline, rule-based extractor works with zero setup; an optional AI-assisted mode (your Anthropic key, your OpenAI key, or **Advo Cloud** credits) produces cleaner splits and flags opinion vs. fact. Every chunk gets a bias score from the same Tone & bias check engine, and a "📝 From your notes" tag so you always know where it came from.
- **Full fact management** — edit or delete any fact in place, undo the last change from the toast, and autosave to this browser's local storage so a refresh never loses a Sync result (API/license keys are never included — they stay memory-only)
- **Optional passphrase encryption** for that autosave — off by default; turn it on in **Privacy & storage** for AES-GCM encryption of your saved fact bank on disk, keyed from a passphrase Advo never stores (so there's no password reset — losing it means losing that data, by design, since nothing about it is recoverable server-side)
- **Best time to post** — a collapsed panel of general, attributed posting-time benchmarks per platform (not personalized account data, which Advo can't access by design)

See [`advo-instructions.md`](advo-instructions.md) for the full guide.

## Fonts

The two optional accessibility fonts under **Settings → Appearance** are embedded directly in `advo.html` (as `data:` URIs, not linked from a CDN) so they work fully offline like everything else in the app:

- **[Atkinson Hyperlegible](https://github.com/googlefonts/atkinson-hyperlegible)** — © Braille Institute of America, Inc.
- **[Lexend](https://github.com/googlefonts/lexend)** — © The Lexend Project Authors

Both are licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL), which explicitly permits embedding/bundling. Full license text for each is in [`fonts-licenses/`](fonts-licenses).

## Design principles

- **No fake capabilities.** Advo never claims to detect what else is open in your browser, fetch live data on its own, or classify political bias as objective fact. Every heuristic (readability, tier badges, tone check, outlet lean, SEO/title notes, best-time-to-post) is labeled as a heuristic or general guidance, not proof or personalized data.
- **Every rating is attributed.** Outlet-lean badges cite AllSides Media Bias Ratings by name — Advo doesn't invent its own political classifications.
- **Offline-first.** The core app has zero external dependencies and works from a local file. Contributions that require a server or an account to use the basic app won't be accepted. The one exception is the optional, paid **Advo Cloud** Sync backend (see below) — it's opt-in, clearly labeled, and every feature works without it.
- **Secure by default.** Every value Advo renders that could come from outside the app (a Sync result, an imported file, an Advo Cloud response) is HTML-escaped before it's displayed, and links built from that data are checked against an `http(s)://`-only allowlist before they're made clickable — so a malformed or malicious fact can't inject script or a `javascript:` link. A restrictive Content-Security-Policy is set in the page as a second layer. Advo makes network requests only to the endpoints documented above — no analytics, no telemetry, nothing sent anywhere else. It's one readable HTML file; nothing is obfuscated or minified, so you (or anyone) can read exactly what it does.

## Advo Cloud (optional, paid)

Sync can research a subject for you, but that requires *some* AI it can
reach — a local model, your own API key, or Advo Cloud: a one-time credit
pack with zero setup. It's the only part of Advo that costs money or leaves
your machine, and it's entirely optional — everything else in the app is
free and offline whether or not you ever touch it.

Two independent ways to buy credits, either or both of which a given Advo
Cloud server can offer:

- **Card, via Lemon Squeezy** — buy credits, get a license key by email,
  paste it in.
- **Stellar (XLM)** — pay straight from your own Stellar wallet to the
  developer's address, no card processor or account involved. Advo shows the
  exact amount, address, and a one-time memo to send it with, then picks up
  the payment automatically within a few seconds — the license key appears
  right there, ready to use.

The same credits also power AI-assisted **note extraction** (see Features
above) — it's the same `/research` endpoint with a different prompt, so
turning on AI-assisted mode for your imported notes doesn't require any
separate purchase or setup beyond the license key you already have.

The full server behind both payment options is open source too — see
[`cloud-worker/`](cloud-worker) and [`cloud-worker/SETUP.md`](cloud-worker/SETUP.md)
if you'd rather run your own instead of using the hosted one.

## Build it yourself

Requires [Node.js](https://nodejs.org) 18+.

```bash
npm install
npm start              # run the desktop app locally
npm run dist:linux     # build Linux AppImage + .deb into dist/
npm run dist:win       # build Windows installer + portable .exe into dist/ (run this on Windows, or via the GitHub Actions workflow)
```

Pushing a tag like `v1.0.1` triggers [`.github/workflows/build.yml`](.github/workflows/build.yml), which builds on real Windows and Linux GitHub runners and attaches the installers to a new GitHub Release automatically.

**The Windows installer is branded** — `build/icon.ico` (taskbar/desktop icon), `build/installerSidebar.bmp` (the welcome/finish page artwork, 164×314), and `build/license.txt` (the MIT license page) are wired up in `package.json`'s `nsis` config, so a from-source build gets Advo's real icon, a branded install wizard, and an explicit license step instead of electron-builder's generic defaults. One honest caveat: this isn't code-signed (that requires a paid certificate), so Windows SmartScreen will still show an "unknown publisher" warning on first run regardless of how the installer looks — that's normal for an indie-built app and isn't something installer branding can fix.

## Where this is headed

Today, Advo is a single free tool. The longer-term intention — internally codenamed **ARCC** — is to grow this into a full content-creation engine and platform that serves creators at any level, from someone posting for the first time to a full-time creator running multiple channels. Nothing about that changes the promise above: the core app stays free, offline, and account-free forever; anything built toward that platform vision will be optional and additive, the same way Advo Cloud is today.

## Contributing

Issues and pull requests are welcome. Please keep [`advo-instructions.md`](advo-instructions.md) in sync with any user-facing change.

## License

[MIT](LICENSE)
