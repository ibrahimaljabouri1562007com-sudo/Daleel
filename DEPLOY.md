# 🚀 DEPLOY.md — Taking مركز الدليل (Al-Daleel) live

A plain-language, copy-paste checklist for putting this site on a **rented public
server** and updating it safely afterwards.

There are **two roads** for changing the live site — keep them straight:

| Road | What changes | Who | How | Speed |
|------|--------------|-----|-----|-------|
| **1. Content** | books, articles, uploads | the **website admin** | logs into the site in a browser (password) | instant, live |
| **2. Code** | design, Flask features, `app.py`, templates | **you (developer)** | `git push` → server `git pull` → **restart** | after restart |

The database (`daleel.db`) and `static/uploads/` are **gitignored**, so Road 2
(pushing code) **never wipes** the content the admin added on Road 1. ✅

---

## Part A — One-time server setup (first launch)

### 1. Rent a server & get in
- Beginner-friendly hosts (recommended, handle HTTPS for you): **Render, Railway, PythonAnywhere**.
- Full control: a **VPS** (DigitalOcean, Hetzner, Linode) — you get raw SSH.

On a VPS you connect from your laptop's terminal with the key/credentials the host gives you:
```bash
ssh youruser@YOUR_SERVER_IP
```
An **SSH key** (a secret file on your laptop) is the preferred "password" for this — set one up in the host's dashboard and it logs you in automatically.

### 2. Install Python (if the server doesn't have it)
```bash
python3 --version        # check. If missing, install via the server's package manager
```

### 3. Get the code onto the server
```bash
git clone https://github.com/ibrahimaljabouri1562007com-sudo/Daleel.git
cd Daleel
```

### 4. Install dependencies
```bash
pip install -r requirements.txt      # Flask + MarkupSafe + waitress
```

### 5. 🔐 Set the production secrets (CRITICAL — do NOT skip)
The app warns you at startup if these are missing. Set **real** values, never the dev defaults:

**Linux / macOS:**
```bash
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_PASSWORD="a-strong-password-you-choose"
```
**Windows (PowerShell) — if the server is Windows:**
```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:ADMIN_PASSWORD = "a-strong-password-you-choose"
```
> These live on the **server only** — never commit them to GitHub (the repo is public).
> For a permanent setup put them in the host's "Environment Variables" panel, or a
> `.env`/systemd service file, so they survive reboots.

### 5b. 📧 Email setup — REQUIRED for the اتصل بنا contact form
The on-page contact form **already works** and saves every message to the database.
But to also **deliver those messages to an inbox** (e.g. the Daleel Gmail), you must
set SMTP env vars. **Until you do, messages are stored but NOT emailed.**

Set these on the server (same way as the secrets above):
```
MAIL_SERVER    = smtp.gmail.com      # Gmail (or your provider's SMTP host)
MAIL_PORT      = 465                 # 465 = SSL (default), or 587 = STARTTLS
MAIL_USERNAME  = daleel-account@gmail.com
MAIL_PASSWORD  = <16-char Google App Password>   # NOT the real Gmail password
MAIL_TO        = info@daleelconsult.org          # where you read the messages
```

**⚠️ Gmail needs a Google "App Password" — the real password will NOT work:**
1. Sign in to the Daleel Google account.
2. Turn ON **2-Step Verification** (Google Account → Security). App Passwords require it.
3. Go to **Google Account → Security → App passwords**.
4. Create one named e.g. "Daleel website" → Google shows a **16-character code**.
5. Use that code as `MAIL_PASSWORD`.

An App Password only permits sending mail and can be revoked anytime without changing
the account's real password. When set, form submissions are emailed to `MAIL_TO`
(with the visitor's address as Reply-To, so you can reply straight to them).

### 6. Run it with the PRODUCTION server (not `python app.py`)
`python app.py` is the **development** server (single-user, not for the public).
Use **waitress** instead — it's in requirements.txt and works on Windows & Linux:
```bash
waitress-serve --host=0.0.0.0 --port=8000 app:app
```
(On Linux you can alternatively `pip install gunicorn` then `gunicorn -b 0.0.0.0:8000 app:app`.)

### 7. HTTPS (the 🔒 padlock)
Because the admin types a password, the site should be `https://`.
- Beginner hosts (Render/Railway/PythonAnywhere): **free & automatic** — nothing to do.
- VPS: put **nginx + Let's Encrypt (certbot)** in front of waitress.

---

## Part B — The forever update cycle (Road 2: shipping a code change)

Every time you change design or a Flask feature:

**On your laptop:**
```powershell
git add .
git commit -m "describe the change"
git push                       # goes to GitHub
```

**On the server terminal (ssh in first):**
```bash
cd Daleel
git pull                       # download the new code (leaves daleel.db untouched)
# then RESTART the app so it loads the new code:
#   stop the running waitress process, then start it again (step A6)
```
> The **restart is essential** — a running app holds the OLD code in memory until
> restarted. Pull without restart = public still sees the old version. 🔄

---

## Part C — Protect the admin's content 💾
- `daleel.db` + `static/uploads/` are gitignored → deploys never touch them.
- **Back them up regularly** — just copy the files somewhere safe:
```bash
cp daleel.db  daleel.backup.db
```

---

## Quick pre-launch checklist ☑️
- [ ] Server rented, SSH access working
- [ ] `git clone` done on the server
- [ ] `pip install -r requirements.txt` done
- [ ] `SECRET_KEY` set to a real random value (no startup warning)
- [ ] `ADMIN_PASSWORD` set to a strong password (no startup warning)
- [ ] 📧 Email: `MAIL_*` env vars set + Google **App Password** created (contact form delivers)
- [ ] Running via **waitress**, not `python app.py`
- [ ] HTTPS active (padlock shows)
- [ ] Admin can log in & add a book (Road 1 works)
- [ ] A test `git push` → server `git pull` → restart shows the change (Road 2 works)
- [ ] `daleel.db` backup taken
