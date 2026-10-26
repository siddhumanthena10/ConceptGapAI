import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash, abort
from werkzeug.utils import secure_filename

BASE = os.path.abspath(os.path.dirname(__file__))
# Set DATA_DIR=/data when using a persistent disk; otherwise deployment storage is temporary.
DATA_DIR = os.environ.get("DATA_DIR", BASE)
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "conceptgap.db")
UPLOADS = os.path.join(DATA_DIR, "uploads")
ALLOWED = {"pdf", "doc", "docx", "ppt", "pptx", "txt"}

app = Flask(__name__)
app.secret_key = os.environ.get("CONCEPTGAP_SECRET_KEY", "local-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
os.makedirs(UPLOADS, exist_ok=True)

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        branch TEXT NOT NULL DEFAULT 'CME', pattern TEXT NOT NULL DEFAULT 'C23',
        year INTEGER NOT NULL DEFAULT 1, semester INTEGER NOT NULL DEFAULT 1,
        subject TEXT DEFAULT '', resource_type TEXT NOT NULL DEFAULT 'Study Material',
        session_year TEXT DEFAULT '', source_url TEXT DEFAULT '', filename TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)""")
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
        if not c.execute("SELECT id FROM admins WHERE username=?", (admin_username,)).fetchone():
            c.execute("INSERT INTO admins(username,password) VALUES(?,?)", (admin_username, admin_password))

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if not session.get("admin"): return redirect(url_for("admin_login"))
        return fn(*a, **kw)
    return wrapped

@app.route("/")
def index():
    with db() as c: count = c.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    return render_template("index.html", resource_count=count)

@app.route("/library")
def library():
    f = {k: request.args.get(k, "").strip() for k in ("q","branch","pattern","year","semester","resource_type")}
    sql, args = "SELECT * FROM resources WHERE 1=1", []
    for k in ("branch","pattern","resource_type"):
        if f[k]: sql += f" AND {k}=?"; args.append(f[k])
    for k in ("year","semester"):
        if f[k].isdigit(): sql += f" AND {k}=?"; args.append(int(f[k]))
    if f["q"]:
        sql += " AND (title LIKE ? OR subject LIKE ? OR session_year LIKE ?)"
        term = "%" + f["q"] + "%"
        args += [term,term,term]
    sql += " ORDER BY pattern,branch,year,semester,title"
    with db() as c: rows = c.execute(sql,args).fetchall()
    return render_template("library.html", resources=rows, filters=f)

@app.route("/resource/<int:rid>/download")
def download(rid):
    with db() as c: r = c.execute("SELECT * FROM resources WHERE id=?", (rid,)).fetchone()
    if not r: abort(404)
    if r["filename"]: return send_from_directory(UPLOADS, r["filename"], as_attachment=True)
    if r["source_url"].startswith(("https://","http://")): return redirect(r["source_url"])
    abort(404)

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        with db() as c:
            r = c.execute("SELECT * FROM admins WHERE username=? AND password=?",
                          (request.form.get("username","").strip(), request.form.get("password",""))).fetchone()
        if r:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET","POST"])
@login_required
def admin():
    if request.method == "POST":
        title = request.form.get("title","").strip()
        branch, pattern = request.form.get("branch","CME"), request.form.get("pattern","C23")
        year, sem = request.form.get("year","1"), request.form.get("semester","1")
        subject = request.form.get("subject","").strip()
        typ = request.form.get("resource_type","Previous Paper")
        session_year = request.form.get("session_year","").strip()
        source = request.form.get("source_url","").strip()
        upload = request.files.get("file")
        filename = ""
        if upload and upload.filename:
            ext = upload.filename.rsplit(".",1)[-1].lower() if "." in upload.filename else ""
            if ext not in ALLOWED:
                flash("Unsupported file type. Use PDF, DOC, DOCX, PPT, PPTX or TXT.", "error")
                return redirect(url_for("admin"))
            filename = secure_filename(upload.filename)
            stem, suffix = os.path.splitext(filename)
            n, candidate = 1, filename
            while os.path.exists(os.path.join(UPLOADS,candidate)):
                candidate = f"{stem}_{n}{suffix}"; n += 1
            filename = candidate
            upload.save(os.path.join(UPLOADS,filename)); source = ""
        if not title or (not filename and not source.startswith(("http://","https://"))):
            flash("Enter a title and upload a file or provide an http/https URL.", "error")
            return redirect(url_for("admin"))
        if not year.isdigit() or not sem.isdigit() or int(year) not in (1,2,3) or int(sem) not in range(1,7):
            flash("Choose a valid year and semester.", "error")
            return redirect(url_for("admin"))
        with db() as c:
            c.execute("""INSERT INTO resources(title,branch,pattern,year,semester,subject,resource_type,session_year,source_url,filename)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (title,branch,pattern,int(year),int(sem),subject,typ,session_year,source,filename))
        flash("Resource added.", "success")
        return redirect(url_for("admin"))
    with db() as c: rows = c.execute("SELECT * FROM resources ORDER BY id DESC").fetchall()
    return render_template("admin.html", resources=rows)

@app.route("/admin/delete/<int:rid>", methods=["POST"])
@login_required
def delete(rid):
    with db() as c:
        r = c.execute("SELECT * FROM resources WHERE id=?", (rid,)).fetchone()
        if r:
            if r["filename"]:
                p = os.path.join(UPLOADS,r["filename"])
                if os.path.isfile(p): os.remove(p)
            c.execute("DELETE FROM resources WHERE id=?", (rid,))
    return redirect(url_for("admin"))

@app.errorhandler(413)
def too_large(e): return "File too large. Maximum size is 15 MB.", 413

@app.errorhandler(404)
def missing(e): return render_template("404.html"), 404

init_db()
if __name__ == "__main__":
    app.run(debug=True)
