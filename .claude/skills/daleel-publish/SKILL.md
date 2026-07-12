---
name: daleel-publish
description: >-
  Publish new content — an article, a video, a book/booklet, or a downloadable
  tool/template — to the Daleel center website (daleelconsult.org). Drives the
  site's admin panel through the browser: logs in as admin, opens the right "add"
  form, fills the fields, submits, and confirms the new entry is live. Use this
  whenever the user wants to publish, post, add, or upload a book, booklet, video,
  lesson, article, tool, or template to Daleel / مركز الدليل / daleelconsult.org —
  even if they don't say the word "admin" or name the exact section. If the user
  just says "add this to the site" or "انشر" in the Daleel context, this is the skill.
---

# Publish content to Daleel (daleelconsult.org)

This skill publishes one piece of content to the Daleel website by driving the
site's own admin panel in a browser. The site has five publishable content
types, and this skill handles all five from **one shared path** with small
per-type differences in which fields to collect.

> **The five types (and where each lands):**
> - **Article** (مقال) → shows under the library's *Articles* section
> - **Video** (فيديو) → shows under the library's *Videos* section
> - **Book / booklet** (كتاب / كُتيّب) → shows under the library's *Booklets* section
> - **Tool / template** (أداة / نموذج) → shows under the library's *Tools & templates* section
> - **Album photo** (صورة ألبوم المدير) → shows in the director's photo album (`/director/album`)

## ⚠️ Safety first — read before running

This is the **safe first version**. It describes the full path but **stops before
performing a live admin login**. Follow these rules every time:

1. **Never log in automatically.** When you reach the login step, **pause and ask
   the user to confirm** before any real admin login happens. In this version,
   treat the login as a documented checkpoint, not an automatic action.
2. **Never hardcode or print the password.** The admin password lives in the
   `ADMIN_PASSWORD` environment variable (that's how the Daleel app itself reads
   it). Read it from there or ask the user to enter it directly in the browser.
   Do **not** write it into this file, into chat, or into any log.
3. **Confirm the target site** before doing anything (see Step 0). Publishing to
   the *live* site is a real, public action — treat it like sending mail.

## Step 0 — Establish the target and the base URL

Before touching the browser, confirm with the user **which site** you're
publishing to, because the base URL differs:

| Target | Base URL |
|---|---|
| Local development | `http://localhost:5000` |
| Live production | `https://daleelconsult.org` |

Call this the **base URL** below. If the user hasn't said which, ask — do not
assume production.

## Step 1 — Identify the content type

Figure out whether this is an **article**, a **video**, or a **book**. If the
user hasn't made it obvious, ask one short question. The type decides which form
you open and which fields you collect (Step 3).

## Step 2 — Open the browser and go to the admin login

1. Open Chrome (use the browser connector).
2. Navigate to `<base URL>/admin/login`.
3. **CHECKPOINT (safe version):** stop here. Tell the user you've reached the
   login page and ask them to confirm before proceeding. Do not type the
   password. When live login is later enabled, it will be `POST /admin/login`
   with the password from `ADMIN_PASSWORD` — never typed from this file.

Once logged in, the site shows admin controls (an add "+" and edit pencils) on
the library and home pages.

## Step 3 — Collect the fields for this content type

Ask the user for the fields below **for the chosen type only**. Required fields
are marked ✱ — do not proceed without them. This is the "road" you give the user
to fill in chat; collect everything before opening the form so the form is filled
in one clean pass.

### Article (مقال) — form at `<base URL>/admin/posts/new`
- ✱ **Title** (`title`)
- **Author** (`author`) — e.g. "د. جمال الجبوري"
- **Date** (`date`) — human display date, e.g. "أكتوبر 3، 2025"
- **Excerpt** (`excerpt`) — short summary shown in the listing
- **Body** (`body`) — full text. Supports simple markup: `### ` heading,
  `> ` quote, `- ` bullet, blank line = new paragraph, `**bold**`, `==highlight==`
- **Cover image** (`image`) — optional; PNG/JPG/WEBP/GIF

### Video (فيديو) — form at `<base URL>/admin/videos/new`
- ✱ **Title** (`title`)
- ✱ **One source is required**, either:
  - **URL** (`url`) — a YouTube/Vimeo link (it auto-embeds), or
  - **Video file** (`video`) — MP4/WEBM/OGG/MOV/M4V upload
- **Poster / thumbnail** (`poster`) — optional cover image; PNG/JPG/WEBP/GIF

### Book / booklet (كتاب) — form at `<base URL>/admin/books/new`
- ✱ **Title** (`title`)
- ✱ **Cover image** (`cover`) — required; PNG/JPG/WEBP/GIF
- **Description** (`description`) — optional
- **Document file** (`file`) — optional; PDF/DOC/DOCX

### Tool / template (أداة / نموذج) — form at `<base URL>/admin/tools/new`
- ✱ **Title** (`title`)
- ✱ **Download file** (`file`) — required; PDF/DOC/DOCX/XLS/XLSX/PPT/PPTX/CSV/TXT/ZIP/RAR
- **Description** (`description`) — optional
- **Cover / icon** (`cover`) — optional image; PNG/JPG/WEBP/GIF (a default 🧰 icon shows if omitted)

### Album photo (صورة ألبوم المدير) — form at `<base URL>/admin/album/new`
- ✱ **Image** (`image`) — required; PNG/JPG/WEBP/GIF
- **Caption** (`caption`) — optional short text shown under the photo

> **Why the field lists differ:** the types are ~90% the same flow, but each has
> its own required media — a book needs a cover, a video needs a source, a tool
> needs a download file, an article is mostly text. Collect only what its form
> actually accepts.

## Step 4 — Fill the form and submit

1. Navigate to the form route for the chosen type (from Step 3).
2. Fill each field with the values you collected. For file fields (cover, poster,
   video, document, image), upload the file the user provided.
3. Review the filled form with the user if anything looks ambiguous.
4. Submit. On success the site shows a green confirmation
   (e.g. "تم نشر … بنجاح") and redirects to the relevant library/home section.

## Step 5 — Verify it went live (do not skip)

Publishing isn't done until you've *seen* it. After submitting:

1. Navigate to where the new item should appear:
   - Article → `<base URL>/library#articles`
   - Video → `<base URL>/library#videos`
   - Book → `<base URL>/library#booklets`
   - Tool / template → `<base URL>/library#tools`
   - Album photo → `<base URL>/director/album`
2. Confirm the new entry is visible with the correct title and media.
3. Report back to the user: what was published, its type, and the URL where it
   now appears. If it's missing, say so plainly and check for a validation error
   (e.g. a missing required field or an unsupported file type).

## Quick reference — routes and required fields

| Type | Form route | Submits to | Required | Lands on |
|---|---|---|---|---|
| Article | `/admin/posts/new` | `POST /admin/posts` | title | `/library#articles` |
| Video | `/admin/videos/new` | `POST /admin/videos` | title + (url or file) | `/library#videos` |
| Book | `/admin/books/new` | `POST /admin/books` | title + cover | `/library#booklets` |
| Tool / template | `/admin/tools/new` | `POST /admin/tools` | title + file | `/library#tools` |
| Album photo | `/admin/album/new` | `POST /admin/album` | image | `/director/album` |

Allowed uploads: images `png/jpg/jpeg/webp/gif` · docs `pdf/doc/docx` ·
tool files `pdf/doc/docx/xls/xlsx/ppt/pptx/csv/txt/zip/rar` ·
video `mp4/webm/ogg/mov/m4v`.
