# Daleel — project conventions

مركز الدليل (daleelconsult.org) — a Flask app. This file ships with the repo, so
**every Claude that opens this project inherits these conventions automatically.**
It holds the *judgment layer*: how to work here cleanly. The step-by-step *paths*
live as skills in `.claude/skills/` (see "The toolkit" below).

## The app in one breath (the "kitchen" model)
- `app.py` = the chef — routes are the doorways/gatekeepers
- `daleel.db` = the fridge — SQLite memory (books, videos, posts, news, messages)
- `templates/` = plate molds — Jinja (one `base.html`, RTL Arabic)
- `static/` = pantry — css/js/images, plus `uploads/` for admin-added files

## First, get your bearings — take the tour (once, at the start)

**Do this one time, right after you first open this project — before you take on
any task.** It is a *setup step to load the context into your head*, **not** a
routine you repeat: once you've done it, every later request in this session builds
on what you learned here, so you never need to tour again.

Walk these in order — a quick skim is enough (read deeper only if the task is large):

1. **`app.py`** — the routes (the site's doorways), the shared helpers you're
   expected to reuse (`save_upload`/`take_upload`, `_ordered`/`get_one`, the
   `admin_required` gate), and **`init_db()`**, which defines the whole database
   (books, videos, posts, news, messages).
2. **`templates/base.html`** — the shared page skeleton and the right-to-left
   Arabic layout that every page extends.
3. **`static/css/style.css`** — the visual system, so anything new you build matches.

**Why this comes first:** everything below — the clean-code rules, the "reuse the
existing helpers" guidance, the workflow — only truly makes sense once you've *seen*
the code it refers to. Tour once at the start, and the rest of this file stops being
abstract and becomes obvious.

## ⭐ The core workflow — code change → verify → offer to ship

This is the most important rule here. **Whenever the user asks to modify the
code**, follow these steps in order — do not skip step 2, and do not do step 4
without an explicit yes:

1. **Make the change**, staying consistent with the existing code and layout
   (see "Clean-code conventions" below).
2. **Run it locally and show the user (ALWAYS).** Start/reload the app
   (`start.bat`, or `python app.py` → `http://localhost:5000`) and open the
   affected page so the user can *see* the change working. Capture real proof —
   a preview screenshot and the console — don't just claim it works.
3. **Verify (ASVL loop).** Look for two problem classes and fix them before
   moving on:
   - **Flaws** — the new change doesn't do what was asked
   - **Regressions** — something that used to work is now broken
   Repeat run→observe→fix until it's clean.
4. **Then raise the ship question.** Once the user has seen it working locally,
   *proactively ask*: **"Want me to ship this to GitHub?"** Do **not** push on
   your own. Ship only if the user says yes — using the `daleel-ship` skill.

> **Why this order:** local verification is cheap and reversible, so it's
> automatic. Pushing to GitHub is *outward and public*, so it needs the user's
> go-signal — but Claude asks for it at the right moment (after the user has seen
> the result), instead of making the user remember to ask.

## When you add a publishing feature — keep a skill in sync

Some features let the site **publish new content** (a new kind of book, video,
post, event — anything an admin adds through the site). When you build one, the job
**isn't done** until the publishing toolkit can drive it too — so it can later be
published by plain request or command.

After the feature is built and verified, do one of these:

- **Usually — extend `daleel-publish`.** If it follows the same admin-form pattern
  (a form → save to the DB, like books/videos/articles), add it as a new
  *variation* inside the existing `daleel-publish` skill. One skill, a new branch —
  don't duplicate a near-identical skill.
- **Only if genuinely different — create a new skill.** If its publishing path is
  truly different (a different mechanism/flow, not just new fields), give it its own
  skill under `.claude/skills/`, plus a matching `/command` if useful.

**Why:** the app and the skills must grow together. A new publish feature that ships
without skill coverage leaves a future Claude unable to drive it — which defeats the
whole point of the toolkit.

## The go-signal rule (outward actions always confirm)

The dividing line: **automate what's cheap/safe/reversible; ask before anything
outward-facing or hard to undo.**

- ⚡ **Automatic (no go-signal):** editing code, running it locally, the ASVL
  verify loop, deterministic checks, formatting.
- 🛑 **Needs a go-signal (confirm first):**
  - **Push to GitHub** — public. Asked as part of the core workflow above.
  - **Publish to the LIVE site** (daleelconsult.org) — public. The `daleel-publish`
    skill pauses at a login checkpoint; never publish to production unprompted.
  - **Destructive ops** — deleting content, dropping DB data, force-push. Never
    without explicit confirmation.

## Working protocols (Delta tool set)

Named protocols that govern *how* to work here. Both are **automatic** — applied
without being asked — and both end by reporting to the user.

### ASVL — Agentic Self-Verification Loop
Never hand back unverified work. On every build/change:
**run it → observe real output (local preview + console) → detect flaws &
regressions → fix → repeat → then report**, confirming it was verified live.
This is the engine behind the core workflow above.

### SWS — Skip-When-Stuck
When genuinely stuck on one sub-problem — repeated failed attempts, no real
progress over a relatively long stretch — **stop looping.** Skip that issue,
continue with the rest of the flow, and at the end **clearly report** what was
skipped and why, so the user can make the simple move that unblocks it.
Guardrails: only skip when the issue is **non-blocking** to the rest of the work;
**never skip silently**; prefer surfacing a specific question over grinding.

## Clean-code conventions (match the house style)

Editing cleanly is judgment, not a fixed path — so these are principles, not a
script. Keep new work indistinguishable from what's already here:

- **Match the surrounding style** — naming, comment density, the "kitchen" vocabulary
  already used in `app.py`. Read the nearby code before adding to it.
- **RTL Arabic** is the content language. UI strings, flash messages, and content
  are Arabic; keep them consistent with existing phrasing.
- **Never hardcode secrets.** `SECRET_KEY`, `ADMIN_PASSWORD`, and mail credentials
  come from environment variables only (see `DEPLOY.md`). Never write a real secret
  into a file, a commit, or chat.
- **Respect `.gitignore`.** `daleel.db`, `static/uploads/*`, and `__pycache__/` stay
  out of git. Never force them in.
- **Reuse the shared helpers** — `save_upload`/`take_upload` for files, `_ordered`/
  `get_one` for reads, the `admin_required` gate for every editing route. Don't
  reinvent what `app.py` already provides.
- **User-facing content** flows through the existing markup filters
  (`render_article`, `to_embed`) — don't bypass them with raw HTML.

## The toolkit (paths live as skills; buttons as commands)

Available in this repo — use them instead of re-deriving the steps:

| Invoke | What it does |
|---|---|
| `/publish` or "publish to Daleel" → **daleel-publish** skill | Publish an article / video / book (safe: pauses before live login) |
| `/ship` or "ship to GitHub" → **daleel-ship** skill | The git add → commit → push workflow (branch `main`, secret-safe) |

When these skills apply, follow them — they encode the exact, tested paths.
