"""Just A Game - Athlete Adaptability Tracking.

A small, dependency-free web app (Python standard library only) that gives
coaches a place to log athlete activity and record Measurement Games test
results, and gives participants a portal to see their own progress, test
results and points.

Run locally:
    python3 app.py
Then open http://localhost:8000

See README.md for deployment options and customisation notes.
"""
import os
import sys
import datetime
from wsgiref.simple_server import WSGIRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Router, Response, App, redirect
from urllib.parse import urlencode
import db
from auth import verify_password, hash_password, new_session_token, generate_temp_password
from constants import APP_NAME, all_measurement_games
import views

router = Router()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

SESSION_COOKIE = "jag_session"


# ---------------------------------------------------------------- helpers --

def get_current_user(req):
    token = req.get_cookie(SESSION_COOKIE)
    if not token:
        return None
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.session_id = ?",
            (token,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def require_role(req, role):
    user = get_current_user(req)
    if not user or user["role"] != role:
        return None
    return user


def require_admin(req):
    """Returns the coach user dict if logged in as coach AND is_admin=1, else None."""
    user = get_current_user(req)
    if not user or user["role"] != "coach" or not user.get("is_admin"):
        return None
    return user


def flash_redirect(path, message):
    qs = urlencode({"flash": message})
    return redirect(f"{path}?{qs}")


# ------------------------------------------------------------ PWA / app-on-phone
#
# Served from a dedicated root-level route (not under /static/) so the
# service worker's default scope is "/" and covers every page route in
# this app. If it were served from /static/sw.js instead, its scope would
# default to /static/ and would NOT control /, /login, /dashboard, etc.

SERVICE_WORKER_JS = """
const CACHE_NAME = "jag-portal-v1";
const ASSETS_TO_CACHE = [
  "/static/css/style.css",
  "/static/img/logo.png",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Only ever cache static assets (CSS/images). Pages and form posts always
  // go to the network so logins, results and sessions are never stale.
  const url = new URL(event.request.url);
  if (event.request.method === "GET" && url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});
""".strip()


@router.get("/sw.js")
def service_worker(req):
    return Response(SERVICE_WORKER_JS, content_type="text/javascript; charset=utf-8")


# --------------------------------------------------------------- auth routes


@router.get("/")
def index(req):
    user = get_current_user(req)
    if user and user["role"] == "coach":
        return redirect("/coach")
    if user and user["role"] == "participant":
        return redirect("/dashboard")
    return redirect("/login")


@router.get("/login")
def login_get(req):
    return Response(views.login_page())


@router.post("/login")
def login_post(req):
    login = req.form_get("login").strip()
    password = req.form_get("password")
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE (lower(email) = ? OR lower(username) = ?) AND active = 1",
            (login.lower(), login.lower()),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return Response(views.login_page(error="Incorrect email, username or password.", prefill_login=login), status=401)

        token = new_session_token()
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)",
            (token, row["id"], db.now()),
        )
        conn.commit()

        resp = redirect("/coach" if row["role"] == "coach" else "/dashboard")
        resp.set_cookie(SESSION_COOKIE, token, max_age=60 * 60 * 24 * 14)
        return resp
    finally:
        conn.close()


@router.get("/forgot-password")
def forgot_password(req):
    return Response(views.forgot_password_page())


@router.get("/logout")
def logout(req):
    token = req.get_cookie(SESSION_COOKIE)
    if token:
        conn = db.get_conn()
        try:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (token,))
            conn.commit()
        finally:
            conn.close()
    resp = redirect("/login")
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# ---------------------------------------------------------- participant view


@router.get("/dashboard")
def dashboard(req):
    user = require_role(req, "participant")
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        measurement_sessions = db.measurement_sessions_for(conn, user["id"])
        return Response(views.participant_dashboard(user, measurement_sessions))
    finally:
        conn.close()


# ---------------------------------------------------------------- coach views


@router.get("/coach")
def coach_dashboard(req):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        def make_summary(p):
            return {
                "id": p["id"], "name": p["name"], "sport": p["sport"],
                "programme": p["programme"],
                "test_count": db.count_measurement_sessions(conn, p["id"]),
            }
        message = req.get_query("flash")
        if coach.get("is_admin"):
            group_groups, ungrouped = db.list_participants_by_group(conn)
            group_summaries = [(g, [make_summary(p) for p in ps]) for g, ps in group_groups]
            ungrouped_summaries = [make_summary(p) for p in ungrouped]
        else:
            # Regular coaches only see their assigned groups
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if coach_group_ids:
                placeholders = ",".join("?" * len(coach_group_ids))
                groups = conn.execute(
                    f"SELECT * FROM participant_groups WHERE id IN ({placeholders}) ORDER BY sort_order, id",
                    coach_group_ids,
                ).fetchall()
                group_summaries = []
                for group in groups:
                    participants = conn.execute(
                        "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
                        (group["id"],),
                    ).fetchall()
                    group_summaries.append((group, [make_summary(p) for p in participants]))
            else:
                group_summaries = []
            ungrouped_summaries = []
        return Response(views.coach_dashboard_for(coach, group_summaries, ungrouped_summaries, message=message))
    finally:
        conn.close()


@router.get("/coach/participants/new")
def new_participant_get(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        groups = db.list_participant_groups(conn)
        return Response(views.new_participant_form(coach, groups=groups))
    finally:
        conn.close()


@router.post("/coach/participants/new")
def new_participant_post(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    email = req.form_get("email").strip().lower()
    password = req.form_get("password") or "Athlete123!"
    sport = req.form_get("sport")
    programme = req.form_get("programme").strip()
    group_id = req.form_get("group_id").strip() or None

    conn = db.get_conn()
    try:
        groups = db.list_participant_groups(conn)
        if not name or not email:
            return Response(views.new_participant_form(coach, groups=groups, error="Name and email are required."), status=400)

        existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing:
            return Response(views.new_participant_form(coach, groups=groups, error="A user with that email already exists."), status=400)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, sport, programme, group_id, created_at) "
            "VALUES (?, ?, ?, 'participant', ?, ?, ?, ?)",
            (name, email, hash_password(password), sport, programme, group_id or None, db.now()),
        )
        conn.commit()
        return flash_redirect("/coach", f"Added participant {name}. Share their login: {email} / {password}")
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>")
def coach_participant_detail(req, participant_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'", (participant_id,)
        ).fetchone()
        if not participant:
            return Response(views.simple_message_page("Not found", "Participant not found.", user=coach), status=404)
        # Non-admin coaches can only access participants in their assigned groups
        if not coach.get("is_admin"):
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if participant["group_id"] not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this participant.", user=coach), status=403)
        measurement_sessions = db.measurement_sessions_for(conn, participant_id)
        groups = db.list_participant_groups(conn)
        message = req.get_query("flash")
        return Response(views.coach_participant_detail(
            coach, dict(participant), measurement_sessions, groups=groups, message=message,
        ))
    finally:
        conn.close()


@router.get("/coach/progress")
def all_progress(req):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        if coach.get("is_admin"):
            # Admins see all groups and ungrouped
            group_groups, ungrouped = db.list_participants_by_group(conn)
            groups_data = []
            for group, participants in group_groups:
                ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in participants]
                groups_data.append((dict(group), ps_data))
            if ungrouped:
                ug_data = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in ungrouped]
                groups_data.append((None, ug_data))
        else:
            # Non-admin coaches see only their assigned groups
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            groups_data = []
            for gid in coach_group_ids:
                group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (gid,)).fetchone()
                if not group:
                    continue
                participants = conn.execute(
                    "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name", (gid,)
                ).fetchall()
                ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in participants]
                groups_data.append((dict(group), ps_data))
        return Response(views.all_progress_page(coach, groups_data))
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/progress")
def group_progress(req, group_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        # Non-admins can only view their assigned groups
        if not coach.get("is_admin"):
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        participants = conn.execute(
            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()
        participants_sessions = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in participants]
        return Response(views.group_progress_page(coach, dict(group), participants_sessions))
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/achievement-summary")
def group_achievement_summary(req, group_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        if not coach.get("is_admin"):
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        participants = conn.execute(
            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()
        participants_sessions = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in participants]
        return Response(views.group_achievement_summary_page(coach, dict(group), participants_sessions))
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>/progress")
def coach_participant_progress(req, participant_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'", (participant_id,)
        ).fetchone()
        if not participant:
            return Response(views.simple_message_page("Not found", "Participant not found.", user=coach), status=404)
        if not coach.get("is_admin"):
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if participant["group_id"] not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this participant.", user=coach), status=403)
        measurement_sessions = db.measurement_sessions_for(conn, participant_id)
        return Response(views.participant_progress_page(coach, dict(participant), measurement_sessions))
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/measurement")
def log_measurement_session(req, participant_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    # Check group access for non-admins
    if not coach.get("is_admin"):
        conn = db.get_conn()
        try:
            p = conn.execute("SELECT group_id FROM users WHERE id = ?", (participant_id,)).fetchone()
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
        finally:
            conn.close()
        if not p or p["group_id"] not in coach_group_ids:
            return flash_redirect("/coach", "You don't have access to that participant.")
    date = req.form_get("date") or db.today()

    results = []
    for game in all_measurement_games():
        field_values = {}
        for field in game["fields"]:
            raw = req.form_get(f"mg__{game['key']}__{field['key']}").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            field_values[field["key"]] = value
            results.append((game["key"], field["key"], value))

        # Computed fields (e.g. the Skipping Rope Sprint average) -- only
        # calculated once every field they depend on has a value.
        for computed in game.get("computed", []):
            inputs = [field_values.get(k) for k in computed["of"]]
            if all(v is not None for v in inputs):
                avg = round(sum(inputs) / len(inputs), 2)
                results.append((game["key"], computed["key"], avg))

    if not results:
        return flash_redirect(
            f"/coach/participants/{participant_id}",
            "No results entered -- fill in at least one field before saving.",
        )

    conn = db.get_conn()
    try:
        db.create_measurement_session(conn, participant_id, date, coach["id"], results)
    finally:
        conn.close()
    return flash_redirect(f"/coach/participants/{participant_id}", "Measurement Games results saved.")


@router.post("/coach/participants/<int:participant_id>/reset-password")
def reset_participant_password(req, participant_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'", (participant_id,)
        ).fetchone()
        if not participant:
            return flash_redirect("/coach", "Participant not found.")
        temp_password = generate_temp_password()
        db.update_password(conn, participant_id, temp_password)
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (participant_id,))
        conn.commit()
        return flash_redirect(
            f"/coach/participants/{participant_id}",
            f"Password reset for {participant['name']}. New password: {temp_password} "
            f"-- share this with them now, it won't be shown again.",
        )
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/measurement/<int:session_id>/delete")
def delete_measurement_session(req, participant_id, session_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_measurement_session(conn, session_id)
    finally:
        conn.close()
    return flash_redirect(f"/coach/participants/{participant_id}", "Measurement Games session deleted.")


# --------------------------------------------------------------- account / auth


@router.get("/account/password")
def account_get(req):
    user = get_current_user(req)
    if not user:
        return redirect("/login")
    return Response(views.account_page(user))


@router.post("/account/profile")
def account_profile_post(req):
    user = get_current_user(req)
    if not user:
        return redirect("/login")

    name     = req.form_get("name").strip()
    email    = req.form_get("email").strip().lower()
    username = req.form_get("username").strip()

    if not name or not email:
        return Response(views.account_page(user, profile_error="Name and email are required."), status=400)

    conn = db.get_conn()
    try:
        existing_email = conn.execute(
            "SELECT id FROM users WHERE lower(email) = ? AND id != ?", (email, user["id"]),
        ).fetchone()
        if existing_email:
            return Response(views.account_page(user, profile_error="That email is already used by another account."), status=400)

        if username:
            existing_username = conn.execute(
                "SELECT id FROM users WHERE lower(username) = ? AND id != ?", (username.lower(), user["id"]),
            ).fetchone()
            if existing_username:
                return Response(views.account_page(user, profile_error="That username is already taken."), status=400)

        db.update_profile(conn, user["id"], name, email, username or None)
        updated_user = get_current_user(req)
        return Response(views.account_page(updated_user, profile_success="Details updated."))
    finally:
        conn.close()


@router.post("/account/password")
def change_password_post(req):
    user = get_current_user(req)
    if not user:
        return redirect("/login")

    current_password = req.form_get("current_password")
    new_password = req.form_get("new_password")
    confirm_password = req.form_get("confirm_password")

    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            return Response(views.account_page(user, password_error="Current password is incorrect."), status=400)
        if not new_password or len(new_password) < 8:
            return Response(views.account_page(user, password_error="New password must be at least 8 characters."), status=400)
        if new_password != confirm_password:
            return Response(views.account_page(user, password_error="New password and confirmation don't match."), status=400)

        db.update_password(conn, user["id"], new_password)
        return Response(views.account_page(user, password_success="Password updated."))
    finally:
        conn.close()


# --------------------------------------------------------------- manage coaches


@router.get("/coach/coaches")
def list_coaches(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        coaches = db.list_coaches(conn)
        groups = db.list_participant_groups(conn)
        coach_group_map = {c["id"]: db.get_coach_group_ids(conn, c["id"]) for c in coaches}
        message = req.get_query("flash")
        return Response(views.coach_list_page(coach, coaches, groups=groups, coach_group_map=coach_group_map, message=message))
    finally:
        conn.close()


@router.get("/coach/coaches/new")
def new_coach_get(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    return Response(views.new_coach_form(coach))


@router.post("/coach/coaches/new")
def new_coach_post(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    email = req.form_get("email").strip().lower()
    password = req.form_get("password") or "CoachTemp123!"

    if not name or not email:
        return Response(views.new_coach_form(coach, error="Name and email are required."), status=400)

    conn = db.get_conn()
    try:
        existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing:
            return Response(views.new_coach_form(coach, error="A user with that email already exists."), status=400)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, sport, programme, created_at) "
            "VALUES (?, ?, ?, 'coach', NULL, NULL, ?)",
            (name, email, hash_password(password), db.now()),
        )
        conn.commit()
        return flash_redirect("/coach/coaches", f"Added coach {name}. Share their login: {email} / {password}")
    finally:
        conn.close()


@router.post("/coach/coaches/<int:coach_id>/reset-password")
def reset_coach_password(req, coach_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role = 'coach'", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Coach not found.")
        temp_password = generate_temp_password()
        db.update_password(conn, coach_id, temp_password)
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (coach_id,))
        conn.commit()
        return flash_redirect(
            "/coach/coaches",
            f"Password reset for {target['name']}. New password: {temp_password} "
            f"-- share this with them now, it won't be shown again.",
        )
    finally:
        conn.close()


@router.post("/coach/coaches/<int:coach_id>/assign-group")
def assign_coach_group(req, coach_id):
    admin = require_admin(req)
    if not admin:
        return redirect("/login")
    group_ids = [gid for gid in req.form_get_list("group_id") if gid.strip()]
    conn = db.get_conn()
    try:
        db.set_coach_groups(conn, coach_id, group_ids)
        return flash_redirect("/coach/coaches", "Coach groups updated.")
    finally:
        conn.close()


@router.post("/coach/coaches/<int:coach_id>/toggle-admin")
def toggle_admin(req, coach_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    if int(coach_id) == coach["id"]:
        return flash_redirect("/coach/coaches", "You can't change your own admin status.")
    conn = db.get_conn()
    try:
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role = 'coach'", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Coach not found.")
        new_admin = 0 if target["is_admin"] else 1
        db.set_admin_status(conn, coach_id, new_admin)
        action = "granted admin rights to" if new_admin else "removed admin rights from"
        return flash_redirect("/coach/coaches", f"{action.capitalize()} {target['name']}.")
    finally:
        conn.close()


@router.post("/coach/coaches/<int:coach_id>/toggle")
def toggle_coach(req, coach_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    # core.py's router passes path params as strings even for <int:...>
    # patterns (the "int:" prefix only restricts the URL's regex match to
    # digits) -- compare as ints here or this always evaluates False.
    if int(coach_id) == coach["id"]:
        return flash_redirect("/coach/coaches", "You can't deactivate your own account.")

    conn = db.get_conn()
    try:
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role = 'coach'", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Coach not found.")
        new_active = 0 if target["active"] else 1
        db.set_active(conn, coach_id, new_active)
        action = "reactivated" if new_active else "deactivated"
        return flash_redirect("/coach/coaches", f"{target['name']} {action}.")
    finally:
        conn.close()


# --------------------------------------------------------- participant groups


@router.post("/coach/participants/<int:participant_id>/move-group")
def move_participant_group(req, participant_id):
    """AJAX endpoint — moves a participant to a new group via drag-and-drop."""
    coach = require_admin(req)
    if not coach:
        return Response("", status=403)
    group_id = req.form_get("group_id").strip() or None
    conn = db.get_conn()
    try:
        db.assign_participant_group(conn, participant_id, group_id)
    finally:
        conn.close()
    return Response("ok")


@router.post("/coach/participants/<int:participant_id>/assign-group")
def assign_participant_group(req, participant_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    group_id = req.form_get("group_id").strip() or None
    conn = db.get_conn()
    try:
        db.assign_participant_group(conn, participant_id, group_id)
        return flash_redirect(f"/coach/participants/{participant_id}", "Group updated.")
    finally:
        conn.close()


@router.post("/coach/groups/new")
def group_new(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("group_name").strip()
    if not name:
        return flash_redirect("/coach", "Group name is required.")
    conn = db.get_conn()
    try:
        db.add_participant_group(conn, name, coach["id"])
        return flash_redirect("/coach", f'Group "{name}" created.')
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/edit")
def group_edit_get(req, group_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        return Response(views.edit_group_page(coach, dict(group)))
    finally:
        conn.close()


@router.post("/coach/groups/<int:group_id>/edit")
def group_edit_post(req, group_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("group_name").strip()
    icon_url = req.form_get("icon_url").strip() or None
    if not name:
        conn = db.get_conn()
        try:
            group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
            return Response(views.edit_group_page(coach, dict(group), error="Group name is required."), status=400)
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        db.update_participant_group(conn, group_id, name, icon_url)
        return flash_redirect("/coach", f'Group "{name}" updated.')
    finally:
        conn.close()


@router.post("/coach/groups/reorder")
def groups_reorder(req):
    coach = require_admin(req)
    if not coach:
        return Response("", status=403)
    ids_str = req.form_get("ids")
    if ids_str:
        try:
            ids = [int(i) for i in ids_str.split(",") if i.strip()]
            conn = db.get_conn()
            try:
                db.reorder_items(conn, "participant_groups", ids)
            finally:
                conn.close()
        except ValueError:
            pass
    return Response("ok")


@router.post("/coach/groups/<int:group_id>/delete")
def group_delete(req, group_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_participant_group(conn, group_id)
        return flash_redirect("/coach", "Group deleted. Participants moved to ungrouped.")
    finally:
        conn.close()


# ------------------------------------------------------------------ resources


def _resources_page_response(coach, conn, message=None, error=None, status=200):
    folder_groups, ungrouped = db.list_resources_by_folder(conn)
    folders = db.list_folders(conn)
    return Response(
        views.resources_page(coach, folder_groups, ungrouped, folders, message=message, error=error),
        status=status,
    )


@router.get("/coach/resources")
def resources_list(req):
    coach = require_role(req, "coach")
    if not coach:
        user = get_current_user(req)
        return redirect("/dashboard" if user else "/login")
    conn = db.get_conn()
    try:
        return _resources_page_response(coach, conn, message=req.get_query("flash"))
    finally:
        conn.close()


@router.post("/coach/resources/new")
def resources_new(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    url = req.form_get("url").strip()
    description = req.form_get("description").strip()
    folder_id = req.form_get("folder_id").strip() or None
    if not name or not url:
        conn = db.get_conn()
        try:
            return _resources_page_response(coach, conn, error="Name and URL are required.", status=400)
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        db.add_resource(conn, name, description, url, coach["id"], folder_id)
        return flash_redirect("/coach/resources", f'"{name}" added.')
    finally:
        conn.close()


@router.get("/coach/resources/<int:resource_id>/edit")
def resource_edit_get(req, resource_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        resource = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
        if not resource:
            return flash_redirect("/coach/resources", "Resource not found.")
        folders = db.list_folders(conn)
        return Response(views.edit_resource_page(coach, dict(resource), folders))
    finally:
        conn.close()


@router.post("/coach/resources/<int:resource_id>/edit")
def resource_edit_post(req, resource_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    url = req.form_get("url").strip()
    description = req.form_get("description").strip()
    folder_id = req.form_get("folder_id").strip() or None
    if not name or not url:
        conn = db.get_conn()
        try:
            resource = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
            folders = db.list_folders(conn)
            return Response(
                views.edit_resource_page(coach, dict(resource), folders, error="Name and URL are required."),
                status=400,
            )
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        db.update_resource(conn, resource_id, name, description, url, folder_id)
        return flash_redirect("/coach/resources", f'"{name}" updated.')
    finally:
        conn.close()


@router.post("/coach/resources/<int:resource_id>/delete")
def resources_delete(req, resource_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_resource(conn, resource_id)
        return flash_redirect("/coach/resources", "Resource deleted.")
    finally:
        conn.close()


@router.post("/coach/resources/<int:resource_id>/move")
def resource_move(req, resource_id):
    coach = require_admin(req)
    if not coach:
        return Response("", status=403)
    folder_id = req.form_get("folder_id").strip() or None
    conn = db.get_conn()
    try:
        db.move_resource(conn, resource_id, folder_id)
    finally:
        conn.close()
    return Response("ok")


@router.post("/coach/resources/reorder")
def resources_reorder(req):
    coach = require_role(req, "coach")
    if not coach:
        return Response("", status=403)
    ids_str = req.form_get("ids")
    if ids_str:
        try:
            ids = [int(i) for i in ids_str.split(",") if i.strip()]
            conn = db.get_conn()
            try:
                db.reorder_items(conn, "resources", ids)
            finally:
                conn.close()
        except ValueError:
            pass
    return Response("ok")


@router.post("/coach/resources/folders/new")
def folder_new(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("folder_name").strip()
    if not name:
        return flash_redirect("/coach/resources", "Folder name is required.")
    conn = db.get_conn()
    try:
        db.add_folder(conn, name, coach["id"])
        return flash_redirect("/coach/resources", f'Folder "{name}" created.')
    finally:
        conn.close()


@router.post("/coach/resources/folders/<int:folder_id>/delete")
def folder_delete(req, folder_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_folder(conn, folder_id)
        return flash_redirect("/coach/resources", "Folder deleted. Resources moved to Ungrouped.")
    finally:
        conn.close()


@router.post("/coach/resources/folders/reorder")
def folders_reorder(req):
    coach = require_role(req, "coach")
    if not coach:
        return Response("", status=403)
    ids_str = req.form_get("ids")
    if ids_str:
        try:
            ids = [int(i) for i in ids_str.split(",") if i.strip()]
            conn = db.get_conn()
            try:
                db.reorder_items(conn, "resource_folders", ids)
            finally:
                conn.close()
        except ValueError:
            pass
    return Response("ok")


# ------------------------------------------------------------------- bootstrap

application = App(router, STATIC_DIR)


class _FastRequestHandler(WSGIRequestHandler):
    """Skip the reverse-DNS lookup wsgiref normally does on every request.

    On cloud hosts (Render, Railway, etc.) that lookup has no PTR record to
    resolve and can hang for a long time - and since this dev server is
    single-threaded, one hung lookup blocks every other request behind it,
    which looks exactly like the whole app being stuck loading.
    """

    def address_string(self):
        return self.client_address[0]


def main():
    from wsgiref.simple_server import make_server

    db.init_db()
    seeded = db.seed_demo_data()
    if seeded:
        print("Seeded demo data (coach + 3 demo participants). See README.md for credentials.")
    db.patch_demo_data()
    db.maybe_reset_coach_password()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"{APP_NAME} running at http://localhost:{port}  (Ctrl+C to stop)")
    with make_server(host, port, application, handler_class=_FastRequestHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
