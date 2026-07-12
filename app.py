"""
مركز الدليل — Flask app.

Phase 2: structure (templates/ + static/, one base.html).
Phase 3 (in progress): the fridge (database) + first feature = publish books.

Kitchen model:
  app.py         = chef (routes = the gatekeeper/doorways)
  daleel.db      = fridge (memory: books, later messages/posts)
  templates/     = plate molds (Jinja)
  static/        = pantry (css/js/images) + uploads/ (admin-added files)
"""
import os
import re
import html
import uuid
import smtplib
import sqlite3
from email.message import EmailMessage
from functools import wraps
from datetime import datetime
from markupsafe import Markup

from flask import (
    Flask, render_template, request, redirect, url_for, abort, flash, jsonify,
    session, send_from_directory
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB + uploads are RELOCATABLE via env vars so they can live on a persistent disk
# (e.g. Render's /var/data) that survives redeploys. Default = in-project, which is
# exactly the old behaviour, so local dev + PythonAnywhere are unaffected.
DB_PATH = os.environ.get("DATABASE_PATH") or os.path.join(BASE_DIR, "daleel.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR") or os.path.join(BASE_DIR, "static", "uploads")

# what the gatekeeper accepts (the "laws" for incoming files)
ALLOWED_IMAGE = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_DOC = {"pdf", "doc", "docx"}
ALLOWED_VIDEO = {"mp4", "webm", "ogg", "mov", "m4v"}
# downloadable tools/templates accept a wider set (spreadsheets, slides, archives)
ALLOWED_TOOL = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
                "csv", "txt", "zip", "rar"}

app = Flask(__name__)
# signs the session cookie + flash messages. Set a strong value via env in prod.
app.secret_key = os.environ.get("SECRET_KEY", "dev-daleel-key-change-me")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Templates reference admin-uploaded files as "static/uploads/<name>". This more-
# specific route intercepts those URLs and serves them from UPLOAD_DIR wherever it
# lives — so uploads work even when UPLOAD_DIR is on a persistent disk OUTSIDE the
# project (Render). With the default UPLOAD_DIR it serves the same files as before.
@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


def to_embed(url):
    """Turn a YouTube/Vimeo *page* link into an inline-embed URL so the video
    plays ON the page (no jump to youtube.com). Returns None for other URLs."""
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]+)", url or "")
    if m:
        return "https://www.youtube.com/embed/" + m.group(1)
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)", url or "")
    if m:
        return "https://player.vimeo.com/video/" + m.group(1)
    return None


app.jinja_env.filters["embed"] = to_embed


def _inline(s):
    """Inline formatting inside a line. Escapes HTML first (safe), then applies:
    **bold** -> <strong>, ==highlight== -> gold <mark>."""
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"==(.+?)==", r'<mark class="hl">\1</mark>', s)
    return s


def render_article(text):
    """Turn the admin's simple markup into safe HTML (matches the toolbar):
       '### '  -> subheading      '> '  -> quote      '- '  -> bullet list
       blank line -> new paragraph      **bold**  ==highlight=="""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    out, para, items = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para.clear()

    def flush_list():
        if items:
            out.append("<ul>" + "".join("<li>%s</li>" % i for i in items) + "</ul>")
            items.clear()

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            flush_para(); flush_list(); continue
        if line.startswith("### "):
            flush_para(); flush_list()
            out.append("<h3>%s</h3>" % _inline(line[4:].strip()))
        elif line.startswith("> "):
            flush_para(); flush_list()
            out.append('<blockquote class="article-quote">%s</blockquote>'
                       % _inline(line[2:].strip()))
        elif line.startswith("- "):
            flush_para()
            items.append(_inline(line[2:].strip()))
        else:
            flush_list()
            para.append(line)
    flush_para(); flush_list()
    return Markup("".join(out))


app.jinja_env.filters["article"] = render_article

# ---- admin auth (single password -> signed session) -----------------------
# Password is read from the env and stored only as a HASH (never plaintext).
# Change it by setting ADMIN_PASSWORD before launching; default is for local dev.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "daleel2026")
ADMIN_HASH = generate_password_hash(ADMIN_PASSWORD)

# Safety net: loudly warn if the app is launched with the built-in dev secrets
# still in place. On a rented/public server you MUST set real values:
#   SECRET_KEY  and  ADMIN_PASSWORD  (see DEPLOY.md).
def _warn_if_insecure_defaults():
    problems = []
    if os.environ.get("SECRET_KEY") is None:
        problems.append("SECRET_KEY is using the built-in dev value")
    if os.environ.get("ADMIN_PASSWORD") is None:
        problems.append("ADMIN_PASSWORD is using the built-in dev value")
    if problems:
        print("  [!] SECURITY: " + "; ".join(problems) +
              ".\n      Fine for local dev — but SET THESE before going public "
              "(see DEPLOY.md).")


_warn_if_insecure_defaults()

# Article body uses simple markup: a line starting with "### " is a heading;
# blank lines separate paragraphs. The detail template renders it accordingly.
SEED_ARTICLE_BODY = """تُسهم مقاربات «نانسي كارترايت» في فلسفة العلم والسببية في إضاءة كيفية تشكّل الأثر داخل البيئات المعقّدة، ولا سيما في العمل الإنساني متعدد القطاعات. إذ تُبرز هذه المقاربات أنّ الفاعلية لا تُنتجها «قوانين عامة» مجرّدة بقدر ما ==تُشكّلها قدرات سببية تُفعَّل بشروط سياقية محدّدة==.

### ١. السببية المشروطة بالسياق
لا تعمل السببية –وفق كارترايت– في الفراغ؛ بل تتحدد نتائجها بتركيب الشروط المحيطة. في سياقات الإغاثة، تُدخل الفرق المتنوّعة تعدّدية في السياقات التفسيرية، ما يخفّض خطر «تعميم حلّ واحد» على مجتمعات متباينة.

### ٢. النماذج الواقعية بدل القوانين الكاسحة
تؤكد كارترايت أنّ **النماذج الجيدة تُحاكي تعقيد الواقع** أكثر من اعتمادها على «قوانين» شمولية. في العمل الإنساني، تصبح نظرية التغيير والمنطق الإطاري أكثر واقعية حين تُبنى بمشاركة مجتمعية وتمثيل تنوّع أصحاب المصلحة.

### ٣. «الميول/القدرات» وشروط التفعيل
تطرح كارترايت مفهوم القدرات السببية: عناصر تمتلك قابلية لإحداث أثر، لكنها لا تعمل إلا تحت شروط تمكينية مناسبة. وتحويل هذه القابليات إلى أثر يتطلب:

- تفويضاً واضحاً وقنوات قرار شفافة
- حماية نفسية للفريق
- أدوات عمل مناسبة وتعليماً مستمراً

تُظهر خبرة العمل الإنساني أنّ جمع خبرات متنوّعة شرطٌ لازم لكنه غير كافٍ. فالأثر الأعلى يتحقق عندما تُهيّأ شروط التفعيل المؤسسي لهذه الخبرات.

> الأثر لا يظهر إلا حين تتفاعل المكوّنات في سياق ملائم يطلق قدراتها السببية."""


def admin_required(view):
    """Gate for every editing action. Non-admins get redirected to login;
    the drag-save (JSON) endpoint gets a clean 401 instead of an HTML page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("is_admin"):
            return view(*args, **kwargs)
        # JSON drag-save endpoints get a clean 401; page routes redirect to login
        if request.endpoint and request.endpoint.endswith("_reorder"):
            return jsonify(ok=False, error="unauthorized"), 401
        return redirect(url_for("admin_login", next=request.path))
    return wrapped


@app.context_processor
def inject_admin():
    """Make `is_admin` available in every template (drives UI gating)."""
    return {"is_admin": bool(session.get("is_admin"))}


@app.errorhandler(404)
def error_404(e):
    return render_template("error.html", code="٤٠٤",
                           message="عذرًا، الصفحة التي تبحث عنها غير موجودة."), 404


@app.errorhandler(405)
def error_405(e):
    return render_template("error.html", code="",
                           message="تعذّر تنفيذ هذا الإجراء بهذه الطريقة. يرجى العودة والمحاولة من جديد."), 405


@app.errorhandler(500)
def error_500(e):
    return render_template("error.html", code="٥٠٠",
                           message="حدث خطأ غير متوقّع في الخادم. نعتذر عن ذلك — يرجى المحاولة بعد قليل."), 500


@app.context_processor
def inject_asset_version():
    """Cache-busting stamp for css/js: changes whenever the files change, so
    browsers always fetch the fresh version (no stale asset bugs)."""
    v = 0
    for f in ("static/css/style.css", "static/js/main.js"):
        try:
            v = max(v, int(os.path.getmtime(os.path.join(BASE_DIR, f))))
        except OSError:
            pass
    return {"ASSET_V": v}


# ------------------------------------------------------------------ fridge --
def get_db():
    """Open the fridge. Rows come back name-addressable (row['title'])."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the books shelf if missing, and seed it with the 4 existing
    booklets so nothing from Phase 1 is lost. Runs once, safely."""
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            cover       TEXT,          -- path relative to static/
            file        TEXT,          -- path relative to static/ (nullable)
            position    INTEGER,       -- display order (drag-to-reorder)
            created_at  TEXT
        )
        """
    )
    # migration: older DBs were created before 'position' existed -> add + backfill
    cols = [r[1] for r in conn.execute("PRAGMA table_info(books)")]
    if "position" not in cols:
        conn.execute("ALTER TABLE books ADD COLUMN position INTEGER")
        for i, r in enumerate(
            conn.execute("SELECT id FROM books ORDER BY id ASC").fetchall(), start=1
        ):
            conn.execute("UPDATE books SET position=? WHERE id=?", (i, r["id"]))

    # seed only if the shelf is empty
    count = conn.execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"]
    if count == 0:
        seed = [
            ("خبرات ميدانية من واقع العمل الإغاثي", "assets/img/book-3.jpg"),
            ("توظيف أوامر الذكاء الاصطناعي في المشروعات الإنسانية", "assets/img/book-2.jpg"),
            ("تقييم المشروعات الإنسانية", "assets/img/book-1.jpg"),
            ("إدارة المخاطر الأمنية أثناء التدخل الإنساني", "assets/img/book-4.jpg"),
            ("الاستثمار الاجتماعي المؤثر في العمل التنموي العربي", "assets/img/book-impact-investment.png"),
            ("١٤ خطوة لاستثمار اجتماعي ناجح", "assets/img/book-14-steps.jpg"),
            ("دليل تقدير احتياجات المستفيدين من خدمات الجمعيات الخيرية", "assets/img/book-needs-assessment.jpg"),
        ]
        now = datetime.utcnow().isoformat()
        conn.executemany(
            "INSERT INTO books (title, description, cover, file, position, created_at) "
            "VALUES (?, ?, ?, NULL, ?, ?)",
            [(t, "", cover, i, now) for i, (t, cover) in enumerate(seed, start=1)],
        )

    # ---- videos shelf ----
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            poster     TEXT,           -- optional cover image (path under static/)
            src_type   TEXT,           -- 'file' | 'url'
            src        TEXT,           -- static/ path (file) OR external URL
            position   INTEGER,
            created_at TEXT
        )
        """
    )
    if conn.execute("SELECT COUNT(*) AS n FROM videos").fetchone()["n"] == 0:
        conn.execute(
            "INSERT INTO videos (title, poster, src_type, src, position, created_at) "
            "VALUES (?, NULL, 'file', ?, 1, ?)",
            ("صياغة الأوامر الذكية باستخدام ChatGPT",
             "assets/video/lesson-chatgpt.mp4", datetime.utcnow().isoformat()),
        )

    # ---- "what's new" (جديدنا, home page) shelf ----
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            body       TEXT,           -- formatted text (same markup as articles)
            image      TEXT,           -- optional image (path under static/)
            src_type   TEXT,           -- video: 'file' | 'url' | NULL
            src        TEXT,
            position   INTEGER,
            created_at TEXT
        )
        """
    )

    # ---- main articles (المقالات page) shelf ----
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            author     TEXT,
            date       TEXT,           -- human display date
            image      TEXT,           -- cover image (path under static/)
            excerpt    TEXT,           -- listing summary
            body       TEXT,           -- full article text (paragraphs)
            position   INTEGER,
            created_at TEXT
        )
        """
    )
    if conn.execute("SELECT COUNT(*) AS n FROM posts").fetchone()["n"] == 0:
        conn.execute(
            "INSERT INTO posts (title, author, date, image, excerpt, body, position, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (
                "نظرية القدرات السببية عند نانسي كارترايت وتفعيل التنوع في فرق العمل الإنسانية",
                "د. جمال الجبوري – دكتوراه في إدارة الأعمال",
                "أكتوبر 3، 2025",
                "assets/img/article-teams.webp",
                "تُسهم مقاربات «نانسي كارترايت» في فلسفة العلم والسببية في إضاءة كيفية تشكّل الأثر داخل "
                "البيئات المعقّدة، ولا سيما في العمل الإنساني متعدد القطاعات …",
                SEED_ARTICLE_BODY,
                datetime.utcnow().isoformat(),
            ),
        )

    # ---- contact messages (from the اتصل بنا on-page form) ----
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT NOT NULL,
            subject    TEXT,
            body       TEXT NOT NULL,
            created_at TEXT
        )
        """
    )

    # ---- director photo album (مدير المركز) ----
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS album (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            image      TEXT NOT NULL,   -- path under static/
            caption    TEXT,            -- optional caption
            position   INTEGER,
            created_at TEXT
        )
        """
    )
    # seed with the existing sample photos so the album isn't empty on first run
    if conn.execute("SELECT COUNT(*) AS n FROM album").fetchone()["n"] == 0:
        seed_album = [
            "assets/img/IMG-2.png",
            "assets/img/2147785631-r.jpg",
            "assets/img/2148483874.jpg",
            "assets/img/2149300712-r.jpg",
            "assets/img/810-r5nujzk2.jpg",
            "assets/img/article-teams.webp",
        ]
        now = datetime.utcnow().isoformat()
        conn.executemany(
            "INSERT INTO album (image, caption, position, created_at) "
            "VALUES (?, NULL, ?, ?)",
            [(img, i, now) for i, img in enumerate(seed_album, start=1)],
        )

    # ---- downloadable tools & templates (أدوات ونماذج) shelf ----
    # Same admin-form pattern as books: title + optional cover + a download file.
    # No seed — the section starts empty (as it does now) until an admin adds one.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tools (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            cover       TEXT,          -- optional icon/cover (path under static/)
            file        TEXT,          -- the downloadable file (path under static/)
            position    INTEGER,       -- display order (drag-to-reorder)
            created_at  TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def _ordered(table):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM %s ORDER BY position IS NULL, position ASC, id ASC" % table
    ).fetchall()
    conn.close()
    return rows


def get_one(table, item_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM %s WHERE id = ?" % table, (item_id,)
    ).fetchone()
    conn.close()
    return row


def get_books():
    return _ordered("books")


def get_videos():
    return _ordered("videos")


def get_posts():
    return _ordered("posts")


def get_news():
    return _ordered("news")


def get_album():
    return _ordered("album")


def get_tools():
    return _ordered("tools")


def next_position(table):
    conn = get_db()
    p = conn.execute(
        "SELECT COALESCE(MAX(position), 0) + 1 AS p FROM %s" % table
    ).fetchone()["p"]
    conn.close()
    return p


def reorder_table(table):
    """Shared handler body for the drag-save endpoints."""
    data = request.get_json(silent=True) or {}
    order = data.get("order")
    if not isinstance(order, list) or not order:
        return jsonify(ok=False, error="bad order"), 400
    conn = get_db()
    for pos, item_id in enumerate(order, start=1):
        conn.execute(
            "UPDATE %s SET position=? WHERE id=?" % table, (pos, int(item_id))
        )
    conn.commit()
    conn.close()
    return jsonify(ok=True)


def allowed(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def remove_upload(rel_path):
    """Delete a file from static/uploads if it lives there. NEVER touches the
    shared seed images in assets/img (other pages may use them)."""
    if rel_path and rel_path.startswith("uploads/"):
        p = os.path.join(BASE_DIR, "static", rel_path)
        if os.path.exists(p):
            os.remove(p)


def save_upload(fileobj, allowed_set):
    """Save an uploaded file under static/uploads with a unique name.
    Returns the path relative to static/ (e.g. 'uploads/ab12.jpg') or None."""
    if not fileobj or fileobj.filename == "":
        return None
    if not allowed(fileobj.filename, allowed_set):
        return None
    ext = fileobj.filename.rsplit(".", 1)[1].lower()
    unique = f"{uuid.uuid4().hex}.{ext}"          # Arabic-safe unique name
    fileobj.save(os.path.join(UPLOAD_DIR, unique))
    return f"uploads/{unique}"


def take_upload(field, allowed_set, bad_type_msg):
    """Read an optional uploaded file. Returns (path, error_msg):
      - (None, None)  -> nothing was uploaded (fine for optional fields)
      - (None, msg)   -> a file WAS chosen but its type isn't allowed
      - (path, None)  -> saved OK
    Lets routes show a gentle in-form message instead of a raw 400."""
    f = request.files.get(field)
    if not f or not f.filename:
        return None, None
    path = save_upload(f, allowed_set)
    if not path:
        return None, bad_type_msg
    return path, None


# ------------------------------------------------------------------ routes --
@app.route("/")
def home():
    return render_template("index.html", news=get_news())


@app.route("/director")
def director():
    return render_template("director.html")


@app.route("/director/album")
def album():
    # مدير المركز — ألبوم الصور. تُدار من لوحة المشرف (إضافة/حذف/تبديل/ترتيب).
    return render_template("album.html", photos=get_album())


@app.route("/articles", methods=["GET", "POST"])
def articles():
    # المقالات now lives inside the library's "مقالات تعليمية" section.
    # Accept POST too so any stale/old form can't hit a 405.
    return redirect(url_for("library") + "#articles")


@app.route("/articles/<int:post_id>")
def post_detail(post_id):
    post = get_one("posts", post_id)
    if post is None:
        abort(404)
    return render_template("article_detail.html", post=post)


@app.route("/library")
def library():
    # OUT trip: pull each shelf from the fridge, hand them to the mold
    return render_template(
        "library.html",
        books=get_books(),
        videos=get_videos(),
        posts=get_posts(),
        tools=get_tools(),
    )


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def send_contact_email(name, email, subject, body):
    """Best-effort: forward a contact-form message to the center's inbox via SMTP.
    Credentials come ONLY from env vars (see DEPLOY.md) — never hardcoded. If SMTP
    is not configured, returns False and the message still lives safely in the DB."""
    server = os.environ.get("MAIL_SERVER")
    user = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    if not (server and user and password):
        return False  # not configured -> the DB copy is the record
    port = int(os.environ.get("MAIL_PORT", "465"))
    mail_to = os.environ.get("MAIL_TO", "info@daleelconsult.org")
    msg = EmailMessage()
    msg["Subject"] = "[موقع الدليل] " + (subject or "رسالة جديدة")
    msg["From"] = user
    msg["To"] = mail_to
    msg["Reply-To"] = email
    msg.set_content(
        "الاسم: %s\nالبريد: %s\nالموضوع: %s\n\n%s"
        % (name, email, subject or "-", body)
    )
    try:
        if port == 465:
            with smtplib.SMTP_SSL(server, port, timeout=10) as s:
                s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(server, port, timeout=10) as s:
                s.starttls()
                s.login(user, password)
                s.send_message(msg)
        return True
    except Exception:
        return False  # a delivery hiccup must not lose the message (DB has it)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # honeypot: bots auto-fill the hidden 'website' field; humans never see it
        if request.form.get("website"):
            return redirect(url_for("contact") + "#form")

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        body = (request.form.get("message") or "").strip()

        if not name or not EMAIL_RE.match(email) or not body:
            flash("يرجى إدخال الاسم وبريدٍ إلكتروني صحيح ونص الرسالة.", "error")
            return redirect(url_for("contact") + "#form")

        conn = get_db()
        conn.execute(
            "INSERT INTO messages (name, email, subject, body, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (name[:120], email[:160], subject[:200], body[:5000],
             datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

        send_contact_email(name, email, subject, body)  # best-effort forward
        flash("تم إرسال رسالتك بنجاح، سنعود إليك قريبًا. شكرًا لتواصلك معنا.",
              "success")
        return redirect(url_for("contact") + "#form")

    return render_template("contact.html")


# ----- admin auth (login / logout) ------------------------------------------

def safe_next(target):
    """Only allow redirects to a local path (blocks open-redirect attacks like
    ?next=http://evil.com). Anything not a plain '/path' falls back to library."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("library")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("library"))
    error = None
    nxt = request.values.get("next", "")
    if request.method == "POST":
        if check_password_hash(ADMIN_HASH, request.form.get("password", "")):
            session["is_admin"] = True
            flash("مرحبًا بك، تم تسجيل الدخول كمشرف.", "success")
            return redirect(safe_next(nxt))
        error = "كلمة المرور غير صحيحة."
    return render_template("admin_login.html", error=error, next=nxt)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("تم تسجيل الخروج.", "success")
    return redirect(url_for("library"))


@app.route("/admin/books/new")
@admin_required
def book_new():
    """Show the publish-a-book form (the '+' leads here)."""
    return render_template("admin_book_new.html")


@app.route("/admin/books", methods=["POST"])
@admin_required
def book_create():
    """IN trip: gatekeeper checks the submission, then store in the fridge."""
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not title:
        flash("يجب إدخال عنوان للكتاب.", "error")
        return redirect(url_for("book_new"))

    cover, err = take_upload(
        "cover", ALLOWED_IMAGE,
        "صيغة صورة الغلاف غير مدعومة. الصيغ المقبولة: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("book_new"))
    if not cover:
        flash("يجب إضافة صورة غلاف للكتاب.", "error")
        return redirect(url_for("book_new"))

    doc, err = take_upload(
        "file", ALLOWED_DOC,
        "صيغة الملف غير مدعومة. الصيغ المقبولة: PDF, DOC, DOCX.")
    if err:
        flash(err, "error"); return redirect(url_for("book_new"))

    conn = get_db()
    nextpos = (conn.execute(
        "SELECT COALESCE(MAX(position), 0) + 1 AS p FROM books"
    ).fetchone()["p"])
    conn.execute(
        "INSERT INTO books (title, description, cover, file, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, cover, doc, nextpos, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    flash("تم نشر الكتاب بنجاح.", "success")
    return redirect(url_for("library") + "#booklets")


@app.route("/admin/books/reorder", methods=["POST"])
@admin_required
def book_reorder():
    return reorder_table("books")


@app.route("/admin/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def book_delete(book_id):
    """Remove a book. POST-only (destructive). Also cleans its uploaded files."""
    conn = get_db()
    row = conn.execute(
        "SELECT cover, file FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    if row is None:
        conn.close()
        abort(404)
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    # tidy the disk (uploads only; seed images are left alone)
    remove_upload(row["cover"])
    remove_upload(row["file"])
    flash("تم حذف الكتاب.", "success")
    return redirect(url_for("library") + "#booklets")


# ----- admin: videos --------------------------------------------------------
@app.route("/admin/videos/new")
@admin_required
def video_new():
    return render_template("admin_video_new.html")


@app.route("/admin/videos", methods=["POST"])
@admin_required
def video_create():
    title = (request.form.get("title") or "").strip()
    url = (request.form.get("url") or "").strip()

    if not title:
        flash("يجب إدخال عنوان للفيديو.", "error")
        return redirect(url_for("video_new"))

    video_file, err = take_upload(
        "video", ALLOWED_VIDEO,
        "صيغة ملف الفيديو غير مدعومة. الصيغ المقبولة: MP4, WEBM, OGG, MOV, M4V.")
    if err:
        flash(err, "error"); return redirect(url_for("video_new"))

    if not video_file and not url:
        flash("أدخل رابط فيديو أو ارفع ملفًا (أحدهما مطلوب).", "error")
        return redirect(url_for("video_new"))

    poster, err = take_upload(
        "poster", ALLOWED_IMAGE,
        "صيغة صورة الغلاف غير مدعومة. الصيغ المقبولة: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("video_new"))

    src_type, src = ("file", video_file) if video_file else ("url", url)

    conn = get_db()
    conn.execute(
        "INSERT INTO videos (title, poster, src_type, src, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, poster, src_type, src, next_position("videos"),
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    flash("تم نشر الفيديو بنجاح.", "success")
    return redirect(url_for("library") + "#videos")


@app.route("/admin/videos/reorder", methods=["POST"])
@admin_required
def video_reorder():
    return reorder_table("videos")


@app.route("/admin/videos/<int:video_id>/delete", methods=["POST"])
@admin_required
def video_delete(video_id):
    conn = get_db()
    row = conn.execute(
        "SELECT poster, src_type, src FROM videos WHERE id = ?", (video_id,)
    ).fetchone()
    if row is None:
        conn.close()
        abort(404)
    conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()
    remove_upload(row["poster"])
    if row["src_type"] == "file":
        remove_upload(row["src"])
    flash("تم حذف الفيديو.", "success")
    return redirect(url_for("library") + "#videos")


# ============================================================================
#  MODIFY (edit-in-place) — books / videos
#  A new file replaces the old (and deletes it); leaving a file field empty
#  keeps the existing one. Text fields always update.
# ============================================================================
@app.route("/admin/books/<int:book_id>/edit")
@admin_required
def book_edit(book_id):
    item = get_one("books", book_id)
    if item is None:
        abort(404)
    return render_template("admin_book_new.html", item=item,
                           action=url_for("book_update", book_id=book_id))


@app.route("/admin/books/<int:book_id>", methods=["POST"])
@admin_required
def book_update(book_id):
    item = get_one("books", book_id)
    if item is None:
        abort(404)
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للكتاب.", "error")
        return redirect(url_for("book_edit", book_id=book_id))
    cover, err = take_upload("cover", ALLOWED_IMAGE,
                             "صيغة صورة الغلاف غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("book_edit", book_id=book_id))
    doc, err = take_upload("file", ALLOWED_DOC,
                           "صيغة الملف غير مدعومة. المقبول: PDF, DOC, DOCX.")
    if err:
        flash(err, "error"); return redirect(url_for("book_edit", book_id=book_id))
    new_cover = item["cover"]
    if cover:
        remove_upload(item["cover"]); new_cover = cover
    new_file = item["file"]
    if doc:
        remove_upload(item["file"]); new_file = doc
    conn = get_db()
    conn.execute("UPDATE books SET title=?, description=?, cover=?, file=? WHERE id=?",
                 (title, description, new_cover, new_file, book_id))
    conn.commit(); conn.close()
    flash("تم تحديث الكتاب.", "success")
    return redirect(url_for("library") + "#booklets")


@app.route("/admin/videos/<int:video_id>/edit")
@admin_required
def video_edit(video_id):
    item = get_one("videos", video_id)
    if item is None:
        abort(404)
    return render_template("admin_video_new.html", item=item,
                           action=url_for("video_update", video_id=video_id))


@app.route("/admin/videos/<int:video_id>", methods=["POST"])
@admin_required
def video_update(video_id):
    item = get_one("videos", video_id)
    if item is None:
        abort(404)
    title = (request.form.get("title") or "").strip()
    url = (request.form.get("url") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للفيديو.", "error")
        return redirect(url_for("video_edit", video_id=video_id))
    new_video, err = take_upload("video", ALLOWED_VIDEO,
                                 "صيغة ملف الفيديو غير مدعومة. المقبول: MP4, WEBM, OGG, MOV, M4V.")
    if err:
        flash(err, "error"); return redirect(url_for("video_edit", video_id=video_id))
    new_poster, err = take_upload("poster", ALLOWED_IMAGE,
                                  "صيغة صورة الغلاف غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("video_edit", video_id=video_id))

    # video: remove (checkbox) > replace (file/url) > keep
    src_type, src = item["src_type"], item["src"]
    if request.form.get("remove_video"):
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = None, None
    elif new_video:
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = "file", new_video
    elif url:
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = "url", url
    # poster: remove (checkbox) > replace (new upload) > keep
    poster = item["poster"]
    if request.form.get("remove_poster"):
        remove_upload(item["poster"]); poster = None
    elif new_poster:
        remove_upload(item["poster"]); poster = new_poster

    conn = get_db()
    conn.execute("UPDATE videos SET title=?, poster=?, src_type=?, src=? WHERE id=?",
                 (title, poster, src_type, src, video_id))
    conn.commit(); conn.close()
    flash("تم تحديث الفيديو.", "success")
    return redirect(url_for("library") + "#videos")


# ============================================================================
#  MAIN ARTICLES (المقالات page) — full CRUD + reorder, plugged into engine
# ============================================================================
def _post_form_values():
    return (
        (request.form.get("title") or "").strip(),
        (request.form.get("author") or "").strip(),
        (request.form.get("date") or "").strip(),
        (request.form.get("excerpt") or "").strip(),
        (request.form.get("body") or "").strip(),
    )


@app.route("/admin/posts/new")
@admin_required
def post_new():
    return render_template("admin_post_new.html")


@app.route("/admin/posts", methods=["POST"])
@admin_required
def post_create():
    title, author, date, excerpt, body = _post_form_values()
    if not title:
        flash("يجب إدخال عنوان للمقال.", "error")
        return redirect(url_for("post_new"))
    image, err = take_upload("image", ALLOWED_IMAGE,
                             "صيغة صورة المقال غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("post_new"))
    conn = get_db()
    conn.execute(
        "INSERT INTO posts (title, author, date, image, excerpt, body, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, author, date, image, excerpt, body, next_position("posts"),
         datetime.utcnow().isoformat()),
    )
    conn.commit(); conn.close()
    flash("تم نشر المقال بنجاح.", "success")
    return redirect(url_for("library") + "#articles")


@app.route("/admin/posts/<int:post_id>/edit")
@admin_required
def post_edit(post_id):
    item = get_one("posts", post_id)
    if item is None:
        abort(404)
    return render_template("admin_post_new.html", item=item,
                           action=url_for("post_update", post_id=post_id))


@app.route("/admin/posts/<int:post_id>", methods=["POST"])
@admin_required
def post_update(post_id):
    item = get_one("posts", post_id)
    if item is None:
        abort(404)
    title, author, date, excerpt, body = _post_form_values()
    if not title:
        flash("يجب إدخال عنوان للمقال.", "error")
        return redirect(url_for("post_edit", post_id=post_id))
    image, err = take_upload("image", ALLOWED_IMAGE,
                             "صيغة صورة المقال غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("post_edit", post_id=post_id))
    new_image = item["image"]
    if request.form.get("remove_image"):
        remove_upload(item["image"]); new_image = None
    elif image:
        remove_upload(item["image"]); new_image = image
    conn = get_db()
    conn.execute(
        "UPDATE posts SET title=?, author=?, date=?, image=?, excerpt=?, body=? WHERE id=?",
        (title, author, date, new_image, excerpt, body, post_id))
    conn.commit(); conn.close()
    flash("تم تحديث المقال.", "success")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/admin/posts/reorder", methods=["POST"])
@admin_required
def post_reorder():
    return reorder_table("posts")


@app.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
@admin_required
def post_delete(post_id):
    item = get_one("posts", post_id)
    if item is None:
        abort(404)
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit(); conn.close()
    remove_upload(item["image"])
    flash("تم حذف المقال.", "success")
    return redirect(url_for("library") + "#articles")


# ============================================================================
#  "WHAT'S NEW" (جديدنا, home page) — title + text (markup) + image/video
# ============================================================================
def _news_media(back):
    """Shared image+video handling for news create/update. Returns
    (image, src_type, src, error_response). image/src default None."""
    image, err = take_upload("image", ALLOWED_IMAGE,
                             "صيغة الصورة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        return None, None, None, err
    url = (request.form.get("url") or "").strip()
    vid, err = take_upload("video", ALLOWED_VIDEO,
                           "صيغة ملف الفيديو غير مدعومة. المقبول: MP4, WEBM, OGG, MOV, M4V.")
    if err:
        return None, None, None, err
    if vid:
        return image, "file", vid, None
    if url:
        return image, "url", url, None
    return image, None, None, None


@app.route("/admin/news/new")
@admin_required
def news_new():
    return render_template("admin_news_new.html")


@app.route("/admin/news", methods=["POST"])
@admin_required
def news_create():
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للخبر.", "error")
        return redirect(url_for("news_new"))
    image, src_type, src, err = _news_media("news_new")
    if err:
        flash(err, "error"); return redirect(url_for("news_new"))
    conn = get_db()
    conn.execute(
        "INSERT INTO news (title, body, image, src_type, src, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, body, image, src_type, src, next_position("news"),
         datetime.utcnow().isoformat()),
    )
    conn.commit(); conn.close()
    flash("تم نشر الخبر بنجاح.", "success")
    return redirect(url_for("home") + "#news")


@app.route("/admin/news/<int:news_id>/edit")
@admin_required
def news_edit(news_id):
    item = get_one("news", news_id)
    if item is None:
        abort(404)
    return render_template("admin_news_new.html", item=item,
                           action=url_for("news_update", news_id=news_id))


@app.route("/admin/news/<int:news_id>", methods=["POST"])
@admin_required
def news_update(news_id):
    item = get_one("news", news_id)
    if item is None:
        abort(404)
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للخبر.", "error")
        return redirect(url_for("news_edit", news_id=news_id))
    new_image, err = take_upload("image", ALLOWED_IMAGE,
                                 "صيغة الصورة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("news_edit", news_id=news_id))
    url = (request.form.get("url") or "").strip()
    new_vid, err = take_upload("video", ALLOWED_VIDEO,
                               "صيغة ملف الفيديو غير مدعومة. المقبول: MP4, WEBM, OGG, MOV, M4V.")
    if err:
        flash(err, "error"); return redirect(url_for("news_edit", news_id=news_id))

    # image: remove (checkbox) > replace (new upload) > keep
    image = item["image"]
    if request.form.get("remove_image"):
        remove_upload(item["image"]); image = None
    elif new_image:
        remove_upload(item["image"]); image = new_image
    # video: remove (checkbox) > replace (file/url) > keep
    src_type, src = item["src_type"], item["src"]
    if request.form.get("remove_video"):
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = None, None
    elif new_vid:
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = "file", new_vid
    elif url:
        if item["src_type"] == "file":
            remove_upload(item["src"])
        src_type, src = "url", url

    conn = get_db()
    conn.execute("UPDATE news SET title=?, body=?, image=?, src_type=?, src=? WHERE id=?",
                 (title, body, image, src_type, src, news_id))
    conn.commit(); conn.close()
    flash("تم تحديث الخبر.", "success")
    return redirect(url_for("home") + "#news")


@app.route("/admin/news/reorder", methods=["POST"])
@admin_required
def news_reorder():
    return reorder_table("news")


@app.route("/admin/news/<int:news_id>/delete", methods=["POST"])
@admin_required
def news_delete(news_id):
    item = get_one("news", news_id)
    if item is None:
        abort(404)
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit(); conn.close()
    remove_upload(item["image"])
    if item["src_type"] == "file":
        remove_upload(item["src"])
    flash("تم حذف الخبر.", "success")
    return redirect(url_for("home") + "#news")


# ============================================================================
#  DIRECTOR ALBUM (ألبوم مدير المركز) — add / delete / replace / reorder
#  Same admin-form pattern as books; each entry is one image + optional caption.
# ============================================================================
@app.route("/admin/album/new")
@admin_required
def album_new():
    return render_template("admin_album_new.html")


@app.route("/admin/album", methods=["POST"])
@admin_required
def album_create():
    caption = (request.form.get("caption") or "").strip()
    image, err = take_upload("image", ALLOWED_IMAGE,
                             "صيغة الصورة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("album_new"))
    if not image:
        flash("يجب اختيار صورة.", "error"); return redirect(url_for("album_new"))
    conn = get_db()
    conn.execute(
        "INSERT INTO album (image, caption, position, created_at) VALUES (?, ?, ?, ?)",
        (image, caption, next_position("album"), datetime.utcnow().isoformat()),
    )
    conn.commit(); conn.close()
    flash("تمت إضافة الصورة بنجاح.", "success")
    return redirect(url_for("album"))


@app.route("/admin/album/reorder", methods=["POST"])
@admin_required
def album_reorder():
    return reorder_table("album")


@app.route("/admin/album/<int:photo_id>/delete", methods=["POST"])
@admin_required
def album_delete(photo_id):
    item = get_one("album", photo_id)
    if item is None:
        abort(404)
    conn = get_db()
    conn.execute("DELETE FROM album WHERE id = ?", (photo_id,))
    conn.commit(); conn.close()
    remove_upload(item["image"])  # uploads only; shared seed images are left alone
    flash("تم حذف الصورة.", "success")
    return redirect(url_for("album"))


@app.route("/admin/album/<int:photo_id>/edit")
@admin_required
def album_edit(photo_id):
    item = get_one("album", photo_id)
    if item is None:
        abort(404)
    return render_template("admin_album_new.html", item=item,
                           action=url_for("album_update", photo_id=photo_id))


@app.route("/admin/album/<int:photo_id>", methods=["POST"])
@admin_required
def album_update(photo_id):
    item = get_one("album", photo_id)
    if item is None:
        abort(404)
    caption = (request.form.get("caption") or "").strip()
    image, err = take_upload("image", ALLOWED_IMAGE,
                             "صيغة الصورة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("album_edit", photo_id=photo_id))
    new_image = item["image"]
    if image:  # a new file replaces the old (leaving it empty keeps the current one)
        remove_upload(item["image"]); new_image = image
    conn = get_db()
    conn.execute("UPDATE album SET image=?, caption=? WHERE id=?",
                 (new_image, caption, photo_id))
    conn.commit(); conn.close()
    flash("تم تحديث الصورة.", "success")
    return redirect(url_for("album"))


# ============================================================================
#  TOOLS & TEMPLATES (أدوات ونماذج قابلة للتحميل) — add / edit / delete / reorder
#  Same admin-form pattern as books: title + optional cover + a download file.
#  The download file is the point of this section, so it is the required media.
# ============================================================================
@app.route("/admin/tools/new")
@admin_required
def tool_new():
    """Show the add-a-tool form (the '+' leads here)."""
    return render_template("admin_tool_new.html")


@app.route("/admin/tools", methods=["POST"])
@admin_required
def tool_create():
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للأداة أو النموذج.", "error")
        return redirect(url_for("tool_new"))

    doc, err = take_upload(
        "file", ALLOWED_TOOL,
        "صيغة الملف غير مدعومة. المقبول: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, CSV, TXT, ZIP, RAR.")
    if err:
        flash(err, "error"); return redirect(url_for("tool_new"))
    if not doc:
        flash("يجب إرفاق ملف للتحميل.", "error")
        return redirect(url_for("tool_new"))

    cover, err = take_upload(
        "cover", ALLOWED_IMAGE,
        "صيغة صورة الأيقونة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("tool_new"))

    conn = get_db()
    conn.execute(
        "INSERT INTO tools (title, description, cover, file, position, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, cover, doc, next_position("tools"),
         datetime.utcnow().isoformat()),
    )
    conn.commit(); conn.close()
    flash("تمت إضافة الأداة بنجاح.", "success")
    return redirect(url_for("library") + "#tools")


@app.route("/admin/tools/<int:tool_id>/edit")
@admin_required
def tool_edit(tool_id):
    item = get_one("tools", tool_id)
    if item is None:
        abort(404)
    return render_template("admin_tool_new.html", item=item,
                           action=url_for("tool_update", tool_id=tool_id))


@app.route("/admin/tools/<int:tool_id>", methods=["POST"])
@admin_required
def tool_update(tool_id):
    item = get_one("tools", tool_id)
    if item is None:
        abort(404)
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not title:
        flash("يجب إدخال عنوان للأداة أو النموذج.", "error")
        return redirect(url_for("tool_edit", tool_id=tool_id))
    doc, err = take_upload(
        "file", ALLOWED_TOOL,
        "صيغة الملف غير مدعومة. المقبول: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, CSV, TXT, ZIP, RAR.")
    if err:
        flash(err, "error"); return redirect(url_for("tool_edit", tool_id=tool_id))
    cover, err = take_upload(
        "cover", ALLOWED_IMAGE,
        "صيغة صورة الأيقونة غير مدعومة. المقبول: PNG, JPG, WEBP, GIF.")
    if err:
        flash(err, "error"); return redirect(url_for("tool_edit", tool_id=tool_id))
    # a new file replaces the old (leaving the field empty keeps the current one)
    new_file = item["file"]
    if doc:
        remove_upload(item["file"]); new_file = doc
    # cover: remove (checkbox) > replace (new upload) > keep
    new_cover = item["cover"]
    if request.form.get("remove_cover"):
        remove_upload(item["cover"]); new_cover = None
    elif cover:
        remove_upload(item["cover"]); new_cover = cover
    conn = get_db()
    conn.execute("UPDATE tools SET title=?, description=?, cover=?, file=? WHERE id=?",
                 (title, description, new_cover, new_file, tool_id))
    conn.commit(); conn.close()
    flash("تم تحديث الأداة.", "success")
    return redirect(url_for("library") + "#tools")


@app.route("/admin/tools/reorder", methods=["POST"])
@admin_required
def tool_reorder():
    return reorder_table("tools")


@app.route("/admin/tools/<int:tool_id>/delete", methods=["POST"])
@admin_required
def tool_delete(tool_id):
    item = get_one("tools", tool_id)
    if item is None:
        abort(404)
    conn = get_db()
    conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    conn.commit(); conn.close()
    # tidy the disk (uploads only; shared seed images are left alone)
    remove_upload(item["cover"])
    remove_upload(item["file"])
    flash("تم حذف الأداة.", "success")
    return redirect(url_for("library") + "#tools")


# Ensure the database + all tables exist however the app is launched
# (python app.py, flask run, gunicorn, a fresh download, etc.).
# Safe to run every time: CREATE TABLE IF NOT EXISTS + seed-only-if-empty.
init_db()


if __name__ == "__main__":
    # `python app.py` = the LOCAL DEVELOPMENT server (Flask's built-in).
    # It is NOT for public/production use — on a rented server run a real WSGI
    # server instead (see DEPLOY.md: waitress on Windows, gunicorn on Linux).
    #
    # debug is OFF by default (safe). Turn it on only for local work with
    #   set FLASK_DEBUG=1   (Windows)   then   python app.py
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=debug, host="0.0.0.0", port=port)
