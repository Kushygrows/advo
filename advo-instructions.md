# Advo — Complete Guide

## The menu bar & appearance settings (new)

Above everything else is a small **File / Edit / View / Settings** menu bar, like any desktop app. Nothing in it does anything new — every item just jumps you straight to a panel that already exists (so you don't have to hunt for it on the page) or reuses a button that's already there, except for one genuinely new thing: **Settings → Appearance**.

- **File** — Import your notes, Import fact bank (JSON), Export fact bank (JSON).
- **Edit** — Undo last change, Manage the fact bank, Clear fact bank.
- **View** — switch between Guided/Classic, or jump straight to Video outline, Thumbnail preview, Best time to post, or Session history. If you're in Guided mode and pick something outside the core 4 steps, Advo switches you to Classic automatically (with a quick heads-up) so you're never stuck.
- **Settings → Appearance** — this is the fix for "I can't read this text comfortably":
  - **Font** — Default (your system font), or two fonts chosen specifically for reading legibility: **Atkinson Hyperlegible** (designed by the Braille Institute of America) and **Lexend** (designed to reduce reading effort). Both are professional, standard-looking typefaces, not a novelty font — no Comic Sans here.
  - **Text size** — Small, Default, Large, or X-Large. The whole app reflows to fit — nothing gets cut off or overlaps at any size.
  - **Bolder text** — increases the weight of body text for more contrast, without changing text that's already bold (headings, buttons).
  - Changes apply instantly and are saved on this device, so you only set it once. **Reset to defaults** puts everything back to how Advo ships.
  - **Settings** also has quick links to Privacy & storage and your connected API keys.
- **Settings → Motion** — Advo now has a bit of atmosphere: a slow-drifting glow in the background, a shimmering accent line, and smooth hover/press/panel-transition animations throughout. Two explicit choices here: **⚡ Full motion** (the default look) or **⏸ Reduced (static)**, which turns all of that off completely — no background movement, no transitions, instant state changes. The first time you open Advo on a device, it automatically follows that device's own "reduce motion" system setting until you choose one explicitly yourself; after that, your choice always wins.

## Mobile & touch (new)

Advo automatically adapts to a phone or tablet — no setting to find, it detects the device itself:

- **One "☰ Menu" button** replaces the four File/Edit/View/Settings triggers below a certain screen width, opening all four as one stacked, scrollable list instead of a cramped horizontal row.
- **Bigger tap targets** — buttons, chips, and menu items grow to a comfortable finger-sized minimum on touch screens (this is based on whether your device actually uses touch, not just how narrow the window is, so a touchscreen laptop gets this even at a wide window, and a resized desktop window with a mouse doesn't get oversized buttons it doesn't need).
- **No stuck "hover" glow** — the hover lift/glow effects on buttons and chips only appear for an actual mouse or trackpad, so tapping something on a touchscreen never leaves it looking stuck in a highlighted state.
- **No unexpected zoom** — text fields stay at a comfortable reading size on phones specifically so Safari/Chrome don't zoom the whole page in when you tap into one.
- **Lighter background effects on phones** — the ambient glow trades a little visual richness for battery life and smoothness on phone-class hardware.
- Layout, notch/home-indicator spacing, and everything else described throughout this guide all still apply exactly the same — mobile is the same app and the same fact bank, just fitted to a smaller screen and a finger instead of a cursor.

## Guided vs. Classic view (new)

The first thing you'll see is a small switcher at the top: **🧭 Guided** and **🗂 Classic (all-in-one)**. Both use the exact same app underneath — nothing is different or missing in either one, it's only how much is on screen at once.

- **🧭 Guided** (the default for a first-time user) walks through one step at a time — start a subject, review your sources, choose an angle, generate & export — with a "Continue" button (repeated at the bottom of the step too, so you're never stuck scrolling back up) that won't let you move on until that step is actually usable, and a tip explaining why if it's blocked (e.g. "pick at least one platform before continuing"). The video outline builder lives right there on the final step alongside the platform list, so video creators don't need to leave Guided mode. A few less-common tools (thumbnails, notes import, privacy settings, and so on) are still Classic-only — switch to Classic to reach those.
- **🗂 Classic (all-in-one)** is the original single scrolling page with every panel and power feature visible at once — Sync, notes import, video outline builder, thumbnail preview, best-time-to-post, session history, privacy & storage, all of it.

Your choice is remembered (saved on this device) so the app opens the same way next time. Switch anytime with the top switcher — you'll never lose data moving between them, since they're reading and writing the same fact bank either way. Picking one (from the switcher or the View menu) briefly shows a one-line reminder of what that mode does, then fades away on its own a couple seconds later — it doesn't stick around permanently.

## Watch it first (optional)

There's a 45-second video walkthrough, `advo-tutorial.mp4`. Click **"📺 Watch the 60-second tutorial"** at the top of the app, or just double-click the video file directly. **Keep it in the same folder as `advo.html`** — the in-app link is a relative path, so it only opens if the two files sit together.

## The core loop (30 seconds)

1. **Open it.** Double-click `advo.html` (or your pinned shortcut).
2. **Pick a fact.** Click any fact in the list, or press `1`-`9`.
3. **Pick an angle.** Click a style chip, or press `←` / `→`.
4. **Pick platform(s) or output type.** Check X, Instagram, Facebook, etc. — or check **Blog post** / **Article** / **📚 School report** to pull your whole fact bank into one longer, sourced draft instead of a single-fact caption. Making a video instead? The video outline builder is right there on the same step.
5. **Copy and post.** Click "Copy for [platform]." If a draft is longer than the platform allows, Advo has already auto-trimmed it to fit (source link always kept intact) — see "Drafts that fit the platform automatically" below.

Everything below is optional power tools on top of that loop.

---

## Research a new subject (Sync)

1. Type your subject into the blue "Sync" box near the top.
2. Click **Sync**. It checks — in order — for your own API key, then a connected Advo Cloud key, then a local AI on your machine, then falls back to copy/paste options.
3. If nothing loads automatically: click **Copy this AI prompt**, paste it into Claude, ChatGPT, or any AI chat, then paste its whole reply back into the box that appears right below the prompt — Advo pulls the facts out automatically. (There's also a file-based **Import JSON** in Classic mode's "Manage the fact bank" for re-loading a previously exported fact bank — the paste box above is the one to use for a fresh AI reply, and it works in Guided mode too.)
4. Want independent search results instead of AI? Check **🎯 Also generate smart search queries** — Advo builds a real advanced-search-operator query (`site:`, `filetype:`, `intitle:`, exclusions, date ranges, and so on) instead of a generic keyword search, from two layers working together:
   - **Text analysis** — Advo reads what you actually typed and looks for recognizable patterns: a comparison ("Tesla vs Rivian" becomes an OR search for either name), an exact name or title (Title Case text gets exact-phrase quoting), ranking language ("best," "top," "cheapest" nudges toward review/ranking pages), how-to phrasing ("how to fix...") nudges toward guides and FAQs, and a year or words like "latest"/"recent" add a date filter. Anything it detects shows up as its own labeled checkbox under **🧠 Detected in what you typed** — already turned on, but one click turns any of them back off. If you've already typed real search syntax yourself (`site:`, `filetype:`, `OR`, `-exclude`), Advo notices and leaves it alone rather than duplicating it.
   - **Source category** — pick the category that matches what you're looking for (News, Government & regulatory, Academic & research, Statistics & data, Legal & court records, Company & financial, Reviews, How-to/docs, Forums, Person/biography, or General). Advo highlights a suggested category based on your subject text, but never picks one for you automatically — you always confirm by clicking a category chip. Each category has its own 2 relevant sub-option checkboxes (e.g. "Major outlets only," "Exclude opinion/editorial" for News), plus two controls that apply to every category: **Exact phrase match** and a **Date range** (past week/month/year).
   
   Pick Google, DuckDuckGo, Brave, or Bing and open or copy the finished query.

*Optional advanced step:* under "Advanced: connect your own Anthropic API key," you can paste a real API key for live web search. This costs real money and is visible in your browser's network traffic — only do it on a device you trust.

*Optional, no setup:* under "Advo Cloud — paid, zero setup," click **🛒 Buy credits** to purchase a one-time credit pack (no subscription, no account). You'll get a license key by email — paste it in and click **Use this key**. Every Sync while an Advo Cloud key is connected uses one credit for a live-web-search run on Advo's server, same as bringing your own API key, just without the setup. The key lives in memory only — pasted fresh each session, never saved to disk. Advo Cloud only ever receives the subject you type into Sync; it never sees your fact bank, drafts, or anything else in the app. Want to self-host it instead? The full server code is in `cloud-worker/` — see `cloud-worker/SETUP.md`.

**Prefer to pay with crypto instead of a card?** Right below the Buy credits button is **"or pay with Stellar (XLM)"** — pick a pack, and Advo shows you an exact XLM amount, an address, and a short memo code. Send that from any Stellar wallet (with the memo — that's how Advo matches your payment to your order) and Advo picks it up automatically within a few seconds, showing your new license key right there — no email, no card, no account. This only appears if the Advo Cloud server you're connected to has turned this payment option on.

Either key panel has a **Forget key** button once a key is set, for clearing it from memory without reloading the page.

**💡 Suggest subjects** — don't have a subject yet? Click this (next to Sync) for 5 AI-suggested, narrow-enough-to-research subject ideas, optionally guided by whatever you've typed in the subject box as a general niche. Uses whatever AI connection Sync already has (or gives you a copy/paste prompt if none is connected). Click any suggestion to fill it into the subject box.

**A note on source quality (new):** every fact Sync brings back is checked before it's added — anything without a real, well-formed `http(s)://` link as its source is dropped automatically, and Advo tells you how many (and why) in the status line. This mainly matters on the **local AI** path: your local model has no internet access, so it's drafting from memory, not live research — Advo already flags that in orange every time — and this check catches the specific failure mode of it inventing a source that sounds real but isn't an actual link. It can't verify a source is *accurate*, only that it's a real, checkable link — you still need to spot-check what it actually says.

---

## Import your notes (new — Notion, OneNote, Apple Notes, Obsidian)

Already took notes somewhere else? This panel (right below Sync) turns them into fact-bank entries instead of you retyping everything.

**Getting your notes out of each app** — Advo reads plain text and Markdown; it can't open each app's own file format directly:
- **Obsidian** — no export needed. Click **📁 Select a vault folder** and point it at your vault; it's already a folder of `.md` files.
- **Notion** — `••• → Export → Markdown & CSV`, unzip the download, then **📄 Select files** and pick the `.md` files.
- **OneNote / Apple Notes** — neither has a clean bulk-export to text. Select a note (or several), copy, and paste into the box. For a lot of pages at once, OneNote's "Export a section as Word" (then copy the text out of Word) or Apple Notes' "Export as PDF" (copy the text out of the PDF) both work as a manual bridge.

**Two ways to extract:**

1. **🧮 Quick extract — free, fully offline.** Splits your notes on structure (headings, bullets, paragraphs), keeps fragments that read like standalone, checkable statements, flags ones that read like your own opinion ("I think," "maybe," "TODO," etc.) instead of silently dropping them, and drops exact duplicates. Nothing leaves your device for this option — it never costs anything and never needs any AI connected.
2. **✨ AI-assisted extract.** Better at judgment calls a keyword-based pass can't make. Uses whichever AI Sync already has connected — your own Anthropic key, a connected **Advo Cloud** key (spends 1 credit, same as a Sync), or a local model — or a separate **OpenAI key** you can connect just for this panel (Advanced section, same session-only/never-saved handling as the Anthropic key). If nothing is connected, click Sync's "Check for connected AI" first, or just switch back to Quick extract.

Either way, after extraction you get a **review list** — every candidate shows a tone/bias score (the exact same heuristic as the Tone & Bias Check elsewhere in the app) and an opinion flag where relevant. Everything is checked by default; uncheck anything you don't want. Nothing is added until you click **+ Add checked to fact bank**.

Imported facts get a teal **Personal Note** tag instead of a source-tier badge — they're not an independently verifiable web source, and Advo is upfront about that everywhere they show up (today's pick, citations, video-outline source lists). From there, everything else works exactly like any other fact: pick an angle, pick a platform, or feed it into the video outline builder — **that's** the "turn notes into a content type" step, using tools you already know rather than a separate one-off importer.

---

## Blog post, Article & School report (new)

Everything else in "4. Select platform(s) or output type" builds a short caption from **one** fact — your current pick. **Blog post**, **Article**, and **📚 School report** work differently: check any one of them and Advo pulls in **every fact currently in your fact bank**, not just today's pick, and writes a headline, a sourced paragraph per fact, and a source list at the bottom.

- **Blog post** uses a conversational voice. **Article** uses a more neutral, reported voice. **School report** is written for a school assignment — every source in the list is a real, checkable link your teacher can follow, which doubles as a starting bibliography. Otherwise all three work identically.
- There's no character limit and no "over limit" warning — instead you get a word count and how many facts were used.
- This is a **first draft to edit**, not a finished piece — each paragraph is one sourced fact plus a plain connecting phrase, not synthesized prose. Rewrite the transitions, reorder paragraphs, and put it into your own words before turning anything in or publishing — this is a research starting point, not a finished assignment.
- Want fewer facts in the draft? Delete or clear the ones you don't want from the fact bank first — Blog post/Article/School report always uses the full current bank.

---

## Drafts that fit the platform automatically (new)

Short-form platforms (X, Threads, Instagram, and so on) each have a real character limit. Advo now fits your draft to that limit for you instead of just warning you about it:

- If your fact + angle text is too long for the platform you picked, Advo automatically trims the wording down to a clean sentence (or word) boundary and adds "…" — never mid-word, never mid-sentence. The character-count badge shows what happened, e.g. "229 / 280 chars (auto-trimmed from 496)," so you always know a trim occurred.
- **Your source link is never trimmed.** Advo reserves room for the full "Source: ..." line first, then fits the body text around it — a draft is never posted without its source intact.
- Once trimmed, the note under the draft changes from a warning to "✂️ Automatically trimmed to fit — this copy is ready to post as-is." You can still copy it immediately; there's nothing left for you to manually shorten.
- In the rare case a draft still can't fit — the source link alone is longer than the platform's limit — Advo tells you plainly instead of pretending it fits.
- **X Premium toggle:** X/Twitter genuinely has two tiers — 280 characters free, 25,000 with X Premium. If you check **"I have X Premium"** right on the X preview, Advo re-fits (or un-trims) your draft using the 25,000-character limit instead. Uncheck it and it goes back to 280.
- This toggle only appears for platforms that actually have a real premium character-limit difference. Advo doesn't invent a premium tier for a platform that doesn't genuinely have one — as of this writing, only X qualifies; Threads and the others are a flat limit for every account.

---

## Judge your sources before you post

- **Tier badges** on each fact (Official/Gov, Academic, Org/Association, Secondary — verify) are a quick, mechanical flag based on the source's web address — not proof of accuracy.
- **Diversity line** under the fact list warns you if too many facts share one source.
- **Readability score** on each platform preview (e.g. "42 · dense") — under 50 means simplify before posting.
- **Freshness indicator** next to the subject name turns orange after 14 days — a nudge to re-verify.
- **Search facts** — type in the search box above the fact list to filter instantly.
- **Copy citation** — the 📑 button on any fact copies a ready-to-paste quote + source.
- **📰 Outlet lean badge** — if a fact's source is a major, widely-recognized news outlet (Fox News, CNN, NYT, WSJ, and ~30 others), a colored badge shows its political lean — blue for left, red for right, gray for center. This is always on, no toggle needed.
- **Source lean balance line** — under the fact list, a running count of how your *rated* sources lean (e.g. "1 Lean Left, 1 Center, 1 Right"), with a warning if it's skewed to one side.

**Where these ratings come from:** [AllSides Media Bias Ratings](https://www.allsides.com/media-bias/ratings) — a panel that publishes its methodology and reviews with people across the spectrum. This is their published rating, attributed by name, not Advo's own judgment. Other rating projects sometimes disagree, and ratings change over time (AllSides itself has re-rated several outlets in the past couple of years) — hover any badge for the confidence note, and use the **"Look up a source not covered here"** link for anything not in the built-in list. A lean badge describes the outlet's *general* editorial tendency, never whether one specific fact is accurate.

---

## Check tone & bias before you post (new)

1. Under "4. Select platform(s)," check **🔍 Show tone & bias check on previews**.
2. Every preview now shows a score chip (e.g. "15 · neutral tone," "42 · some charged language," "100 · heavily loaded") plus your draft with words highlighted right in the text — orange for emotionally loaded language, blue for absolute claims like "always" or "everyone."
3. Click **💡 Tips to sound less biased** under any preview for specific fixes: which words to swap (with a suggested neutral replacement), where absolute language needs qualifying, and whether the draft acknowledges another point of view.

**What this does and doesn't do:** it flags loaded language, absolutist phrasing, and one-sided framing — the rhetorical markers that make writing read as biased, regardless of subject. It does **not** label anything "left" or "right" — a real political-lean classification isn't something a static offline tool can honestly claim to do, and building one would mean baking a set of political judgment calls into the app. This is off by default; check the box any time you want a second look before copying a post.

---

## Build a video outline (for YouTube, Rumble, Twitch)

This turns several facts into a structured, timed script instead of one short post. It's on the same step as picking a platform — in Guided mode, scroll down past the platform list on step 4; in Classic mode it's its own numbered panel.

1. Scroll to **"Making a video instead? Build an outline."**
2. Click **✨ Auto-pick facts for me** (picks the 4 strongest facts by an attention/consequence heuristic), or check 3-6 facts by hand.
3. Choose a **video goal**: Informational, Persuasive/advocacy, Myth-bust, or News update — this changes the wording of the opening and closing lines.
4. Check **Talking-points mode** if this is for a livestream — it turns full sentences into short bullets you can riff off instead of read word-for-word.
5. Click **🎬 Generate outline.**

You'll get:
- **3 title ideas**, each with its own copy button and a character-length note (YouTube/search titles generally land best around 40-60 characters — this just flags when a title runs long or short, it isn't a ranking prediction).
- **Suggested tags/keywords**, pulled straight from the words in your selected facts (not a live search-volume tool) — copy the whole list with one click.
- **5 timed sections** — Hook, Context, The Record, The Stakes, Call to Action — each showing its own estimated speaking time and a running timestamp, color-coded so they're easy to tell apart at a glance.
- A **total estimated runtime** (based on ~145 words/minute — treat it as a guide, not a stopwatch). If you've selected more than the recommended 3-6 facts, a note above the checklist flags that The Record section will run long.

From there:
- **🖥 Open teleprompter** — full-screen, auto-scrolling script. Space bar plays/pauses, the speed slider controls scroll rate, A-/A+ resize the text, Esc closes it.
- **📋 Copy full script** — the whole outline as plain text, section-labeled.
- **📝 Generate video description** — a YouTube/Rumble-ready description: hook line, estimated chapter timestamps, and a numbered source list pulled from every fact you used.
- **✂️ Make a 30-45s short version** — condenses the hook + stakes into a short-form script for Shorts/Reels/Rumble Shorts.
- **📌 Generate pinned comment** — a correction/verification note citing your sources. Leave the box blank for a generic "verified as of [date]" note, or type what changed for a specific correction.

*How the outline is actually built:* every fact you selected gets scored two ways — how strong it reads as an opening hook (numbers, dollar signs, short/absolute language) and how strong it reads as a closing stakes beat (deadlines, requirements, consequences). The single best-scoring fact becomes the Hook, the best of what's left becomes the Stakes, and everything else becomes The Record in between. It's a heuristic, not judgment — always read the result before recording.

---

## Thumbnail text preview (new)

Below the video outline, "6. Thumbnail text preview" is a fast, offline way to check whether a headline actually reads at a glance — not a design tool. Type a headline (or click **Use outline HOOK text** to pull it from a generated outline), pick a background, and it renders live on a canvas. **⬇ Download PNG** saves it locally; nothing is uploaded anywhere.

## Best time to post (new)

"7. Best time to post," near the bottom, is a collapsed panel of general, widely-cited posting-time benchmarks per platform. This is **not** personalized data — Advo has no account or analytics access and never will without breaking its own no-account promise. If you have real analytics for your own audience, trust those over this.

---

## Manage the fact bank

- **+ Add to fact bank** — add one fact by hand (needs both the text and a valid `http(s)://` source link).
- **✏️ Edit / 🗑 Delete** — every fact in the list (panel 1) now has its own edit and delete buttons. Editing pre-fills the "add a fact" form; deleting shows an **Undo** action in the toast for a few seconds.
- **🧹 Clear fact bank** — wipes the current fact bank to start over (also undoable from the toast).
- **⬇ Export fact bank (JSON)** — saves your current subject's facts to a file so you can switch back later.
- **⬆ Import JSON** — loads a previously exported (or AI-generated) fact bank. This is also how you switch subjects entirely.

**Advo now autosaves.** Your fact bank, subject, and session history are saved to this browser's local storage as you work, and restored automatically next time you open `advo.html` in the same browser — so a refresh or crash doesn't lose a Sync result. This never includes an API key or Advo Cloud license key; those still live in memory only, cleared the moment you close the tab. The app opens with an empty fact bank the first time — the "See an example first" link on that empty state loads one of a handful of neutral, non-controversial example topics (sleep science, honeybee pollination, renewable energy, space exploration, ocean plastic pollution — never anything political or industry-specific), and a banner above the fact list lets you clear it and start your own whenever you're ready. That autosave is plain text by default — if you're working with sensitive material, see the next section for an optional encrypted version.

---

## Keep sensitive material encrypted (new)

By default, the autosave above is plain text in this browser's local storage. If this device is shared, or your subject is sensitive, open **🔒 Privacy & storage** (bottom of the page) and turn on **Encrypt autosaved data with a passphrase**.

How it works:

- You set a passphrase (8+ characters). From then on, your autosaved fact bank, subject, and history are encrypted on disk using your browser's built-in encryption (AES-GCM, with the key derived from your passphrase — nothing exotic, nothing homemade).
- Advo never stores the passphrase anywhere, exactly like it never stores your API keys — it only lives in memory for the current tab.
- **There is no password reset.** Advo has no account and no server, so if you forget the passphrase, that autosaved data cannot be recovered by Advo, by us, or by anyone — write it down somewhere safe.
- Next time you open Advo on this device, you'll see an unlock screen. Enter your passphrase to restore your data, or **Continue without unlocking** to use the app fresh (your encrypted data stays on disk untouched, and you can unlock it later from the Privacy panel). **Start fresh instead** permanently deletes it — it asks you to confirm by clicking a second time first.
- Turning encryption back off asks for your current passphrase once, then re-saves your data as plain text.

**Honest limit:** this protects the saved data from someone else who gets hold of your files or browser profile. It doesn't protect against something already running inside your own unlocked browser (malware, a rogue extension) — no tool running in a browser tab can promise that.

---

## Keyboard shortcuts

| Key | Action |
|---|---|
| `1`-`9` | Jump to that fact in the list |
| `←` / `→` | Cycle the angle |
| `Space` | Play/pause the teleprompter (only while it's open) |
| `Esc` | Close the teleprompter |

Shortcuts are disabled while you're typing in any text box, while the teleprompter is open (it has its own Space/Esc handling), and when Ctrl/Cmd/Alt is held (so they don't fight with your browser's own shortcuts). Number keys jump within whatever's currently visible if you've typed something into "Search facts."

---

## Extras

- **🔀 Shuffle** — jumps to a different fact + angle combo.
- **📜 Session history** — a running log (bottom of the page) of everything you've copied, synced, exported, imported, or generated this session.

---

## Accessibility

Every clickable fact, angle, and outlet-lean badge is keyboard-reachable (Tab to focus, Enter/Space to activate), the teleprompter traps focus while open and returns it to where you were when you close it, toasts are announced to screen readers and can be dismissed manually or paused by hovering, and every text input has a real label even where the visible design just shows placeholder text.

---

## Honest limits

Advo runs entirely offline in your browser by default, and every core feature — the fact bank, angles, platform formatting, tone & bias check, video outline, thumbnail preview, and the Quick (offline) notes extraction — works with zero internet connection. The only features that ever leave your machine are Sync, the subject-suggestion helper, and AI-assisted notes extraction — and only if you choose to connect something: your own Anthropic or OpenAI key, a paid Advo Cloud key, or a local AI server. Skip all of those and you get copy/paste prompts (or the free offline extractor) instead — nothing is sent anywhere. Tier badges, readability scores, the SEO title/tag notes, the best-time-to-post guide, the outline's hook/stakes/note-extraction scoring, and the automatic character-limit trimming are all mechanical heuristics or general, verified platform rules, not fact-checking or personalized analytics. Imported notes are especially worth double-checking — they reflect what you wrote down, not an independently verified source. Always keep a source link on everything you post, and re-verify anything time-sensitive before you rely on it.

**Security, for the technically curious:** every piece of dynamic content Advo renders — synced facts, imported files, imported notes, Advo Cloud responses — is HTML-escaped before it touches the page, and any link built from that data is checked against an `http(s)://`-only allowlist before it's ever made clickable, so a malicious or malformed fact can't run script or execute a `javascript:` link. A restrictive Content-Security-Policy is set in the page itself as a second layer of protection. Advo makes network requests only to the endpoints documented above (your local AI port, Anthropic's API, OpenAI's API, or Advo Cloud) — nothing is ever sent anywhere else, there's no analytics or telemetry of any kind, and the source is a single readable HTML file you can inspect yourself line by line. Note files you select or a vault folder you point Advo at are read locally in your browser only — nothing is uploaded unless you explicitly turn on AI-assisted extraction with a connected key. Autosaved data is plain text unless you turn on the optional passphrase encryption (**🔒 Privacy & storage**), which uses the browser's built-in Web Crypto API (AES-GCM, PBKDF2 key derivation) — the passphrase itself is never written to disk or sent anywhere, which is also why there's no way to recover it if you forget it.
