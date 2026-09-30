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
from constants import APP_NAME, all_measurement_games, all_active_measurement_games, SESSION_TYPES, SESSION_LABEL_MAP
import views
import mailer

router = Router()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

SESSION_COOKIE  = "jag_session"
VIEW_AS_COOKIE  = "jag_view_as"


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
        if not row:
            return None
        user = dict(row)
        # For participants: inject group's show_leaderboard flag so the nav can
        # conditionally render the Leaderboard link without an extra DB call.
        if user.get("role") == "participant" and user.get("group_id"):
            grp = conn.execute(
                "SELECT show_leaderboard FROM participant_groups WHERE id = ?",
                (user["group_id"],),
            ).fetchone()
            user["show_leaderboard"] = bool(grp and grp["show_leaderboard"]) if grp else False
        return user
    finally:
        conn.close()


# ── Role constants ────────────────────────────────────────────────────────────
STAFF_ROLES = {"practitioner", "org_admin", "system_admin"}


def require_role(req, role):
    """Generic single-role check (used for 'participant')."""
    user = get_current_user(req)
    if not user or user["role"] != role:
        return None
    return user


def require_staff(req):
    """Allow any staff role: practitioner, org_admin, or system_admin."""
    user = get_current_user(req)
    if not user or user["role"] not in STAFF_ROLES:
        return None
    return user


def require_org_admin(req):
    """Allow org_admin or system_admin."""
    user = get_current_user(req)
    if not user or user["role"] not in {"org_admin", "system_admin"}:
        return None
    return user


def require_system_admin(req):
    """Allow system_admin only."""
    user = get_current_user(req)
    if not user or user["role"] != "system_admin":
        return None
    return user


def get_view_as_athlete(req):
    """If a staff user has activated view-as mode, return the athlete they're viewing.

    The athlete dict has extra keys injected:
        _view_as              = True
        _view_as_profile_url  = "/coach/participants/<id>"
    so layout() can render the exit banner automatically.
    """
    staff = require_staff(req)
    if not staff:
        return None
    raw_id = req.get_cookie(VIEW_AS_COOKIE)
    if not raw_id:
        return None
    try:
        athlete_id = int(raw_id)
    except (TypeError, ValueError):
        return None
    conn = db.get_conn()
    try:
        athlete = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'",
            (athlete_id,),
        ).fetchone()
        if not athlete:
            return None
        athlete = dict(athlete)
        # Org scoping — practitioner can only view athletes in their own org
        if staff.get("org_id") and athlete.get("org_id") != staff.get("org_id"):
            return None
        # Inject view-as metadata used by layout() to show the exit banner
        athlete["_view_as"] = True
        athlete["_view_as_profile_url"] = f"/coach/participants/{athlete_id}"
        # Inject leaderboard flag so athlete nav renders correctly
        if athlete.get("group_id"):
            grp = conn.execute(
                "SELECT show_leaderboard FROM participant_groups WHERE id = ?",
                (athlete["group_id"],),
            ).fetchone()
            athlete["show_leaderboard"] = bool(grp and grp["show_leaderboard"]) if grp else False
        return athlete
    finally:
        conn.close()


def require_participant_or_view_as(req):
    """For athlete GET routes: allow real participants OR staff in view-as mode."""
    user = require_role(req, "participant")
    if user:
        return user
    return get_view_as_athlete(req)


def require_admin(req):
    """Backward-compat alias → require_system_admin."""
    return require_system_admin(req)


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
    if user and user["role"] in STAFF_ROLES:
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

        # Award welcome bonus XP to athletes on their first-ever login
        if row["role"] == "participant":
            try:
                if not db._has_awarded_xp_type(conn, row["id"], "welcome_bonus"):
                    from constants import XP_PARTICIPATION
                    db.award_xp(conn, row["id"], "welcome_bonus",
                                XP_PARTICIPATION.get("welcome_bonus", 100),
                                notes="Welcome to Just a Game!")
            except Exception:
                pass

        resp = redirect("/coach" if row["role"] in STAFF_ROLES else "/dashboard")
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
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        pid = user["id"]
        measurement_sessions = db.measurement_sessions_for(conn, pid)
        xp_data = db.get_athlete_xp(conn, pid)
        levels = db.get_all_athlete_levels(conn, pid)
        levels_by_area = db.get_all_athlete_levels_by_area(conn, pid)
        pending_sd = db.get_pending_self_directed_events(conn, pid)
        thresholds_raw = db.get_all_thresholds(conn)
        # Key: "game_key|field_key|level" for per-area lookups in the level grid
        thresholds = {f"{r['game_key']}|{r['field_key']}|{r['level']}": r["threshold_value"]
                      for r in thresholds_raw}
        att_count = db.count_attendance(conn, pid)
        # Active measurement window for this athlete's group
        active_window = None
        already_submitted = False
        try:
            w = db.get_active_window_for_participant(conn, pid)
            if w:
                active_window = dict(w)
                already_submitted = db.athlete_has_submitted(conn, w["id"], pid)
        except Exception:
            pass
        # Recent public resources for dashboard preview (up to 6)
        try:
            _fg, _ug = db.list_resources_by_folder(conn)
            _flat = [r for _f, rs in _fg for r in rs] + list(_ug)
            resources = [dict(r) for r in _flat[:6]]
        except Exception:
            resources = []
        return Response(views.participant_dashboard(
            user, measurement_sessions,
            xp_data=xp_data, levels=levels,
            levels_by_area=levels_by_area,
            pending_self_directed=pending_sd,
            thresholds=thresholds,
            resources=resources,
            attendance_count=att_count,
            active_window=active_window,
            already_submitted=already_submitted,
        ))
    finally:
        conn.close()


@router.get("/athlete/resources")
def athlete_resources(req):
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        folder_groups, ungrouped = db.list_resources_by_folder(conn)
        return Response(views.athlete_resources_page(user, folder_groups, ungrouped))
    finally:
        conn.close()


# ---------------------------------------------------------------- coach views


@router.get("/coach")
def coach_home(req):
    """Practitioner landing page — 'What are you keen to do today?'"""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    return Response(views.practitioner_home_page(coach))


@router.get("/coach/groups")
def coach_dashboard(req):
    coach = require_staff(req)
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
        if coach["role"] in {"org_admin", "system_admin"}:
            group_groups, ungrouped = db.list_participants_by_group(conn)
            group_summaries = [(g, [make_summary(p) for p in ps]) for g, ps in group_groups]
            ungrouped_summaries = [make_summary(p) for p in ungrouped]
        else:
            # Regular coaches: org-scoped if they have an organisation_id, else by assigned groups
            coach_org_id = coach.get("organisation_id")
            if coach_org_id:
                group_groups, _ = db.list_participants_by_group(conn, organisation_id=coach_org_id)
                group_summaries = [(g, [make_summary(p) for p in ps]) for g, ps in group_groups]
            else:
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
        # Build org map for grouped dashboard headers
        orgs = db.list_organisations(conn)
        org_map = {o["id"]: o for o in orgs}

        # Dashboard stat cards
        # Collect all athlete IDs visible to this coach (org-scoped)
        all_athlete_ids = [p["id"] for _, ps in group_summaries for p in ps] + \
                          [p["id"] for p in ungrouped_summaries]

        # Latest phase across these athletes
        latest_phase_raw = None
        latest_phase = None
        if all_athlete_ids:
            placeholders_a = ",".join("?" * len(all_athlete_ids))
            latest_phase_row = conn.execute(
                f"SELECT session_label, session_month FROM measurement_sessions "
                f"WHERE session_label IS NOT NULL AND session_label != '' "
                f"AND participant_id IN ({placeholders_a}) "
                f"ORDER BY date DESC, id DESC LIMIT 1",
                all_athlete_ids,
            ).fetchone()
            if latest_phase_row:
                latest_phase_raw = latest_phase_row["session_label"]
                lbl = SESSION_LABEL_MAP.get(latest_phase_raw, latest_phase_raw)
                sm = latest_phase_row["session_month"] or ""
                if sm:
                    try:
                        import datetime as _dt
                        d = _dt.datetime.strptime(sm, "%Y-%m")
                        sm = d.strftime("%b %Y")
                    except Exception:
                        pass
                latest_phase = f"{lbl}\n{sm}" if sm else lbl

        untested = sum(1 for _, ps in group_summaries for p in ps if p["test_count"] == 0) + \
                   sum(1 for p in ungrouped_summaries if p["test_count"] == 0)
        total_athletes = sum(len(ps) for _, ps in group_summaries) + len(ungrouped_summaries)

        # Org-scoped averages for latest phase
        avg_sprint = None
        avg_balance = None
        phase_completion_n = 0
        phase_completion_total = total_athletes

        if all_athlete_ids and latest_phase_raw:
            placeholders_a = ",".join("?" * len(all_athlete_ids))

            # Avg sprint time: skipping_rope_sprint / average (computed field)
            sprint_row = conn.execute(
                f"SELECT AVG(CAST(mr.value AS REAL)) as avg "
                f"FROM measurement_results mr "
                f"JOIN measurement_sessions ms ON ms.id = mr.session_id "
                f"WHERE ms.session_label = ? AND ms.participant_id IN ({placeholders_a}) "
                f"AND mr.game_key = 'skipping_rope_sprint' AND mr.field_key = 'average' "
                f"AND mr.value IS NOT NULL AND mr.value != ''",
                [latest_phase_raw] + all_athlete_ids,
            ).fetchone()
            avg_sprint = sprint_row["avg"] if sprint_row and sprint_row["avg"] is not None else None

            # Avg balance catch: large_ball_wall_bounce
            balance_row = conn.execute(
                f"SELECT AVG(CAST(mr.value AS REAL)) as avg "
                f"FROM measurement_results mr "
                f"JOIN measurement_sessions ms ON ms.id = mr.session_id "
                f"WHERE ms.session_label = ? AND ms.participant_id IN ({placeholders_a}) "
                f"AND mr.game_key = 'balance_ball_catching' AND mr.field_key = 'large_ball_wall_bounce' "
                f"AND mr.value IS NOT NULL AND mr.value != ''",
                [latest_phase_raw] + all_athlete_ids,
            ).fetchone()
            avg_balance = balance_row["avg"] if balance_row and balance_row["avg"] is not None else None

            # Phase completion: distinct athletes with at least 1 result for the latest phase
            comp_row = conn.execute(
                f"SELECT COUNT(DISTINCT ms.participant_id) as n "
                f"FROM measurement_sessions ms "
                f"JOIN measurement_results mr ON mr.session_id = ms.id "
                f"WHERE ms.session_label = ? AND ms.participant_id IN ({placeholders_a})",
                [latest_phase_raw] + all_athlete_ids,
            ).fetchone()
            phase_completion_n = (comp_row["n"] if comp_row else 0) or 0

        dashboard_stats = {
            "total_athletes": total_athletes,
            "latest_phase": latest_phase,
            "untested": untested,
            "avg_sprint": avg_sprint,
            "avg_balance": avg_balance,
            "phase_completion_n": phase_completion_n,
            "phase_completion_total": phase_completion_total,
        }
        return Response(views.coach_dashboard_for(coach, group_summaries, ungrouped_summaries, message=message, org_map=org_map, stats=dashboard_stats))
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
    setup_login = req.form_get("setup_login") == "1"
    email = req.form_get("email").strip().lower() if setup_login else None
    password = req.form_get("password") or "Athlete123!" if setup_login else None
    sport = req.form_get("sport")
    gender = req.form_get("gender").strip() or None
    programme = req.form_get("programme").strip()
    group_id = req.form_get("group_id").strip() or None

    conn = db.get_conn()
    try:
        groups = db.list_participant_groups(conn)
        if not name:
            return Response(views.new_participant_form(coach, groups=groups, error="Name is required."), status=400)
        if setup_login:
            if not email:
                return Response(views.new_participant_form(coach, groups=groups, error="Email is required when setting up a login."), status=400)
            existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
            if existing:
                return Response(views.new_participant_form(coach, groups=groups, error="A user with that email already exists."), status=400)
        pid = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, sport, gender, programme, group_id, created_at) "
            "VALUES (?, ?, ?, 'participant', ?, ?, ?, ?, ?)",
            (name, email, hash_password(password) if password else None, sport, gender, programme, group_id or None, db.now()),
        ).lastrowid
        athlete_number = db.next_athlete_number(conn)
        conn.execute("UPDATE users SET athlete_number = ? WHERE id = ?", (athlete_number, pid))
        conn.commit()
        if setup_login:
            emailed = mailer.send_welcome_athlete(name, email, password)
            if emailed:
                return flash_redirect("/coach/groups", f"Added {name} (#{athlete_number}). Welcome email sent to {email}.")
            else:
                return flash_redirect("/coach/groups", f"Added {name} (#{athlete_number}). Share their login: {email} / {password}")
        else:
            return flash_redirect("/coach/groups", f"Added {name} (#{athlete_number}) to the system.")
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>")
def coach_participant_detail(req, participant_id):
    coach = require_staff(req)
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
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if participant["group_id"] not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this participant.", user=coach), status=403)
        measurement_sessions = db.measurement_sessions_for(conn, participant_id)
        groups = db.list_participant_groups(conn)
        message = req.get_query("flash")
        xp_data = db.get_athlete_xp(conn, participant_id)
        levels = db.get_all_athlete_levels(conn, participant_id)
        att_count = db.count_attendance(conn, participant_id)
        return Response(views.coach_participant_detail(
            coach, dict(participant), measurement_sessions, groups=groups, message=message,
            xp_data=xp_data, levels=levels, attendance_count=att_count,
        ))
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>/view-as")
def start_view_as(req, participant_id):
    """Set view-as cookie and redirect to the athlete dashboard."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    resp = redirect("/dashboard")
    resp.set_cookie(VIEW_AS_COOKIE, str(participant_id), max_age=60 * 60 * 8, path="/")
    return resp


@router.get("/coach/exit-view-as")
def exit_view_as(req):
    """Clear view-as cookie and return to the athlete's coach profile page."""
    athlete_id = req.get_cookie(VIEW_AS_COOKIE)
    back = f"/coach/participants/{athlete_id}" if athlete_id else "/coach"
    resp = redirect(back)
    resp.delete_cookie(VIEW_AS_COOKIE, path="/")
    return resp


@router.get("/coach/participants/<int:participant_id>/report")
def coach_participant_report(req, participant_id):
    """Individual athlete report — latest scores, gap analysis, S&C recommendations."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'", (participant_id,)
        ).fetchone()
        if not participant:
            return Response(views.simple_message_page("Not found", "Participant not found.", user=coach), status=404)
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if participant["group_id"] not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this participant.", user=coach), status=403)
        sessions = db.measurement_sessions_for(conn, participant_id)
        levels_by_area = db.get_all_athlete_levels_by_area(conn, participant_id)
        thresholds_raw = db.get_all_thresholds(conn)
        return Response(views.individual_athlete_report_page(
            coach, dict(participant), sessions, levels_by_area, thresholds_raw
        ))
    finally:
        conn.close()


@router.get("/coach/reports")
def reports_landing(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        groups = conn.execute(
            "SELECT id, name FROM participant_groups ORDER BY sort_order, name"
        ).fetchall()
        orgs = db.list_organisations(conn)
        sports = [r["sport"] for r in conn.execute(
            "SELECT DISTINCT sport FROM users WHERE role='participant' AND sport IS NOT NULL AND sport != '' ORDER BY sport"
        ).fetchall()]
    finally:
        conn.close()
    return Response(views.reports_landing_page(coach, groups, orgs=orgs, sports=sports))


def _resolve_report_scope(req, conn):
    """Parse group_id / org_id / sport from query string.
    Returns (athletes, scope_label, scope_dict) where scope_dict has group/org keys for views."""
    group_id_raw = req.query.get("group_id", [""])[0].strip()
    org_id_raw   = req.query.get("org_id",   [""])[0].strip()
    sport        = req.query.get("sport",     [""])[0].strip() or None
    group_id = int(group_id_raw) if group_id_raw.isdigit() else None
    org_id   = int(org_id_raw)   if org_id_raw.isdigit()   else None

    sport_clause = " AND sport = ?" if sport else ""
    sport_params = (sport,) if sport else ()

    if group_id:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return None, None, None
        athletes = conn.execute(
            f"SELECT * FROM users WHERE role='participant' AND group_id=?{sport_clause} "
            "ORDER BY CAST(athlete_number AS INTEGER), name",
            (group_id,) + sport_params
        ).fetchall()
        label = group["name"]
        if sport:
            label += f" — {sport}"
        return athletes, label, {"group": dict(group)}

    elif org_id:
        org = conn.execute("SELECT * FROM organisations WHERE id = ?", (org_id,)).fetchone()
        if not org:
            return None, None, None
        athletes = conn.execute(
            f"SELECT u.* FROM users u JOIN participant_groups pg ON u.group_id = pg.id "
            f"WHERE u.role='participant' AND pg.organisation_id=?{sport_clause} "
            "ORDER BY CAST(u.athlete_number AS INTEGER), u.name",
            (org_id,) + sport_params
        ).fetchall()
        label = org["name"]
        if sport:
            label += f" — {sport}"
        return athletes, label, {"group": {"name": label}}

    return None, None, None


@router.get("/coach/reports/baseline")
def reports_baseline(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        athletes, label, scope = _resolve_report_scope(req, conn)
        if athletes is None:
            return flash_redirect("/coach/reports", "Please select an organisation or group.")
        resources = conn.execute(
            "SELECT name, self_organisation FROM resources WHERE self_organisation IS NOT NULL"
        ).fetchall()
        athletes_data = []
        for a in athletes:
            sessions = db.measurement_sessions_for(conn, a["id"])
            if sessions:
                athletes_data.append((dict(a), sessions))
    finally:
        conn.close()
    group_dict = scope["group"]
    group_dict["name"] = label
    return Response(views.baseline_report_page(coach, group_dict, athletes_data, resources=resources))


@router.get("/coach/reports/progress")
def reports_progress(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        athletes, label, scope = _resolve_report_scope(req, conn)
        if athletes is None:
            return flash_redirect("/coach/reports", "Please select an organisation or group.")
        resources = conn.execute(
            "SELECT name, self_organisation FROM resources WHERE self_organisation IS NOT NULL"
        ).fetchall()
        athletes_data = []
        for a in athletes:
            sessions = db.measurement_sessions_for(conn, a["id"])
            athletes_data.append((dict(a), sessions))
    finally:
        conn.close()
    group_dict = scope["group"]
    group_dict["name"] = label
    return Response(views.progress_report_page(coach, group_dict, athletes_data, resources=resources))


@router.get("/coach/reports/completion")
def reports_completion(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        athletes, label, scope = _resolve_report_scope(req, conn)
        if athletes is None:
            return flash_redirect("/coach/reports", "Please select an organisation or group.")
        athletes_data = []
        for a in athletes:
            sessions = db.measurement_sessions_for(conn, a["id"])
            athletes_data.append((dict(a), sessions))
    finally:
        conn.close()
    group_dict = scope["group"]
    group_dict["name"] = label
    try:
        pdf_bytes = views.completion_report_pdf(group_dict, athletes_data)
    except Exception:
        import traceback
        return Response(f"<pre style='color:red;padding:20px;'>Error generating PDF:\n{traceback.format_exc()}</pre>", status=500)
    filename = (label or "completion").replace(" ", "_") + ".pdf"
    resp = Response(body=pdf_bytes, content_type="application/pdf")
    resp.headers.append(("Content-Disposition", f'attachment; filename="{filename}"'))
    resp.headers.append(("Content-Length", str(len(pdf_bytes))))
    return resp


@router.get("/coach/group-hub")
def group_hub_get(req):
    """Group Hub — completion matrix + results entry + session sheet PDF in one place."""
    from constants import find_measurement_game
    coach = require_staff(req)
    if not coach:
        return redirect("/login")

    group_id      = req.get_query("group_id")
    session_label = req.get_query("session_label") or None
    session_month = req.get_query("session_month") or None
    game_key      = req.get_query("game_key") or None

    try:
        group_id = int(group_id) if group_id else None
    except (ValueError, TypeError):
        group_id = None

    conn = db.get_conn()
    try:
        groups = conn.execute(
            "SELECT pg.*, o.name AS org_name "
            "FROM participant_groups pg "
            "LEFT JOIN organisations o ON o.id = pg.organisation_id "
            "ORDER BY o.name NULLS LAST, pg.sort_order, pg.name"
        ).fetchall()
        athletes = []
        game     = None
        existing = {}
        completion_data = {}  # {athlete_id: set(game_keys)}

        if group_id and session_label:
            all_athletes = conn.execute(
                "SELECT id, name FROM users WHERE group_id = ? AND role = 'participant' ORDER BY name",
                (group_id,)
            ).fetchall()
            if all_athletes:
                athlete_ids  = [a["id"] for a in all_athletes]
                placeholders = ",".join("?" * len(athlete_ids))
                done_rows = conn.execute(
                    f"SELECT ms.participant_id, mr.game_key "
                    f"FROM measurement_sessions ms "
                    f"JOIN measurement_results mr ON mr.session_id = ms.id "
                    f"WHERE ms.session_label = ? AND ms.participant_id IN ({placeholders}) "
                    f"GROUP BY ms.participant_id, mr.game_key",
                    [session_label] + athlete_ids,
                ).fetchall()
                for r in done_rows:
                    completion_data.setdefault(r["participant_id"], set()).add(r["game_key"])

            athletes = list(all_athletes)

            if game_key:
                game = find_measurement_game(game_key)
                for a in athletes:
                    sess = db.find_session_by_label(conn, a["id"], session_label)
                    if sess:
                        rows = conn.execute(
                            "SELECT field_key, value FROM measurement_results "
                            "WHERE session_id = ? AND game_key = ?",
                            (sess["id"], game_key)
                        ).fetchall()
                        existing[a["id"]] = {r["field_key"]: r["value"] for r in rows}

        # Fetch XP + level data per athlete for the overview panel
        athlete_xp_levels = {}
        for a in athletes:
            try:
                xp = db.get_athlete_xp(conn, a["id"])
                lvs = db.get_all_athlete_levels(conn, a["id"])
                athlete_xp_levels[a["id"]] = {
                    "total_xp": xp.get("total", 0),
                    "tier": xp.get("tier"),
                    "levels": lvs,
                }
            except Exception:
                pass
        # Active window for selected group (if any)
        active_window = None
        recent_windows = []
        if group_id:
            try:
                w = db.get_active_window_for_group(conn, group_id)
                if w:
                    active_window = dict(w)
                recent_windows = [dict(r) for r in db.get_recent_windows_for_group(conn, group_id)]
            except Exception:
                pass
    finally:
        conn.close()

    return Response(views.group_hub_page(
        coach, [dict(g) for g in groups],
        selected_group_id=group_id,
        selected_label=session_label,
        selected_month=session_month,
        selected_game_key=game_key,
        athletes=[dict(a) for a in athletes],
        game=game,
        existing=existing,
        completion_data={k: list(v) for k, v in completion_data.items()},
        athlete_xp_levels=athlete_xp_levels,
        active_window=active_window,
        recent_windows=recent_windows,
    ))


@router.get("/coach/completion-tracker")
def completion_tracker_get(req):
    """Redirect to Group Hub (completion tracker merged there)."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    qs = req.environ.get("QUERY_STRING", "")
    return redirect("/coach/group-hub" + (("?" + qs) if qs else ""))


@router.get("/coach/group-testing")
def group_testing_get(req):
    """Redirect to Group Hub (group testing merged there)."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    qs = req.environ.get("QUERY_STRING", "")
    return redirect("/coach/group-hub" + (("?" + qs) if qs else ""))


@router.post("/coach/group-testing/save")
def group_testing_save(req):
    """Save results for all athletes in a group for a given game+phase."""
    from constants import find_measurement_game
    coach = require_staff(req)
    if not coach:
        return redirect("/login")

    session_label = req.form_get("session_label") or None
    session_month = req.form_get("session_month") or None
    game_key      = req.form_get("game_key") or None
    date = (session_month + "-01") if session_month else db.today()

    if not session_label or not game_key:
        return flash_redirect("/coach/group-testing", "Missing phase or game.")

    game = find_measurement_game(game_key)
    if not game:
        return flash_redirect("/coach/group-testing", "Unknown game.")

    # Collect athlete ids from submitted field names: athlete_{id}__{field_key}
    athlete_fields = {}
    for key, value in req.form.items():
        if not key.startswith("athlete_"):
            continue
        rest = key[len("athlete_"):]
        if "__" not in rest:
            continue
        aid_str, field_key = rest.split("__", 1)
        try:
            aid = int(aid_str)
        except ValueError:
            continue
        val = value.strip() if value else ""
        if not val:
            continue
        try:
            val = float(val)
        except ValueError:
            continue
        if aid not in athlete_fields:
            athlete_fields[aid] = {}
        athlete_fields[aid][field_key] = val

    if not athlete_fields:
        return flash_redirect(f"/coach/group-testing?session_label={session_label}&session_month={session_month or ''}&game_key={game_key}", "No values entered.")

    conn = db.get_conn()
    try:
        saved_athletes = 0
        for aid, fields in athlete_fields.items():
            athlete = conn.execute("SELECT group_id FROM users WHERE id = ?", (aid,)).fetchone()
            if not athlete:
                continue
            session_id = db.find_or_create_session(
                conn, aid, date, coach["id"],
                group_id=athlete["group_id"],
                session_label=session_label,
                session_month=session_month,
            )
            for field_key, value in fields.items():
                db.upsert_measurement_result(conn, session_id, game_key, field_key, value)

            # Recalculate computed fields for this game
            rows = conn.execute(
                "SELECT field_key, value FROM measurement_results WHERE session_id = ? AND game_key = ?",
                (session_id, game_key)
            ).fetchall()
            current = {r["field_key"]: r["value"] for r in rows}
            for comp in game.get("computed", []):
                inputs = [current.get(k) for k in comp["of"]]
                if all(v is not None for v in inputs):
                    result = round(
                        sum(inputs) if comp.get("formula") == "sum_of" else sum(inputs) / len(inputs), 2
                    )
                    db.upsert_measurement_result(conn, session_id, game_key, comp["key"], result)

            saved_athletes += 1
        conn.commit()
    finally:
        conn.close()

    label_display = SESSION_LABEL_MAP.get(session_label, session_label)
    redirect_to = req.form_get("redirect_to") or None
    # Only allow relative redirects to our own pages
    if redirect_to and redirect_to.startswith("/coach/"):
        dest = redirect_to
    else:
        dest = f"/coach/group-hub?session_label={session_label}&session_month={session_month or ''}&game_key={game_key}"
    return flash_redirect(dest, f"{game['name']} results saved for {saved_athletes} athlete(s) — {label_display}.")


@router.get("/coach/session-sheet")
def session_sheet_get(req):
    """Redirect to Group Hub (session sheet merged there)."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    qs = req.environ.get("QUERY_STRING", "")
    return redirect("/coach/group-hub" + (("?" + qs) if qs else ""))


@router.post("/coach/session-sheet/pdf")
def session_sheet_pdf_post(req):
    """Generate and return blank PDF recording sheet."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    from constants import active_measurement_games, SPORT_SPECIFIC_GAMES, find_measurement_game
    session_label  = req.form_get("session_label") or ""
    session_month  = req.form_get("session_month") or ""
    group_id_raw   = req.form_get("group_id") or ""
    include_names  = req.form_get("include_names") == "1"
    num_blank_rows = int(req.form_get("blank_rows") or "0")
    selected_fields = req.form_get_list("fields")  # list of "game_key||field_key"

    # Parse label display
    label_display = SESSION_LABEL_MAP.get(session_label, session_label or "Recording Sheet")
    try:
        import datetime as _dt
        d = _dt.datetime.strptime(session_month, "%Y-%m")
        month_str = d.strftime("%B %Y")
    except Exception:
        month_str = session_month

    conn = db.get_conn()
    try:
        group_name = ""
        athletes = []
        prefilled = {}   # {athlete_name: {game_key: {field_key: value}}}
        if group_id_raw.isdigit():
            gid = int(group_id_raw)
            g = conn.execute("SELECT name FROM participant_groups WHERE id = ?", (gid,)).fetchone()
            group_name = g["name"] if g else ""
            if include_names:
                rows = conn.execute(
                    "SELECT id, name FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
                    (gid,),
                ).fetchall()
                athletes = [r["name"] for r in rows]
                # Load existing results for the selected phase so the PDF can be pre-populated
                if session_label:
                    for r in rows:
                        sess = db.find_session_by_label(conn, r["id"], session_label)
                        if sess:
                            res_rows = conn.execute(
                                "SELECT game_key, field_key, value FROM measurement_results "
                                "WHERE session_id = ? AND value IS NOT NULL AND value != ''",
                                (sess["id"],),
                            ).fetchall()
                            athlete_results = {}
                            for rr in res_rows:
                                athlete_results.setdefault(rr["game_key"], {})[rr["field_key"]] = rr["value"]
                            if athlete_results:
                                prefilled[r["name"]] = athlete_results
        if num_blank_rows > 0:
            athletes += [""] * num_blank_rows
    finally:
        conn.close()

    # Build selected game/field structure
    # selected_fields = ["game_key||field_key", ...]
    # Group by game_key preserving order
    from collections import OrderedDict
    games_fields = OrderedDict()
    all_games = [g for section in active_measurement_games() for g in section["games"]]
    for sf in selected_fields:
        if "||" not in sf:
            continue
        gk, fk = sf.split("||", 1)
        if gk not in games_fields:
            game = next((g for g in all_games if g["key"] == gk), None)
            if not game:
                # check sport-specific
                for sport_sections in SPORT_SPECIFIC_GAMES.values():
                    for sec in sport_sections:
                        for g in sec["games"]:
                            if g["key"] == gk:
                                game = g
                                break
            games_fields[gk] = {"game": game, "fields": []}
        if games_fields[gk]["game"]:
            field = next(
                (f for f in games_fields[gk]["game"]["fields"] if f["key"] == fk),
                None
            )
            if field:
                games_fields[gk]["fields"].append(field)

    try:
        pdf_bytes = views.session_sheet_pdf(
            label_display, month_str, group_name, athletes,
            list(games_fields.values()), prefilled=prefilled,
        )
    except Exception:
        import traceback
        return Response(f"<pre style='color:red;padding:20px;'>PDF error:\n{traceback.format_exc()}</pre>", status=500)

    safe_label = (label_display + "_" + month_str).replace(" ", "_")
    filename = f"session_sheet_{safe_label}.pdf"
    resp = Response(body=pdf_bytes, content_type="application/pdf")
    resp.headers.append(("Content-Disposition", f'attachment; filename="{filename}"'))
    resp.headers.append(("Content-Length", str(len(pdf_bytes))))
    return resp


@router.get("/coach/progress")
def all_progress(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        if coach["role"] in {"org_admin", "system_admin"}:
            # Admins see all groups and ungrouped
            group_groups, ungrouped = db.list_participants_by_group(conn)
            groups_data = []
            for group, participants in group_groups:
                ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group["id"])) for p in participants]
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
                ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=gid)) for p in participants]
                groups_data.append((dict(group), ps_data))
        sport_filter = req.query.get("sport", [""])[0].strip() or None
        level_str = req.query.get("level", [""])[0].strip()
        max_level = int(level_str) if level_str.isdigit() else None
        return Response(views.all_progress_page(coach, groups_data, sport_filter=sport_filter, max_level=max_level))
    finally:
        conn.close()


@router.get("/coach/progress/pdf")
def progress_stats_pdf(req):
    """Download achievement statistics as a PDF.
    Query params:
      scope=group  + group_id=<int>  → single group
      scope=overall                  → all visible groups combined (org_admin / system_admin)
      scope=orgs                     → one section per organisation (system_admin only)
    """
    import traceback as _tb
    coach = require_staff(req)
    if not coach:
        return redirect("/login")

    scope    = req.query.get("scope", ["group"])[0].strip()
    group_id_str = req.query.get("group_id", [""])[0].strip()
    group_id = int(group_id_str) if group_id_str.isdigit() else None

    conn = db.get_conn()
    try:
        role = coach.get("role", "")

        if scope == "group" and group_id:
            # Per-group PDF — any staff member with access to that group
            group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
            if not group:
                return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
            if role not in {"org_admin", "system_admin"}:
                coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
                if group_id not in coach_group_ids:
                    return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
            participants = conn.execute(
                "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
                (group_id,),
            ).fetchall()
            ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group_id)) for p in participants]
            groups_sections = [(group["name"], ps_data)]
            title    = group["name"]
            subtitle = "Achievement Statistics"
            filename = f"stats_{group['name'].replace(' ', '_')}.pdf"

        elif scope == "overall":
            # All visible groups in one PDF — admins see all, practitioners see their assigned groups
            if role in {"org_admin", "system_admin"}:
                group_rows, _ = db.list_participants_by_group(conn)
            else:
                coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
                group_rows = []
                for gid in coach_group_ids:
                    g = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (gid,)).fetchone()
                    if g:
                        parts = conn.execute(
                            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name", (gid,)
                        ).fetchall()
                        group_rows.append((g, parts))
            groups_sections = []
            for group, participants in group_rows:
                ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group["id"])) for p in participants]
                groups_sections.append((group["name"], ps_data))
            title    = "Programme Overview"
            subtitle = "Achievement Statistics — All Groups"
            filename = "stats_all_groups.pdf"

        elif scope == "programme":
            # All athletes pooled into one section — no group/org breakdown
            if role in {"org_admin", "system_admin"}:
                group_rows, ungrouped = db.list_participants_by_group(conn)
                all_participants = [p for _, parts in group_rows for p in parts] + list(ungrouped)
            else:
                coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
                all_participants = []
                for gid in coach_group_ids:
                    parts = conn.execute(
                        "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name", (gid,)
                    ).fetchall()
                    all_participants.extend(parts)
            ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"])) for p in all_participants]
            groups_sections = [("Programme Overview", ps_data)]
            title    = "Programme Overview"
            subtitle = "Overall Achievement Statistics — All Athletes Combined"
            filename = "stats_programme_overall.pdf"

        elif scope == "orgs" and role == "system_admin":
            # One section per organisation, groups nested inside
            orgs = conn.execute(
                "SELECT * FROM organisations ORDER BY name"
            ).fetchall()
            groups_sections = []
            for org in orgs:
                org_groups = conn.execute(
                    "SELECT * FROM participant_groups WHERE organisation_id = ? ORDER BY name",
                    (org["id"],)
                ).fetchall()
                for group in org_groups:
                    parts = conn.execute(
                        "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
                        (group["id"],)
                    ).fetchall()
                    ps_data = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group["id"])) for p in parts]
                    label = f"{org['name']} — {group['name']}"
                    groups_sections.append((label, ps_data))
            title    = "All Organisations"
            subtitle = "Achievement Statistics — System Overview"
            filename = "stats_by_organisation.pdf"

        else:
            return Response(views.simple_message_page("Access denied", "You don't have permission for this report.", user=coach), status=403)

        try:
            pdf_bytes = views.achievement_stats_pdf(title, subtitle, groups_sections)
        except Exception:
            return Response(
                f"<pre style='color:red;padding:20px;'>Error generating PDF:\n{_tb.format_exc()}</pre>",
                status=500
            )

        resp = Response(body=pdf_bytes, content_type="application/pdf")
        resp.headers.append(("Content-Disposition", f'attachment; filename="{filename}"'))
        resp.headers.append(("Content-Length", str(len(pdf_bytes))))
        return resp
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/progress")
def group_progress(req, group_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        # Non-admins can only view their assigned groups
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        participants = conn.execute(
            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()
        participants_sessions = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group_id)) for p in participants]
        level_str = req.query.get("level", [""])[0].strip()
        max_level = int(level_str) if level_str.isdigit() else None
        return Response(views.group_progress_page(coach, dict(group), participants_sessions, max_level=max_level))
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/achievement-summary")
def group_achievement_summary(req, group_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        participants = conn.execute(
            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()
        participants_sessions = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group_id)) for p in participants]
        level_str = req.query.get("level", [""])[0].strip()
        max_level = int(level_str) if level_str.isdigit() else None
        return Response(views.group_achievement_summary_page(coach, dict(group), participants_sessions, max_level=max_level))
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/scores")
def group_scores_table(req, group_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        participants = conn.execute(
            "SELECT * FROM users WHERE role='participant' AND active=1 AND group_id=? ORDER BY name",
            (group_id,),
        ).fetchall()
        participants_sessions = [(dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group_id)) for p in participants]
        level_str = req.query.get("level", [""])[0].strip()
        max_level = int(level_str) if level_str.isdigit() else None
        return Response(views.group_scores_table_page(coach, dict(group), participants_sessions, max_level=max_level))
    finally:
        conn.close()


@router.get("/coach/groups/<int:group_id>/next-steps")
def group_next_steps(req, group_id):
    """Group Next Steps Report — 5-week session planning guide post-testing."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return Response(views.simple_message_page("Not found", "Group not found.", user=coach), status=404)
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if group_id not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this group.", user=coach), status=403)
        athletes_with_levels = db.get_group_athletes_with_levels(conn, group_id)
        thresholds_raw = db.get_all_thresholds(conn)
        return Response(views.group_next_steps_page(
            coach, dict(group), athletes_with_levels, thresholds_raw
        ))
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>/progress")
def coach_participant_progress(req, participant_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'participant'", (participant_id,)
        ).fetchone()
        if not participant:
            return Response(views.simple_message_page("Not found", "Participant not found.", user=coach), status=404)
        if not coach["role"] in {"org_admin", "system_admin"}:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if participant["group_id"] not in coach_group_ids:
                return Response(views.simple_message_page("Access denied", "You don't have access to this participant.", user=coach), status=403)
        measurement_sessions = db.measurement_sessions_for(conn, participant_id)
        return Response(views.participant_progress_page(coach, dict(participant), measurement_sessions))
    finally:
        conn.close()


@router.get("/coach/session")
def group_session_get(req):
    """Rapid-fire group session entry page."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        if coach["role"] in {"org_admin", "system_admin"}:
            participants = conn.execute(
                "SELECT * FROM users WHERE role='participant' AND active=1 ORDER BY name"
            ).fetchall()
            groups = conn.execute(
                "SELECT * FROM participant_groups ORDER BY sort_order, name"
            ).fetchall()
        else:
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
            if not coach_group_ids:
                participants = []
                groups = []
            else:
                placeholders = ",".join("?" * len(coach_group_ids))
                participants = conn.execute(
                    f"SELECT * FROM users WHERE role='participant' AND active=1 AND group_id IN ({placeholders}) ORDER BY name",
                    coach_group_ids,
                ).fetchall()
                groups = conn.execute(
                    f"SELECT * FROM participant_groups WHERE id IN ({placeholders}) ORDER BY sort_order, name",
                    coach_group_ids,
                ).fetchall()
        return Response(views.group_session_page(coach, [dict(p) for p in participants], [dict(g) for g in groups], session_types=SESSION_TYPES))
    finally:
        conn.close()


@router.post("/coach/session/save")
def group_session_save(req):
    """Rapid-fire save: find-or-create session for athlete+date, upsert one field."""
    import json
    from constants import find_measurement_game
    coach = require_staff(req)
    if not coach:
        return Response('{"error":"unauthenticated"}', status=401, content_type="application/json")
    try:
        athlete_id = int(req.form_get("athlete_id"))
    except (ValueError, TypeError):
        return Response('{"error":"invalid athlete"}', status=400, content_type="application/json")
    date          = req.form_get("date") or db.today()
    session_label = req.form_get("session_label") or None
    session_month = req.form_get("session_month") or None
    game_key      = req.form_get("game_key")
    field_key     = req.form_get("field_key")
    raw           = req.form_get("value").strip()
    if session_month:
        date = session_month + "-01"
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return Response('{"error":"invalid value"}', status=400, content_type="application/json")
    conn = db.get_conn()
    try:
        athlete = conn.execute("SELECT group_id FROM users WHERE id = ?", (athlete_id,)).fetchone()
        athlete_group_id = athlete["group_id"] if athlete else None
        session_id = db.find_or_create_session(conn, athlete_id, date, coach["id"], group_id=athlete_group_id,
                                               session_label=session_label, session_month=session_month)
        db.upsert_measurement_result(conn, session_id, game_key, field_key, value)
        # Recalculate computed fields
        computed_updates = {}
        game = find_measurement_game(game_key)
        if game:
            rows = conn.execute(
                "SELECT field_key, value FROM measurement_results WHERE session_id = ? AND game_key = ?",
                (session_id, game_key),
            ).fetchall()
            current = {r["field_key"]: r["value"] for r in rows}
            for comp in game.get("computed", []):
                inputs = [current.get(k) for k in comp["of"]]
                if all(v is not None for v in inputs):
                    result = round(sum(inputs) if comp.get("formula") == "sum_of" else sum(inputs) / len(inputs), 2)
                    db.upsert_measurement_result(conn, session_id, game_key, comp["key"], result)
                    computed_updates[comp["key"]] = result
        return Response(json.dumps({"ok": True, "session_id": session_id, "computed": computed_updates}),
                        content_type="application/json")
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/measurement/start")
def start_measurement_session(req, participant_id):
    """Quick-save: create a bare session and return its id as JSON."""
    import json
    coach = require_staff(req)
    if not coach:
        return Response('{"error":"unauthenticated"}', status=401, content_type="application/json")
    date          = req.form_get("date") or db.today()
    session_label = req.form_get("session_label") or None
    session_month = req.form_get("session_month") or None
    if session_month:
        date = session_month + "-01"
    conn = db.get_conn()
    try:
        participant = conn.execute("SELECT group_id FROM users WHERE id = ?", (participant_id,)).fetchone()
        participant_group_id = participant["group_id"] if participant else None
        # Reuse existing session for this label rather than always creating a new one
        session_id = db.find_or_create_session(conn, participant_id, date, coach["id"],
                                               group_id=participant_group_id,
                                               session_label=session_label, session_month=session_month)
        return Response(json.dumps({"session_id": session_id}), content_type="application/json")
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>/measurement/phase-results")
def measurement_phase_results(req, participant_id):
    """Return existing results for a phase label as JSON, for pre-filling the form."""
    import json
    coach = require_staff(req)
    if not coach:
        return Response('{"error":"unauthenticated"}', status=401, content_type="application/json")
    label = req.get_query("label") or ""
    if not label:
        return Response("{}", content_type="application/json")
    conn = db.get_conn()
    try:
        existing = db.find_session_by_label(conn, participant_id, label)
        if not existing:
            return Response("{}", content_type="application/json")
        rows = conn.execute(
            "SELECT game_key, field_key, value FROM measurement_results WHERE session_id = ?",
            (existing["id"],)
        ).fetchall()
        data = {}
        for r in rows:
            gk, fk, v = r["game_key"], r["field_key"], r["value"]
            if gk not in data:
                data[gk] = {}
            data[gk][fk] = v
        return Response(json.dumps({"results": data, "session_id": existing["id"],
                                    "session_month": existing.get("session_month") or ""}),
                        content_type="application/json")
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/measurement/<int:session_id>/save-field")
def save_measurement_field(req, participant_id, session_id):
    """Quick-save: upsert one field and return updated computed values as JSON."""
    import json
    from constants import find_measurement_game
    coach = require_staff(req)
    if not coach:
        return Response('{"error":"unauthenticated"}', status=401, content_type="application/json")
    game_key  = req.form_get("game_key")
    field_key = req.form_get("field_key")
    raw       = req.form_get("value").strip()
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return Response('{"error":"invalid value"}', status=400, content_type="application/json")

    conn = db.get_conn()
    try:
        # Verify session belongs to this participant
        session = conn.execute(
            "SELECT id FROM measurement_sessions WHERE id = ? AND participant_id = ?",
            (session_id, participant_id),
        ).fetchone()
        if not session:
            return Response('{"error":"not found"}', status=404, content_type="application/json")

        db.upsert_measurement_result(conn, session_id, game_key, field_key, value)

        # Recalculate computed fields for this game (e.g. skipping rope average)
        computed_updates = {}
        game = find_measurement_game(game_key)
        if game:
            # Load current values for all fields in this game
            rows = conn.execute(
                "SELECT field_key, value FROM measurement_results WHERE session_id = ? AND game_key = ?",
                (session_id, game_key),
            ).fetchall()
            current = {r["field_key"]: r["value"] for r in rows}
            for comp in game.get("computed", []):
                inputs = [current.get(k) for k in comp["of"]]
                if all(v is not None for v in inputs):
                    result = round(sum(inputs) if comp.get("formula") == "sum_of" else sum(inputs) / len(inputs), 2)
                    db.upsert_measurement_result(conn, session_id, game_key, comp["key"], result)
                    computed_updates[comp["key"]] = result

        return Response(json.dumps({"ok": True, "computed": computed_updates}),
                        content_type="application/json")
    finally:
        conn.close()


@router.post("/coach/participants/<int:participant_id>/measurement")
def log_measurement_session(req, participant_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    # Check group access for non-admins
    if not coach["role"] in {"org_admin", "system_admin"}:
        conn = db.get_conn()
        try:
            p = conn.execute("SELECT group_id FROM users WHERE id = ?", (participant_id,)).fetchone()
            coach_group_ids = db.get_coach_group_ids(conn, coach["id"])
        finally:
            conn.close()
        if not p or p["group_id"] not in coach_group_ids:
            return flash_redirect("/coach/groups", "You don't have access to that participant.")
    session_label  = req.form_get("session_label") or None
    session_month  = req.form_get("session_month") or None
    confirm_replace = req.form_get("confirm_replace") == "1"
    date = (session_month + "-01") if session_month else (req.form_get("date") or db.today())

    results = []
    for game in all_active_measurement_games():
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
                result = round(sum(inputs) if computed.get("formula") == "sum_of" else sum(inputs) / len(inputs), 2)
                results.append((game["key"], computed["key"], result))

    if not results:
        return flash_redirect(
            f"/coach/participants/{participant_id}",
            "No results entered -- fill in at least one field before saving.",
        )

    conn = db.get_conn()
    try:
        participant = conn.execute("SELECT * FROM users WHERE id = ?", (participant_id,)).fetchone()
        participant_group_id = participant["group_id"] if participant else None

        # Duplicate session warning
        if session_label and not confirm_replace:
            existing = db.find_session_by_label(conn, participant_id, session_label)
            if existing:
                label_display = SESSION_LABEL_MAP.get(session_label, session_label)
                existing_month = existing.get("session_month") or existing.get("date", "")[:7]
                return Response(views.confirm_replace_session_page(
                    coach, dict(participant), results, session_label, session_month,
                    label_display, existing_month
                ))

        # Merge new results into existing session for this label
        saved_session_id = None
        if session_label and confirm_replace:
            existing = db.find_session_by_label(conn, participant_id, session_label)
            if existing:
                for (game_key, field_key, value) in results:
                    db.upsert_measurement_result(conn, existing["id"], game_key, field_key, value)
                conn.commit()
                saved_session_id = existing["id"]
            else:
                saved_session_id = db.create_measurement_session(
                    conn, participant_id, date, coach["id"], results,
                    group_id=participant_group_id,
                    session_label=session_label, session_month=session_month)
        else:
            saved_session_id = db.create_measurement_session(
                conn, participant_id, date, coach["id"], results,
                group_id=participant_group_id,
                session_label=session_label, session_month=session_month)

        # ── XP Engine: process this session (formal test) ──────────────────
        if saved_session_id:
            try:
                db.process_session_xp(conn, saved_session_id, participant_id, is_formal=True)
            except Exception as _xp_err:
                pass  # XP failure never blocks session save
    finally:
        conn.close()
    label_display = SESSION_LABEL_MAP.get(session_label, "") if session_label else ""
    if label_display:
        msg = f"{label_display} results merged in." if confirm_replace else f"{label_display} results saved."
    else:
        msg = "Measurement Games results saved."
    return flash_redirect(f"/coach/participants/{participant_id}", msg)


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
            return flash_redirect("/coach/groups", "Participant not found.")
        temp_password = generate_temp_password()
        db.update_password(conn, participant_id, temp_password)
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (participant_id,))
        conn.commit()
        p_email = participant.get("email") or ""
        if p_email:
            emailed = mailer.send_password_reset(participant["name"], p_email, temp_password)
        else:
            emailed = False
        if emailed:
            return flash_redirect(
                f"/coach/participants/{participant_id}",
                f"Password reset for {participant['name']}. New password emailed to {p_email}.",
            )
        else:
            return flash_redirect(
                f"/coach/participants/{participant_id}",
                f"Password reset for {participant['name']}. New password: {temp_password} "
                f"-- share this with them now, it won't be shown again.",
            )
    finally:
        conn.close()


@router.get("/coach/participants/<int:participant_id>/measurement/<int:session_id>/edit")
def edit_measurement_session(req, participant_id, session_id):
    """Render the measurement form pre-filled with an existing session's results."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        session = conn.execute(
            "SELECT * FROM measurement_sessions WHERE id = ? AND participant_id = ?",
            (session_id, participant_id),
        ).fetchone()
        if not session:
            return flash_redirect(f"/coach/participants/{participant_id}", "Session not found.")
        participant = conn.execute("SELECT * FROM users WHERE id = ?", (participant_id,)).fetchone()
    finally:
        conn.close()
    s = dict(session)
    return Response(views.edit_measurement_session_page(
        coach, dict(participant), participant_id,
        selected_label=s.get("session_label"),
        selected_month=s.get("session_month"),
    ))


@router.get("/coach/admin/sessions")
def admin_sessions_get(req):
    """System-admin tool: view all sessions for a group so duplicates can be deleted."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        groups = conn.execute(
            "SELECT pg.*, o.name AS org_name FROM participant_groups pg "
            "LEFT JOIN organisations o ON o.id = pg.organisation_id "
            "ORDER BY o.name NULLS LAST, pg.name"
        ).fetchall()
        group_id_str = req.query.get("group_id", [""])[0].strip()
        group_id = int(group_id_str) if group_id_str.isdigit() else None
        athlete_sessions = None
        if group_id:
            participants = conn.execute(
                "SELECT * FROM users WHERE group_id = ? AND role = 'participant' ORDER BY name",
                (group_id,),
            ).fetchall()
            athlete_sessions = [
                (dict(p), db.measurement_sessions_for(conn, p["id"], group_id=group_id))
                for p in participants
            ]
        # Always load ungrouped athletes so the panel is always visible
        ungrouped_rows = conn.execute(
            "SELECT u.*, "
            "(SELECT COUNT(*) FROM measurement_sessions ms WHERE ms.participant_id = u.id) AS _session_count "
            "FROM users u WHERE u.role = 'participant' AND (u.group_id IS NULL OR u.group_id = 0) "
            "ORDER BY u.name"
        ).fetchall()
        ungrouped = [dict(r) for r in ungrouped_rows]

        flash = req.query.get("flash", [""])[0] or None
        return Response(views.admin_sessions_page(
            coach, [dict(g) for g in groups],
            selected_group_id=group_id,
            athlete_sessions=athlete_sessions,
            flash=flash,
            ungrouped=ungrouped,
        ))
    finally:
        conn.close()


@router.post("/coach/admin/sessions/merge")
def admin_sessions_merge(req):
    """System-admin: merge all sessions for every athlete in a group into one baseline."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    group_id_str = req.form_get("group_id").strip()
    target_month = req.form_get("target_month").strip() or None
    group_id = int(group_id_str) if group_id_str.isdigit() else None
    if not group_id:
        return redirect("/coach/admin/sessions")
    conn = db.get_conn()
    try:
        athletes_merged, sessions_removed = db.merge_sessions_for_group(
            conn, group_id, target_label="baseline", target_month=target_month
        )
    finally:
        conn.close()
    msg = f"Merged+{athletes_merged}+athlete(s),+removed+{sessions_removed}+extra+session(s).+All+labelled+Baseline."
    return redirect(f"/coach/admin/sessions?group_id={group_id}&flash={msg}")


@router.post("/coach/admin/athletes/delete")
def admin_athlete_delete(req):
    """System-admin: permanently delete a single participant and all their data."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    participant_id_str = req.form_get("participant_id").strip()
    participant_id = int(participant_id_str) if participant_id_str.isdigit() else None
    if participant_id:
        conn = db.get_conn()
        try:
            db.delete_participant(conn, participant_id)
        finally:
            conn.close()
    return redirect("/coach/admin/sessions?flash=Athlete+deleted.")


@router.post("/coach/admin/athletes/delete-ungrouped")
def admin_athletes_delete_ungrouped(req):
    """System-admin: permanently delete all ungrouped participants."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        ungrouped = conn.execute(
            "SELECT id FROM users WHERE role = 'participant' AND (group_id IS NULL OR group_id = 0)"
        ).fetchall()
        count = len(ungrouped)
        for row in ungrouped:
            db.delete_participant(conn, row["id"])
    finally:
        conn.close()
    return redirect(f"/coach/admin/sessions?flash={count}+ungrouped+athlete(s)+permanently+deleted.")


@router.post("/coach/admin/sessions/delete")
def admin_sessions_delete(req):
    """System-admin: delete a specific measurement session."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    session_id_str = req.form_get("session_id").strip()
    group_id_str   = req.form_get("group_id").strip()
    session_id = int(session_id_str) if session_id_str.isdigit() else None
    group_id   = int(group_id_str)   if group_id_str.isdigit()   else None
    if session_id:
        conn = db.get_conn()
        try:
            db.delete_measurement_session(conn, session_id)
        finally:
            conn.close()
    redirect_url = f"/coach/admin/sessions?group_id={group_id or ''}&flash=Session+deleted."
    return redirect(redirect_url)


@router.post("/coach/participants/<int:participant_id>/measurement/<int:session_id>/delete")
def delete_measurement_session(req, participant_id, session_id):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_measurement_session(conn, session_id)
    finally:
        conn.close()
    return flash_redirect(f"/coach/participants/{participant_id}", "Measurement Games session deleted.")


# ----------------------------------------------------------------- help page


@router.get("/help")
def help_get(req):
    user = get_current_user(req)
    if not user:
        return redirect("/login")
    return Response(views.help_page(user))


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
        organisations = db.list_organisations(conn)
        coach_group_map = {c["id"]: db.get_coach_group_ids(conn, c["id"]) for c in coaches}
        message = req.get_query("flash")
        return Response(views.coach_list_page(coach, coaches, groups=groups, coach_group_map=coach_group_map, organisations=organisations, message=message))
    finally:
        conn.close()


@router.get("/coach/coaches/new")
def new_coach_get(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        organisations = db.list_organisations(conn)
        return Response(views.new_coach_form(coach, organisations=organisations))
    finally:
        conn.close()


@router.post("/coach/coaches/new")
def new_coach_post(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    email = req.form_get("email").strip().lower()
    password = req.form_get("password") or "CoachTemp123!"
    org_id_raw = req.form_get("organisation_id").strip()

    if not name or not email:
        conn = db.get_conn()
        try:
            organisations = db.list_organisations(conn)
        finally:
            conn.close()
        return Response(views.new_coach_form(coach, error="Name and email are required.", organisations=organisations), status=400)

    conn = db.get_conn()
    try:
        organisations = db.list_organisations(conn)
        existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if existing:
            return Response(views.new_coach_form(coach, error="A user with that email already exists.", organisations=organisations), status=400)
        org_id = int(org_id_raw) if org_id_raw.isdigit() else None
        # Set users.organisation text field from org name for display compat
        org_name = None
        if org_id:
            org_row = db.get_organisation(conn, org_id)
            org_name = org_row["name"] if org_row else None
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, organisation, organisation_id, sport, programme, created_at) "
            "VALUES (?, ?, ?, 'practitioner', ?, ?, NULL, NULL, ?)",
            (name, email, hash_password(password), org_name, org_id, db.now()),
        )
        conn.commit()
        emailed = mailer.send_welcome_coach(name, email, password)
        if emailed:
            return flash_redirect("/coach/coaches", f"Added practitioner {name}. Welcome email sent to {email}.")
        else:
            return flash_redirect("/coach/coaches", f"Added practitioner {name}. Share their login: {email} / {password}")
    finally:
        conn.close()


@router.post("/coach/coaches/<int:coach_id>/reset-password")
def reset_coach_password(req, coach_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role IN ('practitioner','org_admin','system_admin')", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Practitioner not found.")
        temp_password = generate_temp_password()
        db.update_password(conn, coach_id, temp_password)
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (coach_id,))
        conn.commit()
        t_email = target.get("email") or ""
        if t_email:
            emailed = mailer.send_password_reset(target["name"], t_email, temp_password)
        else:
            emailed = False
        if emailed:
            return flash_redirect(
                "/coach/coaches",
                f"Password reset for {target['name']}. New password emailed to {t_email}.",
            )
        else:
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
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role IN ('practitioner','org_admin','system_admin')", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Practitioner not found.")
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
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role IN ('practitioner','org_admin','system_admin')", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Practitioner not found.")
        new_active = 0 if target["active"] else 1
        db.set_active(conn, coach_id, new_active)
        action = "reactivated" if new_active else "deactivated"
        return flash_redirect("/coach/coaches", f"{target['name']} {action}.")
    finally:
        conn.close()


# --------------------------------------------------------- coach org assignment


@router.post("/coach/coaches/<int:coach_id>/assign-org")
def assign_coach_org(req, coach_id):
    admin = require_admin(req)
    if not admin:
        return redirect("/login")
    org_id_raw = req.form_get("organisation_id").strip()
    org_id = int(org_id_raw) if org_id_raw.isdigit() else None
    conn = db.get_conn()
    try:
        target = conn.execute("SELECT * FROM users WHERE id = ? AND role IN ('practitioner','org_admin','system_admin')", (coach_id,)).fetchone()
        if not target:
            return flash_redirect("/coach/coaches", "Practitioner not found.")
        # Also update the text field for display compat
        org_name = None
        if org_id:
            org_row = db.get_organisation(conn, org_id)
            org_name = org_row["name"] if org_row else None
        conn.execute(
            "UPDATE users SET organisation_id = ?, organisation = ? WHERE id = ?",
            (org_id, org_name, coach_id),
        )
        conn.commit()
        label = org_name or "none"
        return flash_redirect("/coach/coaches", f"Organisation for {target['name']} set to {label}.")
    finally:
        conn.close()


# --------------------------------------------------------- organisations (admin)


@router.get("/coach/organisations")
def organisations_list(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        orgs = db.list_organisations(conn)
        # Augment with group count and coach count
        orgs_data = []
        for o in orgs:
            group_count = conn.execute(
                "SELECT COUNT(*) AS c FROM participant_groups WHERE organisation_id = ?", (o["id"],)
            ).fetchone()["c"]
            coach_count = conn.execute(
                "SELECT COUNT(*) AS c FROM users WHERE role IN ('practitioner','org_admin','system_admin') AND organisation_id = ?", (o["id"],)
            ).fetchone()["c"]
            orgs_data.append({"org": o, "group_count": group_count, "coach_count": coach_count})
        message = req.get_query("flash")
        return Response(views.organisations_page(coach, orgs_data, message=message))
    finally:
        conn.close()


@router.post("/coach/organisations/new")
def organisation_new(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    org_type = req.form_get("type").strip() or None
    icon_url = req.form_get("icon_url").strip() or None
    if not name:
        return flash_redirect("/coach/organisations", "Organisation name is required.")
    conn = db.get_conn()
    try:
        db.add_organisation(conn, name, org_type, icon_url=icon_url)
        return flash_redirect("/coach/organisations", f'Organisation "{name}" created.')
    finally:
        conn.close()


@router.get("/coach/organisations/<int:org_id>/edit")
def organisation_edit_get(req, org_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        org = db.get_organisation(conn, org_id)
        if not org:
            return flash_redirect("/coach/organisations", "Organisation not found.")
        return Response(views.organisation_form(coach, org=org))
    finally:
        conn.close()


@router.post("/coach/organisations/<int:org_id>/edit")
def organisation_edit_post(req, org_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("name").strip()
    org_type = req.form_get("type").strip() or None
    icon_url = req.form_get("icon_url").strip() or None
    if not name:
        conn = db.get_conn()
        try:
            org = db.get_organisation(conn, org_id)
        finally:
            conn.close()
        return Response(views.organisation_form(coach, org=org, error="Name is required."), status=400)
    conn = db.get_conn()
    try:
        db.update_organisation(conn, org_id, name, org_type, icon_url=icon_url)
        return flash_redirect("/coach/organisations", f'Organisation "{name}" updated.')
    finally:
        conn.close()


@router.post("/coach/organisations/<int:org_id>/delete")
def organisation_delete(req, org_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        org = db.get_organisation(conn, org_id)
        if not org:
            return flash_redirect("/coach/organisations", "Organisation not found.")
        db.delete_organisation(conn, org_id)
        return flash_redirect("/coach/organisations", f'Organisation "{org["name"]}" deleted.')
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
        return flash_redirect("/coach/groups", "Group name is required.")
    conn = db.get_conn()
    try:
        db.add_participant_group(conn, name, coach["id"])
        return flash_redirect("/coach/groups", f'Group "{name}" created.')
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
    show_leaderboard = 1 if req.form_get("show_leaderboard") else 0
    if not name:
        conn = db.get_conn()
        try:
            group = conn.execute("SELECT * FROM participant_groups WHERE id = ?", (group_id,)).fetchone()
            return Response(views.edit_group_page(coach, dict(group), error="Group name is required."), status=400)
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        db.update_participant_group(conn, group_id, name, icon_url, show_leaderboard=show_leaderboard)
        return flash_redirect("/coach/groups", f'Group "{name}" updated.')
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
        return flash_redirect("/coach/groups", "Group deleted. Participants moved to ungrouped.")
    finally:
        conn.close()


@router.post("/coach/groups/<int:group_id>/relabel-sessions")
def group_relabel_sessions(req, group_id):
    """Bulk-tag all unlabelled sessions for a group with a phase label and month."""
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    session_label = req.form_get("session_label") or None
    session_month = req.form_get("session_month") or None
    if not session_label or not session_month:
        return flash_redirect("/coach/groups", "Please select both a phase and a month.")
    conn = db.get_conn()
    try:
        updated = db.relabel_unlabelled_sessions(conn, group_id, session_label, session_month)
    finally:
        conn.close()
    label_display = SESSION_LABEL_MAP.get(session_label, session_label)
    return flash_redirect("/coach/groups", f"{updated} session(s) labelled as '{label_display}'.")


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
    coach = require_staff(req)
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
    self_organisation = req.form_get("self_organisation").strip() or None
    folder_id = req.form_get("folder_id").strip() or None
    if not name or not url:
        conn = db.get_conn()
        try:
            return _resources_page_response(coach, conn, error="Name and URL are required.", status=400)
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        conn.execute(
            "INSERT INTO resources (name, description, url, self_organisation, added_by, folder_id, sort_order, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order),-1)+1 FROM resources), ?)",
            (name, description or None, url, self_organisation, coach["id"], folder_id or None, db.now()),
        )
        conn.commit()
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
        selected_game_keys = db.get_resource_game_keys(conn, resource_id)
        taxonomy_tags = db.get_resource_taxonomy_tags(conn, resource_id)
        return Response(views.edit_resource_page(
            coach, dict(resource), folders,
            selected_game_keys=selected_game_keys,
            taxonomy_tags=taxonomy_tags,
        ))
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
    self_organisation = req.form_get("self_organisation").strip() or None
    folder_id = req.form_get("folder_id").strip() or None
    level_range = req.form_get("level_range").strip() or "multi_level"
    space_requirement = req.form_get("space_requirement").strip() or "unspecified"
    game_keys = [g.strip() for g in req.form_get_list("game_keys") if g.strip()]
    # Collect taxonomy multi-select dimensions
    taxonomy_tags = {}
    for dim in ("D1", "D2", "D3", "D4", "D6", "D8"):
        vals = [v.strip() for v in req.form_get_list(f"tax_{dim}") if v.strip()]
        if vals:
            taxonomy_tags[dim] = vals
    if not name or not url:
        conn = db.get_conn()
        try:
            resource = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
            folders = db.list_folders(conn)
            selected_game_keys = db.get_resource_game_keys(conn, resource_id)
            existing_tax = db.get_resource_taxonomy_tags(conn, resource_id)
            return Response(
                views.edit_resource_page(
                    coach, dict(resource), folders,
                    selected_game_keys=selected_game_keys,
                    taxonomy_tags=existing_tax,
                    error="Name and URL are required.",
                ),
                status=400,
            )
        finally:
            conn.close()
    conn = db.get_conn()
    try:
        db.update_resource(conn, resource_id, name, description, url, folder_id,
                           self_organisation=self_organisation, level_range=level_range,
                           space_requirement=space_requirement)
        db.set_resource_game_keys(conn, resource_id, game_keys)
        db.set_resource_taxonomy_tags(conn, resource_id, taxonomy_tags)
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
    coach = require_staff(req)
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


@router.get("/coach/resources/report")
def resources_report(req):
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    org_id_raw = req.query.get("org_id", [""])[0].strip()
    org_id = int(org_id_raw) if org_id_raw.isdigit() else None
    conn = db.get_conn()
    try:
        folder_groups, ungrouped = db.list_resources_by_folder(conn)
        # Flatten all resources preserving folder grouping
        all_folders = [(f, rs) for f, rs in folder_groups if rs] + ([("__ungrouped__", ungrouped)] if ungrouped else [])
        org = db.get_organisation(conn, org_id) if org_id else None
        orgs = db.list_organisations(conn)
    finally:
        conn.close()
    return Response(views.resources_report_page(coach, all_folders, org=org, orgs=orgs))


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


@router.post("/coach/resources/folders/<int:folder_id>/rename")
def folder_rename(req, folder_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("folder_name").strip()
    if not name:
        return flash_redirect("/coach/resources", "Folder name cannot be empty.")
    conn = db.get_conn()
    try:
        db.rename_folder(conn, folder_id, name)
        return flash_redirect("/coach/resources", f'Folder renamed to "{name}".')
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
    coach = require_staff(req)
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


@router.post("/coach/resources/tags/new")
def tag_new(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    name = req.form_get("tag_name").strip()
    if not name:
        return flash_redirect("/coach/resources", "Tag name is required.")
    conn = db.get_conn()
    try:
        db.add_tag(conn, name)
        return flash_redirect("/coach/resources", f'Tag "{name}" created.')
    except Exception:
        return flash_redirect("/coach/resources", f'Tag "{name}" already exists.')
    finally:
        conn.close()


@router.post("/coach/resources/tags/<int:tag_id>/delete")
def tag_delete(req, tag_id):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        db.delete_tag(conn, tag_id)
        return flash_redirect("/coach/resources", "Tag deleted.")
    finally:
        conn.close()


# ---------------------------------------------------------- CSV import / export


@router.get("/coach/participants/import")
def participant_import_get(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    return Response(views.participant_import_form(coach))


@router.post("/coach/participants/import")
def participant_import_post(req):
    import csv
    import io
    coach = require_admin(req)
    if not coach:
        return redirect("/login")

    # Accept either an uploaded file or pasted textarea content
    file_bytes = req.form_file("csv_file")
    if file_bytes:
        try:
            raw_csv = file_bytes.decode("utf-8-sig").strip()  # utf-8-sig strips Excel BOM
        except UnicodeDecodeError:
            raw_csv = file_bytes.decode("latin-1").strip()
    else:
        raw_csv = req.form_get("csv_data").strip()
    if not raw_csv:
        return Response(views.participant_import_form(coach, error="Please upload a CSV file or paste CSV data below."), status=400)

    # Strip leading blank lines (Excel/Numbers sometimes exports an empty first row)
    lines = [ln for ln in raw_csv.splitlines() if ln.strip().strip(",")]
    raw_csv = "\n".join(lines)

    reader = csv.DictReader(io.StringIO(raw_csv))
    # Accept either "first name"+"last name" pair OR a single "name" column
    norm_fields = {f.strip().lower() for f in (reader.fieldnames or [])}
    has_split_name = "first name" in norm_fields and "last name" in norm_fields
    has_full_name  = "name" in norm_fields
    if not (has_split_name or has_full_name):
        return Response(
            views.participant_import_form(coach, error="CSV must have either a 'name' column or both 'first name' and 'last name' columns."),
            status=400,
        )

    # Normalise column names to lowercase stripped versions
    def col(row, *keys):
        for k in keys:
            for fk in (row or {}):
                if fk.strip().lower() == k:
                    v = row[fk]
                    return v.strip() if v else ""
        return ""

    created, skipped, errors = 0, 0, []
    conn = db.get_conn()
    try:
        for i, row in enumerate(reader, start=2):  # row 1 = header
            # Build full name from split columns or single column
            if has_split_name:
                first = col(row, "first name")
                last  = col(row, "last name")
                name  = f"{first} {last}".strip()
            else:
                name = col(row, "name")
            if not name:
                errors.append(f"Row {i}: name is empty — skipped.")
                skipped += 1
                continue

            athlete_number_raw = col(row, "athlete_number")
            sport        = col(row, "sport") or None
            gender       = col(row, "gender") or None
            organisation = col(row, "organisation") or None
            group_name   = col(row, "group", "group_name") or None
            username     = col(row, "username") or None

            # Deduplication: if athlete_number supplied and already exists, skip
            if athlete_number_raw:
                existing = conn.execute(
                    "SELECT id FROM users WHERE athlete_number = ?", (athlete_number_raw,)
                ).fetchone()
                if existing:
                    errors.append(f"Row {i}: athlete #{athlete_number_raw} already exists — skipped.")
                    skipped += 1
                    continue

            # Resolve organisation → organisations table
            org_id = None
            if organisation:
                org_id = db.find_or_create_organisation(conn, organisation)

            # Resolve group (link to org if known)
            group_id = None
            if group_name:
                group_id = db.find_or_create_group(conn, group_name, coach["id"], organisation_id=org_id)

            # Check username uniqueness
            if username:
                existing_u = conn.execute(
                    "SELECT id FROM users WHERE lower(username) = ?", (username.lower(),)
                ).fetchone()
                if existing_u:
                    errors.append(f"Row {i}: username '{username}' already taken — skipped.")
                    skipped += 1
                    continue

            import secrets as _sec
            placeholder_email = f"_csv_{_sec.token_hex(8)}@noreply.local"
            pid = conn.execute(
                "INSERT INTO users (name, username, email, password_hash, role, sport, gender, organisation, group_id, created_at) "
                "VALUES (?, ?, ?, '', 'participant', ?, ?, ?, ?, ?)",
                (name, username or None, placeholder_email, sport, gender, organisation, group_id, db.now()),
            ).lastrowid

            # Use supplied athlete_number or auto-assign
            if athlete_number_raw:
                an = athlete_number_raw
            else:
                an = db.next_athlete_number(conn)
            conn.execute("UPDATE users SET athlete_number = ? WHERE id = ?", (an, pid))
            conn.commit()
            created += 1
    finally:
        conn.close()

    summary = f"Import complete: {created} added, {skipped} skipped."
    if errors:
        summary += " Issues: " + " | ".join(errors)
    return flash_redirect("/coach/groups", summary)


# ---------------------------------------------------------------------------
# Score CSV import
# ---------------------------------------------------------------------------

@router.get("/coach/scores/import")
def scores_import_get(req):
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        groups = conn.execute(
            "SELECT id, name FROM participant_groups ORDER BY sort_order, name"
        ).fetchall()
        orgs = db.list_organisations(conn)
    finally:
        conn.close()
    return Response(views.scores_import_form(coach, groups=groups, orgs=orgs))


@router.get("/coach/scores/import/template.csv")
def scores_import_template(req):
    import csv, io
    coach = require_admin(req)
    if not coach:
        return redirect("/login")
    from constants import active_measurement_games

    group_id_raw = req.query.get("group_id", [""])[0].strip()
    org_id_raw   = req.query.get("org_id",   [""])[0].strip()
    group_id = int(group_id_raw) if group_id_raw.isdigit() else None
    org_id   = int(org_id_raw)   if org_id_raw.isdigit()   else None

    # Fetch athletes for the filter (if any)
    athletes = []
    filename = "scores_template.csv"
    conn = db.get_conn()
    try:
        if group_id:
            athletes = conn.execute(
                "SELECT athlete_number, name FROM users WHERE role='participant' AND group_id=? "
                "ORDER BY CAST(athlete_number AS INTEGER), name",
                (group_id,)
            ).fetchall()
            row = conn.execute("SELECT name FROM participant_groups WHERE id=?", (group_id,)).fetchone()
            label = row["name"].replace(" ", "_") if row else f"group{group_id}"
            filename = f"scores_{label}.csv"
        elif org_id:
            athletes = conn.execute(
                "SELECT u.athlete_number, u.name FROM users u "
                "JOIN participant_groups pg ON u.group_id = pg.id "
                "WHERE u.role='participant' AND pg.organisation_id=? "
                "ORDER BY CAST(u.athlete_number AS INTEGER), u.name",
                (org_id,)
            ).fetchall()
            row = conn.execute("SELECT name FROM organisations WHERE id=?", (org_id,)).fetchone()
            label = row["name"].replace(" ", "_") if row else f"org{org_id}"
            filename = f"scores_{label}.csv"
    finally:
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header: athlete_number, name (reference), then all score columns
    headers = ["athlete_number", "name"]
    for section in active_measurement_games():
        for game in section["games"]:
            for field in game.get("fields", []):
                headers.append(f"{game['key']}.{field['key']}")
            for field in game.get("computed", []):
                headers.append(f"{game['key']}.{field['key']}")
    writer.writerow(headers)

    if athletes:
        for a in athletes:
            row_data = [a["athlete_number"] or "", a["name"]] + [""] * (len(headers) - 2)
            writer.writerow(row_data)
    else:
        # Blank example row
        writer.writerow(["", ""] + [""] * (len(headers) - 2))

    body = output.getvalue().encode("utf-8")
    resp = Response(body=body, content_type="text/csv; charset=utf-8")
    resp.headers.append(("Content-Disposition", f'attachment; filename="{filename}"'))
    resp.headers.append(("Content-Length", str(len(body))))
    return resp


@router.post("/coach/scores/import")
def scores_import_post(req):
    import csv, io
    from constants import find_any_game, active_measurement_games
    coach = require_admin(req)
    if not coach:
        return redirect("/login")

    file_bytes = req.form_file("csv_file")
    if file_bytes:
        try:
            raw_csv = file_bytes.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            raw_csv = file_bytes.decode("latin-1").strip()
    else:
        raw_csv = req.form_get("csv_data", "").strip()

    session_date = req.form_get("session_date", "").strip()
    group_id_raw = req.form_get("group_id", "").strip()
    group_id = int(group_id_raw) if group_id_raw else None

    conn = db.get_conn()
    try:
        groups = conn.execute(
            "SELECT id, name FROM participant_groups ORDER BY sort_order, name"
        ).fetchall()
    finally:
        conn.close()

    if not raw_csv:
        return Response(views.scores_import_form(coach, groups=groups,
            error="Please upload a CSV file or paste CSV data."), status=400)
    if not session_date:
        return Response(views.scores_import_form(coach, groups=groups,
            error="Please enter a session date."), status=400)

    lines = [ln for ln in raw_csv.splitlines() if ln.strip().strip(",")]
    raw_csv = "\n".join(lines)
    reader = csv.DictReader(io.StringIO(raw_csv))
    fieldnames = reader.fieldnames or []

    # Validate: must have athlete_number
    norm = {f.strip().lower(): f for f in fieldnames}
    if "athlete_number" not in norm:
        return Response(views.scores_import_form(coach, groups=groups,
            error="CSV must have an 'athlete_number' column."), status=400)

    # Parse columns into (game_key, field_key) pairs
    # Column format: game_key.field_key  (dot-separated)
    score_cols = []  # list of (original_col, game_key, field_key, is_computed)
    unknown_cols = []
    for col in fieldnames:
        col_s = col.strip()
        if col_s.lower() in ("athlete_number", "name"):
            continue  # name is a reference column, not a score
        if "." not in col_s:
            unknown_cols.append(col_s)
            continue
        gk, fk = col_s.split(".", 1)
        game = find_any_game(gk)
        if not game:
            unknown_cols.append(col_s)
            continue
        all_field_keys = [f["key"] for f in game.get("fields", [])] + \
                         [f["key"] for f in game.get("computed", [])]
        if fk not in all_field_keys:
            unknown_cols.append(col_s)
            continue
        is_computed = fk in [f["key"] for f in game.get("computed", [])]
        score_cols.append((col, gk, fk, is_computed))

    imported, skipped, errors = 0, 0, []
    conn = db.get_conn()
    try:
        for i, row in enumerate(reader, start=2):
            an = (row.get("athlete_number") or "").strip()
            name_col = (row.get("name") or "").strip()
            athlete = None
            if an:
                athlete = conn.execute(
                    "SELECT id, name, group_id FROM users WHERE athlete_number = ? AND role = 'participant'",
                    (an,)
                ).fetchone()
            # Fallback: match by name (case-insensitive) if no number or number not found
            if not athlete and name_col:
                athlete = conn.execute(
                    "SELECT id, name, group_id FROM users WHERE lower(name) = lower(?) AND role = 'participant'",
                    (name_col,)
                ).fetchone()
            if not athlete:
                label = f"#{an}" if an else f'"{name_col}"' if name_col else f"row {i}"
                errors.append(f"Row {i}: athlete {label} not found — skipped.")
                skipped += 1
                continue

            # Collect non-empty field values for this row
            raw_results = []  # (game_key, field_key, value)
            for col, gk, fk, is_computed in score_cols:
                raw_val = (row.get(col) or "").strip()
                if not raw_val:
                    continue
                try:
                    val = float(raw_val)
                except ValueError:
                    errors.append(f"Row {i}: '{col}' value '{raw_val}' is not a number — skipped field.")
                    continue
                raw_results.append((gk, fk, val))

            if not raw_results:
                errors.append(f"Row {i}: athlete #{an} ({athlete['name']}) has no score values — skipped.")
                skipped += 1
                continue

            # Auto-compute computed fields that weren't supplied
            # Group raw_results by game_key
            from collections import defaultdict
            by_game = defaultdict(dict)
            for gk, fk, val in raw_results:
                by_game[gk][fk] = val

            for section in active_measurement_games():
                for game in section["games"]:
                    gk = game["key"]
                    if gk not in by_game:
                        continue
                    for comp in game.get("computed", []):
                        if comp["key"] in by_game[gk]:
                            continue  # already supplied
                        src_vals = [by_game[gk].get(fk) for fk in comp.get("of", [])]
                        src_vals = [v for v in src_vals if v is not None]
                        if not src_vals:
                            continue
                        if comp.get("formula") == "average_of":
                            computed_val = round(sum(src_vals) / len(src_vals), 3)
                        elif comp.get("formula") == "sum_of":
                            computed_val = round(sum(src_vals), 3)
                        else:
                            continue
                        by_game[gk][comp["key"]] = computed_val
                        raw_results.append((gk, comp["key"], computed_val))

            # Use athlete's own group_id as snapshot if no override given
            snap_group = group_id if group_id else athlete["group_id"]
            session_id = db.find_or_create_session(
                conn, athlete["id"], session_date, coach["id"], group_id=snap_group
            )
            for gk, fk, val in raw_results:
                db.upsert_measurement_result(conn, session_id, gk, fk, val)
            conn.commit()
            imported += 1
    finally:
        conn.close()

    summary = f"Scores imported: {imported} athletes recorded"
    if skipped:
        summary += f", {skipped} skipped"
    if unknown_cols:
        summary += f". Unrecognised columns ignored: {', '.join(unknown_cols)}"
    if errors:
        summary += ". Issues: " + " | ".join(errors[:10])
        if len(errors) > 10:
            summary += f" (and {len(errors)-10} more)"
    return flash_redirect("/coach/groups", summary)


@router.get("/coach/participants/export.csv")
def participant_export_csv(req):
    import csv
    import io
    import secrets
    coach = require_admin(req)
    if not coach:
        return redirect("/login")

    conn = db.get_conn()
    try:
        rows = conn.execute(
            """
            SELECT u.id, u.athlete_number, u.name, u.username, u.email,
                   u.organisation, u.sport, u.gender,
                   pg.name AS group_name
            FROM users u
            LEFT JOIN participant_groups pg ON pg.id = u.group_id
            WHERE u.role = 'participant' AND u.active = 1
            ORDER BY u.athlete_number, u.name
            """
        ).fetchall()

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["athlete_number", "first name", "last name", "organisation", "group", "gender", "sport", "username", "email", "temp_password"])

        for r in rows:
            temp_pw = secrets.token_urlsafe(6)
            db.update_password(conn, r["id"], temp_pw)
            # Split stored name into first / last (last word = last name)
            name_parts = r["name"].strip().split()
            first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else r["name"]
            last_name  = name_parts[-1] if len(name_parts) > 1 else ""
            writer.writerow([
                r["athlete_number"] or "",
                first_name,
                last_name,
                r["organisation"] or "",
                r["group_name"] or "",
                r["gender"] or "",
                r["sport"] or "",
                r["username"] or "",
                r["email"] or "",
                temp_pw,
            ])

        conn.commit()
    finally:
        conn.close()

    csv_bytes = buf.getvalue().encode("utf-8")
    resp = Response(body=csv_bytes, content_type="text/csv; charset=utf-8")
    resp.headers.append(("Content-Disposition", "attachment; filename=\"athletes_export.csv\""))
    resp.headers.append(("Content-Length", str(len(csv_bytes))))
    return resp


# ------------------------------------------------------------------- bootstrap

application = App(router, STATIC_DIR)


# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE & SELF-DIRECTED ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/coach/attendance")
def attendance_list(req):
    """Practitioner: list recent session events."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        if coach["role"] == "system_admin":
            events = db.list_session_events(conn)
        else:
            events = db.list_session_events_for_coach(conn, coach["id"])
    finally:
        conn.close()
    return Response(views.attendance_list_page(coach, events))


@router.get("/coach/attendance/new")
def attendance_new_get(req):
    """Practitioner: form to create a new session event (training day)."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        if coach["role"] == "system_admin":
            groups = db.list_participant_groups(conn)
        else:
            gids = db.get_coach_group_ids(conn, coach["id"])
            groups = [g for g in db.list_participant_groups(conn) if g["id"] in gids]
    finally:
        conn.close()
    return Response(views.attendance_new_page(coach, groups))


@router.post("/coach/attendance/new")
def attendance_new_post(req):
    """Create a session event and redirect to its roll-call page."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    group_id = req.form_get("group_id") or None
    date = req.form_get("date") or db.today()
    notes = req.form_get("notes") or None
    try:
        group_id = int(group_id) if group_id else None
    except ValueError:
        group_id = None
    conn = db.get_conn()
    try:
        event_id = db.create_session_event(conn, group_id, date, coach["id"], notes)
    finally:
        conn.close()
    return redirect(f"/coach/attendance/{event_id}/roll-call")


@router.get("/coach/attendance/<int:event_id>/roll-call")
def attendance_roll_call_get(req, event_id):
    """Practitioner: tick which athletes attended this session event."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        event = db.get_session_event(conn, event_id)
        if not event:
            return flash_redirect("/coach/attendance", "Session not found.")
        # Get all athletes in this group
        if event["group_id"]:
            athletes = conn.execute(
                "SELECT * FROM users WHERE group_id = ? AND role = 'participant' AND active = 1 ORDER BY name",
                (event["group_id"],),
            ).fetchall()
        else:
            athletes = conn.execute(
                "SELECT * FROM users WHERE role = 'participant' AND active = 1 ORDER BY name"
            ).fetchall()
        already_marked = {a["participant_id"] for a in db.get_attendance_for_event(conn, event_id)}
    finally:
        conn.close()
    return Response(views.roll_call_page(coach, dict(event), athletes, already_marked))


@router.post("/coach/attendance/<int:event_id>/roll-call")
def attendance_roll_call_post(req, event_id):
    """Save attendance marks for a session event."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    # Collect all checked athlete IDs from form
    raw = req.form.get("athlete_ids", [])
    if isinstance(raw, str):
        raw = [raw]
    try:
        participant_ids = [int(x) for x in raw if x]
    except ValueError:
        participant_ids = []
    conn = db.get_conn()
    try:
        event = db.get_session_event(conn, event_id)
        if not event:
            return flash_redirect("/coach/attendance", "Session not found.")
        db.mark_attendance(conn, event_id, participant_ids, coach["id"])
        # Award attendance milestone + streak XP for each newly marked athlete
        for pid in participant_ids:
            try:
                db.check_attendance_milestones(conn, pid, session_id=None)
            except Exception:
                pass
            try:
                db.check_attendance_streak(conn, pid)
            except Exception:
                pass
    finally:
        conn.close()
    return flash_redirect(
        f"/coach/attendance/{event_id}/roll-call",
        f"Attendance saved — {len(participant_ids)} athlete{'s' if len(participant_ids) != 1 else ''} marked present.",
    )


@router.get("/coach/attendance/<int:event_id>")
def attendance_view(req, event_id):
    """Practitioner: view attendance summary for a session event."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        event = db.get_session_event(conn, event_id)
        if not event:
            return flash_redirect("/coach/attendance", "Session not found.")
        attendees = db.get_attendance_for_event(conn, event_id)
    finally:
        conn.close()
    return Response(views.attendance_view_page(coach, dict(event), attendees))


@router.post("/coach/attendance/<int:event_id>/delete")
def attendance_delete(req, event_id):
    """System admin: delete a session event and its attendance records."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM session_events WHERE id = ?", (event_id,))
        conn.commit()
    finally:
        conn.close()
    return flash_redirect("/coach/attendance", "Session event deleted.")


# ── Athlete self-directed routes ──────────────────────────────────────────────

@router.get("/athlete/self-directed")
def self_directed_home(req):
    """Athlete: see pending sessions to score and completed self-directed history."""
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        pending = db.get_pending_self_directed_events(conn, user["id"])
        completed = db.get_self_directed_sessions(conn, user["id"])
    finally:
        conn.close()
    return Response(views.self_directed_home_page(user, pending, completed))


@router.get("/athlete/self-directed/<int:event_id>")
def self_directed_entry_get(req, event_id):
    """Athlete: score entry form for a specific session event."""
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        # Verify athlete was actually marked as attending this event
        attended = conn.execute(
            "SELECT id FROM session_attendance WHERE event_id = ? AND participant_id = ?",
            (event_id, user["id"]),
        ).fetchone()
        if not attended:
            return flash_redirect("/athlete/self-directed", "You don't have access to that session.")
        event = db.get_session_event(conn, event_id)
        if not event:
            return flash_redirect("/athlete/self-directed", "Session not found.")
        # Check if already scored
        already = conn.execute(
            "SELECT id FROM measurement_sessions WHERE participant_id = ? "
            "AND attendance_event_id = ? AND session_type = 'self_directed'",
            (user["id"], event_id),
        ).fetchone()
    finally:
        conn.close()
    if already:
        return flash_redirect("/athlete/self-directed", "You've already scored that session.")
    return Response(views.self_directed_entry_page(user, dict(event)))


@router.post("/athlete/self-directed/<int:event_id>")
def self_directed_entry_post(req, event_id):
    """Athlete: submit self-directed scores for a session."""
    user = require_role(req, "participant")
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        # Verify attendance
        attended = conn.execute(
            "SELECT id FROM session_attendance WHERE event_id = ? AND participant_id = ?",
            (event_id, user["id"]),
        ).fetchone()
        if not attended:
            return flash_redirect("/athlete/self-directed", "You don't have access to that session.")
        # Check not already scored
        already = conn.execute(
            "SELECT id FROM measurement_sessions WHERE participant_id = ? "
            "AND attendance_event_id = ? AND session_type = 'self_directed'",
            (user["id"], event_id),
        ).fetchone()
        if already:
            return flash_redirect("/athlete/self-directed", "Already scored.")

        # Collect results (same pattern as formal session recording)
        results = []
        for game in all_active_measurement_games():
            field_values = {}
            for field in game["fields"]:
                raw = (req.form_get(f"mg__{game['key']}__{field['key']}") or "").strip()
                if not raw:
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    continue
                field_values[field["key"]] = value
                results.append((game["key"], field["key"], value))
            for computed in game.get("computed", []):
                inputs = [field_values.get(k) for k in computed["of"]]
                if all(v is not None for v in inputs):
                    result = round(
                        sum(inputs) if computed.get("formula") == "sum_of"
                        else sum(inputs) / len(inputs), 2
                    )
                    results.append((game["key"], computed["key"], result))

        if not results:
            return flash_redirect(
                f"/athlete/self-directed/{event_id}",
                "No scores entered — fill in at least one field.",
            )

        session_id = db.create_self_directed_session(
            conn, user["id"], event_id, results, logged_by=user["id"]
        )
        # Process XP — self-directed (is_formal=False)
        try:
            db.process_session_xp(conn, session_id, user["id"], is_formal=False)
        except Exception:
            pass
    finally:
        conn.close()
    return flash_redirect("/athlete/self-directed", "Scores saved — XP awarded!")


# ══════════════════════════════════════════════════════════════════════════════
# XP ENGINE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/athlete/xp")
def athlete_xp_page(req):
    """Athlete-facing XP profile — rank, total points, recent events."""
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        xp_data = db.get_athlete_xp(conn, user["id"])
        levels = db.get_all_athlete_levels(conn, user["id"])
    finally:
        conn.close()
    return Response(views.athlete_xp_page(user, xp_data, levels))


@router.get("/athlete/report")
def athlete_report(req):
    """Athlete-facing plain-English movement report."""
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        sessions = db.measurement_sessions_for(conn, user["id"])
        levels_by_area = db.get_all_athlete_levels_by_area(conn, user["id"])
        thresholds_raw = db.get_all_thresholds(conn)
    finally:
        conn.close()
    return Response(views.athlete_movement_report_page(
        dict(user), sessions, levels_by_area, thresholds_raw
    ))


@router.get("/athlete/axp-info")
def athlete_axp_info(req):
    """Plain-English AXP points structure explainer for athletes."""
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    return Response(views.axp_info_page(user))


@router.get("/athlete/leaderboard")
def athlete_leaderboard(req):
    """Athlete-facing group leaderboard — only accessible when group has show_leaderboard enabled."""
    from constants import XP_RANK_TIERS, CORE_AAP_GAMES
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    if not user.get("show_leaderboard"):
        return flash_redirect("/dashboard", "Leaderboard is not enabled for your group.")
    group_id = user.get("group_id")
    conn = db.get_conn()
    try:
        group = conn.execute(
            "SELECT * FROM participant_groups WHERE id = ?", (group_id,)
        ).fetchone() if group_id else None
        group_name = group["name"] if group else ""
        athletes = conn.execute(
            "SELECT u.id, u.name FROM users u "
            "JOIN group_members gm ON gm.user_id = u.id "
            "WHERE gm.group_id = ? AND u.role = 'participant' AND u.active = 1",
            (group_id,)
        ).fetchall() if group_id else []
        # Fallback: use group_id column on users if no group_members rows
        if not athletes and group_id:
            athletes = conn.execute(
                "SELECT id, name FROM users WHERE group_id = ? AND role = 'participant' AND active = 1",
                (group_id,)
            ).fetchall()
        ranked = []
        for a in athletes:
            pid = a["id"]
            xp_data = db.get_athlete_xp(conn, pid)
            levels = db.get_all_athlete_levels(conn, pid)
            total_xp = xp_data.get("total_xp", 0)
            tier = XP_RANK_TIERS[0]
            for t in XP_RANK_TIERS:
                if total_xp >= t["min_xp"]:
                    tier = t
            ranked.append({
                "id": pid,
                "name": a["name"],
                "total_xp": total_xp,
                "tier": tier,
                "levels": levels,
            })
        ranked.sort(key=lambda x: x["total_xp"], reverse=True)
    finally:
        conn.close()
    return Response(views.athlete_leaderboard_page(user, ranked, group_name=group_name))


@router.get("/coach/participants/<int:participant_id>/xp")
def coach_participant_xp(req, participant_id):
    """Coach view of an athlete's XP profile."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        participant = conn.execute("SELECT * FROM users WHERE id = ?", (participant_id,)).fetchone()
        if not participant:
            return flash_redirect("/coach/groups", "Participant not found.")
        xp_data = db.get_athlete_xp(conn, participant_id)
        levels = db.get_all_athlete_levels(conn, participant_id)
    finally:
        conn.close()
    return Response(views.athlete_xp_page(dict(participant), xp_data, levels, coach=dict(coach)))


@router.get("/coach/admin/hub")
def admin_hub_get(req):
    """System admin hub — all admin links in one place."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    return Response(views.system_admin_hub_page(coach))


@router.get("/coach/admin/score-distribution")
def score_distribution_get(req):
    """System admin: score percentile distribution report for all scoring areas."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")

    from constants import SCORING_AREAS, XP_GAME_CONFIG, threshold_field_key

    def _percentile(sorted_vals, p):
        n = len(sorted_vals)
        if n == 0:
            return None
        i = (p / 100) * (n - 1)
        lo = int(i)
        hi = lo + 1
        if hi >= n:
            return sorted_vals[lo]
        frac = i - lo
        return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])

    distributions = []
    conn = db.get_conn()
    try:
        for area in SCORING_AREAS:
            game_key = area["game_key"]
            area_field_key = area["field_key"]  # None = pooled
            lower = area["lower_is_better"]
            stored_fk = threshold_field_key(area)  # field_key used in thresholds table

            cfg = XP_GAME_CONFIG.get(game_key, {})
            # Determine which DB field_keys to pool for this scoring area
            if area_field_key is None:
                # Pooled: use ALL score_fields (small+large group combined)
                fields_to_query = cfg.get("score_fields", [])
            else:
                fields_to_query = [area_field_key]

            if not fields_to_query:
                continue

            # Build parameterized IN clause
            placeholders = ",".join("?" * len(fields_to_query))
            rows = conn.execute(
                f"""
                SELECT mr.value
                FROM measurement_results mr
                JOIN measurement_sessions ms ON ms.id = mr.session_id
                WHERE mr.game_key = ? AND mr.field_key IN ({placeholders})
                  AND mr.value IS NOT NULL
                ORDER BY ms.created_at ASC
                """,
                [game_key] + fields_to_query,
            ).fetchall()

            vals = sorted([float(r["value"]) for r in rows])
            n = len(vals)

            if n == 0:
                distributions.append({
                    "game_key": game_key,
                    "display_name": area["display_name"],
                    "field_key": stored_fk,
                    "lower_is_better": lower,
                    "pooled": area_field_key is None,
                    "n": 0,
                })
                continue

            mean = sum(vals) / n
            p25 = _percentile(vals, 25)
            p50 = _percentile(vals, 50)
            p75 = _percentile(vals, 75)
            p90 = _percentile(vals, 90)

            if lower:
                p10 = _percentile(vals, 10)
                suggested = {
                    1: round(mean * 0.97, 2) if mean else None,
                    2: round(p25, 2) if p25 else None,
                    3: round((p25 + p10) / 2, 2) if p25 and p10 else None,
                    4: round(p10, 2) if p10 else None,
                    5: round(p10 * 0.92, 2) if p10 else None,
                }
            else:
                mid_p75_p90 = ((p75 or 0) + (p90 or 0)) / 2 if p75 and p90 else None
                beyond_p90 = (p90 * 1.10) if p90 else None
                suggested = {
                    1: round(mean * 1.03, 1) if mean else None,
                    2: round(p75, 1) if p75 else None,
                    3: round(mid_p75_p90, 1) if mid_p75_p90 else None,
                    4: round(p90, 1) if p90 else None,
                    5: round(beyond_p90, 1) if beyond_p90 else None,
                }

            distributions.append({
                "game_key": game_key,
                "display_name": area["display_name"],
                "field_key": stored_fk,
                "lower_is_better": lower,
                "pooled": area_field_key is None,
                "n": n,
                "min_val": vals[0],
                "max_val": vals[-1],
                "mean": round(mean, 2),
                "p25": round(p25, 2) if p25 is not None else None,
                "p50": round(p50, 2) if p50 is not None else None,
                "p75": round(p75, 2) if p75 is not None else None,
                "p90": round(p90, 2) if p90 is not None else None,
                "suggested": suggested,
            })
    finally:
        conn.close()

    return Response(views.score_distribution_page(coach, distributions))


@router.get("/coach/admin/game-thresholds")
def game_thresholds_get(req):
    """System admin: view and set level achievement thresholds per scoring area."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        thresholds = db.get_all_thresholds(conn)
    finally:
        conn.close()
    from constants import SCORING_AREAS, XP_GAME_CONFIG, threshold_field_key
    return Response(views.game_thresholds_page(
        coach, thresholds, SCORING_AREAS, XP_GAME_CONFIG, threshold_field_key))


@router.post("/coach/admin/game-thresholds/set")
def game_thresholds_set(req):
    """System admin: set or update a single game/level threshold."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    game_key  = req.form_get("game_key")
    level     = req.form_get("level")
    field_key = req.form_get("field_key")
    threshold = req.form_get("threshold_value")
    lower     = req.form_get("lower_is_better") == "1"
    try:
        level = int(level)
        threshold = float(threshold)
    except (TypeError, ValueError):
        return flash_redirect("/coach/admin/game-thresholds", "Invalid level or threshold value.")
    conn = db.get_conn()
    try:
        db.set_game_threshold(conn, game_key, level, field_key, threshold,
                              lower_is_better=lower, set_by=coach["id"])
    finally:
        conn.close()
    return flash_redirect("/coach/admin/game-thresholds",
                          f"Threshold set: {game_key} L{level} = {threshold}")


@router.post("/coach/admin/game-thresholds/delete")
def game_thresholds_delete(req):
    """System admin: remove a threshold."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    game_key = req.form_get("game_key")
    field_key = req.form_get("field_key") or None
    try:
        level = int(req.form_get("level"))
    except (TypeError, ValueError):
        return flash_redirect("/coach/admin/game-thresholds", "Invalid level.")
    conn = db.get_conn()
    try:
        db.delete_game_threshold(conn, game_key, level, field_key=field_key)
    finally:
        conn.close()
    return flash_redirect("/coach/admin/game-thresholds",
                          f"Threshold removed: {game_key} L{level}")


@router.get("/coach/leaderboard")
def coach_leaderboard(req):
    """Group XP leaderboard — ranked by total XP."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    from constants import XP_RANK_TIERS, CORE_AAP_GAMES
    conn = db.get_conn()
    try:
        groups = db.list_participant_groups(conn)
        group_id_str = req.query.get("group_id", [""])[0].strip()
        selected_group_id = int(group_id_str) if group_id_str.isdigit() else None
        ranked_athletes = None
        if selected_group_id:
            athletes = conn.execute(
                "SELECT u.id, u.name, u.athlete_number FROM users u "
                "JOIN group_members gm ON gm.user_id = u.id "
                "WHERE gm.group_id = ? AND u.role = 'participant' AND u.active = 1 "
                "ORDER BY u.name",
                (selected_group_id,)
            ).fetchall()
            ranked_athletes = []
            for a in athletes:
                pid = a["id"]
                xp_data = db.get_athlete_xp(conn, pid)
                levels = db.get_all_athlete_levels(conn, pid)
                total_xp = xp_data.get("total_xp", 0)
                # Determine tier
                tier = XP_RANK_TIERS[0]
                for t in XP_RANK_TIERS:
                    if total_xp >= t["min_xp"]:
                        tier = t
                ranked_athletes.append({
                    "id": pid,
                    "name": a["name"],
                    "athlete_number": a.get("athlete_number"),
                    "total_xp": total_xp,
                    "tier": tier,
                    "levels": levels,
                })
            ranked_athletes.sort(key=lambda x: x["total_xp"], reverse=True)
    finally:
        conn.close()
    return Response(views.group_leaderboard_page(
        coach, groups,
        selected_group_id=selected_group_id,
        ranked_athletes=ranked_athletes
    ))


@router.post("/coach/admin/xp-retroactive")
def xp_retroactive_pass(req):
    """System admin: run the retroactive XP pass over all existing sessions."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        processed = db.retroactive_xp_pass(conn)
    finally:
        conn.close()
    return flash_redirect("/coach/admin/game-thresholds",
                          f"Retroactive XP pass complete — {processed} sessions processed.")


@router.post("/coach/admin/level-retroactive")
def level_retroactive_pass(req):
    """System admin: re-check level thresholds across all sessions.
    Use this after setting thresholds for the first time, since the AXP retroactive
    pass skips sessions that already have XP events."""
    coach = require_system_admin(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        levels, xp = db.retroactive_level_pass(conn)
    finally:
        conn.close()
    return flash_redirect("/coach/admin/game-thresholds",
                          f"Level check complete — {levels} new level(s) awarded, {xp:,} AXP granted.")


class _FastRequestHandler(WSGIRequestHandler):
    """Skip the reverse-DNS lookup wsgiref normally does on every request.

    On cloud hosts (Render, Railway, etc.) that lookup has no PTR record to
    resolve and can hang for a long time - and since this dev server is
    single-threaded, one hung lookup blocks every other request behind it,
    which looks exactly like the whole app being stuck loading.
    """

    def address_string(self):
        return self.client_address[0]


# ── Measurement Windows ───────────────────────────────────────────────────────

@router.post("/coach/groups/<int:group_id>/window/open")
def window_open(req, group_id):
    """Practitioner opens a measurement window for a group."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    session_label = req.form_get("session_label") or None
    session_month = req.form_get("session_month") or None
    conn = db.get_conn()
    try:
        # Only one open window per group at a time
        existing = db.get_active_window_for_group(conn, group_id)
        if existing:
            return flash_redirect(
                f"/coach/window/{existing['id']}",
                "A measurement window is already open for this group.",
            )
        window_id = db.open_measurement_window(
            conn, group_id, coach["id"],
            session_label=session_label,
            session_month=session_month,
        )
    finally:
        conn.close()
    return redirect(f"/coach/window/{window_id}")


@router.get("/coach/window/<int:window_id>")
def window_status(req, window_id):
    """Practitioner live view: who has submitted vs. who is pending."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        window = db.get_measurement_window(conn, window_id)
        if not window:
            return flash_redirect("/coach/group-hub", "Window not found.")
        window = dict(window)
        group_id = window["group_id"]
        # All athletes in the group
        athletes = conn.execute(
            "SELECT id, name, athlete_number FROM users "
            "WHERE group_id = ? AND role = 'participant' ORDER BY name",
            (group_id,),
        ).fetchall()
        athletes = [dict(a) for a in athletes]
        submissions = db.get_window_submissions(conn, window_id)
        submitted_ids = {s["participant_id"] for s in submissions}
        group = conn.execute(
            "SELECT * FROM participant_groups WHERE id = ?", (group_id,)
        ).fetchone()
    finally:
        conn.close()
    return Response(views.measurement_window_status_page(
        coach, window, dict(group), athletes, [dict(s) for s in submissions], submitted_ids
    ))


@router.post("/coach/window/<int:window_id>/close")
def window_close(req, window_id):
    """Close window: commit all submissions and run XP for each."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        window = db.get_measurement_window(conn, window_id)
        if not window:
            return flash_redirect("/coach/group-hub", "Window not found.")
        to_process = db.close_measurement_window(conn, window_id)
        # Award XP for each newly committed session
        xp_total = 0
        for session_id, participant_id in to_process:
            result = db.process_session_xp(conn, session_id, participant_id, is_formal=True)
            xp_total += result.get("total_xp_awarded", 0)
        group_id = window["group_id"]
    finally:
        conn.close()
    msg = f"Window closed. {len(to_process)} session(s) committed, {xp_total} XP awarded."
    return flash_redirect(f"/coach/window/{window_id}", msg)


@router.post("/coach/window/<int:window_id>/reopen")
def window_reopen(req, window_id):
    """Re-open a closed window so absentees can submit."""
    coach = require_staff(req)
    if not coach:
        return redirect("/login")
    conn = db.get_conn()
    try:
        window = db.get_measurement_window(conn, window_id)
        if not window:
            return flash_redirect("/coach/group-hub", "Window not found.")
        db.reopen_measurement_window(conn, window_id)
    finally:
        conn.close()
    return flash_redirect(f"/coach/window/{window_id}", "Window re-opened. Athletes can submit again.")


@router.get("/athlete/window/<int:window_id>")
def athlete_window_get(req, window_id):
    """Athlete self-score entry form for an open measurement window."""
    from constants import active_measurement_games, games_for_max_level
    user = require_participant_or_view_as(req)
    if not user:
        return redirect("/login")
    conn = db.get_conn()
    try:
        window = db.get_measurement_window(conn, window_id)
        if not window or window["status"] != "open":
            return flash_redirect("/dashboard", "This measurement window is not open.")
        # Confirm this athlete is in the right group
        if user.get("group_id") != window["group_id"]:
            return flash_redirect("/dashboard", "This window is not for your group.")
        already = db.athlete_has_submitted(conn, window_id, user["id"])
        group = conn.execute(
            "SELECT * FROM participant_groups WHERE id = ?", (window["group_id"],)
        ).fetchone()
        max_level = group["max_level"] if group and "max_level" in group.keys() else None
        games = games_for_max_level(max_level) if max_level else active_measurement_games()
    finally:
        conn.close()
    return Response(views.athlete_window_submit_page(
        user, dict(window), games, already_submitted=already
    ))


@router.post("/athlete/window/<int:window_id>/submit")
def athlete_window_post(req, window_id):
    """Save athlete's self-scored session from a measurement window."""
    import json
    from constants import active_measurement_games, games_for_max_level, find_measurement_game
    user = require_role(req, "participant")
    if not user:
        return Response('{"error":"unauthenticated"}', status=401, content_type="application/json")
    conn = db.get_conn()
    try:
        window = db.get_measurement_window(conn, window_id)
        if not window or window["status"] != "open":
            return Response('{"error":"window_closed"}', status=400, content_type="application/json")
        if user.get("group_id") != window["group_id"]:
            return Response('{"error":"wrong_group"}', status=403, content_type="application/json")
        if db.athlete_has_submitted(conn, window_id, user["id"]):
            return Response('{"error":"already_submitted"}', status=409, content_type="application/json")

        # Parse submitted scores: expects JSON body {"game_key.field_key": value, ...}
        try:
            body = req.environ.get("wsgi.input").read(int(req.environ.get("CONTENT_LENGTH", 0) or 0))
            data = json.loads(body)
        except Exception:
            return Response('{"error":"bad_json"}', status=400, content_type="application/json")

        date = window["session_month"] + "-01" if window.get("session_month") else db.today()
        session_id = db.create_bare_session(
            conn, user["id"], date, user["id"],
            group_id=user.get("group_id"),
            session_label=window.get("session_label"),
            session_month=window.get("session_month"),
        )

        # Save results and compute derived fields
        saved_games = set()
        for composite_key, raw_value in data.items():
            if "." not in composite_key:
                continue
            game_key, field_key = composite_key.split(".", 1)
            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                continue
            db.upsert_measurement_result(conn, session_id, game_key, field_key, value)
            saved_games.add(game_key)

        # Compute derived fields for each game
        for game_key in saved_games:
            game = find_measurement_game(game_key)
            if not game:
                continue
            rows = conn.execute(
                "SELECT field_key, value FROM measurement_results WHERE session_id = ? AND game_key = ?",
                (session_id, game_key),
            ).fetchall()
            current = {r["field_key"]: r["value"] for r in rows}
            for comp in game.get("computed", []):
                inputs = [current.get(k) for k in comp["of"]]
                if all(v is not None for v in inputs):
                    result = round(
                        sum(inputs) if comp.get("formula") == "sum_of" else sum(inputs) / len(inputs), 2
                    )
                    db.upsert_measurement_result(conn, session_id, game_key, comp["key"], result)

        # Register the submission (XP awarded later, when window is closed)
        db.create_window_submission(conn, window_id, user["id"], session_id)

    finally:
        conn.close()
    return Response('{"ok":true}', content_type="application/json")


def main():
    from wsgiref.simple_server import make_server

    db.init_db()
    seeded = db.seed_demo_data()
    if seeded:
        print("Seeded demo data (coach + 3 demo participants). See README.md for credentials.")
    db.cleanup_demo_data()
    db.maybe_reset_coach_password()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"{APP_NAME} running at http://localhost:{port}  (Ctrl+C to stop)")
    with make_server(host, port, application, handler_class=_FastRequestHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
