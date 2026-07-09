---
description: Publish an article, video, or book to the Daleel website (daleelconsult.org)
argument-hint: [what to publish, e.g. "a video titled ... with this link"]
---
Use the **daleel-publish** skill to publish content to the Daleel website
(daleelconsult.org).

What the user wants to publish: $ARGUMENTS

Follow the skill exactly, including its safety rules:
- Confirm the target first (local `http://localhost:5000` vs live `https://daleelconsult.org`) — never assume production.
- Identify the content type (article / video / book) and collect only that type's fields.
- Never hardcode or print the admin password; it comes from the `ADMIN_PASSWORD` env var.
- Pause at the login checkpoint and confirm before any live admin login (safe version).
- After submitting, verify the new entry is actually live and report where it appears.
