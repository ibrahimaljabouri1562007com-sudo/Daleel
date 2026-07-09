---
description: Save and push Daleel code changes to GitHub (add → commit → push)
argument-hint: [optional: a short note on what changed / the commit message]
---
Use the **daleel-ship** skill to ship the current Daleel changes to GitHub.

Optional note on what changed (use it to inform the commit message): $ARGUMENTS

Follow the skill exactly:
- Run from inside `work here/Daleel/`.
- First show what changed (`git status -sb` + `git diff`) and confirm with the user before committing.
- Eyeball for anything that must NOT ship: `daleel.db`, `static/uploads/`, or any secret (`ADMIN_PASSWORD`, `SECRET_KEY`). Trust `.gitignore`; never force ignored files in.
- Stage, then commit with a clear present-tense message matching the repo's style.
- Confirm before `git push origin main`. Never force-push or bypass hooks.
- Verify it landed ("up to date with 'origin/main'") and report the result.
