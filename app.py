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
from auth import verify_password, hash_password, new_session_token
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


def flash_redirect(path, message):
    qs = urlencode({"flash": message})
    return redirect(f"{path}?{qs}")


def participant_summary(conn, participant_id):
    activities = conn.execute(
        "SELECT * FROM activities WHERE participant_id = ? ORDER BY date DESC, id DESC",
        (participant_id,),
    ).fetchall()
    total_points = sum(a["points"] for a in activities)
    return activities, total_points


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
    email = req.form_get("email").strip().lower()
    password = req.form_get("password")
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ? AND active = 1", (email,)).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return Response(views.login_page(error="Incorrect email or password.", prefill_email=email), status=401)

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
        activities, total_points = participant_summary(conn, user["id"])
        measurement_sessions = db.measurement_sessions_for(conn, user["id"])
        return Response(views.participant_dashboard(
            user,
            [dict(a) for a in activities],
            total_points,
            measurement_sessions,
        ))
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
        participants = conn.execute(
            "SELECT * FROM users WHERE role = 'participant' AND active = 1 ORDER BY name"
        ).fetchall()
        summaries = []
        for p in participants:
            activities, total_points = participant_summary(conn, p["id"])
            test_count = db.count_measurement_sessions(conn, p["id"])
            summaries.append({
                "id": p["id"], "name": p["name"], "sport": p["sport"], "programme": p["programme"],
                "total_points": total_points, "test_count": test_count, "activity_count": len(activities),
            })
        return Response(views.coach_dashboard_for(coach, summaries))
    finally:
        conn.close()


@router.get("/coach/participants/new")
def new_participant_get(req):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    return Response(views.new_participant_form(coach))


@router.post("/coach/participants/new")
def new_participant_post(req):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    email = req.form_get("email").strip().lower()
    password = req.form_get("password") or "Athlete123!"
    sport = req.form_get("sport")
    programme = req.form_get("programme").strip()

    if not name or not email:
        return Response(views.new_participant_form(coach, error="Name and email are required."), status=400)

    conn = db.get_conn()
    try:
        existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing:
            return Response(views.new_participant_form(coach, error="A user with that email already exists."), status=400)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, sport, programme, created_at) "
            "VALUES (?, ?, ?, 'participant', ?, ?, ?)",
            (name, email, hash_password(password), sport, programme, db.now()),
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
        activities, total_points = participant_summary(conn, participant_id)
        measurement_sessions = db.measurement_sessions_for(conn, participant_id)
        message = req.get_query("flash")
        return Response(views.coach_participant_detail(
            coach, dict(participant), [dict(a) for a in activities], total_points,
            measurement_sessions, message=message,
        ))
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/activity")
def log_activity(req, participant_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
    date = req.form_get("date") or db.today()
    title = req.form_get("title").strip()
    category = req.form_get("category")
    notes = req.form_get("notes").strip()
    try:
        points = int(req.form_get("points") or 0)
    except ValueError:
        points = 0

    conn = db.get_conn()
    try:
        conn.execute(
            "INSERT INTO activities (participant_id, date, title, category, notes, points, logged_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (participant_id, date, title, category, notes, points, coach["id"], db.now()),
        )
        conn.commit()
    finally:
        conn.close()
    return flash_redirect(f"/coach/participants/{participant_id}", "Activity logged.")


@router.post("/coach/participants/<int:participant_id>/measurement")
def log_measurement_session(req, participant_id):
    coach = require_role(req, "coach")
    if not coach:
        return redirect("/login")
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
def change_password_get(req):
    user = get_current_user(req)
    if not user:
        return redirect("/login")
    return Response(views.change_password_page(user))


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
            return Response(views.change_password_page(user, error="Current password is incorrect."), status=400)
        if not new_password or len(new_password) < 8:
            return Response(views.change_password_page(user, error="New password must be at least 8 characters."), status=400)
        if new_password != confirm_password:
            return Response(views.change_password_page(user, error="New password and confirmation don't match."), status=400)

        db.update_password(conn, user["id"], new_password)
        return Response(views.change_password_page(user, success="Password updated."))
    finally:
        conn.close()


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
    db.maybe_reset_coach_password()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"{APP_NAME} running at http://localhost:{port}  (Ctrl+C to stop)")
    with make_server(host, port, application, handler_class=_FastRequestHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
