---
name: daleel-ship
description: >-
  Save and publish Daleel code changes to GitHub — the git add → commit → push
  workflow for the Daleel repo (github.com/.../Daleel). Use this whenever the user
  wants to ship, save, publish, push, "send to GitHub", "back up", "commit", or
  "update the repo" for the Daleel project — even if they only say "save my
  changes" or "ارفع التعديلات". It reviews what changed, writes a clear commit
  message, and pushes to origin/main safely, with beginner-friendly checks for the
  common traps (unsaved files, accidentally committing secrets, main vs master).
---

# Ship Daleel changes to GitHub

This skill takes the work sitting in the Daleel project and gets it safely onto
GitHub, using the standard **three moves**: `add` → `commit` → `push`. It is
written for someone still learning git, so it favors *showing what will happen
and confirming* over blind speed.

> **The repo:** branch `main`, remote `origin` →
> `github.com/ibrahimaljabouri1562007com-sudo/Daleel.git`
> Always run these commands from inside `work here/Daleel/`.

## The mental model (git in one breath)

Three moves, three meanings — say them to the user if they're unsure:

1. **`add`** = *choose* which changes to include (put items on the tray).
2. **`commit`** = *save a snapshot* locally, with a message describing it (seal the
   tray with a label). Nothing has left your computer yet.
3. **`push`** = *send* those saved snapshots up to GitHub (mail the tray). This is
   the only step that touches the outside world.

## ⚠️ Before anything — two safety rules

1. **Push is an outward, public action.** Never `push` (or `commit`) without first
   *showing the user what's about to ship and getting a clear yes.* Treat it like
   sending mail — once it's on GitHub, it's out there.
2. **Never bypass safety.** Do not use `--no-verify`, do not force-push
   (`--force` / `-f`), do not skip hooks. If something fails, diagnose it — don't
   power through it.

## Step 1 — See what changed (always start here)

Run these from `work here/Daleel/`:

```bash
git status -sb        # what's changed + which branch, at a glance
git diff              # the actual line-by-line changes (unstaged)
```

Read the output *with* the user. This step answers "what am I about to ship?"
before committing to anything.

### 🪤 Beginner trap: "nothing to commit"
If git says **"nothing to commit, working tree clean"** but the user swears they
changed something, the usual cause is: **the file was never saved in the editor.**
Ask them to save (Ctrl+S) and run `git status` again. Git only sees what's written
to disk, not what's open in the editor.

## Step 2 — Sanity-check for things that must NOT be shipped

Before staging, glance at the list of changed files for anything sensitive:

- **`daleel.db`** — the database. It's in `.gitignore` and should stay out. Never
  force it in.
- **`static/uploads/`** — admin-uploaded files. Also gitignored. Leave them out.
- **Secrets** — `SECRET_KEY`, `ADMIN_PASSWORD`, mail credentials. These live in
  **environment variables**, never in the code. If you ever see a real password or
  secret key written into a committed file, **stop and warn the user** — that's a
  leak, not a normal change.

If `git status` only shows normal source files (`app.py`, `templates/`, `static/css`,
`.claude/`, etc.), you're good. The `.gitignore` already keeps the sensitive stuff
out — trust it, don't override it.

## Step 3 — Stage the changes (`add`)

Default to staging everything that changed (the `.gitignore` protects the rest):

```bash
git add -A
```

If the user only wants *some* of the changes shipped, stage specific files instead:

```bash
git add app.py templates/library.html
```

Then confirm what's staged:

```bash
git status -sb        # staged items show in green / under "Changes to be committed"
```

## Step 4 — Commit (save a labeled snapshot)

Write a **clear, present-tense summary** of *what changed and why* — matching the
style already in this repo's history (short imperative lines, e.g.
"Rename news heading", "Add themed 500 error page"). A good message lets future-you
understand the change at a glance.

```bash
git commit -m "Short imperative summary of the change"
```

Good vs weak messages:

- ✅ `Add publish-book skill under .claude/skills`
- ✅ `Fix video thumbnail not showing on library page`
- ❌ `update` / `stuff` / `asdf` (tells future-you nothing)

**Confirm the message with the user** before committing if there's any doubt.
After committing, the change is saved **locally** — it is still NOT on GitHub yet.

## Step 5 — Push (send it to GitHub)

This is the step that publishes. Confirm with the user first, then:

```bash
git push origin main
```

Watch the output:
- Success → git prints an updated ref line (e.g. `main -> main`). It's now on GitHub.
- **Rejected / "fetch first"** → GitHub has commits you don't have locally
  (maybe edited from another machine or the web). Do **not** force it. Run
  `git pull --rebase origin main`, resolve if needed, then push again.
- **Auth prompt / failure** → the user may need to re-authenticate to GitHub.
  Report it plainly; don't retry blindly.

## Step 6 — Confirm it landed

Don't call it done until it's verified:

```bash
git status -sb        # should say "up to date with 'origin/main'"
git log --oneline -3  # your new commit sits on top
```

Then tell the user: what shipped (the commit message), that it's now on GitHub,
and — if useful — the repo URL:
`https://github.com/ibrahimaljabouri1562007com-sudo/Daleel`

## Quick reference — the whole flow

```bash
cd "work here/Daleel"
git status -sb                 # 1. see what changed
git diff                       # 1. review the actual changes
# 2. eyeball for secrets / db / uploads (gitignore handles these)
git add -A                     # 3. stage
git commit -m "Clear summary"  # 4. save a labeled snapshot (local)
git push origin main           # 5. send to GitHub (confirm first!)
git status -sb                 # 6. confirm "up to date with origin/main"
```

## Notes for this repo specifically
- Branch is **`main`** (not `master`) — push to `main`.
- Remote is **`origin`** → the Daleel GitHub repo.
- `.gitignore` already excludes `daleel.db`, `static/uploads/*`, `__pycache__/`,
  and local reference folders — so a plain `git add -A` is safe here.
