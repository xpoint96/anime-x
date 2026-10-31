from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sqlite3
import urllib.parse
import urllib.request
from functools import wraps
from math import ceil
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from catalog import (
    BY_ID,
    CATALOG,
    COLLECTIONS,
    GENRES,
    KINDS,
    REVIEWS,
    SEASONS,
    SORTS,
    STATUSES,
    apply_filters,
)
PER_PAGE = 24
ROOT = Path(__file__).parent
DB_PATH = ROOT / "users.db"
TELEGRAM_URL = os.environ.get("TELEGRAM_URL", "https://t.me/+tbN-LPPGnjZjODg6")
VK_CLIENT_ID = os.environ.get("VK_CLIENT_ID", "")
VK_REDIRECT_URI = os.environ.get("VK_REDIRECT_URI", "")
CATALOG_PAGES = max(1, ceil(len(CATALOG) / PER_PAGE))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "anime-x-dev-key")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: object) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            vk_id TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


init_db()


@app.template_global()
def catalog_url(page: int) -> str:
    args = request.args.to_dict(flat=True)
    args["page"] = page
    return url_for(request.endpoint or "catalog_page", **args)


@app.context_processor
def inject_globals() -> dict:
    user = None
    if session.get("user_id"):
        user = get_db().execute(
            "SELECT * FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
    return {
        "current_user": user,
        "telegram_url": TELEGRAM_URL,
        "genres": GENRES,
        "kinds": ["все", *KINDS],
        "seasons": ["все", *SEASONS],
        "statuses": ["все", *STATUSES],
        "sorts": SORTS,
        "catalog_total": len(CATALOG),
        "catalog_pages": CATALOG_PAGES,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def paginate(items: list, page: int) -> tuple[list, dict]:
    pages = max(1, ceil(len(items) / PER_PAGE))
    page = min(max(page, 1), pages)
    start = (page - 1) * PER_PAGE
    meta = {
        "page": page,
        "pages": pages,
        "total": len(items),
        "shown": min(PER_PAGE, len(items) - start),
    }
    return items[start : start + PER_PAGE], meta


def query_catalog() -> tuple[list, dict, dict]:
    filters = {
        "q": request.args.get("q", ""),
        "kind": request.args.get("kind", "все"),
        "season": request.args.get("season", "все"),
        "genre": request.args.get("genre", "все"),
        "exclude": request.args.get("exclude", "нет"),
        "status": request.args.get("status", "все"),
        "sort": request.args.get("sort", "new"),
        "page": int(request.args.get("page", 1) or 1),
    }
    filtered = apply_filters(
        CATALOG,
        query=filters["q"],
        kind=filters["kind"],
        season=filters["season"],
        genre=filters["genre"],
        exclude=filters["exclude"],
        status=filters["status"],
        sort=filters["sort"],
    )
    page_items, meta = paginate(filtered, filters["page"])
    return page_items, meta, filters


@app.get("/")
def home():
    newest = CATALOG[:12]
    fresh = [item for item in CATALOG if item["new"]][:8]
    top10 = sorted(CATALOG, key=lambda item: item["rating"], reverse=True)[:10]
    return render_template(
        "home.html",
        newest=newest,
        fresh=fresh,
        top10=top10,
        collections=COLLECTIONS,
        reviews=REVIEWS,
        pages=CATALOG_PAGES,
    )


@app.get("/anonsy")
def anonsy():
    items, meta, filters = query_catalog()
    return render_template(
        "catalog.html",
        items=items,
        meta=meta,
        filters=filters,
        heading="Аниме которые скоро выйдут",
    )


@app.get("/catalog")
def catalog_page():
    items, meta, filters = query_catalog()
    return render_template(
        "catalog.html",
        items=items,
        meta=meta,
        filters=filters,
        heading="Каталог аниме",
    )


@app.get("/title/<int:item_id>")
def title_page(item_id: int):
    item = BY_ID.get(item_id)
    if not item:
        return redirect(url_for("catalog_page"))
    related = [row for row in CATALOG if row["genre"] == item["genre"] and row["id"] != item_id][:6]
    return render_template("title.html", item=item, related=related)


@app.get("/collections")
def collections_page():
    packs = []
    for pack in COLLECTIONS:
        titles = [BY_ID[i] for i in pack["ids"] if i in BY_ID]
        packs.append({**pack, "items": titles})
    return render_template("collections.html", packs=packs)


@app.get("/collections/<slug>")
def collection_detail(slug: str):
    pack = next((row for row in COLLECTIONS if row["slug"] == slug), None)
    if not pack:
        return redirect(url_for("collections_page"))
    items = [BY_ID[i] for i in pack["ids"] if i in BY_ID]
    return render_template("collection.html", pack=pack, items=items)


@app.get("/reviews")
def reviews_page():
    return render_template("reviews.html", reviews=REVIEWS)


@app.get("/top")
def top_page():
    top10 = sorted(CATALOG, key=lambda item: item["rating"], reverse=True)[:10]
    return render_template("top.html", top10=top10)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.args.get("forgot"):
        flash("Сброс пароля пока недоступен — напиши в Telegram.")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
        if row and row["password_hash"] and check_password_hash(row["password_hash"], password):
            if not request.form.get("no_remember"):
                session.permanent = True
            session["user_id"] = row["id"]
            return redirect(request.args.get("next") or url_for("profile"))
        flash("Неверный логин или пароль.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if password2 and password != password2:
            flash("Пароли не совпадают.")
        elif len(name) < 3 or len(password) < 4:
            flash("Имя от 3 символов, пароль от 4.")
        else:
            try:
                db = get_db()
                cur = db.execute(
                    "INSERT INTO users (name, password_hash) VALUES (?, ?)",
                    (name, generate_password_hash(password)),
                )
                db.commit()
                session["user_id"] = cur.lastrowid
                return redirect(url_for("profile"))
            except sqlite3.IntegrityError:
                flash("Такой профиль уже есть.")
    return render_template("register.html")


def _vk_post(url: str, fields: dict) -> dict:
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def vk_redirect_uri() -> str:
    return VK_REDIRECT_URI or url_for("auth_vk_callback", _external=True)


@app.route("/auth/vk", methods=["GET", "POST"])
def auth_vk():
    if not VK_CLIENT_ID:
        flash("Вход через VK ещё не настроен: нужен ID приложения VK.")
        return redirect(url_for("home"))
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    state = secrets.token_urlsafe(32)
    session["vk_verifier"] = verifier
    session["vk_state"] = state
    params = {
        "response_type": "code",
        "client_id": VK_CLIENT_ID,
        "redirect_uri": vk_redirect_uri(),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "scope": "vkid.personal_info",
    }
    return redirect("https://id.vk.ru/authorize?" + urllib.parse.urlencode(params))


@app.get("/auth/vk/callback")
def auth_vk_callback():
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    device_id = request.args.get("device_id", "")
    verifier = session.pop("vk_verifier", None)
    expected = session.pop("vk_state", None)
    if not code or not verifier or state != expected:
        flash("VK не подтвердил вход. Попробуй ещё раз.")
        return redirect(url_for("home"))
    try:
        tokens = _vk_post(
            "https://id.vk.ru/oauth2/auth",
            {
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": verifier,
                "client_id": VK_CLIENT_ID,
                "device_id": device_id,
                "redirect_uri": vk_redirect_uri(),
                "state": state,
            },
        )
        info = _vk_post(
            "https://id.vk.ru/oauth2/user_info",
            {"client_id": VK_CLIENT_ID, "access_token": tokens["access_token"]},
        )
    except Exception:
        flash("Не получилось связаться с VK.")
        return redirect(url_for("home"))

    user = info.get("user") or {}
    vk_id = f"vk{user.get('user_id', '')}"
    display = " ".join(p for p in [user.get("first_name"), user.get("last_name")] if p) or vk_id
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE vk_id = ?", (vk_id,)).fetchone()
    if row:
        user_id = row["id"]
    else:
        name = display
        if db.execute("SELECT 1 FROM users WHERE name = ?", (name,)).fetchone():
            name = f"{display} ({user.get('user_id')})"
        cur = db.execute("INSERT INTO users (name, vk_id) VALUES (?, ?)", (name, vk_id))
        db.commit()
        user_id = cur.lastrowid
    session["user_id"] = user_id
    flash("Вход через VK выполнен.")
    return redirect(url_for("profile"))


@app.post("/auth/yandex")
def auth_yandex():
    name = f"ya_{os.urandom(3).hex()}"
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (name, vk_id) VALUES (?, ?)",
        (name, f"ya{os.urandom(4).hex()}"),
    )
    db.commit()
    session["user_id"] = cur.lastrowid
    flash("Профиль создан через Яндекс.")
    return redirect(url_for("profile"))


@app.get("/logout")
def logout():
    session.clear()
    flash("Ты вышел. Нажми 👤 — откроются вход и регистрация.")
    return redirect(url_for("home"))


@app.get("/profile")
@login_required
def profile():
    return render_template("profile.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5555, debug=True)
