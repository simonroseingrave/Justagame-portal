"""HTML rendering. Pages are built with small Python functions rather than
a templating engine, so there is no extra dependency to install. All
user-supplied text is passed through `esc()` (html.escape) before being
placed in markup to avoid HTML/script injection.
"""
from html import escape as esc

from constants import (
    APP_NAME,
    MEASUREMENT_GAMES,
    all_measurement_games,
)


def layout(title, body, user=None, flash=None, active_nav=None):
    nav = ""
    if user:
        if user["role"] == "coach":
            links = [
                ("/coach", "Dashboard", "dashboard"),
                ("/coach/participants/new", "Add Participant", "new_participant"),
            ]
        else:
            links = [("/dashboard", "My Dashboard", "dashboard")]
        nav_items = "".join(
            f'<a class="nav-link{" active" if active_nav == key else ""}" href="{href}">{label}</a>'
            for href, label, key in links
        )
        nav = f"""
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span>Just A Game <small>{APP_NAME}</small></span>
            </a>
            <nav class="nav">{nav_items}</nav>
            <div class="user-pill">
              <span>{esc(user['name'])}</span>
              <a href="/account/password" class="btn btn-ghost btn-sm">Change password</a>
              <a href="/logout" class="btn btn-ghost btn-sm">Log out</a>
            </div>
          </div>
        </header>
        """
    else:
        nav = f"""
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span>Just A Game <small>{APP_NAME}</small></span>
            </a>
          </div>
        </header>
        """

    flash_html = f'<div class="flash">{esc(flash)}</div>' if flash else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)} - {APP_NAME}</title>
  <link rel="stylesheet" href="/static/css/style.css" />

  <!-- Add to Home Screen / PWA -->
  <link rel="manifest" href="/static/manifest.json" />
  <meta name="theme-color" content="#2D323B" />
  <link rel="apple-touch-icon" href="/static/img/apple-touch-icon.png" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Just A Game" />
  <script>
    if ("serviceWorker" in navigator) {{
      window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js"));
    }}
  </script>
</head>
<body>
  {nav}
  <main class="container">
    {flash_html}
    {body}
  </main>
  <footer class="footer">
    <p>Just A Game &middot; {APP_NAME} &middot; <a href="https://www.justagame.co.nz" target="_blank" rel="noopener">justagame.co.nz</a></p>
  </footer>
</body>
</html>"""


def login_page(error=None, prefill_email=""):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    body = f"""
    <div class="login-wrap">
      <div class="card login-card">
        <img src="/static/img/logo.png" alt="Just A Game" class="login-logo" />
        <h1>{APP_NAME}</h1>
        <p class="muted">Log in to view your progress, or manage athletes as a coach.</p>
        {error_html}
        <form method="post" action="/login">
          <label for="email">Email</label>
          <input type="email" id="email" name="email" value="{esc(prefill_email)}" required autofocus />
          <label for="password">Password</label>
          <input type="password" id="password" name="password" required />
          <button type="submit" class="btn btn-primary btn-block">Log in</button>
        </form>
        <details class="demo-creds">
          <summary>Demo login details</summary>
          <p><strong>Coach:</strong> coach@justagame.co.nz / CoachDemo123!</p>
          <p><strong>Participant:</strong> alex.demo@example.com / Athlete123!</p>
        </details>
      </div>
    </div>
    """
    return layout("Log in", body)


def _measurement_field_input(game_key, field):
    """One labelled number input for a single Measurement Games field."""
    ftype = field["type"]
    step = "0.01" if ftype == "time" else "1"
    suffix = " (seconds)" if ftype == "time" else (f" ({field['unit']})" if field.get("unit") else "")
    input_name = f"mg__{game_key}__{field['key']}"
    return f"""
    <div class="mg-field">
      <label for="{input_name}">{esc(field['label'])}{esc(suffix)}</label>
      <input type="number" step="{step}" min="0" id="{input_name}" name="{input_name}" />
    </div>
    """


def _measurement_game_fieldset(game):
    fields_html = "".join(_measurement_field_input(game["key"], f) for f in game["fields"])
    return f"""
    <fieldset class="mg-game">
      <legend>{esc(game['name'])}</legend>
      <div class="mg-field-grid">{fields_html}</div>
    </fieldset>
    """


def measurement_games_form(participant_id):
    """The coach-facing entry form for recording a Measurement Games test
    session -- one date, with a fieldset per game grouped under each
    section. Coaches can leave any game blank if it wasn't tested that
    day; only filled-in fields get saved (see app.py)."""
    sections_html = "".join(f"""
    <div class="mg-section">
      <h4>{esc(section['section'])}</h4>
      {''.join(_measurement_game_fieldset(g) for g in section['games'])}
    </div>
    """ for section in MEASUREMENT_GAMES)

    return f"""
    <div class="card form-card">
      <h3>Measurement Games</h3>
      <p class="muted">Fill in whichever games were tested this session &mdash; leave the rest blank.
      The Skipping Rope Sprint average is calculated automatically from Time 1/2/3.</p>
      <form method="post" action="/coach/participants/{participant_id}/measurement">
        <label for="mg-date">Date</label>
        <input type="date" id="mg-date" name="date" required />
        {sections_html}
        <button type="submit" class="btn btn-primary">Save Results</button>
      </form>
    </div>
    """


def _format_measurement_value(field_type, value):
    if value is None:
        return "-"
    text = f"{value:g}"  # strips trailing .0 from whole numbers, keeps decimals otherwise
    return f"{text}s" if field_type == "time" else text


def _measurement_session_card(session, show_delete=False, participant_id=None):
    by_game = {}
    for (game_key, field_key), value in session["results"].items():
        by_game.setdefault(game_key, {})[field_key] = value

    game_blocks = []
    for game in all_measurement_games():
        values = by_game.get(game["key"])
        if not values:
            continue
        rows = [
            (f["label"], _format_measurement_value(f["type"], values.get(f["key"])))
            for f in game["fields"] if f["key"] in values
        ]
        for computed in game.get("computed", []):
            if computed["key"] in values:
                rows.append((computed["label"], _format_measurement_value(computed["type"], values[computed["key"]])))
        rows_html = "".join(
            f'<div class="mg-result"><span class="mg-result-label">{esc(label)}</span>'
            f'<span class="mg-result-value">{esc(val)}</span></div>'
            for label, val in rows
        )
        game_blocks.append(f"""
        <div class="mg-result-game">
          <div class="mg-result-game-name">{esc(game['name'])}</div>
          <div class="mg-result-grid">{rows_html}</div>
        </div>
        """)

    delete_html = ""
    if show_delete:
        delete_html = f"""
        <form method="post" action="/coach/participants/{participant_id}/measurement/{session['id']}/delete"
              style="display:inline" onsubmit="return confirm('Delete this Measurement Games session?');">
          <button type="submit" class="btn btn-ghost btn-sm">Delete</button>
        </form>
        """

    return f"""
    <div class="card mg-session-card">
      <div class="mg-session-head">
        <strong>{esc(session['date'])}</strong>
        {delete_html}
      </div>
      {''.join(game_blocks)}
    </div>
    """


def measurement_games_history(sessions, show_delete=False, participant_id=None):
    if not sessions:
        return '<p class="muted">No Measurement Games results recorded yet.</p>'
    return "".join(
        _measurement_session_card(s, show_delete=show_delete, participant_id=participant_id)
        for s in sessions
    )


def participant_dashboard(user, measurement_sessions):
    body = f"""
    <div class="page-head">
      <div>
        <h1>Welcome back, {esc(user['name'].split(' ')[0])}</h1>
        <p class="muted">{esc(user.get('sport') or '')} &middot; {esc(user.get('programme') or '')}</p>
      </div>
    </div>

    <section class="stat-row">
      <div class="card stat-card">
        <div class="stat-number">{len(measurement_sessions)}</div>
        <div class="stat-label">Test Sessions</div>
      </div>
    </section>

    <h2 class="section-title">Measurement Games Results</h2>
    {measurement_games_history(measurement_sessions)}
    """
    return layout("My Dashboard", body, user=user, active_nav="dashboard")


def coach_dashboard(participants):
    rows = []
    for p in participants:
        rows.append(f"""
        <tr>
          <td><a href="/coach/participants/{p['id']}">{esc(p['name'])}</a></td>
          <td>{esc(p['sport'] or '-')}</td>
          <td>{esc(p['programme'] or '-')}</td>
          <td>{p['test_count']}</td>
          <td><a class="btn btn-sm btn-secondary" href="/coach/participants/{p['id']}">Manage</a></td>
        </tr>
        """)
    rows_html = "".join(rows) or '<tr><td colspan="5" class="muted">No participants yet. Add one to get started.</td></tr>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>Coach Dashboard</h1>
        <p class="muted">Record Measurement Games results and track every athlete's progress.</p>
      </div>
      <a class="btn btn-primary" href="/coach/participants/new">+ Add Participant</a>
    </div>
    <div class="card">
      <table class="table">
        <thead><tr><th>Name</th><th>Sport</th><th>Programme</th><th>Tests</th><th></th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """
    return layout("Coach Dashboard", body, user={"name": "Coach", "role": "coach"}, active_nav="dashboard")


def coach_dashboard_for(user, participants):
    html = coach_dashboard(participants)
    # swap the placeholder user pill name for the real logged-in coach name
    return html.replace(">Coach</span>", f">{esc(user['name'])}</span>", 1)


def new_participant_form(user, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    sport_options = "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in
                             ["Cricket", "Football", "Hockey", "Multi-sport"])
    body = f"""
    <div class="page-head"><h1>Add Participant</h1></div>
    {error_html}
    <div class="card form-card">
      <form method="post" action="/coach/participants/new">
        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required />
        <label for="email">Email (used to log in)</label>
        <input type="email" id="email" name="email" required />
        <label for="password">Temporary password</label>
        <input type="text" id="password" name="password" required value="Athlete123!" />
        <label for="sport">Sport</label>
        <select id="sport" name="sport">{sport_options}</select>
        <label for="programme">Programme / notes</label>
        <input type="text" id="programme" name="programme" placeholder="e.g. Athlete Adaptability Programme - Masterton 2026" />
        <button type="submit" class="btn btn-primary">Create Participant</button>
      </form>
    </div>
    """
    return layout("Add Participant", body, user=user, active_nav="new_participant")


def coach_participant_detail(coach, participant, measurement_sessions, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""

    body = f"""
    <div class="page-head">
      <div>
        <h1>{esc(participant['name'])}</h1>
        <p class="muted">{esc(participant['sport'] or '')} &middot; {esc(participant['programme'] or '')} &middot; {esc(participant['email'])}</p>
      </div>
      <a class="btn btn-ghost" href="/coach">&larr; Back to all participants</a>
    </div>
    {message_html}

    <section class="stat-row">
      <div class="card stat-card"><div class="stat-number">{len(measurement_sessions)}</div><div class="stat-label">Test Sessions</div></div>
    </section>

    {measurement_games_form(participant['id'])}

    <h2 class="section-title">Measurement Games History</h2>
    {measurement_games_history(measurement_sessions, show_delete=True, participant_id=participant['id'])}
    """
    return layout(participant["name"], body, user=coach, active_nav="dashboard")


def simple_message_page(title, message, user=None):
    body = f'<div class="card"><p>{esc(message)}</p></div>'
    return layout(title, body, user=user)


def change_password_page(user, error=None, success=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    success_html = f'<div class="flash">{esc(success)}</div>' if success else ""
    body = f"""
    <div class="page-head"><h1>Change Password</h1></div>
    {error_html}
    {success_html}
    <div class="card form-card" style="max-width:420px">
      <form method="post" action="/account/password">
        <label for="current_password">Current password</label>
        <input type="password" id="current_password" name="current_password" required autofocus />
        <label for="new_password">New password</label>
        <input type="password" id="new_password" name="new_password" required minlength="8" />
        <label for="confirm_password">Confirm new password</label>
        <input type="password" id="confirm_password" name="confirm_password" required minlength="8" />
        <button type="submit" class="btn btn-primary btn-block">Update Password</button>
      </form>
    </div>
    """
    return layout("Change Password", body, user=user, active_nav=None)


