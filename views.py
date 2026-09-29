"""HTML rendering. Pages are built with small Python functions rather than
a templating engine, so there is no extra dependency to install. All
user-supplied text is passed through `esc()` (html.escape) before being
placed in markup to avoid HTML/script injection.
"""
import re as _re
import datetime as _dt
from html import escape as esc

from constants import (
    APP_NAME,
    MEASUREMENT_GAMES,
    SPORT_SPECIFIC_GAMES,
    all_measurement_games,
    all_active_measurement_games,
    active_measurement_games,
    games_for_max_level,
    max_game_level,
    SESSION_TYPES,
    SESSION_LABEL_MAP,
    GAME_DISPLAY_NAMES,
    GAME_LEVEL_DESCRIPTIONS,
)


def _session_label_pickers(selected_label=None, selected_month=None):
    """Render session type dropdown + separate month + year selectors."""
    import datetime as _dt2
    now = _dt2.datetime.now()
    cur_m = now.month
    cur_y = now.year
    if selected_month:
        try:
            parts = selected_month.split("-")
            cur_y = int(parts[0])
            cur_m = int(parts[1])
        except Exception:
            pass
    type_opts = "".join(
        f'<option value="{s["key"]}"{"selected" if s["key"] == selected_label else ""}>{esc(s["label"])}</option>'
        for s in SESSION_TYPES
    )
    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    month_opts = "".join(
        f'<option value="{i}"{"selected" if i == cur_m else ""}>{m}</option>'
        for i, m in enumerate(month_names, 1)
    )
    year_opts = "".join(
        f'<option value="{y}"{"selected" if y == cur_y else ""}>{y}</option>'
        for y in range(2026, now.year + 4)
    )
    uid = "sm"  # unique prefix for IDs
    return f"""
    <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:16px;align-items:flex-end;">
      <div>
        <label for="session_label" style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Test Phase</label>
        <select id="session_label" name="session_label" required style="min-width:200px;">
          <option value="">— Select phase —</option>
          {type_opts}
        </select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">Month</label>
        <div style="display:flex;gap:6px;">
          <select id="{uid}_m" style="min-width:130px;" onchange="updateSessionMonth('{uid}')">{month_opts}</select>
          <select id="{uid}_y" style="min-width:80px;"  onchange="updateSessionMonth('{uid}')">{year_opts}</select>
        </div>
        <input type="hidden" id="{uid}_val" name="session_month" value="{cur_y:04d}-{cur_m:02d}" />
      </div>
    </div>
    <script>
    function updateSessionMonth(uid) {{
      var m = document.getElementById(uid + '_m').value;
      var y = document.getElementById(uid + '_y').value;
      document.getElementById(uid + '_val').value = y + '-' + String(m).padStart(2, '0');
    }}
    </script>"""


def _month_select(name="session_month", selected=None):
    """Standalone month+year selectors (reusable without the full label-picker layout)."""
    import datetime as _dt2
    now = _dt2.datetime.now()
    cur_m = now.month
    cur_y = now.year
    if selected:
        try:
            parts = selected.split("-")
            cur_y = int(parts[0])
            cur_m = int(parts[1])
        except Exception:
            pass
    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]
    month_opts = "".join(
        f'<option value="{i}"{"selected" if i == cur_m else ""}>{m}</option>'
        for i, m in enumerate(month_names, 1)
    )
    year_opts = "".join(
        f'<option value="{y}"{"selected" if y == cur_y else ""}>{y}</option>'
        for y in range(2026, now.year + 4)
    )
    uid = name.replace("_", "")
    return f"""<div style="display:flex;gap:6px;">
      <select id="{uid}_m" style="min-width:130px;" onchange="updateSessionMonth('{uid}')">{month_opts}</select>
      <select id="{uid}_y" style="min-width:80px;"  onchange="updateSessionMonth('{uid}')">{year_opts}</select>
    </div>
    <input type="hidden" id="{uid}_val" name="{name}" value="{cur_y:04d}-{cur_m:02d}" />
    <script>
    function updateSessionMonth(uid) {{
      var m = document.getElementById(uid + '_m').value;
      var y = document.getElementById(uid + '_y').value;
      document.getElementById(uid + '_val').value = y + '-' + String(m).padStart(2, '0');
    }}
    </script>"""


def _session_display_label(session):
    """Return a human-readable label for a session, e.g. 'Baseline Test — Sep 2026'."""
    label = SESSION_LABEL_MAP.get(session.get("session_label"), "")
    month = session.get("session_month", "")
    if label and month:
        try:
            d = _dt.datetime.strptime(month, "%Y-%m")
            return f"{label} — {d.strftime('%b %Y')}"
        except Exception:
            return f"{label} — {month}"
    # Fallback for legacy sessions with no label
    return session.get("date", "")[:10]


def layout(title, body, user=None, flash=None, active_nav=None):
    nav = ""
    if user:
        if user["role"] in ("practitioner", "org_admin", "system_admin"):
            is_admin = user.get("is_admin")
            is_sys   = user.get("role") == "system_admin"

            # Core nav — always visible
            links = [
                ("/coach",            "Dashboard",    "dashboard"),
                ("/coach/session",    "Record Session", "session"),
                ("/coach/attendance", "Attendance",   "attendance"),
                ("/coach/group-hub",  "Group Hub",    "group_hub"),
                ("/coach/leaderboard","Leaderboard",  "leaderboard"),
                ("/coach/resources",  "Resources",    "resources"),
                ("/coach/reports",    "Reports",      "progress"),
                ("/help",             "Help",         "help"),
            ]
            nav_items = "".join(
                f'<a class="nav-link{" active" if active_nav == key else ""}" href="{href}">{label}</a>'
                for href, label, key in links
            )

            # "Manage" dropdown — org_admin and system_admin only
            manage_html = ""
            if is_admin:
                manage_active = active_nav in ("new_participant", "coaches", "organisations", "admin_hub")
                manage_items = [
                    ("/coach/participants/new", "➕ Add Participant"),
                    ("/coach/coaches",          "👤 Practitioners"),
                    ("/coach/organisations",    "🏢 Organisations"),
                ]
                if is_sys:
                    manage_items += [
                        ("/coach/admin/hub",              "⚙ Admin Hub"),
                        ("/coach/admin/score-distribution","📊 Score Distribution"),
                        ("/coach/admin/game-thresholds",  "🎯 AAXP Thresholds"),
                    ]
                dropdown_links = "".join(
                    f'<a class="nav-dropdown-item" href="{h}">{l}</a>'
                    for h, l in manage_items
                )
                manage_html = f"""
                <div class="nav-dropdown{' active' if manage_active else ''}">
                  <button class="nav-link nav-dropdown-toggle" onclick="
                    var d=this.nextElementSibling;
                    var open=d.style.display==='block';
                    document.querySelectorAll('.nav-dropdown-menu').forEach(function(m){{m.style.display='none';}});
                    d.style.display=open?'none':'block';
                    event.stopPropagation();">Manage ▾</button>
                  <div class="nav-dropdown-menu" style="display:none;">
                    {dropdown_links}
                  </div>
                </div>"""

        else:
            links = [("/dashboard", "My Dashboard", "dashboard"),
                     ("/athlete/self-directed", "Self-Directed", "self_directed"),
                     ("/athlete/xp", "My AXP", "xp"),
                     ("/athlete/resources", "Resources", "resources")]
            if user.get("show_leaderboard"):
                links.append(("/athlete/leaderboard", "Leaderboard", "leaderboard"))
            links.append(("/help", "Help", "help"))
            nav_items = "".join(
                f'<a class="nav-link{" active" if active_nav == key else ""}" href="{href}">{label}</a>'
                for href, label, key in links
            )
            manage_html = ""

        nav = f"""
        <style>
          .nav-dropdown {{ position: relative; display: inline-block; }}
          .nav-dropdown-toggle {{ background: none; border: none; cursor: pointer;
            font-size: inherit; font-family: inherit; padding: 0; }}
          .nav-dropdown-menu {{
            position: absolute; top: calc(100% + 8px); left: 0;
            background: #fff; border: 1px solid #E5E7EB; border-radius: 10px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12); min-width: 200px;
            z-index: 999; padding: 6px 0;
          }}
          .nav-dropdown-item {{
            display: block; padding: 8px 16px; font-size: 13px;
            color: #2D323B; text-decoration: none; white-space: nowrap;
          }}
          .nav-dropdown-item:hover {{ background: #F4F5F7; }}
          .nav-dropdown.active .nav-dropdown-toggle {{ color: var(--jag-gold, #F0A82E); font-weight: 700; }}
        </style>
        <script>
          document.addEventListener('click', function() {{
            document.querySelectorAll('.nav-dropdown-menu').forEach(function(m) {{
              m.style.display = 'none';
            }});
          }});
        </script>
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span style="font-size:14px;letter-spacing:0.01em;">{APP_NAME}</span>
            </a>
            <nav class="nav" id="main-nav">{nav_items}{manage_html}</nav>
            <div class="user-pill">
              <a href="/account/password" class="btn btn-ghost btn-sm">My Account</a>
              <a href="/logout" class="btn btn-ghost btn-sm">Log out</a>
            </div>
            <button class="nav-toggle" onclick="var n=document.getElementById('main-nav');n.classList.toggle('nav--open');" aria-label="Menu">&#9776;</button>
          </div>
        </header>
        """
    else:
        nav = f"""
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span style="font-size:14px;letter-spacing:0.01em;">{APP_NAME}</span>
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
  <link rel="stylesheet" href="/static/css/style.css?v=20" />
  <link rel="icon" type="image/png" href="/static/img/logo.png" />
  <link rel="shortcut icon" type="image/png" href="/static/img/logo.png" />
  <style>
    /* Folder styling — inlined to bypass CDN caching */
    .res-folder {{ margin-top: 50px; margin-bottom: 32px; }}
    .res-folder-tab {{ font-size: 22px; padding: 10px 20px 10px 14px; gap: 10px; top: -50px; min-width: 220px; background: #EAECEE; border-color: #EAECEE; border-bottom-color: #fff; }}
    .res-folder-tab--ungrouped {{ background: #F3F4F5; border-color: #DDE0E3; border-bottom-color: #fff; }}
    .res-folder-icon {{ font-size: 22px; }}
    .res-folder-toggle {{ gap: 10px; color: #2D323B; }}
    .res-folder-name {{ color: #2D323B; font-size: 22px; }}
    .res-folder-tab--ungrouped .res-folder-toggle {{ color: #6E737B; }}
    .res-folder-tab--ungrouped .res-folder-name {{ color: #6E737B; }}
    .res-count {{ font-size: 14px; padding: 2px 10px; background: rgba(0,0,0,0.08); }}
    .res-folder-chevron {{ font-size: 16px; color: #2D323B; }}
    .res-folder-tab--ungrouped .res-folder-chevron {{ color: #6E737B; }}
    .res-folder-toggle:hover .res-folder-name {{ text-decoration: underline; }}
  </style>

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


def login_page(error=None, prefill_login=""):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    body = f"""
    <div class="login-wrap">
      <div class="card login-card">
        <img src="/static/img/logo.png" alt="Just A Game" class="login-logo" />
        <h1>{APP_NAME}</h1>
        <p class="muted">Log in to view your progress, or manage athletes as a practitioner.</p>
        {error_html}
        <form method="post" action="/login">
          <label for="login">Email or username</label>
          <input type="text" id="login" name="login" value="{esc(prefill_login)}" required autofocus autocomplete="username" />
          <label for="password">Password</label>
          <input type="password" id="password" name="password" required />
          <button type="submit" class="btn btn-primary btn-block">Log in</button>
        </form>
        <p class="forgot-link"><a href="/forgot-password">Forgot your password?</a></p>
        <details class="demo-creds">
          <summary>Demo login details</summary>
          <p><strong>Practitioner:</strong> coach@justagame.co.nz / CoachDemo123!</p>
          <p><strong>Participant:</strong> alex.demo@example.com / Athlete123!</p>
        </details>
      </div>
    </div>
    """
    return layout("Log in", body)


def forgot_password_page():
    body = f"""
    <div class="login-wrap">
      <div class="card login-card">
        <img src="/static/img/logo.png" alt="Just A Game" class="login-logo" />
        <h1>Forgot your password?</h1>
        <p class="muted">
          This app doesn't send reset emails — instead, your practitioner can issue
          you a new password directly. Get in touch with them (or with Just
          A Game) and ask for a password reset; they'll send you a new
          temporary password to log in with.
        </p>
        <a class="btn btn-primary btn-block" href="/login">Back to login</a>
      </div>
    </div>
    """
    return layout("Forgot Password", body)


def _measurement_field_input(game_key, field, is_computed=False):
    """One labelled number input with an inline quick-save button."""
    ftype = field["type"]
    step = "0.01" if ftype == "time" else "1"
    suffix = " (seconds)" if ftype == "time" else (f" ({field['unit']})" if field.get("unit") else "")
    input_id = f"mg__{game_key}__{field['key']}"
    if is_computed:
        return f"""
    <div class="mg-field" style="opacity:0.7;">
      <label for="{input_id}" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
        {esc(field['label'])}{esc(suffix)}
        <span style="font-size:10px;background:rgba(45,50,59,0.1);color:#6E737B;border-radius:999px;
                     padding:1px 8px;font-weight:600;letter-spacing:0.02em;">auto-calculated</span>
      </label>
      <div class="mg-field-row">
        <input type="number" step="{step}" min="0" id="{input_id}" name="{input_id}"
               data-game="{esc(game_key)}" data-field="{esc(field['key'])}" readonly
               style="background:#F3F4F5;color:#6E737B;cursor:not-allowed;border-color:#DDE0E3;" />
        <span style="font-size:12px;color:#6E737B;padding:4px 10px;white-space:nowrap;">auto</span>
      </div>
    </div>
    """
    return f"""
    <div class="mg-field">
      <label for="{input_id}">{esc(field['label'])}{esc(suffix)}</label>
      <div class="mg-field-row">
        <input type="number" step="{step}" min="0" id="{input_id}" name="{input_id}"
               data-game="{esc(game_key)}" data-field="{esc(field['key'])}" />
        <button type="button" class="btn btn-sm mg-save-btn"
                data-game="{esc(game_key)}" data-field="{esc(field['key'])}"
                title="Save this field">&#10003; Save</button>
      </div>
    </div>
    """


def _measurement_game_fieldset(game):
    """Styled collapsible card for a single measurement game."""
    game_key = game["key"]
    card_id = f"mg-card-{game_key}"
    body_id = f"mg-body-{game_key}"
    either_or = game.get("either_or", False)

    if either_or and len(game["fields"]) == 2:
        # Render with a clear OR divider between the two field options
        f0, f1 = game["fields"]
        or_divider = (
            '<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
            '<div style="flex:1;height:1px;background:#DDE0E3;"></div>'
            '<span style="font-size:11px;font-weight:700;color:#6E737B;letter-spacing:.08em;">OR</span>'
            '<div style="flex:1;height:1px;background:#DDE0E3;"></div>'
            '</div>'
        )
        either_note = (
            '<p style="margin:0 0 8px;font-size:12px;color:#6E737B;font-style:italic;">'
            'Record one option only &mdash; whichever applies to this session.</p>'
        )
        fields_html = either_note + _measurement_field_input(game_key, f0) + or_divider + _measurement_field_input(game_key, f1)
    else:
        fields_html = "".join(_measurement_field_input(game_key, f) for f in game["fields"])

    computed_html = "".join(
        _measurement_field_input(game_key, cf, is_computed=True)
        for cf in game.get("computed", [])
    )
    return f"""
    <div class="mg-game-card" id="{card_id}" data-game-key="{esc(game_key)}"
         style="border:1px solid #DDE0E3;border-left:4px solid #2D323B;border-radius:8px;
                margin-bottom:12px;overflow:hidden;transition:box-shadow 0.15s;">
      <div class="mg-game-header" onclick="toggleGameCard('{game_key}')"
           style="display:flex;align-items:center;justify-content:space-between;
                  padding:10px 14px;cursor:pointer;background:#fff;user-select:none;">
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="font-size:14px;font-weight:700;color:#2D323B;">{esc(game['name'])}</span>
          <span id="mg-badge-{game_key}" style="display:none;font-size:11px;font-weight:700;
                padding:2px 9px;border-radius:999px;line-height:1.6;"></span>
        </div>
        <span id="mg-toggle-{game_key}"
              style="font-size:11px;color:#F0A82E;font-weight:700;letter-spacing:0.05em;">&#9650; COLLAPSE</span>
      </div>
      <div id="{body_id}" style="padding:12px 14px 14px;background:#fafafa;border-top:1px solid #DDE0E3;">
        <div class="mg-field-grid">{fields_html}{computed_html}</div>
        <div style="margin-top:10px;text-align:right;">
          <button type="button" class="btn btn-primary btn-sm mg-save-game-btn"
                  data-game="{esc(game_key)}"
                  style="font-size:13px;padding:6px 18px;">&#10003; Save Game</button>
          <span class="mg-game-status" id="mg-status-{game_key}"
                style="font-size:12px;color:#6E737B;margin-left:10px;"></span>
        </div>
      </div>
    </div>
    """


def measurement_games_form(participant_id, selected_label=None, selected_month=None,
                           athlete_levels=None):
    """The coach-facing entry form for recording a Measurement Games test
    session -- one date, with a fieldset per game grouped under each
    section. Each field has its own quick-save button; the session is
    created lazily on the first save. A bulk-submit fallback is also
    available via the full form.

    athlete_levels: optional dict {game_key: highest_level} — when supplied,
    a coloured level badge is shown next to each game name so the coach can
    see at a glance where the athlete currently stands.
    """
    athlete_levels = athlete_levels or {}
    LEVEL_COLOURS_FORM = {
        0: ("#E5E7EB", "#6E737B"),
        1: ("#1EBE8B", "#fff"),
        2: ("#F0A82E", "#2D323B"),
        3: ("#2D323B", "#fff"),
        4: ("#F97316", "#fff"),
        5: ("#8B5CF6", "#fff"),
    }

    def _level_badge_html(game_key):
        lvl = athlete_levels.get(game_key, 0)
        if lvl == 0:
            return ""
        bg, fg = LEVEL_COLOURS_FORM.get(lvl, ("#6E737B", "#fff"))
        return (f'<span style="font-size:10px;font-weight:700;background:{bg};color:{fg};'
                f'border-radius:999px;padding:1px 7px;margin-left:6px;">L{lvl}</span>')

    # Build game chip list and sections HTML together — active games only
    # (deprecated games and hidden fields excluded via active_measurement_games())
    all_games_for_chips = []
    for section in active_measurement_games():
        for g in section["games"]:
            all_games_for_chips.append(g)

    chips_html = "".join(
        f'<button type="button" class="mg-chip mg-chip-active" data-chip-game="{esc(g["key"])}"'
        f' onclick="toggleChip(this)"'
        f' style="padding:5px 14px;border-radius:999px;border:2px solid #2D323B;background:#2D323B;'
        f'color:#F0A82E;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s;">'
        f'{esc(g["name"])}{_level_badge_html(g["key"])}</button>'
        for g in all_games_for_chips
    )

    chip_panel_html = f"""
    <div style="margin-bottom:20px;padding:14px 16px;background:#fff;border:1px solid #DDE0E3;
                border-radius:8px;border-left:4px solid #F0A82E;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
        <span style="font-size:13px;font-weight:700;color:#2D323B;">Games in this session</span>
        <div style="display:flex;gap:6px;">
          <button type="button" onclick="selectAllChips()"
                  style="font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid #DDE0E3;
                         background:#fff;color:#2D323B;cursor:pointer;font-weight:600;">All</button>
          <button type="button" onclick="selectNoChips()"
                  style="font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid #DDE0E3;
                         background:#fff;color:#2D323B;cursor:pointer;font-weight:600;">None</button>
        </div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:7px;">{chips_html}</div>
    </div>
    """

    # Completion status strip — populated by JS after pre-fill/save
    completion_strip_html = """
    <div id="mg-completion-strip" style="display:none;margin-bottom:16px;padding:12px 14px;
         background:#fff;border:1px solid #DDE0E3;border-radius:8px;border-left:4px solid #2D323B;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
        <span style="font-size:12px;font-weight:700;color:#2D323B;text-transform:uppercase;letter-spacing:0.05em;">Session Progress</span>
        <span id="mg-strip-summary" style="font-size:12px;color:#6E737B;"></span>
      </div>
      <div id="mg-strip-pills" style="display:flex;flex-wrap:wrap;gap:6px;"></div>
    </div>"""

    def _fieldset_with_level(g):
        """Wrap _measurement_game_fieldset and inject a level badge into the header."""
        html = _measurement_game_fieldset(g)
        lvl = athlete_levels.get(g["key"], 0)
        if lvl > 0:
            bg, fg = LEVEL_COLOURS_FORM.get(lvl, ("#6E737B", "#fff"))
            badge = (f'<span style="font-size:10px;font-weight:700;background:{bg};color:{fg};'
                     f'border-radius:999px;padding:1px 8px;margin-left:6px;vertical-align:middle;">L{lvl}</span>')
            # Insert badge after the game name span in the header
            html = html.replace(
                f'<span style="font-size:14px;font-weight:700;color:#2D323B;">{esc(g["name"])}</span>',
                f'<span style="font-size:14px;font-weight:700;color:#2D323B;">{esc(g["name"])}</span>{badge}',
                1,
            )
        return html

    sections_html = completion_strip_html + chip_panel_html + "".join(f"""
    <div class="mg-section" style="margin-bottom:24px;">
      <div style="border-left:4px solid #F0A82E;padding-left:10px;margin-bottom:12px;">
        <h4 style="margin:0;font-size:15px;font-weight:700;color:var(--jag-navy);">{esc(section['section'])}</h4>
      </div>
      {''.join(_fieldset_with_level(g) for g in section['games'])}
    </div>
    """ for section in active_measurement_games())

    # Build hidden sport-specific sections (revealed by JS when checkbox ticked)
    sport_sections_html = ""
    for sport, sport_sections in SPORT_SPECIFIC_GAMES.items():
        sport_fieldsets = "".join(
            f"""<div class="mg-section" style="margin-bottom:24px;">
              <div style="border-left:4px solid #F0A82E;padding-left:10px;margin-bottom:12px;">
                <h4 style="margin:0;font-size:15px;font-weight:700;color:var(--jag-navy);">{esc(section['section'])}</h4>
              </div>
              {''.join(_measurement_game_fieldset(g) for g in section['games'])}
            </div>"""
            for section in sport_sections
        )
        sport_sections_html += (
            f'<div class="sport-fields" data-sport="{esc(sport)}" style="display:none;">'
            f'{sport_fieldsets}</div>'
        )

    # Sport selector options
    sport_opts = "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>'
        for s in SPORT_SPECIFIC_GAMES
    )

    sport_ui_html = f"""
    <div style="margin:20px 0 10px; padding-top:18px; border-top:2px solid var(--jag-border);">
      <label style="display:flex; align-items:center; gap:10px; cursor:pointer; margin:0 0 12px; font-size:14px; font-weight:600;">
        <input type="checkbox" id="mg-sport-check" style="width:auto; margin:0;" />
        Sport Specific Testing
      </label>
      <div id="mg-sport-wrap" style="display:none; margin-bottom:16px;">
        <label for="mg-sport-select" style="font-size:13px; font-weight:600; margin:0 0 6px;">Select Sport</label>
        <select id="mg-sport-select" style="max-width:220px;">
          <option value="">— Select sport —</option>
          {sport_opts}
        </select>
      </div>
    </div>
    {sport_sections_html}
    """

    quick_save_js = f"""
    <script>
    (function() {{
      var sessionId = null;
      var baseUrl = '/coach/participants/{participant_id}/measurement';

      function getSessionLabel() {{
        var sel = document.getElementById('session_label');
        return sel ? sel.value : '';
      }}
      function getSessionMonth() {{
        var sel = document.getElementById('session_month');
        return sel ? sel.value : '';
      }}

      // Pre-fill form when a phase label is selected
      async function prefillFromPhase(label) {{
        if (!label) return;
        try {{
          var resp = await fetch(baseUrl + '/phase-results?label=' + encodeURIComponent(label));
          if (!resp.ok) return;
          var data = await resp.json();
          var results = data.results || {{}};
          var prefilled = 0;
          Object.keys(results).forEach(function(gameKey) {{
            Object.keys(results[gameKey]).forEach(function(fieldKey) {{
              var inp = document.getElementById('mg__' + gameKey + '__' + fieldKey);
              if (inp) {{
                inp.value = results[gameKey][fieldKey];
                inp.style.background = '#fffbe6';  // subtle yellow tint to show pre-filled
                prefilled++;
              }}
            }});
          }});
          // Reuse the existing session id so saves go to the right record
          if (data.session_id) {{
            sessionId = data.session_id;
            var doneBtn = document.getElementById('mg-done-btn');
            if (doneBtn) doneBtn.style.display = 'inline-block';
          }}
          // Pre-fill session month if form is still blank
          if (data.session_month) {{
            var monthInput = document.getElementById('session_month');
            if (monthInput && !monthInput.value) monthInput.value = data.session_month;
          }}
          if (prefilled > 0) {{
            var hint = document.getElementById('mg-hint');
            if (hint) hint.textContent = prefilled + ' existing value(s) loaded — update any field and save to merge.';
          }}
          updateGameBadges();
        }} catch(e) {{}}
      }}

      // Update per-game completion badges and the top-of-form progress strip
      function updateGameBadges() {{
        var cards = document.querySelectorAll('.mg-game-card');
        var totalGames = 0;
        var doneGames = 0;
        var partialGames = 0;
        var pillsEl = document.getElementById('mg-strip-pills');
        var summaryEl = document.getElementById('mg-strip-summary');
        var stripEl = document.getElementById('mg-completion-strip');
        if (pillsEl) pillsEl.innerHTML = '';

        cards.forEach(function(card) {{
          var gameKey = card.dataset.gameKey;
          if (!gameKey) return;
          // Only count visible cards (not hidden by chip toggle)
          if (card.style.display === 'none') return;
          var inputs = card.querySelectorAll('input[data-game]:not([readonly])');
          if (inputs.length === 0) return;
          var filled = 0;
          inputs.forEach(function(inp) {{ if (inp.value.trim() !== '') filled++; }});
          totalGames++;

          var badge = document.getElementById('mg-badge-' + gameKey);
          var gameName = card.querySelector('.mg-game-header span[style*="font-weight:700"]');
          var nameText = gameName ? gameName.textContent.trim() : gameKey;
          // Abbreviate for pill
          var abbrev = nameText.length > 14 ? nameText.substring(0, 13) + '…' : nameText;

          var status, badgeStyle, pillStyle, pillIcon;
          if (filled === inputs.length) {{
            status = 'done';
            badgeStyle = 'background:#d1fae5;color:#065f46;';
            pillStyle = 'background:#d1fae5;color:#065f46;border:1px solid #6ee7b7;';
            pillIcon = '✓ ';
            doneGames++;
          }} else if (filled > 0) {{
            status = 'partial';
            badgeStyle = 'background:#fef3c7;color:#92400e;';
            pillStyle = 'background:#fef3c7;color:#92400e;border:1px solid #fcd34d;';
            pillIcon = '◑ ';
            partialGames++;
          }} else {{
            status = 'empty';
            badgeStyle = 'background:#f3f4f6;color:#6b7280;';
            pillStyle = 'background:#f3f4f6;color:#6b7280;border:1px solid #d1d5db;';
            pillIcon = '— ';
          }}

          // Update card header badge
          if (badge) {{
            badge.style.display = 'inline-block';
            badge.style.cssText += badgeStyle;
            badge.textContent = status === 'done' ? '✓ Done'
                              : status === 'partial' ? '◑ Partial'
                              : '— Not started';
          }}

          // Add pill to strip
          if (pillsEl) {{
            var pill = document.createElement('span');
            pill.style.cssText = 'font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;cursor:pointer;' + pillStyle;
            pill.textContent = pillIcon + abbrev;
            pill.title = nameText + ' — ' + (status === 'done' ? 'Complete' : status === 'partial' ? 'Partial' : 'Not started');
            pill.addEventListener('click', function() {{
              card.scrollIntoView({{behavior:'smooth', block:'start'}});
            }});
            pillsEl.appendChild(pill);
          }}
        }});

        // Show strip only once a phase is selected and we have status info
        if (stripEl && totalGames > 0) {{
          stripEl.style.display = 'block';
          if (summaryEl) {{
            summaryEl.textContent = doneGames + '/' + totalGames + ' complete'
              + (partialGames > 0 ? ', ' + partialGames + ' partial' : '');
          }}
        }}
      }}

      var labelSel = document.getElementById('session_label');
      if (labelSel) {{
        labelSel.addEventListener('change', function() {{
          // Reset session so the next ensureSession() picks up the existing one for this label
          sessionId = null;
          prefillFromPhase(labelSel.value);
        }});
        // Pre-fill on page load if a label is already selected
        if (labelSel.value) prefillFromPhase(labelSel.value);
      }}

      function markBtn(btn, state) {{
        if (state === 'saving') {{
          btn.textContent = '...';
          btn.disabled = true;
          btn.style.background = '';
        }} else if (state === 'ok') {{
          btn.textContent = '\\u2713 Saved';
          btn.disabled = false;
          btn.style.background = '#F0A82E';
          btn.style.color = '#2D323B';
          btn.style.borderColor = '#F0A82E';
          setTimeout(function() {{
            btn.textContent = '\\u2713 Save';
            btn.style.background = '';
            btn.style.color = '';
            btn.style.borderColor = '';
          }}, 2000);
        }} else if (state === 'error') {{
          btn.textContent = '! Error';
          btn.disabled = false;
          btn.style.background = '#9b1c1c';
          btn.style.color = '#fff';
          btn.style.borderColor = '#9b1c1c';
          setTimeout(function() {{
            btn.textContent = '\\u2713 Save';
            btn.style.background = '';
            btn.style.color = '';
            btn.style.borderColor = '';
          }}, 3000);
        }}
      }}

      async function ensureSession() {{
        if (sessionId) return sessionId;
        var lbl = getSessionLabel();
        if (!lbl) {{
          alert('Please select a Test Phase before saving.');
          throw new Error('No session label');
        }}
        var resp = await fetch(baseUrl + '/start', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
          body: 'session_label=' + encodeURIComponent(lbl) +
                '&session_month=' + encodeURIComponent(getSessionMonth()),
        }});
        if (!resp.ok) throw new Error('Could not create session');
        var data = await resp.json();
        sessionId = data.session_id;
        // Show the "Done" button once session is started
        var doneBtn = document.getElementById('mg-done-btn');
        if (doneBtn) doneBtn.style.display = 'inline-block';
        return sessionId;
      }}

      async function saveField(gameKey, fieldKey, value, btn) {{
        markBtn(btn, 'saving');
        try {{
          var sid = await ensureSession();
          var resp = await fetch(baseUrl + '/' + sid + '/save-field', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
            body: 'game_key=' + encodeURIComponent(gameKey) +
                  '&field_key=' + encodeURIComponent(fieldKey) +
                  '&value=' + encodeURIComponent(value),
          }});
          var data = await resp.json();
          if (!resp.ok || !data.ok) throw new Error('Save failed');
          // Update any computed fields returned by the server
          Object.keys(data.computed || {{}}).forEach(function(compKey) {{
            var el = document.getElementById('mg__' + gameKey + '__' + compKey);
            if (el) el.value = data.computed[compKey];
          }});
          markBtn(btn, 'ok');
        }} catch(e) {{
          markBtn(btn, 'error');
        }}
      }}

      document.querySelectorAll('.mg-save-btn').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
          var gameKey  = btn.dataset.game;
          var fieldKey = btn.dataset.field;
          var input    = document.getElementById('mg__' + gameKey + '__' + fieldKey);
          var value    = input ? input.value.trim() : '';
          if (!value) {{ alert('Please enter a value first.'); return; }}
          saveField(gameKey, fieldKey, value, btn);
        }});
      }});

      // Save Game button — saves all non-empty, non-computed fields for a game at once
      async function saveGame(gameKey, btn) {{
        var statusEl = document.getElementById('mg-status-' + gameKey);
        var inputs = document.querySelectorAll(
          'input[data-game="' + gameKey + '"]:not([readonly])');
        var toSave = [];
        inputs.forEach(function(inp) {{
          var v = inp.value.trim();
          if (v !== '') toSave.push({{fieldKey: inp.dataset.field, value: v, inp: inp}});
        }});
        if (toSave.length === 0) {{
          if (statusEl) statusEl.textContent = 'Nothing to save — enter at least one value.';
          return;
        }}
        btn.disabled = true;
        btn.textContent = 'Saving…';
        if (statusEl) statusEl.textContent = '';
        try {{
          var sid = await ensureSession();
          var saved = 0;
          for (var i = 0; i < toSave.length; i++) {{
            var item = toSave[i];
            var resp = await fetch(baseUrl + '/' + sid + '/save-field', {{
              method: 'POST',
              headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
              body: 'game_key=' + encodeURIComponent(gameKey) +
                    '&field_key=' + encodeURIComponent(item.fieldKey) +
                    '&value=' + encodeURIComponent(item.value),
            }});
            var data = await resp.json();
            if (data.ok) {{
              item.inp.style.background = '#f0fff4';
              // Update computed fields
              Object.keys(data.computed || {{}}).forEach(function(ck) {{
                var el = document.getElementById('mg__' + gameKey + '__' + ck);
                if (el) el.value = data.computed[ck];
              }});
              saved++;
            }}
          }}
          btn.textContent = '✓ Saved';
          btn.style.background = '#F0A82E';
          btn.style.color = '#2D323B';
          btn.style.borderColor = '#F0A82E';
          if (statusEl) statusEl.textContent = saved + ' field' + (saved !== 1 ? 's' : '') + ' saved.';
          updateGameBadges();
          setTimeout(function() {{
            btn.textContent = '✓ Save Game';
            btn.style.background = '';
            btn.style.color = '';
            btn.style.borderColor = '';
            btn.disabled = false;
          }}, 2500);
        }} catch(e) {{
          btn.textContent = '! Error';
          btn.disabled = false;
          if (statusEl) statusEl.textContent = 'Save failed — try again.';
        }}
      }}

      document.querySelectorAll('.mg-save-game-btn').forEach(function(btn) {{
        btn.addEventListener('click', function() {{ saveGame(btn.dataset.game, btn); }});
      }});

      // Allow pressing Enter in a field to trigger its save button
      document.querySelectorAll('input[data-game][data-field]').forEach(function(inp) {{
        inp.addEventListener('keydown', function(e) {{
          if (e.key === 'Enter') {{
            e.preventDefault();
            var btn = inp.parentElement.querySelector('.mg-save-btn');
            if (btn) btn.click();
          }}
        }});
      }});

      // Sport-specific toggle
      var sportCheck  = document.getElementById('mg-sport-check');
      var sportWrap   = document.getElementById('mg-sport-wrap');
      var sportSelect = document.getElementById('mg-sport-select');
      if (sportCheck) {{
        sportCheck.addEventListener('change', function() {{
          sportWrap.style.display = sportCheck.checked ? 'block' : 'none';
          if (!sportCheck.checked && sportSelect) {{
            sportSelect.value = '';
            document.querySelectorAll('.sport-fields').forEach(function(el) {{ el.style.display = 'none'; }});
          }}
        }});
      }}
      if (sportSelect) {{
        sportSelect.addEventListener('change', function() {{
          var chosen = sportSelect.value;
          document.querySelectorAll('.sport-fields').forEach(function(el) {{
            el.style.display = (el.dataset.sport === chosen) ? 'block' : 'none';
          }});
        }});
      }}
    }})();
    </script>
    <script>
    // Game card collapse/expand
    function toggleGameCard(gameKey) {{
      var body   = document.getElementById('mg-body-' + gameKey);
      var toggle = document.getElementById('mg-toggle-' + gameKey);
      if (!body) return;
      var collapsed = body.style.display === 'none';
      body.style.display = collapsed ? '' : 'none';
      if (toggle) toggle.innerHTML = collapsed ? '&#9650; COLLAPSE' : '&#9660; EXPAND';
    }}

    // Chip toggle — show/hide corresponding game card
    function toggleChip(btn) {{
      var gameKey = btn.dataset.chipGame;
      var card    = document.getElementById('mg-card-' + gameKey);
      var active  = btn.classList.contains('mg-chip-active');
      if (active) {{
        btn.classList.remove('mg-chip-active');
        btn.style.background = '#F3F4F5';
        btn.style.color      = '#6E737B';
        btn.style.borderColor= '#DDE0E3';
        if (card) card.style.display = 'none';
      }} else {{
        btn.classList.add('mg-chip-active');
        btn.style.background = '#2D323B';
        btn.style.color      = '#F0A82E';
        btn.style.borderColor= '#2D323B';
        if (card) card.style.display = '';
      }}
    }}

    function selectAllChips() {{
      document.querySelectorAll('.mg-chip').forEach(function(btn) {{
        if (!btn.classList.contains('mg-chip-active')) toggleChip(btn);
      }});
    }}

    function selectNoChips() {{
      document.querySelectorAll('.mg-chip').forEach(function(btn) {{
        if (btn.classList.contains('mg-chip-active')) toggleChip(btn);
      }});
    }}
    </script>"""

    return f"""
    <div class="card form-card">
      <h3>Base Adaptability Testing</h3>
      <p class="muted">Select the test phase and month, then enter values and click <strong>&#10003; Save</strong> next to each field.
      The Skipping Rope Sprint average is calculated automatically from Time 1/2/3.</p>
      {_session_label_pickers(selected_label=selected_label, selected_month=selected_month)}
      {sections_html}
      {sport_ui_html}
      <div style="margin-top:16px; display:flex; gap:12px; align-items:center;">
        <a id="mg-done-btn" href="/coach/participants/{participant_id}" class="btn btn-primary"
           style="display:none;">&#10003; Done &mdash; View Results</a>
        <span class="muted" style="font-size:13px;" id="mg-hint">Save at least one field to finish the session.</span>
      </div>
      {quick_save_js}
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
    for game in all_active_measurement_games():
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

    action_html = ""
    if show_delete and participant_id:
        action_html = f"""
        <div style="display:flex;gap:8px;align-items:center;">
          <a href="/coach/participants/{participant_id}/measurement/{session['id']}/edit"
             class="btn btn-ghost btn-sm">&#9998; Edit</a>
          <form method="post" action="/coach/participants/{participant_id}/measurement/{session['id']}/delete"
                style="display:inline" onsubmit="return confirm('Delete this Measurement Games session?');">
            <button type="submit" class="btn btn-ghost btn-sm">Delete</button>
          </form>
        </div>
        """

    display_label = _session_display_label(session)
    return f"""
    <div class="card mg-session-card">
      <div class="mg-session-head">
        <strong>{esc(display_label)}</strong>
        {action_html}
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


def _calc_improvement_pct(measurement_sessions):
    """Average % improvement across all fields, first vs latest session.
    Returns None if fewer than 2 sessions."""
    if len(measurement_sessions) < 2:
        return None
    latest = measurement_sessions[0]
    first  = measurement_sessions[-1]
    improvements = []
    for game in all_active_measurement_games():
        for field in game["fields"] + game.get("computed", []):
            fv = first["results"].get((game["key"], field["key"]))
            lv = latest["results"].get((game["key"], field["key"]))
            if fv is None or lv is None or fv == 0:
                continue
            if field["type"] == "time":
                imp = (fv - lv) / fv * 100   # lower time = improvement
            else:
                imp = (lv - fv) / fv * 100   # higher score = improvement
            improvements.append(imp)
    if not improvements:
        return None
    return sum(improvements) / len(improvements)


def participant_dashboard(user, measurement_sessions,
                           xp_data=None, levels=None,
                           pending_self_directed=None, thresholds=None,
                           resources=None, attendance_count=None,
                           active_window=None, already_submitted=False):
    """Full athlete dashboard: rank hero, XP progress, game level grid, guided steps, nudge."""
    from constants import CORE_AAP_GAMES, XP_GAME_CONFIG, find_measurement_game

    first_name = esc(user['name'].split(' ')[0])
    name = user['name']
    parts = name.strip().split()
    inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
    sport = esc(user.get('sport') or '')
    programme = esc(user.get('programme') or '')
    session_count = len(measurement_sessions)
    att_count = attendance_count or 0

    # ── XP & rank ────────────────────────────────────────────────────────────
    xp_data = xp_data or {}
    total_xp = xp_data.get("total", 0)
    tier = xp_data.get("tier") or {"label": "Starter", "colour": "#6E737B"}
    next_tier = xp_data.get("next_tier")
    xp_progress = xp_data.get("progress", 0.0)
    tier_colour = tier["colour"]
    tier_label = esc(tier["label"])

    xp_bar_pct = int(xp_progress * 100)
    if next_tier:
        xp_to_next = next_tier["min_xp"] - total_xp
        xp_next_label = (f'<span style="font-size:12px;color:#6E737B;">'
                         f'{xp_to_next:,} AXP to {esc(next_tier["label"])}</span>')
    else:
        xp_next_label = '<span style="font-size:12px;color:#1EBE8B;font-weight:700;">Max rank reached!</span>'

    # ── Active measurement window banner ──────────────────────────────────────
    window_banner = ""
    if active_window:
        wid = active_window["id"]
        label_txt = esc(active_window.get("session_label") or "")
        label_part = f' — <strong>{label_txt}</strong>' if label_txt else ''
        if already_submitted:
            window_banner = f"""
    <div style="background:#065F46;border-radius:14px;padding:16px 20px;margin-bottom:20px;
                display:flex;align-items:center;gap:14px;">
      <span style="font-size:24px;">✅</span>
      <div>
        <div style="font-weight:700;color:#fff;font-size:15px;">Scores submitted{label_part}</div>
        <div style="color:#A7F3D0;font-size:13px;margin-top:2px;">
          Your scores have been recorded. AAXP will be awarded when your practitioner closes the session.
        </div>
      </div>
    </div>"""
        else:
            window_banner = f"""
    <div style="background:#92400E;border-radius:14px;padding:16px 20px;margin-bottom:20px;
                display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
      <span style="font-size:24px;">📋</span>
      <div style="flex:1;min-width:180px;">
        <div style="font-weight:700;color:#fff;font-size:15px;">Measurement session open{label_part}</div>
        <div style="color:#FDE68A;font-size:13px;margin-top:2px;">
          Your practitioner has opened a testing session. Enter your scores now.
        </div>
      </div>
      <a href="/athlete/window/{wid}"
         style="background:#F0A82E;color:#2D323B;font-weight:700;font-size:14px;
                border-radius:10px;padding:10px 20px;text-decoration:none;white-space:nowrap;">
        Enter My Scores →
      </a>
    </div>"""

    # ── Hero card ─────────────────────────────────────────────────────────────
    sport_pill = (f'<span style="font-size:12px;font-weight:600;'
                  f'background:rgba(240,168,46,0.15);color:#F0A82E;'
                  f'border-radius:999px;padding:2px 10px;">{sport}</span>') if sport else ''
    hero = f"""
    <div style="background:#2D323B;border-radius:20px;padding:28px;margin-bottom:24px;
                position:relative;overflow:hidden;">
      <div style="position:absolute;top:-30px;right:-30px;width:180px;height:180px;
                  border-radius:50%;background:rgba(240,168,46,0.08);pointer-events:none;"></div>
      <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
        <!-- Avatar -->
        <div style="width:72px;height:72px;border-radius:50%;background:#F0A82E;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;font-size:26px;color:#2D323B;flex-shrink:0;
                    box-shadow:0 4px 20px rgba(240,168,46,0.4);">{inits}</div>
        <!-- Name + rank -->
        <div style="flex:1;min-width:200px;">
          <div style="font-size:13px;color:#9CA3AF;margin-bottom:2px;">Welcome back</div>
          <h1 style="margin:0 0 8px;font-size:26px;color:#fff;font-weight:800;">{first_name}!</h1>
          <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
            <span style="font-size:12px;font-weight:700;background:{tier_colour};color:#fff;
                         border-radius:999px;padding:3px 12px;letter-spacing:0.04em;">{tier_label}</span>
            {sport_pill}
          </div>
        </div>
        <!-- XP block -->
        <div style="text-align:right;flex-shrink:0;">
          <div style="font-size:32px;font-weight:800;color:#F0A82E;line-height:1;">{total_xp:,}</div>
          <div style="font-size:11px;color:#9CA3AF;margin-bottom:8px;letter-spacing:0.05em;">TOTAL AXP</div>
          {xp_next_label}
        </div>
      </div>
      <!-- XP progress bar -->
      <div style="margin-top:20px;">
        <div style="background:rgba(255,255,255,0.1);border-radius:999px;height:6px;overflow:hidden;">
          <div style="background:{tier_colour};width:{xp_bar_pct}%;height:100%;
                      border-radius:999px;transition:width 0.6s ease;"></div>
        </div>
      </div>
    </div>"""

    # ── Pending self-directed nudge ───────────────────────────────────────────
    nudge_html = ""
    if pending_self_directed:
        count = len(pending_self_directed)
        nudge_html = f"""
        <a href="/athlete/self-directed" style="text-decoration:none;display:block;
           background:rgba(240,168,46,0.1);border:1.5px solid #F0A82E;border-radius:12px;
           padding:14px 18px;margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🏃</div>
            <div style="flex:1;">
              <div style="font-size:14px;font-weight:700;color:#2D323B;">
                {count} self-directed session{'s' if count > 1 else ''} ready to score
              </div>
              <div style="font-size:12px;color:#6E737B;margin-top:2px;">
                Tap to record your scores and earn AXP →
              </div>
            </div>
          </div>
        </a>"""

    # ── Quick stats ───────────────────────────────────────────────────────────
    levels = levels or {}
    games_with_level = sum(1 for g in CORE_AAP_GAMES if levels.get(g, 0) >= 1)
    imp_pct = _calc_improvement_pct(measurement_sessions)
    imp_stat = f'{imp_pct:+.1f}%' if imp_pct is not None else '—'
    stats_html = f"""
    <section class="stat-row" style="margin-bottom:24px;">
      <div class="card stat-card">
        <div class="stat-number">{att_count}</div>
        <div class="stat-label">Sessions Attended</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{session_count}</div>
        <div class="stat-label">Test Sessions</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{games_with_level}<span style="font-size:16px;color:#6E737B;">/8</span></div>
        <div class="stat-label">Games Level 1+</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{imp_stat}</div>
        <div class="stat-label">Avg Improvement</div>
      </div>
    </section>"""

    # ── Level colours ─────────────────────────────────────────────────────────
    LEVEL_COLOURS = {
        0: ("#6E737B", "#fff"),
        1: ("#1EBE8B", "#fff"),
        2: ("#F0A82E", "#2D323B"),
        3: ("#2D323B", "#fff"),
        4: ("#F97316", "#fff"),
        5: ("#8B5CF6", "#fff"),
    }

    # ── Game level grid + guided steps ───────────────────────────────────────
    thresholds = thresholds or {}
    game_cards = ""
    for game_key in CORE_AAP_GAMES:
        game_def = find_measurement_game(game_key)
        if not game_def:
            continue
        game_name = esc(game_def["name"])
        current_level = levels.get(game_key, 0)
        next_level = current_level + 1
        bg_col, txt_col = LEVEL_COLOURS.get(current_level, ("#6E737B", "#fff"))
        level_label = f"L{current_level}" if current_level > 0 else "—"

        # Guided step: what's needed for next level
        cfg = XP_GAME_CONFIG.get(game_key, {})
        primary_field = cfg.get("primary_field")
        guide_html = ""
        if next_level <= 5 and primary_field:
            threshold_key = f"{game_key}|{next_level}"
            threshold_val = thresholds.get(threshold_key)
            if threshold_val is not None:
                lower_better = cfg.get("lower_is_better", False)
                direction = "or lower" if lower_better else "or more"
                # Find field label
                field_label = primary_field.replace("_", " ").title()
                for f in game_def.get("fields", []) + game_def.get("computed", []):
                    if f["key"] == primary_field:
                        field_label = f["label"]
                        break
                guide_html = (
                    f'<div style="font-size:11px;color:#6E737B;margin-top:6px;line-height:1.4;">'
                    f'Next level: <strong style="color:#2D323B;">{threshold_val} {direction}</strong>'
                    f'<br><span style="color:#9CA3AF;">{esc(field_label)}</span>'
                    f'</div>'
                )
            else:
                if next_level <= 5:
                    guide_html = '<div style="font-size:11px;color:#9CA3AF;margin-top:6px;">Thresholds not yet set</div>'
        elif current_level >= 5:
            guide_html = '<div style="font-size:11px;color:#8B5CF6;font-weight:700;margin-top:6px;">Max level reached!</div>'

        game_cards += f"""
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;
                    padding:14px 16px;display:flex;flex-direction:column;gap:4px;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
            <div style="font-size:13px;font-weight:600;color:#2D323B;line-height:1.3;">{game_name}</div>
            <div style="font-size:13px;font-weight:800;background:{bg_col};color:{txt_col};
                        border-radius:999px;padding:2px 10px;white-space:nowrap;flex-shrink:0;">{level_label}</div>
          </div>
          {guide_html}
        </div>"""

    level_grid = f"""
    <h2 class="section-title" style="margin-bottom:12px;">Game Levels & Next Steps</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:28px;">
      {game_cards}
    </div>"""

    # ── Resource quick links ──────────────────────────────────────────────────
    resource_links_html = ""
    if resources:
        tiles = ""
        for r in resources[:6]:
            r_name = esc(r.get("name", ""))
            r_url = r.get("url", "")
            tag_names = ", ".join(esc(t) for t in (r.get("tag_names") or []))
            tiles += f"""
            <a href="{esc(r_url)}" target="_blank" rel="noopener"
               style="display:block;background:#fff;border:1px solid #E5E7EB;border-radius:10px;
                      padding:12px 14px;text-decoration:none;
                      transition:box-shadow 0.15s,border-color 0.15s;"
               onmouseover="this.style.boxShadow='0 2px 12px rgba(0,0,0,0.08)';this.style.borderColor='#F0A82E'"
               onmouseout="this.style.boxShadow='';this.style.borderColor='#E5E7EB'">
              <div style="font-size:13px;font-weight:600;color:#2D323B;">{r_name}</div>
              {f'<div style="font-size:11px;color:#9CA3AF;margin-top:3px;">{tag_names}</div>' if tag_names else ''}
            </a>"""
        more_link = (f'<a href="/athlete/resources" style="font-size:13px;color:#2D323B;'
                     f'font-weight:600;">View all resources →</a>'
                     if len(resources) > 6 else '')
        resource_links_html = f"""
        <h2 class="section-title" style="margin-bottom:12px;">Resources</h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:8px;">
          {tiles}
        </div>
        <div style="margin-bottom:28px;">{more_link}</div>"""

    # ── Recent results summary ────────────────────────────────────────────────
    history_html = ""
    if measurement_sessions:
        history_html = f"""
        <h2 class="section-title" style="margin-bottom:12px;">Recent Test Results</h2>
        {measurement_games_history(measurement_sessions)}"""

    body = f"""
    <div style="max-width:860px;">
      {window_banner}
      {hero}
      {nudge_html}
      {stats_html}
      {level_grid}
      {resource_links_html}
      {history_html}
    </div>"""
    return layout("My Dashboard", body, user=user, active_nav="dashboard")


def athlete_resources_page(athlete, resources_by_tag, all_tags, selected_tag_id=None):
    """Athlete-facing resource browser — tag chips + resource grid."""
    # Tag filter bar
    tag_chips = '<a href="/athlete/resources" style="display:inline-block;padding:5px 14px;' \
                f'border-radius:999px;font-size:13px;font-weight:600;text-decoration:none;margin:3px;' \
                f'background:{"#2D323B" if not selected_tag_id else "#E5E7EB"};' \
                f'color:{"#fff" if not selected_tag_id else "#2D323B"};">All</a>'
    for t in all_tags:
        active = (selected_tag_id == t["id"])
        tag_chips += (
            f'<a href="/athlete/resources?tag={t["id"]}" '
            f'style="display:inline-block;padding:5px 14px;border-radius:999px;font-size:13px;'
            f'font-weight:600;text-decoration:none;margin:3px;'
            f'background:{"#2D323B" if active else "#E5E7EB"};'
            f'color:{"#fff" if active else "#2D323B"};">{esc(t["name"])}</a>'
        )

    # Build resource tiles per tag group (or flat if filtered)
    content_html = ""
    if selected_tag_id:
        # Flat view for a single tag
        items = resources_by_tag.get(selected_tag_id, [])
        if items:
            tiles = _athlete_resource_tiles(items)
            content_html = f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;">{tiles}</div>'
        else:
            content_html = '<p style="color:#9CA3AF;font-size:14px;padding:20px 0;">No resources in this category.</p>'
    else:
        # Grouped by tag
        if resources_by_tag:
            for t in all_tags:
                items = resources_by_tag.get(t["id"], [])
                if not items:
                    continue
                tiles = _athlete_resource_tiles(items)
                content_html += f"""
                <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:24px 0 10px;">{esc(t['name'])}</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:8px;">
                  {tiles}
                </div>"""
            # Untagged
            untagged = resources_by_tag.get(None, [])
            if untagged:
                tiles = _athlete_resource_tiles(untagged)
                content_html += f"""
                <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:24px 0 10px;">Other</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;">
                  {tiles}
                </div>"""
        else:
            content_html = '<p style="color:#9CA3AF;font-size:14px;padding:32px 0;text-align:center;">No resources have been shared yet.</p>'

    body = f"""
    <div style="max-width:900px;padding-top:28px;">
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 16px;">Resources</h2>
      <div style="margin-bottom:20px;line-height:2.2;">{tag_chips}</div>
      {content_html}
    </div>"""
    return layout("Resources", body, user=athlete, active_nav="resources")


def _athlete_resource_tiles(items):
    html = ""
    for r in items:
        r_name = esc(r.get("name", ""))
        r_url = r.get("url", "")
        r_notes = esc(r.get("notes") or "")
        thumb = _gdrive_thumbnail(r_url) if "drive.google.com" in r_url else None
        img_html = (f'<img src="{thumb}" alt="" style="width:100%;height:100px;'
                    f'object-fit:cover;border-radius:8px 8px 0 0;display:block;">'
                    if thumb else '')
        html += f"""
        <a href="{esc(r_url)}" target="_blank" rel="noopener"
           style="display:flex;flex-direction:column;background:#fff;
                  border:1px solid #E5E7EB;border-radius:12px;text-decoration:none;
                  overflow:hidden;transition:box-shadow 0.15s,border-color 0.15s;"
           onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.1)';this.style.borderColor='#F0A82E'"
           onmouseout="this.style.boxShadow='';this.style.borderColor='#E5E7EB'">
          {img_html}
          <div style="padding:12px 14px;flex:1;">
            <div style="font-size:13px;font-weight:700;color:#2D323B;line-height:1.3;">{r_name}</div>
            {f'<div style="font-size:12px;color:#6E737B;margin-top:4px;">{r_notes}</div>' if r_notes else ''}
          </div>
        </a>"""
    return html


def _athlete_tile(p, is_admin=False):
    """Render a single athlete as a clickable tile with initials avatar."""
    name = p['name']
    parts = name.strip().split()
    inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
    sport = esc(p.get('sport') or '')
    drag = '<span class="drag-handle" title="Drag to move group" style="position:absolute;top:6px;right:8px;font-size:11px;color:#bbb;line-height:1;">&#9776;</span>' if is_admin else ""
    sport_badge = (f'<span style="font-size:10px;font-weight:600;background:rgba(240,168,46,0.15);color:#CF8F1F;'
                   f'border-radius:999px;padding:2px 8px;white-space:nowrap;">{sport}</span>') if sport else ''
    an = p.get('athlete_number') or ''
    number_badge = (f'<span style="position:absolute;top:6px;left:8px;font-size:10px;font-weight:700;'
                    f'color:var(--jag-navy);opacity:0.45;">#{esc(an)}</span>') if an else ''
    return f"""<a href="/coach/participants/{p['id']}" class="athlete-tile" data-id="{p['id']}" data-sport="{esc(p.get('sport') or '')}"
      style="position:relative;display:flex;flex-direction:column;align-items:center;gap:8px;
             padding:20px 12px 16px;background:var(--jag-card);border:2px solid var(--jag-border);
             border-radius:14px;text-decoration:none;color:inherit;cursor:pointer;
             transition:box-shadow 0.18s ease,border-color 0.18s ease,transform 0.18s ease;"
      onmouseover="this.style.boxShadow='0 6px 20px rgba(0,0,0,0.13)';this.style.borderColor='#F0A82E';this.style.transform='translateY(-2px)';"
      onmouseout="this.style.boxShadow='';this.style.borderColor='var(--jag-border)';this.style.transform='';">
      {number_badge}
      {drag}
      <div style="width:54px;height:54px;border-radius:50%;background:#2D323B;display:flex;align-items:center;
                  justify-content:center;font-weight:800;font-size:19px;color:#F0A82E;flex-shrink:0;
                  box-shadow:0 3px 12px rgba(45,50,59,0.35);">{inits}</div>
      <span style="font-weight:700;font-size:13px;text-align:center;line-height:1.3;word-break:break-word;">{esc(name)}</span>
      {sport_badge}
    </a>"""


def edit_group_page(user, group, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    try:
        icon_url = group["icon_url"] or ""
    except Exception:
        icon_url = ""
    icon_preview = (
        '<img src="' + esc(icon_url) + '" style="margin-top:8px;width:32px;height:32px;'
        'object-fit:contain;border-radius:4px;border:1px solid var(--jag-border);"'
        ' onerror="this.style.display=\'none\'">'
    ) if icon_url else ""
    lb_checked = "checked" if group.get("show_leaderboard") else ""
    body = f"""
    <div class="page-head">
      <h1>Edit Group</h1>
      <a class="btn btn-ghost" href="/coach">&larr; Back</a>
    </div>
    {error_html}
    <div class="card form-card" style="max-width:480px;">
      <form method="post" action="/coach/groups/{group['id']}/edit">
        <label for="group_name">Group name</label>
        <input type="text" id="group_name" name="group_name" required value="{esc(group['name'])}" />
        <label for="icon_url">Icon URL <span class="muted" style="font-weight:400;">(optional — paste a favicon or logo URL)</span></label>
        <input type="url" id="icon_url" name="icon_url" value="{esc(icon_url)}" placeholder="https://example.com/favicon.ico" />
        {icon_preview}
        <div style="margin-top:20px;padding:14px 16px;background:#F9FAFB;border-radius:8px;
                    border:1px solid var(--jag-border);">
          <label style="display:flex;align-items:flex-start;gap:12px;cursor:pointer;margin:0;">
            <input type="checkbox" name="show_leaderboard" value="1" {lb_checked}
                   style="width:18px;height:18px;margin-top:2px;accent-color:#2D323B;flex-shrink:0;" />
            <span>
              <strong style="font-size:14px;color:#2D323B;">Show group leaderboard to athletes</strong>
              <span style="display:block;font-size:12px;color:#6E737B;margin-top:2px;">
                When enabled, athletes in this group can view a ranked AXP leaderboard
                for their group. Leave off for programmes focused on individual progress.
              </span>
            </span>
          </label>
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:16px;">Save Changes</button>
      </form>
    </div>
    """
    return layout(f"Edit Group — {group['name']}", body, user=user, active_nav="dashboard")


def coach_dashboard_for(user, group_summaries, ungrouped_summaries, message=None, org_map=None, stats=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    is_admin = user.get("is_admin")
    org_map = org_map or {}

    # ---- helper: render one group section ----
    def _render_group(group, participants, indent=False):
        gkey = f"g{group['id']}"
        count = len(participants)
        tiles_html = "".join(_athlete_tile(p, is_admin=is_admin) for p in participants)
        empty_msg = '<p class="muted" style="font-size:13px;padding:8px 0;">No athletes in this group yet.</p>'
        tiles_wrap = (f'<div id="body-{gkey}" class="athlete-tiles-wrap" data-group-list-id="{group["id"]}"'
                      f' style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;padding:8px 0 4px;">'
                      f'{tiles_html or empty_msg}</div>')
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder groups" style="color:var(--jag-muted);cursor:grab;font-size:16px;">&#9776;</span>' if is_admin else ""
        summary_link = (f'<a href="/coach/groups/{group["id"]}/achievement-summary" class="btn btn-sm" style="font-size:12px;background:var(--jag-green);color:var(--jag-navy);font-weight:600;border:none;">&#128200; Group Stats</a>'
                        f'<a href="/coach/groups/{group["id"]}/scores" class="btn btn-sm btn-ghost" style="font-size:12px;">&#128203; Scores Table</a>')
        type_opts_rl = "".join(
            f'<option value="{s["key"]}">{esc(s["label"])}</option>'
            for s in SESSION_TYPES
        )
        relabel_form = f"""
        <div id="relabel-{gkey}" style="display:none;margin-top:10px;padding:12px 14px;
             background:#fffbe6;border:1px solid #F0A82E;border-radius:8px;font-size:13px;">
          <strong style="display:block;margin-bottom:8px;">Tag Existing Unlabelled Sessions</strong>
          <p style="margin:0 0 10px;color:#6E737B;font-size:12px;">
            Assigns a phase label to each athlete's most recent unlabelled session.
            Athletes who already have that label are skipped.
          </p>
          <form method="post" action="/coach/groups/{group['id']}/relabel-sessions"
                style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;margin-bottom:4px;">Phase</label>
              <select name="session_label" required style="font-size:13px;min-width:160px;">{type_opts_rl}</select>
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;margin-bottom:4px;">Month</label>
              {_month_select(name="session_month")}
            </div>
            <button type="submit" class="btn btn-primary" style="font-size:12px;"
                    onclick="return confirm('Tag all unlabelled sessions for this group?');">Apply</button>
          </form>
        </div>""" if is_admin else ""
        admin_btns = f"""<a href="/coach/groups/{group['id']}/edit" class="btn btn-ghost btn-sm" style="font-size:12px;">Edit</a>
            <button class="btn btn-ghost btn-sm" style="font-size:12px;"
                    onclick="var el=document.getElementById('relabel-{gkey}');el.style.display=el.style.display==='none'?'block':'none';">
              &#127991; Tag Sessions
            </button>
            <form method="post" action="/coach/groups/{group['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete group \\'{esc(group['name'])}\\'? Participants move to ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm" style="font-size:12px;">Delete</button>
            </form>""" if is_admin else ""
        left_pad = "margin-left:20px;" if indent else ""
        return f"""
        <div class="group-section" data-group-id="{group['id']}" data-group-key="{gkey}" style="margin-bottom:20px;{left_pad}">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
            {folder_handle}
            <div style="border-left:4px solid var(--jag-green);padding-left:12px;flex:1;min-width:0;cursor:pointer;"
                 onclick="toggleGroup('{gkey}')">
              <div style="display:flex;align-items:center;gap:8px;">
                <h3 style="margin:0;font-size:17px;font-weight:700;color:var(--jag-navy);line-height:1.2;">{esc(group['name'])}</h3>
                <span id="toggle-{gkey}" style="font-size:13px;color:var(--jag-muted);user-select:none;">&#9660;</span>
              </div>
              <span class="muted group-count" style="font-size:13px;">{count} athlete{"s" if count != 1 else ""}</span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
              {summary_link}
              {admin_btns}
            </div>
          </div>
          {relabel_form}
          {tiles_wrap}
        </div>"""

    # ---- bucket group_summaries by org_id ----
    # Using a list to preserve insertion/sort order
    org_order = []   # list of org_ids in order encountered
    org_buckets = {} # org_id (or None) → [(group, participants), ...]
    for group, participants in group_summaries:
        oid = group["organisation_id"] if "organisation_id" in group.keys() else None
        if oid not in org_buckets:
            org_order.append(oid)
            org_buckets[oid] = []
        org_buckets[oid].append((group, participants))

    # ---- build org-level sections ----
    all_sections = ""
    for oid in org_order:
        bucket = org_buckets[oid]
        group_html = "".join(_render_group(g, ps, indent=(oid is not None)) for g, ps in bucket)
        total_athletes = sum(len(ps) for _, ps in bucket)

        if oid and oid in org_map:
            org = org_map[oid]
            okey = f"org{oid}"
            _raw_logo = org["icon_url"] or ""
            _logo_src = _gdrive_thumbnail(_raw_logo) or _raw_logo or None
            logo_html = (
                f'<img src="{esc(_logo_src)}" alt="{esc(org["name"])} logo" '
                f'style="height:44px;width:auto;max-width:120px;object-fit:contain;border-radius:4px;flex-shrink:0;" '
                f'onerror="this.style.display=\'none\'" />'
            ) if _logo_src else ""
            type_badge = (f'<span style="font-size:11px;background:rgba(255,255,255,0.35);color:var(--jag-navy);'
                          f'border-radius:999px;padding:2px 10px;font-weight:600;">{esc(org["type"])}</span>') if org["type"] else ""
            group_count = len(bucket)
            all_sections += f"""
        <div class="org-section" style="margin-bottom:32px;" data-org-id="{oid}">
          <div style="background:linear-gradient(135deg,var(--jag-navy) 0%,#3d4451 100%);
                      border-radius:10px 10px 0 0;padding:14px 18px;
                      display:flex;align-items:center;gap:14px;cursor:pointer;flex-wrap:wrap;"
               onclick="toggleOrg('{okey}')">
            {logo_html}
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <span style="font-size:20px;font-weight:800;color:#fff;line-height:1.2;">{esc(org["name"])}</span>
                {type_badge}
                <span id="toggle-{okey}" style="font-size:13px;color:rgba(255,255,255,0.6);user-select:none;margin-left:4px;">&#9660;</span>
              </div>
              <span style="font-size:13px;color:rgba(255,255,255,0.65);">{group_count} group{"s" if group_count != 1 else ""} &middot; {total_athletes} athlete{"s" if total_athletes != 1 else ""}</span>
            </div>
          </div>
          <div id="body-{okey}" style="border:1px solid var(--jag-border);border-top:none;border-radius:0 0 10px 10px;padding:16px 12px 4px;">
            <div class="org-groups-container" data-org-id="{oid}">
              {group_html}
            </div>
          </div>
        </div>"""
        else:
            # Groups with no org — show under "Other Groups" label
            all_sections += f"""
        <div class="org-section" style="margin-bottom:32px;">
          <div style="border-left:4px solid var(--jag-border);padding-left:14px;margin-bottom:12px;">
            <h2 style="margin:0;font-size:18px;font-weight:700;color:var(--jag-muted);">Other Groups</h2>
            <span style="font-size:13px;color:var(--jag-muted);">{len(bucket)} group{"s" if len(bucket) != 1 else ""} not assigned to an organisation</span>
          </div>
          <div class="org-groups-container">
            {group_html}
          </div>
        </div>"""

    # ---- ungrouped athletes section ----
    ug_count = len(ungrouped_summaries)
    ug_tiles = "".join(_athlete_tile(p, is_admin=is_admin) for p in ungrouped_summaries)
    ug_empty = '<p class="muted" style="font-size:13px;padding:8px 0;">No ungrouped athletes.</p>'
    ug_wrap = (f'<div id="body-ungrouped" class="athlete-tiles-wrap" data-group-list-id="ungrouped"'
               f' style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;padding:8px 0 4px;">'
               f'{ug_tiles or ug_empty}</div>')
    ungrouped_section = f"""
    <div class="group-section" data-group-key="ungrouped" style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;cursor:pointer;"
           onclick="toggleGroup('ungrouped')">
        <div style="border-left:4px solid var(--jag-border);padding-left:12px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <h3 style="margin:0;font-size:17px;font-weight:700;color:var(--jag-muted);line-height:1.2;">Ungrouped</h3>
            <span id="toggle-ungrouped" style="font-size:13px;color:var(--jag-muted);user-select:none;">&#9660;</span>
          </div>
          <span class="muted group-count" style="font-size:13px;">{ug_count} athlete{"s" if ug_count != 1 else ""}</span>
        </div>
      </div>
      {ug_wrap}
    </div>""" if ungrouped_summaries else ""

    # ---- sport filter bar ----
    all_sports = sorted(set(
        p.get("sport") or ""
        for _, participants in list(group_summaries) + [("__ug__", ungrouped_summaries)]
        for p in (participants if isinstance(participants, list) else [])
        if p.get("sport")
    ))
    if all_sports:
        sport_btns = "".join(
            f'<button onclick="filterSport(this, \'{esc(s)}\')" '
            f'style="padding:5px 14px;border-radius:999px;border:1px solid var(--jag-border);'
            f'background:var(--jag-card);font-size:13px;cursor:pointer;transition:background 0.15s,color 0.15s;">'
            f'{esc(s)}</button>'
            for s in all_sports
        )
        filter_bar = f"""
        <div id="sport-filter" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:20px;">
          <span style="font-size:13px;color:var(--jag-muted);font-weight:600;">Filter by sport:</span>
          <button onclick="filterSport(this, '')" class="filter-active"
            style="padding:5px 14px;border-radius:999px;border:1px solid var(--jag-green);
                   background:var(--jag-green);color:var(--jag-navy);font-size:13px;cursor:pointer;font-weight:600;">All</button>
          {sport_btns}
        </div>"""
        filter_js = """
        <script>
        function filterSport(btn, sport) {
          document.querySelectorAll('#sport-filter button').forEach(function(b) {
            var isSel = (b === btn);
            b.style.background = isSel ? 'var(--jag-green)' : 'var(--jag-card)';
            b.style.color = isSel ? 'var(--jag-navy)' : 'inherit';
            b.style.borderColor = isSel ? 'var(--jag-green)' : 'var(--jag-border)';
            b.style.fontWeight = isSel ? '600' : '400';
          });
          document.querySelectorAll('.athlete-tile').forEach(function(tile) {
            var ts = tile.dataset.sport || '';
            tile.style.display = (!sport || ts === sport) ? 'flex' : 'none';
          });
          document.querySelectorAll('.group-section').forEach(function(sec) {
            var wrap = sec.querySelector('.athlete-tiles-wrap');
            if (!wrap) return;
            var visible = Array.from(wrap.querySelectorAll('.athlete-tile')).filter(function(t){ return t.style.display !== 'none'; }).length;
            var badge = sec.querySelector('.group-count');
            if (badge) badge.textContent = visible + (visible === 1 ? ' athlete' : ' athletes');
            sec.style.display = visible === 0 ? 'none' : 'block';
          });
        }
        </script>"""
    else:
        filter_bar = filter_js = ""

    if not group_summaries and not ungrouped_summaries:
        content = '<p class="muted">No participants yet. Add one to get started.</p>' if is_admin else '<p class="muted">You haven\'t been assigned to a group yet. Contact an admin.</p>'
    else:
        content = f'<div id="groups-container">{all_sections}</div>{ungrouped_section}'

    create_group_form = f"""
    <div id="create-group-panel" style="display:none; margin-top:10px; max-width:400px;">
      <form method="post" action="/coach/groups/new" style="display:flex;gap:8px;">
        <input type="text" name="group_name" placeholder="Group name…" required style="flex:1;" />
        <button type="submit" class="btn btn-primary btn-sm" style="white-space:nowrap;">Create</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="document.getElementById('create-group-panel').style.display='none';">Cancel</button>
      </form>
    </div>""" if is_admin else ""

    action_btns = f"""
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
      <a class="btn btn-primary" href="/coach/participants/new">+ Add Participant</a>
      <button type="button" class="btn btn-primary" onclick="var p=document.getElementById('create-group-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Create Group</button>
      <a class="btn btn-primary" href="/coach/session">Record Session</a>
      {'<a class="btn btn-ghost" href="/coach/participants/import" title="Bulk-import athletes from CSV">&#8679; Import Athletes</a><a class="btn btn-ghost" href="/coach/participants/export.csv" title="Export all athletes with new temp passwords">&#8681; Export Athletes</a><a class="btn btn-ghost" href="/coach/scores/import" title="Bulk-import test scores from CSV">&#8679; Import Scores</a><a class="btn btn-ghost" href="/coach/admin/game-thresholds" title="Set XP level thresholds and run retroactive AXP pass">&#9881; AXP Thresholds</a><a class="btn btn-ghost" href="/coach/admin/score-distribution" title="View score percentile distributions to inform threshold setting">&#128202; Score Distribution</a>' if is_admin else ''}
    </div>
    {create_group_form}""" if is_admin else ""

    sortable_js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.2/Sortable.min.js"></script>
    <script>
    function post(url, body) {
      fetch(url, { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: body });
    }
    // Make groups sortable within each org container
    document.querySelectorAll('.org-groups-container').forEach(function(gc) {
      Sortable.create(gc, {
        handle: '.folder-handle', animation: 150,
        onEnd: function() {
          var ids = Array.from(document.querySelectorAll('#groups-container .group-section[data-group-id]'))
                        .map(function(el){ return el.dataset.groupId; });
          post('/coach/groups/reorder', 'ids=' + ids.join(','));
        }
      });
    });
    document.querySelectorAll('.athlete-tiles-wrap').forEach(function(wrap) {
      Sortable.create(wrap, {
        group: { name:'participants', pull:true, put:true },
        handle: '.drag-handle:not(.folder-handle)',
        animation: 150,
        ghostClass: 'athlete-tile-ghost',
        onEnd: function(evt) {
          var fromWrap = evt.from, toWrap = evt.to, itemId = evt.item.dataset.id;
          if (fromWrap !== toWrap) {
            var newGroupId = toWrap.dataset.groupListId;
            post('/coach/participants/' + itemId + '/move-group',
                 'group_id=' + (newGroupId === 'ungrouped' ? '' : newGroupId));
            updateCount(fromWrap);
            updateCount(toWrap);
          }
        }
      });
    });
    function updateCount(wrap) {
      var section = wrap.closest('.group-section');
      if (!section) return;
      var badge = section.querySelector('.group-count');
      if (!badge) return;
      var n = wrap.querySelectorAll('.athlete-tile').length;
      badge.textContent = n + (n === 1 ? ' athlete' : ' athletes');
    }
    </script>""" if is_admin else ""

    if is_admin:
        subtitle = 'Viewing all participants &mdash; administrator access.'
    elif user.get("organisation"):
        org_name = esc(user["organisation"])
        subtitle = f'Showing all groups for <strong>{org_name}</strong>.'
    elif group_summaries:
        names = ", ".join(f'<strong>{esc(g["name"])}</strong>' for g, _ in group_summaries)
        subtitle = f'Your assigned group{"s" if len(group_summaries) > 1 else ""}: {names}'
    else:
        subtitle = 'No group assigned yet &mdash; contact an admin.'

    collapse_js = """
    <script>
    function toggleGroup(key) {
      var wrap = document.getElementById('body-' + key);
      var toggle = document.getElementById('toggle-' + key);
      if (!wrap) return;
      var isCollapsed = wrap.style.display === 'none';
      wrap.style.display = isCollapsed ? 'grid' : 'none';
      if (toggle) toggle.innerHTML = isCollapsed ? '&#9660;' : '&#9654;';
      try { localStorage.setItem('jag-grp-' + key, isCollapsed ? '0' : '1'); } catch(e) {}
    }
    function toggleOrg(key) {
      var wrap = document.getElementById('body-' + key);
      var toggle = document.getElementById('toggle-' + key);
      if (!wrap) return;
      var isCollapsed = wrap.style.display === 'none';
      wrap.style.display = isCollapsed ? 'block' : 'none';
      if (toggle) toggle.innerHTML = isCollapsed ? '&#9660;' : '&#9654;';
      try { localStorage.setItem('jag-org-' + key, isCollapsed ? '0' : '1'); } catch(e) {}
    }
    // Restore collapsed state on load
    document.querySelectorAll('[data-group-key]').forEach(function(sec) {
      var key = sec.dataset.groupKey;
      var collapsed;
      try { collapsed = localStorage.getItem('jag-grp-' + key) === '1'; } catch(e) { collapsed = false; }
      if (collapsed) {
        var wrap = document.getElementById('body-' + key);
        if (wrap) wrap.style.display = 'none';
        var toggle = document.getElementById('toggle-' + key);
        if (toggle) toggle.innerHTML = '&#9654;';
      }
    });
    document.querySelectorAll('.org-section[data-org-id]').forEach(function(sec) {
      var oid = sec.dataset.orgId;
      var key = 'org' + oid;
      var collapsed;
      try { collapsed = localStorage.getItem('jag-org-' + key) === '1'; } catch(e) { collapsed = false; }
      if (collapsed) {
        var wrap = document.getElementById('body-' + key);
        if (wrap) wrap.style.display = 'none';
        var toggle = document.getElementById('toggle-' + key);
        if (toggle) toggle.innerHTML = '&#9654;';
      }
    });
    </script>"""

    # ---- stat cards ----
    if stats:
        latest_phase = stats.get("latest_phase") or "None yet"
        # Split label from month onto two lines
        phase_parts = latest_phase.split("\n") if "\n" in latest_phase else [latest_phase, ""]
        phase_line1 = esc(phase_parts[0])
        phase_line2 = esc(phase_parts[1]) if len(phase_parts) > 1 else ""
        phase_html = f'<div style="font-size:15px;font-weight:800;color:var(--jag-navy);line-height:1.2;">{phase_line1}</div>'
        if phase_line2:
            phase_html += f'<div style="font-size:12px;color:var(--jag-muted);margin-top:2px;">{phase_line2}</div>'
        untested = stats.get("untested", 0)
        untested_color = "color:#9b1c1c;" if untested > 0 else "color:var(--jag-navy);"

        # Avg sprint time
        avg_sprint = stats.get("avg_sprint")
        avg_sprint_str = f"{avg_sprint:.2f}s" if avg_sprint is not None else "—"

        # Avg balance catch
        avg_balance = stats.get("avg_balance")
        avg_balance_str = f"{avg_balance:.1f}" if avg_balance is not None else "—"

        # Phase completion mini bar
        comp_n = stats.get("phase_completion_n", 0)
        comp_total = stats.get("phase_completion_total", 0)
        if comp_total > 0:
            comp_pct = int(round(100 * comp_n / comp_total))
            comp_bar_fill = f'<div style="height:6px;background:var(--jag-gold);border-radius:3px;width:{comp_pct}%;transition:width 0.4s;"></div>'
            comp_bar = f'<div style="background:#e5e7eb;border-radius:3px;height:6px;margin-top:6px;">{comp_bar_fill}</div>'
            comp_label_str = f"{comp_n}/{comp_total}"
            comp_pct_str = f"{comp_pct}%"
        else:
            comp_label_str = "—"
            comp_pct_str = ""
            comp_bar = ""

        comp_html = (
            f'<div style="font-size:22px;font-weight:800;color:var(--jag-navy);line-height:1;">{comp_pct_str}</div>'
            f'<div style="font-size:11px;color:var(--jag-muted);margin-top:2px;">{comp_label_str} athletes</div>'
            f'{comp_bar}'
        )

        stat_cards_html = f"""
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:24px;">
          <div class="card stat-card">
            <div class="stat-number">{stats['total_athletes']}</div>
            <div class="stat-label">Total Athletes</div>
          </div>
          <div class="card stat-card">
            {phase_html}
            <div class="stat-label" style="margin-top:6px;">Latest Phase</div>
          </div>
          <div class="card stat-card">
            {comp_html}
            <div class="stat-label" style="margin-top:6px;">Phase Completion</div>
          </div>
          <div class="card stat-card">
            <div class="stat-number">{avg_sprint_str}</div>
            <div class="stat-label">Avg Sprint Time</div>
          </div>
          <div class="card stat-card">
            <div class="stat-number">{avg_balance_str}</div>
            <div class="stat-label">Avg Balance Catch</div>
          </div>
          <div class="card stat-card">
            <div class="stat-number" style="{untested_color}">{untested}</div>
            <div class="stat-label">Not Yet Tested</div>
          </div>
        </div>"""
    else:
        stat_cards_html = ""

    body = f"""
    <style>.athlete-tile {{transition:box-shadow 0.18s ease,border-color 0.18s ease,transform 0.18s ease;}}</style>
    <div style="max-width:1320px;">
    <div class="page-head">
      <div>
        <h1>Practitioner Dashboard</h1>
        <p class="muted">{subtitle}</p>
      </div>
    </div>
    {stat_cards_html}
    {action_btns}
    {message_html}
    <div style="margin-top:28px;">
      {filter_bar}
      {content}
    </div>
    </div>
    {sortable_js}
    {filter_js}
    {collapse_js}
    """
    return layout("Practitioner Dashboard", body, user=user, active_nav="dashboard")


def new_participant_form(user, error=None, groups=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    sport_options = "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in
                             ["Cricket", "Football", "Hockey", "Touch", "Volleyball", "Multi-sport"])
    groups = groups or []
    group_opts = '<option value="">— No group —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )
    body = f"""
    <div class="page-head"><h1>Add Participant</h1></div>
    {error_html}
    <div class="card form-card">
      <form method="post" action="/coach/participants/new">
        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required />
        <label for="gender">Gender</label>
        <select id="gender" name="gender">
          <option value="">— Not specified —</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="Non-binary">Non-binary</option>
          <option value="Prefer not to say">Prefer not to say</option>
        </select>
        <label for="sport">Sport</label>
        <select id="sport" name="sport">{sport_options}</select>
        <label for="programme">Programme / notes</label>
        <input type="text" id="programme" name="programme" placeholder="e.g. Athlete Adaptability Programme - Masterton 2026" />
        <label for="group_id">Group (optional)</label>
        <select id="group_id" name="group_id">{group_opts}</select>

        <div style="margin:20px 0 10px; padding-top:16px; border-top:1px solid var(--jag-border);">
          <label style="display:flex; align-items:center; gap:10px; cursor:pointer; font-weight:600;">
            <input type="checkbox" id="setup-login" name="setup_login" value="1"
                   style="width:auto; margin:0;"
                   onchange="document.getElementById('login-fields').style.display=this.checked?'block':'none';" />
            Set up login account
          </label>
          <p class="muted" style="margin:4px 0 0; font-size:13px;">Check this to give the athlete access to their own dashboard.</p>
        </div>

        <div id="login-fields" style="display:none;">
          <label for="email">Email (used to log in)</label>
          <input type="email" id="email" name="email" />
          <label for="password">Temporary password</label>
          <input type="text" id="password" name="password" value="Athlete123!" />
        </div>

        <button type="submit" class="btn btn-primary" style="margin-top:16px;">Add Participant</button>
      </form>
    </div>
    """
    return layout("Add Participant", body, user=user, active_nav="new_participant")


def coach_participant_detail(coach, participant, measurement_sessions, groups=None, message=None,
                             xp_data=None, levels=None, attendance_count=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    groups = groups or []
    current_group_id = participant.get("group_id")
    group_opts = '<option value="">— No group —</option>' + "".join(
        f'<option value="{g["id"]}" {"selected" if current_group_id == g["id"] else ""}>{esc(g["name"])}</option>'
        for g in groups
    )
    current_group_name = next((g["name"] for g in groups if g["id"] == current_group_id), None)

    is_admin = coach.get("is_admin")
    group_form = f"""
    <div class="card form-card" style="max-width:360px; margin-bottom:20px;">
      <h3 style="margin-top:0; font-size:14px; color:var(--jag-muted); text-transform:uppercase; letter-spacing:.04em;">Assign Group</h3>
      <form method="post" action="/coach/participants/{participant['id']}/assign-group" style="display:flex; gap:8px;">
        <select name="group_id" style="flex:1;">{group_opts}</select>
        <button type="submit" class="btn btn-primary btn-sm">Save</button>
      </form>
    </div>
    """ if (is_admin and groups) else ""

    reset_btn = f"""<form method="post" action="/coach/participants/{participant['id']}/reset-password"
          onsubmit="return confirm('Reset {esc(participant['name'])}&#39;s password? They will need the new one to log in again.');">
      <button type="submit" class="btn btn-ghost btn-sm">Reset Password</button>
    </form>""" if is_admin else ""

    # Build large avatar for the profile header
    name = participant['name']
    parts = name.strip().split()
    inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
    avatar = (f'<div style="width:64px;height:64px;border-radius:50%;background:#2D323B;'
              f'display:flex;align-items:center;justify-content:center;font-weight:800;font-size:22px;'
              f'color:#F0A82E;flex-shrink:0;box-shadow:0 4px 14px rgba(45,50,59,0.35);">{inits}</div>')

    sport_pill = (f'<span style="font-size:12px;font-weight:600;background:rgba(240,168,46,0.15);color:#CF8F1F;'
                  f'border-radius:999px;padding:2px 10px;">{esc(participant["sport"] or "")}</span>'
                  ) if participant.get("sport") else ""
    group_pill = (f'<span style="font-size:12px;font-weight:600;background:var(--jag-green);color:var(--jag-navy);'
                  f'border-radius:999px;padding:2px 10px;">{esc(current_group_name)}</span>'
                  ) if current_group_name else ""
    an = participant.get("athlete_number") or ""
    number_pill = (f'<span style="font-size:12px;font-weight:700;background:var(--jag-navy);color:var(--jag-gold);'
                   f'border-radius:999px;padding:2px 10px;letter-spacing:.04em;">#{esc(an)}</span>'
                   ) if an else ""
    gender_val = participant.get("gender") or ""
    gender_pill = (f'<span style="font-size:12px;font-weight:600;background:var(--jag-bg);color:var(--jag-muted);'
                   f'border-radius:999px;padding:2px 10px;border:1px solid var(--jag-border);">{esc(gender_val)}</span>'
                   ) if gender_val else ""
    org_val = participant.get("organisation") or ""
    org_text = (f'<p style="margin:0;font-size:13px;color:var(--jag-muted);">{esc(org_val)}</p>') if org_val else ""
    session_count = len(measurement_sessions)
    att_count = attendance_count or 0

    # ── XP summary card ───────────────────────────────────────────────────────
    from constants import CORE_AAP_GAMES
    xp_data = xp_data or {}
    levels = levels or {}
    total_xp = xp_data.get("total", 0)
    tier = xp_data.get("tier") or {"label": "Starter", "colour": "#6E737B"}
    tier_colour = tier["colour"]
    tier_label = esc(tier["label"])
    games_with_level = sum(1 for g in CORE_AAP_GAMES if levels.get(g, 0) >= 1)
    LEVEL_COLOURS = {
        0: ("#E5E7EB", "#6E737B"),
        1: ("#1EBE8B", "#fff"),
        2: ("#F0A82E", "#2D323B"),
        3: ("#2D323B", "#fff"),
        4: ("#F97316", "#fff"),
        5: ("#8B5CF6", "#fff"),
    }
    level_badges = ""
    from constants import find_measurement_game
    for gk in CORE_AAP_GAMES:
        gdef = find_measurement_game(gk)
        gname = esc(gdef["name"][:22] + ("…" if len(gdef["name"]) > 22 else "")) if gdef else esc(gk)
        lvl = levels.get(gk, 0)
        bg, fg = LEVEL_COLOURS.get(lvl, ("#E5E7EB", "#6E737B"))
        label = f"L{lvl}" if lvl > 0 else "—"
        level_badges += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:5px 10px;background:#F3F4F5;border-radius:6px;">'
            f'<span style="font-size:12px;color:#2D323B;">{gname}</span>'
            f'<span style="font-size:11px;font-weight:700;background:{bg};color:{fg};'
            f'border-radius:999px;padding:1px 8px;">{label}</span></div>'
        )
    xp_card = f"""
    <div style="background:#2D323B;border-radius:14px;padding:18px 20px;margin-bottom:20px;
                display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;">
      <div style="flex:0 0 auto;text-align:center;padding-right:20px;
                  border-right:1px solid rgba(255,255,255,0.1);">
        <div style="font-size:28px;font-weight:800;color:#F0A82E;line-height:1;">{total_xp:,}</div>
        <div style="font-size:10px;color:#9CA3AF;letter-spacing:0.06em;margin-bottom:8px;">TOTAL AXP</div>
        <span style="font-size:11px;font-weight:700;background:{tier_colour};color:#fff;
                     border-radius:999px;padding:2px 10px;">{tier_label}</span>
        <div style="font-size:11px;color:#9CA3AF;margin-top:8px;">{att_count} sessions attended</div>
      </div>
      <div style="flex:1;min-width:240px;">
        <div style="font-size:10px;font-weight:700;color:#9CA3AF;letter-spacing:0.06em;
                    margin-bottom:8px;text-transform:uppercase;">
          Game Levels &nbsp;
          <span style="background:rgba(255,255,255,0.1);color:#fff;border-radius:999px;
                       padding:1px 7px;">{games_with_level}/8</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
          {level_badges}
        </div>
      </div>
      <div style="flex:0 0 auto;align-self:flex-end;">
        <a href="/coach/participants/{participant['id']}/xp"
           style="font-size:12px;color:#F0A82E;text-decoration:none;font-weight:600;">
          Full AXP history →
        </a>
      </div>
    </div>"""

    # Build group transfer history notice
    group_lookup = {g["id"]: g["name"] for g in groups} if groups else {}
    prior_group_ids = {
        s["group_id"] for s in measurement_sessions
        if s.get("group_id") and s["group_id"] != current_group_id
    }
    transfer_notice = ""
    if prior_group_ids:
        prior_names = ", ".join(
            esc(group_lookup.get(gid, f"Group #{gid}")) for gid in sorted(prior_group_ids)
        )
        transfer_notice = f"""
        <div style="background:rgba(240,168,46,0.1);border:1px solid rgba(240,168,46,0.35);border-radius:8px;
                    padding:10px 14px;margin-bottom:16px;font-size:13px;color:#7A5800;display:flex;gap:8px;align-items:center;">
          <span style="font-size:16px;">&#128257;</span>
          <span>This athlete has measurement history from a previous group: <strong>{prior_names}</strong>.
          Their full session history is shown below; group stats pages only count sessions recorded while in each group.</span>
        </div>"""

    body = f"""
    <div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:20px;">
      {avatar}
      <div style="flex:1;min-width:0;">
        <h1 style="margin:0 0 4px;font-size:26px;">{esc(participant['name'])}</h1>
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px;">
          {number_pill}{sport_pill}{gender_pill}{group_pill}
          <span style="font-size:12px;color:var(--jag-muted);">{esc(participant['email'] or '')}</span>
        </div>
        {org_text}
        {f'<p style="margin:0;font-size:13px;color:var(--jag-muted);">{esc(participant["programme"])}</p>' if participant.get("programme") else ""}
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start;">
        {reset_btn}
        <a class="btn btn-primary" href="/coach/participants/{participant['id']}/progress">&#128200; Achievement Statistics</a>
        <a class="btn btn-ghost" href="/coach">&larr; Back</a>
      </div>
    </div>
    {message_html}
    {group_form}
    {transfer_notice}
    {xp_card}

    <section class="stat-row" style="margin-bottom:20px;">
      <div class="card stat-card">
        <div class="stat-number">{session_count}</div>
        <div class="stat-label">Test Sessions (all groups)</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{att_count}</div>
        <div class="stat-label">Sessions Attended</div>
      </div>
    </section>

    {measurement_games_form(participant['id'], athlete_levels=levels)}

    <h2 class="section-title">Measurement Games History</h2>
    {measurement_games_history(measurement_sessions, show_delete=True, participant_id=participant['id'])}
    """
    return layout(participant["name"], body, user=coach, active_nav="dashboard")


def participant_progress_page(coach, participant, measurement_sessions):
    """Progress page: first vs latest comparison + full trend across all sessions."""
    pid = participant["id"]
    n = len(measurement_sessions)

    if n == 0:
        body = f"""
        <div class="page-head">
          <div><h1>{esc(participant['name'])} &mdash; Achievement Statistics</h1></div>
          <a class="btn btn-ghost" href="/coach/participants/{pid}">&larr; Back</a>
        </div>
        <div class="card"><p class="muted">No test sessions recorded yet.</p></div>"""
        return layout(f"{participant['name']} Achievement Statistics", body, user=coach, active_nav="dashboard")

    # sessions are most-recent-first; oldest = last
    latest = measurement_sessions[0]
    first  = measurement_sessions[-1]

    def fmt(val, ftype):
        if val is None:
            return "—"
        if ftype == "time":
            return f"{val:.2f}s"
        return str(int(val)) if val == int(val) else str(val)

    def delta_html(first_val, latest_val, ftype):
        if first_val is None or latest_val is None:
            return '<span class="muted">—</span>'
        diff = latest_val - first_val
        if diff == 0:
            return '<span class="muted">no change</span>'
        # For time fields lower is better; for number/points higher is better
        improved = (diff < 0) if ftype == "time" else (diff > 0)
        colour = "#0f6e62" if improved else "#9b1c1c"
        sign = "+" if diff > 0 else ""
        suffix = "s" if ftype == "time" else ""
        arrow = "&#9650;" if diff > 0 else "&#9660;"
        raw = f"{sign}{diff:.2f}{suffix}"
        if first_val != 0:
            pct = abs(diff / first_val) * 100
            pct_sign = "+" if improved else "−"
            return (f'<span style="color:{colour}; font-weight:700;">{arrow} {pct_sign}{pct:.1f}%</span>'
                    f'<br><small style="color:{colour}; font-weight:400;">{raw}</small>')
        return f'<span style="color:{colour}; font-weight:700;">{arrow} {raw}</span>'

    # Build game sections
    sections_html = ""
    for section in active_measurement_games():
        game_cards = ""
        for game in section["games"]:
            all_fields = game["fields"] + game.get("computed", [])
            # Only include fields that have data in at least one session
            active_fields = [f for f in all_fields
                             if any(s["results"].get((game["key"], f["key"])) is not None
                                    for s in measurement_sessions)]
            if not active_fields:
                continue

            # Header row: First date + Latest date (or just date if only 1 session)
            if n == 1:
                date_headers = f'<th>{first["date"]}</th>'
            else:
                date_headers = f'<th>{first["date"]}<br><small class="muted">First</small></th>'
                if n > 2:
                    date_headers += f'<th class="muted" style="font-size:12px;">({n-2} more)</th>'
                date_headers += f'<th>{latest["date"]}<br><small class="muted">Latest</small></th>'
                date_headers += '<th>Change</th>'

            rows = ""
            for field in active_fields:
                fkey = field["key"]
                ftype = field["type"]
                flabel = field["label"]
                first_val  = first["results"].get((game["key"], fkey))
                latest_val = latest["results"].get((game["key"], fkey))

                if n == 1:
                    rows += f"""<tr>
                      <td>{esc(flabel)}</td>
                      <td>{fmt(first_val, ftype)}</td>
                    </tr>"""
                else:
                    mid_cell = f'<td class="muted" style="font-size:12px; text-align:center;">…</td>' if n > 2 else ""
                    rows += f"""<tr>
                      <td>{esc(flabel)}</td>
                      <td>{fmt(first_val, ftype)}</td>
                      {mid_cell}
                      <td>{fmt(latest_val, ftype)}</td>
                      <td>{delta_html(first_val, latest_val, ftype)}</td>
                    </tr>"""

            game_cards += f"""
            <div class="card" style="margin-bottom:16px;">
              <h3 style="margin:0 0 12px; font-size:15px;">{esc(game['name'])}</h3>
              <table class="table">
                <thead><tr><th>Measurement</th>{date_headers}</tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

        if game_cards:
            sections_html += f'<h2 class="section-title">{esc(section["section"])}</h2>{game_cards}'

    # Full trend table — shown when 2+ sessions
    trend_html = ""
    if n >= 2:
        trend_rows = ""
        for session in reversed(measurement_sessions):  # chronological order
            trend_rows += f'<tr><td colspan="99" style="background:var(--jag-bg); font-weight:700; font-size:12px; padding:6px 12px;">{session["date"]}</td></tr>'
            for game in all_active_measurement_games():
                all_fields = game["fields"] + game.get("computed", [])
                game_results = [(f, session["results"].get((game["key"], f["key"]))) for f in all_fields]
                game_results = [(f, v) for f, v in game_results if v is not None]
                if not game_results:
                    continue
                for field, val in game_results:
                    trend_rows += f"""<tr>
                      <td style="padding-left:20px; font-size:13px; color:var(--jag-muted);">{esc(game['name'])}</td>
                      <td style="font-size:13px;">{esc(field['label'])}</td>
                      <td style="font-size:13px; font-weight:600;">{fmt(val, field['type'])}</td>
                    </tr>"""

        trend_html = f"""
        <h2 class="section-title">All Sessions (chronological)</h2>
        <div class="card">
          <table class="table">
            <thead><tr><th>Game</th><th>Measurement</th><th>Value</th></tr></thead>
            <tbody>{trend_rows}</tbody>
          </table>
        </div>"""

    if not sections_html:
        sections_html = '<div class="card"><p class="muted">No measurements recorded yet.</p></div>'

    # Build a "Best Improvements" highlight card (shown when 2+ sessions)
    highlights_html = ""
    if n >= 2:
        improvements = []
        for section in active_measurement_games():
            for game in section["games"]:
                for field in game["fields"] + game.get("computed", []):
                    fv = first["results"].get((game["key"], field["key"]))
                    lv = latest["results"].get((game["key"], field["key"]))
                    if fv is None or lv is None:
                        continue
                    diff = lv - fv
                    improved = (diff < 0) if field["type"] == "time" else (diff > 0)
                    if not improved:
                        continue
                    if field["type"] == "time":
                        pct_imp = abs(diff / fv) * 100 if fv else 0
                        disp = f"−{abs(diff):.2f}s ({pct_imp:.1f}% faster)"
                    else:
                        pct_imp = abs(diff / fv) * 100 if fv else 0
                        disp = f"+{abs(diff):.0f} ({pct_imp:.1f}% better)"
                    improvements.append((pct_imp, game["name"], field["label"], disp))
        improvements.sort(reverse=True)
        top = improvements[:4]
        if top:
            cards = "".join(
                f'<div style="background:#fffbeb;border:2px solid #f59e0b;border-radius:10px;padding:12px 16px;min-width:160px;flex:1;">'
                f'<div style="font-size:11px;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;">{esc(gn)} &middot; {esc(fl)}</div>'
                f'<div style="font-size:18px;font-weight:800;color:#92400e;">{esc(disp)}</div>'
                f'</div>'
                for _, gn, fl, disp in top
            )
            highlights_html = f"""
            <div style="margin-bottom:24px;">
              <h2 style="font-size:16px;font-weight:700;color:var(--jag-navy);margin:0 0 10px;">&#127942; Top Improvements</h2>
              <div style="display:flex;flex-wrap:wrap;gap:10px;">{cards}</div>
            </div>"""

    body = f"""
    <div class="page-head">
      <div>
        <h1>{esc(participant['name'])} &mdash; Achievement Statistics</h1>
        <p class="muted">{esc(participant.get('sport') or '')} &middot; {n} test session{"s" if n != 1 else ""}</p>
      </div>
      <a class="btn btn-ghost" href="/coach/participants/{pid}">&larr; Back</a>
    </div>
    {highlights_html}
    {sections_html}
    {trend_html}
    """
    return layout(f"{participant['name']} Achievement Statistics", body, user=coach, active_nav="dashboard")


def _progress_for_participant(p_name, p_id, sessions):
    """Return dict: {(game_key, field_key): {first, latest, ftype, flabel, game_name}}"""
    if not sessions:
        return {}
    first  = sessions[-1]   # oldest
    latest = sessions[0]    # most recent
    out = {}
    for game in all_active_measurement_games():
        all_fields = game["fields"] + game.get("computed", [])
        for field in all_fields:
            key = (game["key"], field["key"])
            fv = first["results"].get(key)
            lv = latest["results"].get(key)
            if fv is not None or lv is not None:
                out[key] = {
                    "first": fv, "latest": lv,
                    "ftype": field["type"],
                    "flabel": field["label"],
                    "game_name": game["name"],
                    "game_key": game["key"],
                    "n": len(sessions),
                }
    return out


def _level_filter_bar(max_level, base_url, extra_params=""):
    """Render a level-filter pill bar for report pages.

    max_level: int or None (None = All Levels)
    base_url:  URL without query params, e.g. '/coach/groups/5/progress'
    extra_params: any other query params to preserve, e.g. '&sport=Cricket'
    """
    top = max_game_level()
    sep = "?" if "?" not in base_url else "&"

    def pill(label, level_val, active):
        href = base_url + (f"{sep}level={level_val}" if level_val is not None else "") + extra_params
        if active:
            style = ("display:inline-block;padding:4px 14px;border-radius:999px;font-size:13px;"
                     "font-weight:700;background:#2D323B;color:#fff;text-decoration:none;")
        else:
            style = ("display:inline-block;padding:4px 14px;border-radius:999px;font-size:13px;"
                     "font-weight:600;background:#fff;color:#2D323B;border:1px solid #DDE0E3;"
                     "text-decoration:none;")
        return f'<a href="{href}" style="{style}">{label}</a>'

    pills = pill("All Levels", None, max_level is None)
    for lvl in range(1, top + 1):
        label = f"Level {lvl}" + (" only" if top > 1 else "")
        pills += " " + pill(label, lvl, max_level == lvl)

    return (
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;'
        f'margin-bottom:20px;padding:10px 14px;background:#F3F4F5;'
        f'border-radius:8px;border:1px solid #DDE0E3;">'
        f'<span style="font-size:12px;font-weight:600;color:#6E737B;'
        f'text-transform:uppercase;letter-spacing:.05em;margin-right:4px;">View:</span>'
        f'{pills}'
        f'</div>'
    )


def _fmt_val(val, ftype):
    if val is None:
        return "—"
    if ftype == "time":
        return f"{val:.2f}s"
    return str(int(val)) if val == int(val) else str(val)


def _delta_cell(first_val, latest_val, ftype):
    if first_val is None or latest_val is None:
        return '<td class="muted">—</td>'
    diff = latest_val - first_val
    if diff == 0:
        return '<td class="muted">±0</td>'
    improved = (diff < 0) if ftype == "time" else (diff > 0)
    colour = "#0f6e62" if improved else "#9b1c1c"
    sign = "+" if diff > 0 else ""
    suffix = "s" if ftype == "time" else ""
    arrow = "&#9650;" if diff > 0 else "&#9660;"
    raw = f"{sign}{diff:.2f}{suffix}"
    if first_val != 0:
        pct = abs(diff / first_val) * 100
        pct_sign = "+" if improved else "−"
        return (f'<td style="color:{colour}; font-weight:700; white-space:nowrap;">'
                f'{arrow} {pct_sign}{pct:.1f}%<br>'
                f'<small style="font-weight:400;">{raw}</small></td>')
    return f'<td style="color:{colour}; font-weight:700;">{arrow}{raw}</td>'


def group_progress_page(coach, group, participants_sessions, max_level=None):
    """Progress summary for a group: each measurement, each participant, first→latest.
    participants_sessions: list of (participant_dict, sessions_list)
    max_level: int or None — filters games to those up to this level (None = all)
    """
    active = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Ungrouped"
    group_id = group["id"] if group else None
    base_url = f'/coach/groups/{group_id}/progress' if group_id else '/coach'

    if not active:
        body = f"""
        <div class="page-head"><div><h1>{gname} &mdash; Group Achievement Statistics</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Back</a></div>
        <div class="card"><p class="muted">No test sessions recorded for this group yet.</p></div>"""
        return layout(f"{group['name']} Progress", body, user=coach, active_nav="progress")

    level_bar = _level_filter_bar(max_level, base_url)
    game_sections = games_for_max_level(max_level)

    # Build one table per game
    sections_html = ""
    for section in game_sections:
        game_cards = ""
        for game in section["games"]:
            all_fields = game["fields"] + game.get("computed", [])
            # Only fields with any data in this group
            active_fields = [
                f for f in all_fields
                if any(
                    s["results"].get((game["key"], f["key"])) is not None
                    for _, sessions in active for s in sessions
                )
            ]
            if not active_fields:
                continue

            header_names = "".join(f'<th colspan="3" style="text-align:center; border-left:2px solid var(--jag-border);">{esc(p["name"])}<br><small class="muted">{n} session{"s" if n!=1 else ""}</small></th>'
                                   for p, sessions in active
                                   for n in [len(sessions)])
            sub_headers = "".join('<th style="border-left:2px solid var(--jag-border);">First</th><th>Latest</th><th>Change</th>'
                                  for _ in active)

            rows = ""
            for field in active_fields:
                fkey = field["key"]
                ftype = field["type"]
                cells = ""
                for p, sessions in active:
                    first_s  = sessions[-1] if sessions else None
                    latest_s = sessions[0]  if sessions else None
                    fv = first_s["results"].get((game["key"], fkey)) if first_s else None
                    lv = latest_s["results"].get((game["key"], fkey)) if latest_s else None
                    cells += f'<td style="border-left:2px solid var(--jag-border);">{_fmt_val(fv, ftype)}</td>'
                    cells += f'<td>{_fmt_val(lv, ftype)}</td>'
                    cells += _delta_cell(fv, lv, ftype)
                rows += f'<tr><td style="font-size:13px;">{esc(field["label"])}</td>{cells}</tr>'

            game_cards += f"""
            <div class="card" style="margin-bottom:16px; overflow-x:auto;">
              <h3 style="margin:0 0 12px; font-size:15px;">{esc(game['name'])}</h3>
              <table class="table" style="min-width:400px;">
                <thead>
                  <tr><th></th>{header_names}</tr>
                  <tr><th>Measurement</th>{sub_headers}</tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

        if game_cards:
            sections_html += f'<h2 class="section-title">{esc(section["section"])}</h2>{game_cards}'

    if not sections_html:
        sections_html = '<div class="card"><p class="muted">No measurements recorded yet.</p></div>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>{gname} &mdash; Group Achievement Statistics</h1>
        <p class="muted">{len(active)} athlete{"s" if len(active)!=1 else ""} with test data</p>
      </div>
      <a class="btn btn-ghost" href="/coach">&larr; Back</a>
    </div>
    {level_bar}
    {sections_html}"""
    return layout(f"{group['name'] if group else 'Group'} Progress", body, user=coach, active_nav="progress")


def group_achievement_summary_page(coach, group, participants_sessions, max_level=None):
    """One-page collective summary: average % improvement per field across all group members.
    max_level: int or None — filters game breakdown to those up to this level (None = all)
    """
    # Only athletes with at least 2 sessions contribute to the averages
    active = [(p, s) for p, s in participants_sessions if len(s) >= 2]
    all_with_sessions = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Group"
    group_id = group["id"] if group else None
    base_url = f'/coach/groups/{group_id}/achievement-summary' if group_id else '/coach'

    if not active:
        # Show waiting state but still list athletes with single sessions
        any_html = ""
        if all_with_sessions:
            any_html = '<p class="muted" style="margin-top:16px;">Athletes with 1 session (need one more to unlock improvements):</p><ul style="margin:6px 0 0;padding-left:20px;">'
            for p, _ in all_with_sessions:
                any_html += f'<li><a href="/coach/participants/{p["id"]}">{esc(p["name"])}</a></li>'
            any_html += '</ul>'
        body = f"""
        <div class="page-head">
          <div><h1>{gname} &mdash; Achievement Summary</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
        </div>
        <div class="card">
          <p class="muted">No athletes in this group have two or more test sessions yet — come back after the second round of measurements.</p>
          {any_html}
        </div>"""
        return layout(f"{group['name']} Achievement Summary", body, user=coach, active_nav="progress")

    athlete_count = len(active)

    # ---- Overall group improvement (direction-corrected avg per athlete, then averaged) ----
    athlete_imps = []
    for _p, sessions in active:
        imp = _calc_improvement_pct(sessions)
        if imp is not None:
            athlete_imps.append(imp)
    overall_avg = sum(athlete_imps) / len(athlete_imps) if athlete_imps else None

    # ---- Hero summary card ----
    if overall_avg is not None:
        oa_sign = "+" if overall_avg >= 0 else ""
        oa_colour = "#0f6e62" if overall_avg >= 0 else "#9b1c1c"
        hero_stat = f'<div style="font-size:48px;font-weight:900;color:{oa_colour};line-height:1;">{oa_sign}{overall_avg:.1f}%</div>'
        hero_sub = '<div style="font-size:13px;opacity:0.65;margin-top:6px;">across all measurement fields</div>'
    else:
        hero_stat = '<div style="font-size:48px;font-weight:900;color:rgba(255,255,255,0.4);line-height:1;">—</div>'
        hero_sub = '<div style="font-size:13px;opacity:0.55;margin-top:6px;">not enough data yet</div>'

    best_athlete = max(active, key=lambda x: (_calc_improvement_pct(x[1]) or -999), default=None)
    best_stat = ""
    if best_athlete:
        bp, _ = best_athlete
        bimp = _calc_improvement_pct(best_athlete[1])
        if bimp is not None:
            bsign = "+" if bimp >= 0 else ""
            binits = "".join(w[0].upper() for w in bp['name'].split()[:2])
            best_stat = f"""
            <div style="text-align:center;padding:0 20px;border-left:1px solid rgba(255,255,255,0.15);">
              <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.65;margin-bottom:8px;">Top Performer</div>
              <div style="width:40px;height:40px;border-radius:50%;background:#F0A82E;display:flex;align-items:center;
                          justify-content:center;font-weight:800;font-size:15px;color:#2D323B;margin:0 auto 6px;">{binits}</div>
              <div style="font-size:13px;font-weight:700;">{esc(bp['name'])}</div>
              <div style="font-size:18px;font-weight:800;color:#F0A82E;">{bsign}{bimp:.1f}%</div>
            </div>"""

    hero_card = f"""
    <div class="card" style="background:var(--jag-navy);color:#fff;border-color:var(--jag-navy);margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
        <div style="flex:1;min-width:180px;">
          <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.65;margin-bottom:6px;">Average Group Improvement</div>
          {hero_stat}
          {hero_sub}
        </div>
        <div style="display:flex;gap:0;align-items:center;flex-wrap:wrap;">
          <div style="text-align:center;padding:0 20px;border-left:1px solid rgba(255,255,255,0.15);">
            <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.65;margin-bottom:6px;">Athletes</div>
            <div style="font-size:36px;font-weight:900;color:#F0A82E;line-height:1;">{athlete_count}</div>
            <div style="font-size:12px;opacity:0.55;margin-top:4px;">with 2+ sessions</div>
          </div>
          {best_stat}
        </div>
      </div>
    </div>"""

    # ---- Athlete improvement grid (sorted best → worst) ----
    def _athlete_imp_card(p, sessions):
        imp = _calc_improvement_pct(sessions)
        lvl = get_improvement_level(imp)
        initials = "".join(w[0].upper() for w in p['name'].split()[:2])
        if imp is not None:
            isign = "+" if imp >= 0 else ""
            ic = "#0f6e62" if imp >= 0 else "#9b1c1c"
            imp_str = f'<span style="font-size:17px;font-weight:800;color:{ic};">{isign}{imp:.1f}%</span>'
        else:
            imp_str = '<span style="font-size:14px;color:var(--jag-muted);">Baseline</span>'
        bar_w = int((lvl['progress'] or 0) * 100)
        return f"""
        <a href="/coach/participants/{p['id']}" style="display:flex;align-items:center;gap:12px;
           padding:12px 14px;background:var(--jag-card);border:1px solid var(--jag-border);
           border-radius:10px;text-decoration:none;color:inherit;
           transition:box-shadow 0.15s ease,border-color 0.15s ease,transform 0.15s ease;"
           onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.1)';this.style.borderColor='#F0A82E';this.style.transform='translateY(-1px)';"
           onmouseout="this.style.boxShadow='';this.style.borderColor='var(--jag-border)';this.style.transform='';">
          <div style="width:40px;height:40px;border-radius:50%;background:#2D323B;flex-shrink:0;
               display:flex;align-items:center;justify-content:center;
               font-weight:800;font-size:14px;color:#F0A82E;">{initials}</div>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{esc(p['name'])}</div>
            <div style="font-size:11px;color:var(--jag-muted);margin-bottom:4px;">{esc(lvl['name'])}</div>
            <div style="background:var(--jag-border);border-radius:999px;height:4px;overflow:hidden;">
              <div style="width:{bar_w}%;height:100%;border-radius:999px;background:var(--jag-green);"></div>
            </div>
          </div>
          <div style="flex-shrink:0;text-align:right;">{imp_str}</div>
        </a>"""

    sorted_active = sorted(active, key=lambda x: (_calc_improvement_pct(x[1]) or -999), reverse=True)
    athlete_cards_html = "".join(_athlete_imp_card(p, s) for p, s in sorted_active)
    athlete_grid = f"""
    <div style="margin-bottom:36px;">
      <div style="border-left:4px solid var(--jag-green);padding-left:12px;margin-bottom:16px;">
        <h2 style="margin:0 0 2px;font-size:17px;font-weight:700;">Athletes</h2>
        <p class="muted" style="margin:0;">Sorted by highest improvement &mdash; click to view full profile</p>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;">
        {athlete_cards_html}
      </div>
    </div>"""

    # ---- Per-game measurement breakdown ----
    level_bar = _level_filter_bar(max_level, base_url)
    sections_html = ""
    for section in games_for_max_level(max_level):
        game_cards = ""
        for game in section["games"]:
            all_fields = game["fields"] + game.get("computed", [])
            rows = ""
            for field in all_fields:
                fkey  = field["key"]
                ftype = field["type"]
                # Direction-corrected improvement % per athlete for this field
                athlete_field_pcts = []  # list of (direction_corrected_pct, participant)
                for p, sessions in active:
                    first_s  = sessions[-1]
                    latest_s = sessions[0]
                    fv = first_s["results"].get((game["key"], fkey))
                    lv = latest_s["results"].get((game["key"], fkey))
                    if fv is not None and lv is not None and fv != 0:
                        raw = (lv - fv) / fv * 100
                        # direction-correct: for time, lower=better so negate
                        corrected = -raw if ftype == "time" else raw
                        athlete_field_pcts.append((corrected, p))

                if not athlete_field_pcts:
                    continue

                vals = [v for v, _ in athlete_field_pcts]
                avg = sum(vals) / len(vals)
                n = len(vals)
                improved = avg >= 0
                colour = "#0f6e62" if improved else "#9b1c1c"
                sign = "+" if avg >= 0 else ""
                bar_pct = min(100, abs(avg) / 40 * 100)

                # Individual athlete chips
                chips = ""
                for pct_val, p in sorted(athlete_field_pcts, key=lambda x: x[0], reverse=True):
                    ac = "#0f6e62" if pct_val > 0 else ("#9b1c1c" if pct_val < 0 else "#6E737B")
                    asign = "+" if pct_val > 0 else ""
                    initials = "".join(w[0].upper() for w in p['name'].split()[:2])
                    chips += (
                        f'<a href="/coach/participants/{p["id"]}" title="{esc(p["name"])}: {asign}{pct_val:.1f}%"'
                        f' style="display:inline-flex;align-items:center;gap:4px;padding:3px 8px;'
                        f'background:var(--jag-bg);border-radius:999px;font-size:11px;'
                        f'white-space:nowrap;color:{ac};font-weight:600;text-decoration:none;'
                        f'border:1px solid var(--jag-border);">'
                        f'<span style="width:18px;height:18px;border-radius:50%;background:#2D323B;'
                        f'display:inline-flex;align-items:center;justify-content:center;'
                        f'font-size:9px;font-weight:700;color:#F0A82E;flex-shrink:0;">{initials}</span>'
                        f'{asign}{pct_val:.1f}%</a>'
                    )

                rows += f"""<tr>
                  <td style="font-size:13px;font-weight:600;vertical-align:middle;">{esc(field['label'])}</td>
                  <td style="vertical-align:middle;white-space:nowrap;width:140px;">
                    <div style="font-size:18px;font-weight:800;color:{colour};">{sign}{avg:.1f}%</div>
                    <div style="background:var(--jag-border);border-radius:999px;height:5px;margin-top:4px;overflow:hidden;width:100px;">
                      <div style="width:{bar_pct:.0f}%;height:100%;border-radius:999px;background:{'#0f6e62' if improved else '#9b1c1c'};"></div>
                    </div>
                    <div style="font-size:11px;color:var(--jag-muted);margin-top:3px;">{n} of {athlete_count}</div>
                  </td>
                  <td><div style="display:flex;flex-wrap:wrap;gap:4px;">{chips}</div></td>
                </tr>"""

            if rows:
                game_cards += f"""
                <div class="card" style="margin-bottom:16px;overflow-x:auto;">
                  <h3 style="margin:0 0 14px;font-size:15px;">{esc(game['name'])}</h3>
                  <table class="table" style="width:100%;">
                    <thead><tr>
                      <th>Measurement</th>
                      <th>Group avg</th>
                      <th>By athlete &mdash; click to view profile</th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                  </table>
                </div>"""

        if game_cards:
            sections_html += f'<h2 class="section-title">{esc(section["section"])}</h2>{game_cards}'

    if not sections_html:
        sections_html = '<div class="card"><p class="muted">No measurements recorded yet.</p></div>'

    prog_link = f'/coach/groups/{group_id}/progress' if group_id else '/coach'
    body = f"""
    <div class="page-head">
      <div>
        <h1>{gname} &mdash; Achievement Summary</h1>
        <p class="muted">First session to most recent &mdash; {athlete_count} athlete{"s" if athlete_count != 1 else ""} with 2+ sessions</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <a class="btn btn-ghost" href="{prog_link}">Individual stats &rarr;</a>
        <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
      </div>
    </div>
    {level_bar}
    {hero_card}
    {athlete_grid}
    <div style="border-left:4px solid var(--jag-green);padding-left:12px;margin-bottom:20px;">
      <h2 style="margin:0 0 2px;font-size:17px;font-weight:700;">Measurement Breakdown</h2>
      <p class="muted" style="margin:0;">Group average per field with individual athlete results</p>
    </div>
    {sections_html}"""
    return layout(f"{group['name']} Achievement Summary", body, user=coach, active_nav="progress")


def group_scores_table_page(coach, group, participants_sessions, max_level=None):
    """Flat table: rows = athletes, columns = every measurement field (latest session values).
    max_level: int or None — filters columns to games up to this level (None = all)
    """
    active = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Group"
    group_id = group["id"] if group else None
    summary_url = f'/coach/groups/{group_id}/achievement-summary' if group_id else '/coach'
    base_url = f'/coach/groups/{group_id}/scores' if group_id else '/coach'

    if not active:
        body = f"""
        <div class="page-head">
          <div><h1>{gname} &mdash; Scores Table</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
        </div>
        <div class="card"><p class="muted">No test sessions recorded for this group yet.</p></div>"""
        return layout(f"{group['name']} Scores Table", body, user=coach, active_nav="progress")

    # Build the full column list from games at the selected level
    # Use base MEASUREMENT_GAMES only (sport-specific vary per athlete — keep it simple)
    # Column spec: list of (section_name, game_name, game_key, field_label, field_key, field_type)
    level_bar = _level_filter_bar(max_level, base_url)
    cols = []
    for section in games_for_max_level(max_level):
        for game in section["games"]:
            for field in game["fields"] + game.get("computed", []):
                cols.append({
                    "section": section["section"],
                    "game": game["name"],
                    "game_key": game["key"],
                    "label": field["label"],
                    "key": field["key"],
                    "type": field["type"],
                })

    # Only keep columns that have at least one value in this group
    def has_data(col):
        return any(
            s["results"].get((col["game_key"], col["key"])) is not None
            for _, sessions in active
            for s in sessions[:1]  # latest only
        )
    cols = [c for c in cols if has_data(c)]

    if not cols:
        body = f"""
        <div class="page-head">
          <div><h1>{gname} &mdash; Scores Table</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
        </div>
        <div class="card"><p class="muted">No measurement data recorded yet.</p></div>"""
        return layout(f"{group['name']} Scores Table", body, user=coach, active_nav="progress")

    # Build grouped header rows (game name spanning its fields)
    # Group cols by game_key preserving order
    from itertools import groupby as _groupby
    game_spans = []
    for game_key, grp in _groupby(cols, key=lambda c: c["game_key"]):
        grp = list(grp)
        game_spans.append((grp[0]["game"], len(grp)))

    header_row1 = '<th style="min-width:140px;">Athlete</th>'
    for game_name, span in game_spans:
        header_row1 += (f'<th colspan="{span}" style="text-align:center;border-left:2px solid var(--jag-border);'
                        f'font-size:12px;padding:8px 10px;color:var(--jag-navy);font-weight:700;">'
                        f'{esc(game_name)}</th>')

    header_row2 = '<th></th>'
    for i, col in enumerate(cols):
        bl = 'border-left:2px solid var(--jag-border);' if i == 0 or col["game_key"] != cols[i-1]["game_key"] else ''
        header_row2 += f'<th style="{bl}font-size:11px;padding:6px 10px;white-space:nowrap;">{esc(col["label"])}</th>'

    # Build rows
    data_rows = ""
    for p, sessions in sorted(active, key=lambda x: x[0]["name"]):
        latest = sessions[0] if sessions else None
        first = sessions[-1] if sessions else None
        inits = "".join(w[0].upper() for w in p["name"].split()[:2])
        athlete_cell = (
            f'<td style="white-space:nowrap;padding:10px 12px;">'
            f'<a href="/coach/participants/{p["id"]}" style="display:flex;align-items:center;gap:8px;text-decoration:none;color:inherit;">'
            f'<div style="width:30px;height:30px;border-radius:50%;background:#2D323B;display:flex;align-items:center;'
            f'justify-content:center;font-weight:800;font-size:11px;color:#F0A82E;flex-shrink:0;">{inits}</div>'
            f'<span style="font-weight:600;font-size:13px;">{esc(p["name"])}</span>'
            f'</a></td>'
        )
        cells = ""
        for i, col in enumerate(cols):
            bl = 'border-left:2px solid var(--jag-border);' if i == 0 or col["game_key"] != cols[i-1]["game_key"] else ''
            lv = latest["results"].get((col["game_key"], col["key"])) if latest else None
            fv = first["results"].get((col["game_key"], col["key"])) if first and first != latest else None
            if lv is None:
                cells += f'<td style="{bl}color:var(--jag-muted);text-align:center;">—</td>'
            else:
                val_str = f"{lv:.2f}s" if col["type"] == "time" else (str(int(lv)) if lv == int(lv) else str(lv))
                # improvement indicator (only if 2+ sessions and not same session)
                change_html = ""
                if fv is not None and fv != 0 and first != latest:
                    raw = (lv - fv) / fv * 100
                    corrected = -raw if col["type"] == "time" else raw
                    imp = corrected > 0
                    c = "#0f6e62" if imp else "#9b1c1c"
                    sign = "+" if corrected >= 0 else ""
                    change_html = (f'<div style="font-size:10px;color:{c};font-weight:700;line-height:1;">'
                                   f'{sign}{corrected:.0f}%</div>')
                cells += (f'<td style="{bl}text-align:center;padding:8px 10px;">'
                          f'<div style="font-weight:700;font-size:13px;">{val_str}</div>'
                          f'{change_html}</td>')
        data_rows += f"<tr>{athlete_cell}{cells}</tr>"

    session_note = f'{len(active)} athlete{"s" if len(active)!=1 else ""} &mdash; showing latest session values'
    if any(len(s) >= 2 for _, s in active):
        session_note += ' &mdash; <span style="color:#0f6e62;font-weight:600;">green %</span> = improvement from first session'

    print_css = """
    <style>
    @media print {
      .topbar, .nav-link, .no-print { display: none !important; }
      body { background: #fff !important; }
      .container { max-width: 100% !important; padding: 0 !important; }
      .card { border: none !important; border-radius: 0 !important; overflow: visible !important; box-shadow: none !important; }
      table { font-size: 10px !important; }
      th, td { padding: 5px 7px !important; }
      .print-header { display: block !important; }
      a { color: inherit !important; text-decoration: none !important; }
    }
    .print-header { display: none; margin-bottom: 12px; }
    .print-header h2 { font-size: 16px; font-weight: 700; }
    .print-header p { font-size: 12px; color: #6E737B; margin-top: 2px; }
    </style>"""

    body = f"""
    {print_css}
    <div class="print-header">
      <h2>{gname} &mdash; Scores Table</h2>
      <p>{session_note}</p>
    </div>
    <div class="page-head no-print">
      <div>
        <h1>{gname} &mdash; Scores Table</h1>
        <p class="muted">{session_note}</p>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button onclick="window.print()" class="btn btn-ghost" style="display:flex;align-items:center;gap:6px;">
          &#128438; Print / Save PDF
        </button>
        <a class="btn btn-ghost" href="{summary_url}">&#128200; Group Stats</a>
        <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
      </div>
    </div>
    <div class="no-print">{level_bar}</div>
    <div class="card" style="overflow-x:auto;padding:0;">
      <table class="table" style="width:100%;min-width:600px;border-collapse:collapse;">
        <thead style="background:var(--jag-bg);">
          <tr style="border-bottom:1px solid var(--jag-border);">{header_row1}</tr>
          <tr style="border-bottom:2px solid var(--jag-border);">{header_row2}</tr>
        </thead>
        <tbody>{data_rows}</tbody>
      </table>
    </div>"""
    return layout(f"{group['name']} Scores Table", body, user=coach, active_nav="progress")


def _overall_achievement_html(groups_data):
    """Build the programme-wide aggregate improvement section for the admin page.
    Combines all participants across all groups; shows avg % improvement per field.
    Only counts athletes with 2+ sessions.
    """
    # Flatten all (participant, sessions) pairs
    all_ps = [(p, s) for _, ps in groups_data for p, s in ps if len(s) >= 2]
    if not all_ps:
        return ""

    athlete_count = len(all_ps)
    sections_html = ""

    for section in active_measurement_games():
        game_cards = ""
        for game in section["games"]:
            all_fields = game["fields"] + game.get("computed", [])
            rows = ""
            for field in all_fields:
                fkey  = field["key"]
                ftype = field["type"]
                pcts  = []
                for _p, sessions in all_ps:
                    first_s  = sessions[-1]
                    latest_s = sessions[0]
                    fv = first_s["results"].get((game["key"], fkey))
                    lv = latest_s["results"].get((game["key"], fkey))
                    if fv is not None and lv is not None and fv != 0:
                        pcts.append((lv - fv) / fv * 100)

                if not pcts:
                    continue

                n        = len(pcts)
                avg      = sum(pcts) / n
                improved = (avg < 0) if ftype == "time" else (avg > 0)
                colour   = "#0f6e62" if improved else "#9b1c1c"
                arrow    = "&#9650;" if avg > 0 else "&#9660;"
                sign     = "+" if avg > 0 else ""
                coverage = f'{n} of {athlete_count} athlete{"s" if athlete_count != 1 else ""}'

                rows += f"""<tr>
                  <td style="font-size:13px;">{esc(field['label'])}</td>
                  <td style="color:{colour}; font-weight:700; white-space:nowrap; font-size:16px;">
                    {arrow} {sign}{avg:.1f}%
                  </td>
                  <td class="muted" style="font-size:12px;">{coverage}</td>
                </tr>"""

            if rows:
                game_cards += f"""
                <div class="card" style="margin-bottom:16px;">
                  <h3 style="margin:0 0 12px; font-size:15px;">{esc(game['name'])}</h3>
                  <table class="table" style="width:100%;">
                    <thead><tr>
                      <th>Measurement</th>
                      <th>Avg improvement</th>
                      <th>Athletes</th>
                    </tr></thead>
                    <tbody>{rows}</tbody>
                  </table>
                </div>"""

        if game_cards:
            sections_html += f'<h2 class="section-title">{esc(section["section"])}</h2>{game_cards}'

    if not sections_html:
        return ""

    return f"""
    <h2 class="section-title" style="margin-top:40px; padding-top:24px; border-top:2px solid var(--jag-border);">
      Programme-Wide Achievement Report
    </h2>
    <div class="card" style="margin-bottom:12px; background:var(--jag-bg); border:1px solid var(--jag-border);">
      <p class="muted" style="margin:0; font-size:13px;">
        Combined average improvement across all {athlete_count} athlete{"s" if athlete_count != 1 else ""} with 2+ sessions, regardless of group.
      </p>
    </div>
    {sections_html}"""


def _round_table(athletes_sessions, game):
    """Build a session-round comparison table for a single game.

    Columns  = measurement rounds (oldest = Round 1 / Baseline, newest = Round N).
    Rows     = one per field, showing group-average value for that round.
    Last row = average % change from Round 1 to each subsequent round.

    athletes_sessions: list of (participant_dict, sessions_list)  — already sport-filtered.
    Returns HTML string or "" if no data.
    """
    if not athletes_sessions:
        return ""

    all_fields = game["fields"] + game.get("computed", [])
    max_rounds = max((len(s) for _, s in athletes_sessions), default=0)
    if max_rounds == 0:
        return ""

    # For round index r (0 = oldest = baseline), sessions are newest-first so oldest = sessions[-(r+1)]
    rounds = []
    for r in range(max_rounds):
        dates = []
        field_vals = {f["key"]: [] for f in all_fields}
        n_athletes = 0
        for _p, sessions in athletes_sessions:
            if len(sessions) <= r:
                continue
            session = sessions[-(r + 1)]   # oldest first
            dates.append(session["date"])
            n_athletes += 1
            for field in all_fields:
                val = session["results"].get((game["key"], field["key"]))
                if val is not None:
                    field_vals[field["key"]].append(val)
        if not dates:
            break
        date_label = min(dates) if min(dates) == max(dates) else f"{min(dates)[:7]}…"
        avgs = {k: (sum(v) / len(v) if v else None) for k, v in field_vals.items()}
        rounds.append({"date": date_label, "avgs": avgs, "n": n_athletes})

    if not rounds:
        return ""

    active_fields = [f for f in all_fields if any(rd["avgs"].get(f["key"]) is not None for rd in rounds)]
    if not active_fields:
        return ""

    # Header
    header_cells = '<th style="min-width:150px;">Measurement</th>'
    for i, rd in enumerate(rounds):
        label = "Baseline" if i == 0 else f"Round {i + 1}"
        header_cells += (
            f'<th style="text-align:center;border-left:2px solid var(--jag-border);min-width:110px;">'
            f'{label}<br>'
            f'<small style="font-weight:400;color:var(--jag-muted);">{rd["date"]}</small><br>'
            f'<small style="font-weight:400;color:var(--jag-muted);">{rd["n"]} athlete{"s" if rd["n"]!=1 else ""}</small>'
            f'</th>'
        )

    # Field rows
    field_rows = ""
    for field in active_fields:
        cells = f'<td style="font-size:13px;font-weight:600;">{esc(field["label"])}</td>'
        for rd in rounds:
            avg = rd["avgs"].get(field["key"])
            bl = "border-left:2px solid var(--jag-border);"
            if avg is None:
                cells += f'<td style="{bl}text-align:center;color:var(--jag-muted);">—</td>'
            else:
                val_str = f"{avg:.2f}s" if field["type"] == "time" else f"{avg:.1f}"
                cells += f'<td style="{bl}text-align:center;font-weight:700;">{val_str}</td>'
        field_rows += f"<tr>{cells}</tr>"

    # % change row (only shown when 2+ rounds)
    pct_row = ""
    if len(rounds) >= 2:
        pct_cells = '<td style="font-size:12px;color:var(--jag-muted);font-weight:600;font-style:italic;">Avg % change vs baseline</td>'
        for i, rd in enumerate(rounds):
            bl = "border-left:2px solid var(--jag-border);"
            if i == 0:
                pct_cells += f'<td style="{bl}text-align:center;color:var(--jag-muted);font-size:12px;">—</td>'
                continue
            pcts = []
            for field in active_fields:
                fv = rounds[0]["avgs"].get(field["key"])
                lv = rd["avgs"].get(field["key"])
                if fv is not None and lv is not None and fv != 0:
                    raw = (lv - fv) / fv * 100
                    corrected = -raw if field["type"] == "time" else raw
                    pcts.append(corrected)
            if pcts:
                avg_pct = sum(pcts) / len(pcts)
                sign = "+" if avg_pct >= 0 else ""
                colour = "#0f6e62" if avg_pct >= 0 else "#9b1c1c"
                pct_cells += (f'<td style="{bl}text-align:center;font-weight:800;font-size:15px;color:{colour};">'
                              f'{sign}{avg_pct:.1f}%</td>')
            else:
                pct_cells += f'<td style="{bl}text-align:center;color:var(--jag-muted);">—</td>'
        pct_row = f'<tr style="border-top:2px solid var(--jag-border);background:var(--jag-bg);">{pct_cells}</tr>'

    return f"""
    <div class="card" style="margin-bottom:14px;overflow-x:auto;padding:0;">
      <div style="padding:12px 16px 10px;border-bottom:0.5px solid var(--jag-border);
                  background:var(--jag-bg);border-radius:var(--radius) var(--radius) 0 0;">
        <h3 style="margin:0;font-size:14px;font-weight:700;color:var(--jag-navy);">{esc(game["name"])}</h3>
      </div>
      <table class="table" style="width:100%;">
        <thead><tr style="background:var(--jag-bg);">{header_cells}</tr></thead>
        <tbody>{field_rows}{pct_row}</tbody>
      </table>
    </div>"""


def all_progress_page(coach, groups_data, sport_filter=None, max_level=None):
    """Overview page: programme stats, group cards, round-based measurement tables.
    Accessible to all coaches (admins see all groups; non-admins see their groups only).
    sport_filter: optional sport string to filter athlete averages.
    max_level: int or None — filters game tables to those up to this level (None = all)
    """
    is_admin = coach.get("is_admin")

    # Collect all sports
    all_sports = sorted(set(
        p.get("sport") or ""
        for _, ps in groups_data
        for p, _ in ps
        if p.get("sport")
    ))

    def _filter(ps):
        if not sport_filter:
            return ps
        return [(p, s) for p, s in ps if (p.get("sport") or "") == sport_filter]

    # Unfiltered totals for hero
    total_athletes = sum(len(ps) for _, ps in groups_data)
    total_sessions = sum(len(s) for _, ps in groups_data for _, s in ps)
    total_groups   = sum(1 for g, _ in groups_data if g)
    all_with_2     = [(p, s) for _, ps in groups_data for p, s in ps if len(s) >= 2]
    all_imps       = [i for i in (_calc_improvement_pct(s) for _, s in all_with_2) if i is not None]
    overall_imp    = sum(all_imps) / len(all_imps) if all_imps else None

    oi_str = f'{"+" if overall_imp >= 0 else ""}{overall_imp:.1f}%' if overall_imp is not None else "—"
    oi_col = "#0f6e62" if (overall_imp or 0) >= 0 else "#9b1c1c"

    hero_card = f"""
    <div class="card" style="background:var(--jag-navy);color:#fff;border-color:var(--jag-navy);margin-bottom:24px;">
      <div style="display:flex;gap:0;flex-wrap:wrap;align-items:center;">
        <div style="flex:1;min-width:160px;text-align:center;padding:0 24px;">
          <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.6;margin-bottom:4px;">Total Athletes</div>
          <div style="font-size:36px;font-weight:900;color:#F0A82E;">{total_athletes}</div>
        </div>
        <div style="flex:1;min-width:160px;text-align:center;padding:0 24px;border-left:0.5px solid rgba(255,255,255,0.15);">
          <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.6;margin-bottom:4px;">Groups</div>
          <div style="font-size:36px;font-weight:900;color:#F0A82E;">{total_groups}</div>
        </div>
        <div style="flex:1;min-width:160px;text-align:center;padding:0 24px;border-left:0.5px solid rgba(255,255,255,0.15);">
          <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.6;margin-bottom:4px;">Total Sessions</div>
          <div style="font-size:36px;font-weight:900;color:#F0A82E;">{total_sessions}</div>
        </div>
        <div style="flex:1;min-width:160px;text-align:center;padding:0 24px;border-left:0.5px solid rgba(255,255,255,0.15);">
          <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.06em;opacity:0.6;margin-bottom:4px;">Programme Avg Improvement</div>
          <div style="font-size:36px;font-weight:900;color:{oi_col};">{oi_str}</div>
        </div>
      </div>
    </div>"""

    # Group summary cards
    group_cards_html = ""
    for group, ps in groups_data:
        if not group:
            continue
        gname = esc(group["name"])
        gid   = group["id"]
        count = len(ps)
        with_sessions = len([p for p, s in ps if s])
        with_2 = [(p, s) for p, s in ps if len(s) >= 2]
        gimps = [i for i in (_calc_improvement_pct(s) for _, s in with_2) if i is not None]
        gavg  = sum(gimps) / len(gimps) if gimps else None
        gsign = "+" if (gavg or 0) >= 0 else ""
        gcol  = "#0f6e62" if (gavg or 0) >= 0 else "#9b1c1c"
        gavg_str = f'<span style="font-size:20px;font-weight:900;color:{gcol};">{gsign}{gavg:.1f}%</span>' if gavg is not None else '<span style="color:var(--jag-muted);font-size:14px;">No data yet</span>'
        group_cards_html += f"""
        <div style="background:var(--jag-card);border:0.5px solid var(--jag-border);border-radius:12px;padding:16px 18px;">
          <div style="border-left:3px solid var(--jag-green);padding-left:10px;margin-bottom:12px;">
            <div style="font-weight:700;font-size:15px;">{gname}</div>
            <div style="font-size:12px;color:var(--jag-muted);">{count} athlete{"s" if count!=1 else ""} &middot; {with_sessions} tested</div>
          </div>
          <div style="margin-bottom:12px;">{gavg_str}<div style="font-size:11px;color:var(--jag-muted);margin-top:2px;">avg improvement</div></div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <a href="/coach/groups/{gid}/achievement-summary" class="btn btn-sm" style="font-size:11px;background:var(--jag-green);color:var(--jag-navy);font-weight:700;border:none;">Group Stats</a>
            <a href="/coach/groups/{gid}/scores" class="btn btn-ghost btn-sm" style="font-size:11px;">Scores Table</a>
          </div>
        </div>"""

    group_cards = f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:32px;">{group_cards_html}</div>' if group_cards_html else ""

    # Sport filter bar
    current_sport_label = esc(sport_filter) if sport_filter else "All sports"
    sport_btns = f'<a href="/coach/progress" class="btn btn-sm{"" if sport_filter else " btn-primary"}" style="border-radius:999px;{"background:var(--jag-green);color:var(--jag-navy);font-weight:700;border:none;" if not sport_filter else ""}">All</a>'
    for s in all_sports:
        active_style = "background:var(--jag-green);color:var(--jag-navy);font-weight:700;border:none;" if sport_filter == s else ""
        sport_btns += f'<a href="/coach/progress?sport={esc(s)}" class="btn btn-sm btn-ghost" style="border-radius:999px;{active_style}">{esc(s)}</a>'

    filter_bar = ""
    if all_sports:
        filter_bar = f"""
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:24px;">
          <span style="font-size:13px;color:var(--jag-muted);font-weight:600;">Filter averages by sport:</span>
          {sport_btns}
        </div>"""

    # Per-group measurement tables
    group_sections_html = ""
    for group, ps in groups_data:
        gname = esc(group["name"]) if group else "Ungrouped"
        gid   = group["id"] if group else None
        filtered = _filter(ps)
        if not filtered:
            continue

        filter_note = f' &mdash; {esc(sport_filter)} athletes only' if sport_filter else ""
        tables_html = ""
        for section in games_for_max_level(max_level):
            sec_tables = "".join(_round_table(filtered, game) for game in section["games"])
            if sec_tables:
                tables_html += f'<h3 style="font-size:14px;color:var(--jag-muted);text-transform:uppercase;letter-spacing:0.05em;margin:20px 0 10px;">{esc(section["section"])}</h3>{sec_tables}'

        if not tables_html:
            tables_html = '<div class="card"><p class="muted">No measurement data yet.</p></div>'

        links = ""
        if gid:
            links = (f'<a href="/coach/groups/{gid}/achievement-summary" class="btn btn-sm" '
                     f'style="font-size:12px;background:var(--jag-green);color:var(--jag-navy);font-weight:700;border:none;">Group Stats</a>'
                     f'<a href="/coach/groups/{gid}/scores" class="btn btn-ghost btn-sm" style="font-size:12px;">Scores Table</a>'
                     f'<a href="/coach/progress/pdf?scope=group&group_id={gid}" class="btn btn-ghost btn-sm no-print" style="font-size:12px;">&#128196; PDF</a>')

        group_sections_html += f"""
        <div style="margin-bottom:44px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
            <div style="border-left:4px solid var(--jag-green);padding-left:12px;flex:1;">
              <h2 style="margin:0;font-size:19px;font-weight:700;color:var(--jag-navy);">{gname}</h2>
              <span style="font-size:13px;color:var(--jag-muted);">Group averages{filter_note}</span>
            </div>
            <div style="display:flex;gap:6px;">{links}</div>
          </div>
          {tables_html}
        </div>"""

    if not group_sections_html:
        group_sections_html = '<div class="card"><p class="muted">No test data recorded yet.</p></div>'

    # Admin-only overall programme table
    overall_html = ""
    if is_admin:
        all_filtered = _filter([(p, s) for _, ps in groups_data for p, s in ps])
        if all_filtered:
            filter_note = f' &mdash; {esc(sport_filter)} athletes only' if sport_filter else ""
            overall_tables = ""
            for section in games_for_max_level(max_level):
                sec_tables = "".join(_round_table(all_filtered, game) for game in section["games"])
                if sec_tables:
                    overall_tables += f'<h3 style="font-size:14px;color:var(--jag-muted);text-transform:uppercase;letter-spacing:0.05em;margin:20px 0 10px;">{esc(section["section"])}</h3>{sec_tables}'
            if overall_tables:
                overall_html = f"""
                <div style="margin-top:48px;padding-top:24px;border-top:2px solid var(--jag-border);">
                  <div style="border-left:4px solid var(--jag-navy);padding-left:12px;margin-bottom:20px;">
                    <h2 style="margin:0;font-size:19px;font-weight:700;color:var(--jag-navy);">Programme Overall</h2>
                    <span style="font-size:13px;color:var(--jag-muted);">All groups combined{filter_note} &mdash; admin view</span>
                  </div>
                  {overall_tables}
                </div>"""

    # PDF download buttons — shown based on role
    role = coach.get("role", "")
    btn_style = 'style="background:#F0A82E;color:#2D323B;font-weight:700;border:none;padding:8px 16px;border-radius:6px;font-size:13px;text-decoration:none;display:inline-block;"'
    pdf_btns = ""
    # Simple overall: all athletes pooled, no breakdown — available to all staff
    pdf_btns += f'<a href="/coach/progress/pdf?scope=programme" {btn_style}>&#128196; Overall Programme PDF</a>'
    # All groups broken out as separate sections
    pdf_btns += f'<a href="/coach/progress/pdf?scope=overall" {btn_style}>&#128196; All Groups PDF</a>'
    if role == "system_admin":
        pdf_btns += f'<a href="/coach/progress/pdf?scope=orgs" {btn_style}>&#128196; By Organisation PDF</a>'

    # Prominent download bar shown in the page body (not just the header)
    download_bar = f"""
    <div class="no-print" style="background:#2D323B;border-radius:10px;padding:14px 20px;
         margin-bottom:24px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <span style="color:#F0A82E;font-weight:700;font-size:13px;">&#128196; Download PDF Reports</span>
      <span style="flex:1;min-width:0;"></span>
      {pdf_btns}
    </div>""" if pdf_btns else ""

    body = f"""
    <div class="page-head">
      <div>
        <h1>Achievement Statistics Overview</h1>
        <p class="muted">Group averages across all measurement rounds{(" &mdash; " + esc(sport_filter) + " athletes") if sport_filter else ""}</p>
      </div>
    </div>
    {download_bar}
    {hero_card}
    {group_cards}
    {filter_bar}
    {group_sections_html}
    {overall_html}"""
    return layout("Achievement Statistics", body, user=coach, active_nav="progress")


def achievement_stats_pdf(title, subtitle, groups_sections, max_level=None):
    """Generate a landscape A4 PDF of Achievement Statistics round tables.

    groups_sections: list of (group_name_str, athletes_sessions_list) tuples.
    Returns bytes.
    """
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from constants import games_for_max_level

    JAG_NAVY  = colors.HexColor("#2D323B")
    JAG_GOLD  = colors.HexColor("#F0A82E")
    JAG_LIGHT = colors.HexColor("#F3F4F5")
    JAG_GREEN = colors.HexColor("#2E7D32")
    JAG_RED   = colors.HexColor("#9b1c1c")
    JAG_GREY  = colors.HexColor("#6E737B")

    buf = io.BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buf, pagesize=page_size,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )

    # Styles
    t_style  = ParagraphStyle("t",  fontName="Helvetica-Bold", fontSize=16, textColor=JAG_NAVY)
    s_style  = ParagraphStyle("s",  fontName="Helvetica",      fontSize=9,  textColor=JAG_GREY)
    g_style  = ParagraphStyle("g",  fontName="Helvetica-Bold", fontSize=11, textColor=colors.white)
    gm_style = ParagraphStyle("gm", fontName="Helvetica-Bold", fontSize=9,  textColor=JAG_NAVY)
    hdr_s    = ParagraphStyle("hd", fontName="Helvetica-Bold", fontSize=7,  textColor=colors.white,
                               alignment=TA_CENTER, leading=9)
    fld_s    = ParagraphStyle("fl", fontName="Helvetica-Bold", fontSize=7,  textColor=JAG_NAVY,
                               alignment=TA_LEFT, leading=9)
    val_s    = ParagraphStyle("vl", fontName="Helvetica",      fontSize=8,  alignment=TA_CENTER)
    pct_s    = ParagraphStyle("pc", fontName="Helvetica-Bold", fontSize=8,  alignment=TA_CENTER)
    pct_g    = ParagraphStyle("pg", fontName="Helvetica-Bold", fontSize=8,  textColor=JAG_GREEN, alignment=TA_CENTER)
    pct_r    = ParagraphStyle("pr", fontName="Helvetica-Bold", fontSize=8,  textColor=JAG_RED,   alignment=TA_CENTER)
    sec_s    = ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=7,  textColor=JAG_GREY,
                               alignment=TA_LEFT, leading=9)

    today = _dt.date.today().strftime("%d %B %Y")
    story = []

    # Page title block
    story.append(Paragraph(title, t_style))
    story.append(Spacer(1, 1*mm))
    story.append(Paragraph(f"{subtitle} &nbsp;&middot;&nbsp; Generated {today} &nbsp;&middot;&nbsp; Just A Game", s_style))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=JAG_GOLD))
    story.append(Spacer(1, 6*mm))

    page_w = page_size[0] - 24*mm   # usable width after margins
    field_col_w = 44*mm

    def _pdf_round_data(athletes_sessions, game):
        """Return (rounds_meta, active_fields, rows_data) for one game, or None if no data."""
        all_fields = game["fields"] + game.get("computed", [])
        max_rounds = max((len(s) for _, s in athletes_sessions), default=0)
        if max_rounds == 0:
            return None
        rounds = []
        for r in range(max_rounds):
            dates, n_athletes = [], 0
            field_vals = {f["key"]: [] for f in all_fields}
            for _p, sessions in athletes_sessions:
                if len(sessions) <= r:
                    continue
                sess = sessions[-(r + 1)]
                dates.append(sess["date"])
                n_athletes += 1
                for field in all_fields:
                    v = sess["results"].get((game["key"], field["key"]))
                    if v is not None:
                        field_vals[field["key"]].append(v)
            if not dates:
                break
            d_label = min(dates) if min(dates) == max(dates) else f"{min(dates)[:7]}…"
            avgs = {k: (sum(v)/len(v) if v else None) for k, v in field_vals.items()}
            rounds.append({"date": d_label, "avgs": avgs, "n": n_athletes})
        if not rounds:
            return None
        active = [f for f in all_fields if any(rd["avgs"].get(f["key"]) is not None for rd in rounds)]
        if not active:
            return None
        return rounds, active

    for group_name, athletes_sessions in groups_sections:
        if not athletes_sessions:
            continue

        # Group header band
        g_hdr_data = [[Paragraph(group_name or "Ungrouped", g_style)]]
        n_a  = len(athletes_sessions)
        n_s  = len([p for p, s in athletes_sessions if s])
        with_2 = [(p, s) for p, s in athletes_sessions if len(s) >= 2]
        gimps = []
        for _, sessions in with_2:
            pct = _calc_improvement_pct(sessions)
            if pct is not None:
                gimps.append(pct)
        gavg_str = f"Avg improvement: {'+' if (sum(gimps)/len(gimps))>=0 else ''}{sum(gimps)/len(gimps):.1f}%" if gimps else "No comparison data yet"

        g_hdr_tbl = Table(g_hdr_data, colWidths=[page_w])
        g_hdr_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,-1), JAG_NAVY),
            ("TOPPADDING",  (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(g_hdr_tbl)
        story.append(Paragraph(
            f"{n_a} athlete{'s' if n_a!=1 else ''} &nbsp;&middot;&nbsp; {n_s} tested &nbsp;&middot;&nbsp; {gavg_str}",
            s_style
        ))
        story.append(Spacer(1, 3*mm))

        has_any_data = False
        for section in games_for_max_level(max_level):
            section_header_added = False
            for game in section["games"]:
                result = _pdf_round_data(athletes_sessions, game)
                if result is None:
                    continue
                rounds, active_fields = result
                has_any_data = True

                if not section_header_added:
                    story.append(Paragraph(section["section"].upper(), sec_s))
                    story.append(Spacer(1, 1*mm))
                    section_header_added = True

                # Game name row
                story.append(Paragraph(game["name"], gm_style))
                story.append(Spacer(1, 1*mm))

                # Build table: rows = fields, cols = rounds
                n_rounds = len(rounds)
                round_col_w = max(18*mm, (page_w - field_col_w) / n_rounds)
                col_widths = [field_col_w] + [round_col_w] * n_rounds

                # Header row
                hdr_row = [Paragraph("Measurement", hdr_s)]
                for i, rd in enumerate(rounds):
                    label = "Baseline" if i == 0 else f"Round {i+1}"
                    hdr_row.append(Paragraph(
                        f"{label}<br/><font size='6'>{rd['date']}<br/>{rd['n']} athlete{'s' if rd['n']!=1 else ''}</font>",
                        hdr_s
                    ))

                tbl_data = [hdr_row]

                # Field rows
                for field in active_fields:
                    row = [Paragraph(field["label"], fld_s)]
                    for rd in rounds:
                        avg = rd["avgs"].get(field["key"])
                        if avg is None:
                            row.append(Paragraph("—", val_s))
                        else:
                            val_str = f"{avg:.2f}s" if field["type"] == "time" else f"{avg:.1f}"
                            row.append(Paragraph(val_str, val_s))
                    tbl_data.append(row)

                # % change row (if 2+ rounds)
                if n_rounds >= 2:
                    pct_row = [Paragraph("Avg % change vs baseline", fld_s)]
                    for i, rd in enumerate(rounds):
                        if i == 0:
                            pct_row.append(Paragraph("—", val_s))
                            continue
                        pcts = []
                        for field in active_fields:
                            fv = rounds[0]["avgs"].get(field["key"])
                            lv = rd["avgs"].get(field["key"])
                            if fv is not None and lv is not None and fv != 0:
                                raw = (lv - fv) / fv * 100
                                corrected = -raw if field["type"] == "time" else raw
                                pcts.append(corrected)
                        if pcts:
                            ap = sum(pcts) / len(pcts)
                            sign = "+" if ap >= 0 else ""
                            style = pct_g if ap >= 0 else pct_r
                            pct_row.append(Paragraph(f"{sign}{ap:.1f}%", style))
                        else:
                            pct_row.append(Paragraph("—", val_s))
                    tbl_data.append(pct_row)

                tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
                style_cmds = [
                    ("BACKGROUND",     (0,0), (-1,0),  JAG_NAVY),
                    ("TEXTCOLOR",      (0,0), (-1,0),  colors.white),
                    ("FONTNAME",       (0,0), (-1,0),  "Helvetica-Bold"),
                    ("ALIGN",          (0,0), (-1,-1), "CENTER"),
                    ("ALIGN",          (0,0), (0,-1),  "LEFT"),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, JAG_LIGHT]),
                    ("GRID",           (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
                    ("TOPPADDING",     (0,0), (-1,-1), 3),
                    ("BOTTOMPADDING",  (0,0), (-1,-1), 3),
                    ("LEFTPADDING",    (0,0), (-1,-1), 4),
                    ("RIGHTPADDING",   (0,0), (-1,-1), 4),
                ]
                if n_rounds >= 2:
                    # Highlight % change row
                    last = len(tbl_data) - 1
                    style_cmds.append(("BACKGROUND", (0, last), (-1, last), JAG_LIGHT))
                    style_cmds.append(("LINEABOVE",  (0, last), (-1, last), 1.0, JAG_GOLD))
                tbl.setStyle(TableStyle(style_cmds))
                story.append(tbl)
                story.append(Spacer(1, 3*mm))

        if not has_any_data:
            story.append(Paragraph("No measurement data recorded yet for this group.", s_style))
            story.append(Spacer(1, 3*mm))

        story.append(Spacer(1, 4*mm))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Completion Tracker
# ---------------------------------------------------------------------------

def completion_tracker_page(coach, groups, selected_group_id=None, selected_label=None,
                             selected_month=None, selected_game_keys=None,
                             athletes=None, completion=None):
    """Matrix: athletes × selected games — green tick if complete, link to entry if not."""
    athletes        = athletes or []
    completion      = completion or {}   # {athlete_id: set of game_keys with data}
    selected_game_keys = selected_game_keys or []
    all_games       = all_measurement_games()

    group_opts = '<option value="">— Select group —</option>' + "".join(
        f'<option value="{g["id"]}" {"selected" if g["id"] == selected_group_id else ""}>{esc(g["name"])}</option>'
        for g in groups
    )
    type_opts = '<option value="">— Select phase —</option>' + "".join(
        f'<option value="{s["key"]}" {"selected" if s["key"] == selected_label else ""}>{esc(s["label"])}</option>'
        for s in SESSION_TYPES
    )

    # Game checkboxes
    game_checkboxes = ""
    for game in all_games:
        checked = "checked" if game["key"] in selected_game_keys else ""
        game_checkboxes += f"""
        <label style="display:flex;align-items:center;gap:7px;font-size:13px;cursor:pointer;
                      padding:5px 10px;border:1px solid #DDE0E3;border-radius:6px;
                      background:{'#2D323B' if checked else '#fff'};
                      color:{'#F0A82E' if checked else '#2D323B'};">
          <input type="checkbox" name="games" value="{esc(game['key'])}" {checked}
                 style="width:auto;margin:0;" />
          {esc(game['name'])}
        </label>"""

    selector_form = f"""
    <form method="get" action="/coach/completion-tracker">
      <div style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;margin-bottom:16px;">
        <div>
          <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Group</label>
          <select name="group_id" required style="min-width:180px;">{group_opts}</select>
        </div>
        <div>
          <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Test Phase</label>
          <select name="session_label" required style="min-width:180px;">{type_opts}</select>
        </div>
        <div>
          <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Month</label>
          {_month_select(name="session_month", selected=selected_month)}
        </div>
        <button type="submit" class="btn btn-primary" style="white-space:nowrap;">View Tracker</button>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:8px;">
          Games to track <span style="font-weight:400;color:#6E737B;">(select all that apply)</span>
        </label>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">{game_checkboxes}</div>
      </div>
    </form>"""

    matrix_html = ""
    if athletes and selected_game_keys:
        games_to_show = [g for g in all_games if g["key"] in selected_game_keys]

        # Column headers — abbreviated for space
        col_headers = "".join(
            f'<th title="{esc(g["name"])}" style="padding:8px 6px;font-size:11px;font-weight:700;'
            f'text-align:center;min-width:70px;max-width:90px;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis;">{esc(g["name"])}</th>'
            for g in games_to_show
        )

        # Summary counts per game
        total = len(athletes)
        game_totals = {g["key"]: sum(1 for a in athletes if g["key"] in completion.get(a["id"], set())) for g in games_to_show}

        summary_cells = "".join(
            f'<td style="text-align:center;font-size:12px;color:#6E737B;padding:4px 6px;">'
            f'{game_totals[g["key"]]}/{total}</td>'
            for g in games_to_show
        )

        label_display = SESSION_LABEL_MAP.get(selected_label, selected_label or "")
        try:
            import datetime as _dt2
            em = _dt2.datetime.strptime(selected_month, "%Y-%m")
            month_display = em.strftime("%B %Y")
        except Exception:
            month_display = selected_month or ""

        # Entry URL base for "not done" cells
        base_params = f"group_id={selected_group_id}&session_label={selected_label or ''}&session_month={selected_month or ''}"

        rows_html = ""
        for a in athletes:
            done = completion.get(a["id"], set())
            cells = ""
            for g in games_to_show:
                if g["key"] in done:
                    cells += (
                        f'<td style="text-align:center;padding:6px;">'
                        f'<a href="/coach/participants/{a["id"]}" title="View results"'
                        f'   style="display:inline-block;background:#d1fae5;color:#065f46;'
                        f'          border-radius:50%;width:28px;height:28px;line-height:28px;'
                        f'          font-size:15px;text-decoration:none;font-weight:700;">&#10003;</a>'
                        f'</td>'
                    )
                else:
                    entry_url = f'/coach/group-testing?{base_params}&game_key={g["key"]}'
                    cell_title = f'Enter {esc(g["name"])} for {esc(a["name"])}'
                    cells += (
                        f'<td style="text-align:center;padding:6px;">'
                        f'<a href="{entry_url}" title="{cell_title}"'
                        f'   style="display:inline-block;background:#fee2e2;color:#991b1b;'
                        f'          border-radius:50%;width:28px;height:28px;line-height:26px;'
                        f'          font-size:17px;text-decoration:none;border:1px solid #fca5a5;">&#8212;</a>'
                        f'</td>'
                    )
            rows_html += f'<tr style="border-bottom:1px solid #DDE0E3;"><td style="font-weight:600;padding:8px 12px;white-space:nowrap;">{esc(a["name"])}</td>{cells}</tr>'

        # Overall completion %
        total_cells = total * len(games_to_show)
        done_cells = sum(len(completion.get(a["id"], set()) & set(g["key"] for g in games_to_show)) for a in athletes)
        pct = round(100 * done_cells / total_cells) if total_cells else 0
        bar_color = "#10b981" if pct == 100 else ("#F0A82E" if pct >= 50 else "#ef4444")

        matrix_html = f"""
        <div class="card" style="overflow-x:auto;margin-top:16px;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
            <div>
              <h3 style="margin:0 0 2px;">{esc(label_display)} &mdash; {esc(month_display)}</h3>
              <span class="muted" style="font-size:13px;">{total} athletes &middot; {len(games_to_show)} games selected</span>
            </div>
            <div style="text-align:right;">
              <div style="font-size:22px;font-weight:700;color:{bar_color};">{pct}%</div>
              <div style="font-size:12px;color:#6E737B;">overall completion</div>
              <div style="margin-top:4px;height:6px;width:120px;background:#DDE0E3;border-radius:3px;">
                <div style="height:100%;width:{pct}%;background:{bar_color};border-radius:3px;"></div>
              </div>
            </div>
          </div>
          <div style="font-size:12px;color:#6E737B;margin-bottom:10px;">
            <span style="display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;
                         background:#d1fae5;color:#065f46;border-radius:50%;font-weight:700;font-size:13px;">&#10003;</span>
            = complete &nbsp;
            <span style="display:inline-block;width:22px;height:22px;line-height:20px;text-align:center;
                         background:#fee2e2;color:#991b1b;border-radius:50%;font-size:15px;border:1px solid #fca5a5;">&#8212;</span>
            = not done &mdash; click to enter results
          </div>
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#2D323B;color:#fff;">
                <th style="text-align:left;padding:8px 12px;min-width:160px;">Athlete</th>
                {col_headers}
              </tr>
            </thead>
            <tbody>
              {rows_html}
              <tr style="background:#f9fafb;border-top:2px solid #DDE0E3;">
                <td style="padding:6px 12px;font-size:12px;color:#6E737B;font-weight:600;">Completed</td>
                {summary_cells}
              </tr>
            </tbody>
          </table>
        </div>"""

    elif selected_group_id and selected_label and not athletes:
        matrix_html = '<p class="muted" style="margin-top:16px;">No athletes found in this group.</p>'

    body = f"""
    <div class="page-head"><h1>Completion Tracker</h1></div>
    <p class="muted" style="margin-bottom:20px;">
      Select a group, phase, and which games to track. Click a red cell to go straight to data entry for that game.
    </p>
    <div class="card form-card">{selector_form}</div>
    {matrix_html}"""

    return layout("Completion Tracker", body, user=coach, active_nav="completion_tracker")


# Group Testing (enter results for a whole group game-by-game)
# ---------------------------------------------------------------------------

def group_testing_page(coach, groups, selected_group_id=None, selected_label=None,
                       selected_month=None, selected_game_key=None,
                       athletes=None, game=None, existing=None, completion_data=None):
    """Game-by-game group data entry: athletes as rows, fields as columns, one Save All."""
    athletes = athletes or []
    existing = existing or {}          # {athlete_id: {field_key: value}}
    completion_data = completion_data or {}  # {athlete_id: [game_keys]}

    group_opts = '<option value="">— Select group —</option>' + "".join(
        f'<option value="{g["id"]}" {"selected" if g["id"] == selected_group_id else ""}>{esc(g["name"])}</option>'
        for g in groups
    )
    type_opts = '<option value="">— Select phase —</option>' + "".join(
        f'<option value="{s["key"]}" {"selected" if s["key"] == selected_label else ""}>{esc(s["label"])}</option>'
        for s in SESSION_TYPES
    )
    game_opts = '<option value="">— Select game —</option>' + "".join(
        f'<option value="{g["key"]}" {"selected" if g["key"] == selected_game_key else ""}>{esc(g["name"])}</option>'
        for g in all_measurement_games()
    )

    selector_form = f"""
    <form method="get" action="/coach/group-testing"
          style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;margin-bottom:24px;">
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Group</label>
        <select name="group_id" required style="min-width:180px;">{group_opts}</select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Test Phase</label>
        <select name="session_label" required style="min-width:180px;">{type_opts}</select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Month</label>
        {_month_select(name="session_month", selected=selected_month)}
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Game</label>
        <select name="game_key" required style="min-width:200px;">{game_opts}</select>
      </div>
      <button type="submit" class="btn btn-primary" style="white-space:nowrap;">Load Athletes</button>
    </form>"""

    table_html = ""
    if game and athletes:
        fields = [f for f in game["fields"] if True]  # all enterable fields
        computed_keys = {c["key"] for c in game.get("computed", [])}

        def _th_suffix(field):
            if field["type"] == "time":
                return '<br><small style="font-weight:400;font-size:11px;">seconds</small>'
            u = field.get("unit", "")
            return f'<br><small style="font-weight:400;font-size:11px;">{esc(u)}</small>' if u else ""

        col_headers = "".join(
            f'<th style="min-width:120px;">{esc(f["label"])}{_th_suffix(f)}</th>'
            for f in fields
        )

        rows_html = ""
        for a in athletes:
            aid = a["id"]
            existing_vals = existing.get(aid, {})
            cells = ""
            for f in fields:
                val = existing_vals.get(f["key"], "")
                step = "0.01" if f["type"] == "time" else "1"
                bg = "background:#fffbe6;" if val != "" else ""
                cells += (
                    f'<td><input type="number" step="{step}" min="0" '
                    f'name="athlete_{aid}__{f["key"]}" value="{esc(str(val)) if val != "" else ""}" '
                    f'style="width:100%;{bg}" /></td>'
                )
            rows_html += f'<tr><td style="font-weight:600;white-space:nowrap;">{esc(a["name"])}</td>{cells}</tr>'

        label_display = SESSION_LABEL_MAP.get(selected_label, selected_label or "")
        try:
            import datetime as _dt2
            em = _dt2.datetime.strptime(selected_month, "%Y-%m")
            month_display = em.strftime("%B %Y")
        except Exception:
            month_display = selected_month or ""

        table_html = f"""
        <div class="card" style="overflow-x:auto;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
            <div>
              <h3 style="margin:0 0 2px;">{esc(game['name'])}</h3>
              <span class="muted" style="font-size:13px;">{esc(label_display)} &middot; {esc(month_display)}</span>
            </div>
            <div style="font-size:13px;color:#6E737B;">
              Existing values shown in yellow &mdash; update or leave to keep.
            </div>
          </div>
          <form method="post" action="/coach/group-testing/save">
            <input type="hidden" name="session_label" value="{esc(selected_label or '')}" />
            <input type="hidden" name="session_month" value="{esc(selected_month or '')}" />
            <input type="hidden" name="game_key" value="{esc(selected_game_key or '')}" />
            <table style="width:100%;border-collapse:collapse;">
              <thead>
                <tr style="background:#2D323B;color:#fff;">
                  <th style="text-align:left;padding:8px 12px;min-width:150px;">Athlete</th>
                  {col_headers}
                </tr>
              </thead>
              <tbody>
                {"".join(f'<tr style="border-bottom:1px solid #DDE0E3;">{r}</tr>' for r in rows_html.replace("</tr>","").split("<tr>")[1:])}
              </tbody>
            </table>
            <div style="margin-top:16px;display:flex;gap:12px;align-items:center;">
              <button type="submit" class="btn btn-primary">&#10003; Save All Results</button>
              <span style="font-size:13px;color:#6E737B;">Only fields with a value entered will be saved.</span>
            </div>
          </form>
        </div>"""

        # Fix: rebuild rows cleanly
        table_html = f"""
        <div class="card" style="overflow-x:auto;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
            <div>
              <h3 style="margin:0 0 2px;">{esc(game['name'])}</h3>
              <span class="muted" style="font-size:13px;">{esc(label_display)} &middot; {esc(month_display)}</span>
            </div>
            <span style="font-size:13px;color:#6E737B;">Yellow = existing value</span>
          </div>
          <form method="post" action="/coach/group-testing/save">
            <input type="hidden" name="session_label" value="{esc(selected_label or '')}" />
            <input type="hidden" name="session_month" value="{esc(selected_month or '')}" />
            <input type="hidden" name="game_key" value="{esc(selected_game_key or '')}" />
            <table style="width:100%;border-collapse:collapse;">
              <thead>
                <tr style="background:#2D323B;color:#fff;">
                  <th style="text-align:left;padding:8px 12px;min-width:160px;font-weight:600;">Athlete</th>
                  {col_headers}
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            <div style="margin-top:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
              <button type="submit" class="btn btn-primary" style="font-size:15px;padding:10px 28px;">
                &#10003; Save All Results
              </button>
              <span style="font-size:13px;color:#6E737B;">Blank fields are skipped — only filled values are saved.</span>
            </div>
          </form>
        </div>"""

    elif selected_group_id and selected_label and selected_game_key and not athletes:
        table_html = '<div class="card"><p class="muted">No athletes found in this group.</p></div>'

    # ── Compact completion matrix ─────────────────────────────────────────────
    matrix_html = ""
    if completion_data and selected_group_id and selected_label:
        all_games = all_measurement_games()
        # Build base URL for clicking a game cell to load that game
        base_params = (
            f"group_id={esc(str(selected_group_id))}"
            f"&session_label={esc(selected_label or '')}"
            f"&session_month={esc(selected_month or '')}"
        )
        # Gather all athlete IDs present in completion_data
        matrix_athlete_ids = list(completion_data.keys())
        # Build athlete name lookup from the athletes list (already loaded)
        # But completion_data keys are ints; athletes list may be empty if game not yet selected.
        # We need names — pull from athletes or from the outer scope.
        # athletes may be empty list if no game selected; re-use sorted keys with names from athletes OR
        # we pass a small name map. For now, build from whatever athletes list is available.
        athlete_name_map = {a["id"]: a["name"] for a in athletes} if athletes else {}
        # If athletes not loaded (no game selected), we still have completion_data keys.
        # We'll just show athlete IDs if names aren't available — but actually app always
        # passes athletes=[] when no game; we need names from somewhere.
        # Solution: app.py already loads all_athletes before the game-specific step;
        # completion_data keys are the same athlete IDs. We pass athlete name via a
        # dedicated list embedded in the matrix using all_athletes from app route.
        # For view-side: we reconstruct from whatever we have. If athletes list is empty,
        # fall through gracefully without names — but the app was updated so athletes IS
        # populated whenever completion_data is non-empty (we always load all_athletes).
        # Actually re-reading app.py: athletes = list(all_athletes) only when game_key is set.
        # When game_key is None, athletes stays [].
        # Fix: use athletes list if available, otherwise skip names (show "—").
        # Actually the matrix won't have athlete names in that case.
        # Better fix already in app.py: pass athletes list from all_athletes regardless of game.
        # We'll handle it here: iterate completion_data keys sorted, use name_map or id.

        # Compute per-game done counts
        game_done_counts = {}
        for gk_set in completion_data.values():
            for gk in gk_set:
                game_done_counts[gk] = game_done_counts.get(gk, 0) + 1

        total_athletes_in_matrix = len(completion_data)
        total_games = len(all_games)
        done_cells = sum(len(v) for v in completion_data.values())
        total_cells = total_athletes_in_matrix * total_games
        overall_pct = int(round(100 * done_cells / total_cells)) if total_cells else 0
        bar_fill_pct = overall_pct

        # Header row — game abbreviations
        game_headers = ""
        for g in all_games:
            abbrev = g["name"][:12] + ("…" if len(g["name"]) > 12 else "")
            is_active = g["key"] == selected_game_key
            active_style = "background:#F0A82E;color:#2D323B;" if is_active else ""
            game_url = f"/coach/group-testing?{base_params}&game_key={esc(g['key'])}"
            game_headers += (
                f'<th style="min-width:52px;max-width:64px;font-size:11px;font-weight:600;'
                f'text-align:center;padding:6px 4px;white-space:normal;word-break:break-word;'
                f'cursor:pointer;{active_style}" title="{esc(g["name"])}">'
                f'<a href="{game_url}" style="color:inherit;text-decoration:none;">{esc(abbrev)}</a>'
                f'</th>'
            )

        # Athlete rows
        athlete_rows = ""
        for aid, done_set in sorted(completion_data.items(), key=lambda x: athlete_name_map.get(x[0], "")):
            aname = athlete_name_map.get(aid, f"#{aid}")
            cells = ""
            for g in all_games:
                done = g["key"] in done_set
                game_url = f"/coach/group-testing?{base_params}&game_key={esc(g['key'])}"
                is_active = g["key"] == selected_game_key
                if done:
                    cell_style = "background:#d1fae5;color:#065f46;font-weight:700;text-align:center;font-size:13px;"
                    cell_content = "✓"
                else:
                    cell_style = "background:#fee2e2;color:#9b1c1c;text-align:center;font-size:13px;"
                    cell_content = f'<a href="{game_url}" style="color:#9b1c1c;text-decoration:none;font-weight:600;">—</a>'
                if is_active:
                    cell_style += "outline:2px solid #F0A82E;outline-offset:-2px;"
                cells += f'<td style="{cell_style}">{cell_content}</td>'
            athlete_rows += (
                f'<tr style="border-bottom:1px solid #f0f0f0;">'
                f'<td style="font-size:13px;font-weight:600;white-space:nowrap;padding:5px 10px;'
                f'position:sticky;left:0;background:#fff;z-index:1;">{esc(aname)}</td>'
                f'{cells}'
                f'</tr>'
            )

        # Summary row — done/total per game
        summary_cells = '<td style="font-size:11px;color:#6E737B;font-weight:600;padding:5px 10px;position:sticky;left:0;background:#f9fafb;">Done</td>'
        for g in all_games:
            n = game_done_counts.get(g["key"], 0)
            pct = int(round(100 * n / total_athletes_in_matrix)) if total_athletes_in_matrix else 0
            color = "#065f46" if pct == 100 else ("#92400e" if pct == 0 else "#1e40af")
            summary_cells += f'<td style="text-align:center;font-size:11px;font-weight:700;color:{color};background:#f9fafb;">{n}/{total_athletes_in_matrix}</td>'

        matrix_html = f"""
        <div class="card" style="margin-bottom:20px;">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
            <div>
              <span style="font-size:13px;font-weight:700;color:#2D323B;">Completion — {esc(SESSION_LABEL_MAP.get(selected_label, selected_label or ''))}</span>
              <span style="font-size:12px;color:#6E737B;margin-left:10px;">{done_cells}/{total_cells} fields &nbsp;·&nbsp; {overall_pct}% overall</span>
            </div>
            <div style="font-size:11px;color:#6E737B;">Click a game header or — to switch to that game</div>
          </div>
          <div style="background:#e5e7eb;border-radius:4px;height:5px;margin-bottom:14px;">
            <div style="height:5px;background:#F0A82E;border-radius:4px;width:{bar_fill_pct}%;transition:width 0.4s;"></div>
          </div>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
              <thead>
                <tr style="background:#2D323B;color:#fff;">
                  <th style="text-align:left;padding:6px 10px;font-size:13px;min-width:130px;position:sticky;left:0;background:#2D323B;z-index:2;">Athlete</th>
                  {game_headers}
                </tr>
              </thead>
              <tbody>{athlete_rows}</tbody>
              <tfoot><tr>{summary_cells}</tr></tfoot>
            </table>
          </div>
        </div>"""

    body = f"""
    <div class="page-head"><h1>Group Testing</h1></div>
    <p class="muted" style="margin-bottom:20px;">Select a group, phase, and game to enter results for all athletes at once.</p>
    <div class="card form-card">{selector_form}</div>
    {matrix_html}
    {table_html}
    <style>
      table td, table th {{ padding: 8px 10px; }}
      table tbody tr:nth-child(even) {{ background: #f9fafb; }}
      table input[type=number] {{ border:1px solid #DDE0E3;border-radius:5px;padding:5px 8px;font-size:14px; }}
      table input[type=number]:focus {{ border-color:#2D323B;outline:none; }}
    </style>"""

    return layout("Group Testing", body, user=coach, active_nav="group_testing")


# Session Sheet (blank printable PDF for field recording)
# ---------------------------------------------------------------------------

def session_sheet_page(coach, groups, session_types):
    """Form to select phase, month, group, games/fields → download blank PDF."""
    group_opts = '<option value="">— No group / blank rows only —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )
    type_opts = "".join(
        f'<option value="{s["key"]}">{esc(s["label"])}</option>' for s in session_types
    )

    # Build game checkboxes with nested field checkboxes (Level 1 only)
    game_blocks = ""
    for section in games_for_max_level(1):
        games_html = ""
        for game in section["games"]:
            fields_html = "".join(
                f"""<label style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:400;margin:4px 0 4px 20px;cursor:pointer;">
                  <input type="checkbox" name="fields" value="{esc(game['key'])}||{esc(f['key'])}"
                         class="field-cb cb-{esc(game['key'])}" style="width:auto;margin:0;" />
                  {esc(f['label'])}{"<span style='color:var(--jag-muted);font-size:11px;margin-left:4px;'>(" + esc(f.get('unit','')) + ")</span>" if f.get('unit') else ""}
                </label>"""
                for f in game["fields"]
            )
            games_html += f"""
            <div style="margin-bottom:10px;">
              <label style="display:flex;align-items:center;gap:8px;font-size:14px;font-weight:700;cursor:pointer;">
                <input type="checkbox" class="game-cb" data-game="{esc(game['key'])}"
                       style="width:auto;margin:0;"
                       onchange="toggleGameFields(this)" />
                {esc(game['name'])}
              </label>
              <div class="game-fields-{esc(game['key'])}" style="display:none;">
                {fields_html}
              </div>
            </div>"""
        game_blocks += f"""
        <div style="margin-bottom:18px;">
          <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                      color:var(--jag-muted);margin-bottom:8px;">{esc(section['section'])}</div>
          {games_html}
        </div>"""

    body = f"""
    <div class="page-head">
      <div>
        <h1>Session Recording Sheet</h1>
        <p class="muted">Choose your test phase, group, and fields — then download a blank PDF to take to the field.</p>
      </div>
    </div>
    <form method="post" action="/coach/session-sheet/pdf">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:820px;">
        <div class="card">
          <h3 style="margin-top:0;">Session Details</h3>
          <label>Test Phase
            <select name="session_label" required>{type_opts}</select>
          </label>
          <label>Month
            {_month_select("session_month")}
          </label>
          <label>Group
            <select name="group_id">{group_opts}</select>
          </label>
          <label style="display:flex;align-items:center;gap:8px;margin-top:14px;cursor:pointer;">
            <input type="checkbox" name="include_names" value="1" checked style="width:auto;margin:0;" />
            <span style="font-size:13px;font-weight:600;">Pre-fill athlete names from group</span>
          </label>
          <label style="margin-top:14px;">Extra blank rows
            <input type="number" name="blank_rows" value="0" min="0" max="30" style="max-width:100px;" />
          </label>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">Games &amp; Fields</h3>
          <p class="muted" style="font-size:13px;">Tick the games to include, then the specific fields within each.</p>
          {game_blocks}
        </div>
      </div>
      <div style="margin-top:20px;max-width:820px;">
        <button type="submit" class="btn btn-primary" style="font-size:15px;padding:12px 28px;">
          &#8681; Download PDF Recording Sheet
        </button>
      </div>
    </form>
    <script>
    function toggleGameFields(cb) {{
      var gameKey = cb.dataset.game;
      var wrap = document.querySelector('.game-fields-' + gameKey);
      if (!wrap) return;
      wrap.style.display = cb.checked ? 'block' : 'none';
      wrap.querySelectorAll('input[type=checkbox]').forEach(function(c) {{
        c.checked = cb.checked;
      }});
    }}
    </script>
    """
    return layout("Session Recording Sheet", body, user=coach, active_nav="group_hub")


# ──────────────────────────────────────────────────────────────────────────────
# GROUP HUB — combined completion matrix + group entry + session sheet PDF
# ──────────────────────────────────────────────────────────────────────────────

def group_hub_page(coach, groups, selected_group_id=None, selected_label=None,
                   selected_month=None, selected_game_key=None,
                   athletes=None, game=None, existing=None, completion_data=None,
                   athlete_xp_levels=None, active_window=None, recent_windows=None):
    """Single page combining:
      1. Selector form (group + phase + month + optional game)
      2. Completion matrix (shown when group+phase selected)
      3. Game entry table (shown when game also selected)
      4. Session Sheet PDF download panel (collapsible)
    """
    athletes        = athletes or []
    existing        = existing or {}
    completion_data = completion_data or {}

    # ── Selector form ─────────────────────────────────────────────────────────
    # Group the group options by organisation using <optgroup>
    from collections import OrderedDict as _OD
    _org_buckets = _OD()  # org_name -> [group, ...]
    for _g in groups:
        _on = _g.get("org_name") or "No Organisation"
        _org_buckets.setdefault(_on, []).append(_g)
    group_opts = '<option value="">— Select group —</option>'
    for _on, _glist in _org_buckets.items():
        group_opts += f'<optgroup label="{esc(_on)}">'
        for _g in _glist:
            _sel = "selected" if _g["id"] == selected_group_id else ""
            group_opts += f'<option value="{_g["id"]}" {_sel}>{esc(_g["name"])}</option>'
        group_opts += "</optgroup>"
    type_opts = '<option value="">— Select phase —</option>' + "".join(
        f'<option value="{s["key"]}" {"selected" if s["key"] == selected_label else ""}>{esc(s["label"])}</option>'
        for s in SESSION_TYPES
    )
    game_opts = '<option value="">— Select game (optional) —</option>' + "".join(
        f'<option value="{g["key"]}" {"selected" if g["key"] == selected_game_key else ""}>{esc(g["name"])}</option>'
        for g in all_measurement_games()
    )
    selector_form = f"""
    <form method="get" action="/coach/group-hub"
          style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;">
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Group</label>
        <select name="group_id" required style="min-width:175px;">{group_opts}</select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Test Phase</label>
        <select name="session_label" required style="min-width:175px;">{type_opts}</select>
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Month</label>
        {_month_select(name="session_month", selected=selected_month)}
      </div>
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">
          Game <span style="font-weight:400;color:#6E737B;">(to enter results)</span>
        </label>
        <select name="game_key" style="min-width:200px;">{game_opts}</select>
      </div>
      <button type="submit" class="btn btn-primary" style="white-space:nowrap;">Load</button>
    </form>"""

    # ── Athlete overview panel (XP rank + level summary) ─────────────────────
    athlete_xp_levels = athlete_xp_levels or {}
    overview_html = ""
    if athletes and athlete_xp_levels:
        from constants import CORE_AAP_GAMES
        LEVEL_COLOURS_HUB = {
            0: ("#E5E7EB", "#6E737B"),
            1: ("#1EBE8B", "#fff"),
            2: ("#F0A82E", "#2D323B"),
            3: ("#2D323B", "#fff"),
            4: ("#F97316", "#fff"),
            5: ("#8B5CF6", "#fff"),
        }
        tiles = ""
        for a in athletes:
            aid = a["id"]
            aname = esc(a.get("name", ""))
            an = a.get("athlete_number") or ""
            ax = athlete_xp_levels.get(aid, {})
            levels = ax.get("levels", {})
            tier = ax.get("tier") or {"label": "Starter", "colour": "#6E737B"}
            total_xp = ax.get("total_xp", 0)
            tier_colour = tier["colour"]

            # Initials avatar
            parts = a.get("name", "").strip().split()
            inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else (parts[0][0].upper() if parts else "?")

            # Mini level dots — 8 core games
            dots = ""
            for gk in CORE_AAP_GAMES:
                lvl = levels.get(gk, 0)
                bg, _ = LEVEL_COLOURS_HUB.get(lvl, ("#E5E7EB", "#6E737B"))
                from constants import find_measurement_game as _fmg
                gdef = _fmg(gk)
                title = f"{gdef['name']}: L{lvl}" if (gdef and lvl > 0) else (gdef["name"] if gdef else gk)
                dots += (f'<div title="{esc(title)}" style="width:10px;height:10px;border-radius:50%;'
                         f'background:{bg};flex-shrink:0;"></div>')

            tiles += f"""
            <a href="/coach/participants/{aid}"
               style="display:flex;flex-direction:column;background:#fff;border:1px solid #E5E7EB;
                      border-radius:12px;padding:14px;text-decoration:none;min-width:140px;flex:1;
                      transition:box-shadow 0.15s,border-color 0.15s;"
               onmouseover="this.style.boxShadow='0 4px 14px rgba(0,0,0,0.1)';this.style.borderColor='#F0A82E'"
               onmouseout="this.style.boxShadow='';this.style.borderColor='#E5E7EB'">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <div style="width:38px;height:38px;border-radius:50%;background:#2D323B;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:13px;color:#F0A82E;flex-shrink:0;">{inits}</div>
                <div style="min-width:0;">
                  <div style="font-size:13px;font-weight:700;color:#2D323B;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{aname}</div>
                  {f'<div style="font-size:11px;color:#9CA3AF;">#{esc(an)}</div>' if an else ''}
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
                <span style="font-size:10px;font-weight:700;background:{tier_colour};color:#fff;
                             border-radius:999px;padding:1px 7px;">{esc(tier['label'])}</span>
                <span style="font-size:11px;color:#6E737B;">{total_xp:,} AXP</span>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:3px;">{dots}</div>
            </a>"""

        overview_html = f"""
        <div class="card" style="margin-bottom:0;">
          <div style="font-size:13px;font-weight:700;color:#2D323B;margin-bottom:12px;">
            Group Overview
            <span style="font-size:11px;font-weight:400;color:#6E737B;margin-left:6px;">
              {len(athletes)} athlete{'s' if len(athletes) != 1 else ''} · dots = game levels (green=L1 → purple=L5)
            </span>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:10px;">{tiles}</div>
        </div>"""

    # ── Completion matrix ─────────────────────────────────────────────────────
    matrix_html = ""
    if completion_data and selected_group_id and selected_label:
        all_games  = all_measurement_games()
        base_params = (
            f"group_id={esc(str(selected_group_id))}"
            f"&session_label={esc(selected_label or '')}"
            f"&session_month={esc(selected_month or '')}"
        )
        athlete_name_map = {a["id"]: a["name"] for a in athletes}

        game_done_counts = {}
        for gk_set in completion_data.values():
            for gk in gk_set:
                game_done_counts[gk] = game_done_counts.get(gk, 0) + 1

        total_athl  = len(completion_data)
        total_cells = total_athl * len(all_games)
        done_cells  = sum(len(v) for v in completion_data.values())
        overall_pct = int(round(100 * done_cells / total_cells)) if total_cells else 0

        game_headers = ""
        for g in all_games:
            abbrev     = g["name"][:12] + ("…" if len(g["name"]) > 12 else "")
            is_active  = g["key"] == selected_game_key
            hdr_style  = "background:#F0A82E;color:#2D323B;" if is_active else ""
            game_url   = f"/coach/group-hub?{base_params}&game_key={esc(g['key'])}"
            game_headers += (
                f'<th style="min-width:52px;max-width:64px;font-size:11px;font-weight:600;'
                f'text-align:center;padding:6px 4px;white-space:normal;word-break:break-word;'
                f'cursor:pointer;{hdr_style}" title="{esc(g["name"])}">'
                f'<a href="{game_url}" style="color:inherit;text-decoration:none;">{esc(abbrev)}</a></th>'
            )

        athlete_rows = ""
        for aid, done_set in sorted(completion_data.items(),
                                    key=lambda x: athlete_name_map.get(x[0], "")):
            aname = athlete_name_map.get(aid, f"#{aid}")
            cells = ""
            for g in all_games:
                done      = g["key"] in done_set
                game_url  = f"/coach/group-hub?{base_params}&game_key={esc(g['key'])}"
                is_active = g["key"] == selected_game_key
                outline   = "outline:2px solid #F0A82E;outline-offset:-2px;" if is_active else ""
                if done:
                    cells += f'<td style="background:#d1fae5;color:#065f46;font-weight:700;text-align:center;font-size:13px;{outline}">✓</td>'
                else:
                    cells += (
                        f'<td style="background:#fee2e2;color:#9b1c1c;text-align:center;font-size:13px;{outline}">'
                        f'<a href="{game_url}" style="color:#9b1c1c;text-decoration:none;font-weight:600;">—</a></td>'
                    )
            profile_url = f"/coach/participants/{aid}"
            athlete_rows += (
                f'<tr style="border-bottom:1px solid #f0f0f0;">'
                f'<td style="font-size:13px;font-weight:600;white-space:nowrap;padding:5px 10px;'
                f'position:sticky;left:0;background:#fff;z-index:1;">'
                f'<a href="{profile_url}" style="color:inherit;text-decoration:none;">{esc(aname)}</a></td>'
                f'{cells}</tr>'
            )

        summary_cells = (
            '<td style="font-size:11px;color:#6E737B;font-weight:600;padding:5px 10px;'
            'position:sticky;left:0;background:#f9fafb;">Done</td>'
        )
        for g in all_games:
            n     = game_done_counts.get(g["key"], 0)
            pct_g = int(round(100 * n / total_athl)) if total_athl else 0
            col   = "#065f46" if pct_g == 100 else ("#92400e" if pct_g == 0 else "#1e40af")
            summary_cells += (
                f'<td style="text-align:center;font-size:11px;font-weight:700;color:{col};'
                f'background:#f9fafb;">{n}/{total_athl}</td>'
            )

        label_display_m = esc(SESSION_LABEL_MAP.get(selected_label, selected_label or ""))
        matrix_html = f"""
        <div class="card" style="margin-bottom:0;">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      flex-wrap:wrap;gap:10px;margin-bottom:10px;">
            <span style="font-size:13px;font-weight:700;color:#2D323B;">
              Completion — {label_display_m}
            </span>
            <span style="font-size:12px;color:#6E737B;">
              {done_cells}/{total_cells} &nbsp;·&nbsp; {overall_pct}% &nbsp;·&nbsp;
              Click a game header or — to load that game below
            </span>
          </div>
          <div style="background:#e5e7eb;border-radius:4px;height:5px;margin-bottom:14px;">
            <div style="height:5px;background:#F0A82E;border-radius:4px;width:{overall_pct}%;
                        transition:width 0.4s;"></div>
          </div>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
              <thead>
                <tr style="background:#2D323B;color:#fff;">
                  <th style="text-align:left;padding:6px 10px;font-size:13px;min-width:130px;
                             position:sticky;left:0;background:#2D323B;z-index:2;">Athlete</th>
                  {game_headers}
                </tr>
              </thead>
              <tbody>{athlete_rows}</tbody>
              <tfoot><tr>{summary_cells}</tr></tfoot>
            </table>
          </div>
        </div>"""

    # ── Game entry table ──────────────────────────────────────────────────────
    entry_html = ""
    if game and athletes:
        fields = [f for f in game["fields"]]
        either_or_game = game.get("either_or", False)

        def _th_sfx(field):
            if field["type"] == "time":
                return '<br><small style="font-weight:400;font-size:11px;">seconds</small>'
            u = field.get("unit", "")
            return f'<br><small style="font-weight:400;font-size:11px;">{esc(u)}</small>' if u else ""

        if either_or_game and len(fields) == 2:
            or_th = '<th style="min-width:40px;text-align:center;padding:4px;color:#F0A82E;font-size:12px;font-weight:700;">OR</th>'
            col_headers = (
                f'<th style="min-width:120px;">{esc(fields[0]["label"])}{_th_sfx(fields[0])}</th>'
                + or_th +
                f'<th style="min-width:120px;">{esc(fields[1]["label"])}{_th_sfx(fields[1])}</th>'
            )
        else:
            col_headers = "".join(
                f'<th style="min-width:120px;">{esc(f["label"])}{_th_sfx(f)}</th>'
                for f in fields
            )
        rows_html = ""
        for a in athletes:
            aid  = a["id"]
            vals = existing.get(aid, {})
            cells = ""
            for i, f in enumerate(fields):
                if either_or_game and i == 1:
                    cells += '<td style="text-align:center;color:#6E737B;font-size:11px;font-weight:700;padding:0 4px;">OR</td>'
                val  = vals.get(f["key"], "")
                step = "0.01" if f["type"] == "time" else "1"
                bg   = "background:#fffbe6;" if val != "" else ""
                cells += (
                    f'<td><input type="number" step="{step}" min="0" '
                    f'name="athlete_{aid}__{f["key"]}" value="{esc(str(val)) if val != "" else ""}" '
                    f'style="width:100%;{bg}" /></td>'
                )
            rows_html += (
                f'<tr style="border-bottom:1px solid #DDE0E3;">'
                f'<td style="font-weight:600;white-space:nowrap;">{esc(a["name"])}</td>{cells}</tr>'
            )

        lbl_disp = SESSION_LABEL_MAP.get(selected_label, selected_label or "")
        try:
            import datetime as _dt2
            em = _dt2.datetime.strptime(selected_month, "%Y-%m")
            month_disp = em.strftime("%B %Y")
        except Exception:
            month_disp = selected_month or ""

        entry_html = f"""
        <div class="card" style="overflow-x:auto;margin-bottom:0;">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      flex-wrap:wrap;gap:10px;margin-bottom:14px;">
            <div>
              <h3 style="margin:0 0 2px;">{esc(game['name'])}</h3>
              <span class="muted" style="font-size:13px;">
                {esc(lbl_disp)} &middot; {esc(month_disp)} &nbsp;·&nbsp;
                <span style="color:#92400e;">Yellow = existing value</span>
                {"&nbsp;·&nbsp;<span style='color:#2D323B;font-weight:600;'>Record Small OR Large group — not both</span>" if either_or_game else ""}
              </span>
            </div>
          </div>
          <form method="post" action="/coach/group-testing/save">
            <input type="hidden" name="session_label"  value="{esc(selected_label or '')}" />
            <input type="hidden" name="session_month"  value="{esc(selected_month or '')}" />
            <input type="hidden" name="game_key"       value="{esc(selected_game_key or '')}" />
            <input type="hidden" name="redirect_to"    value="/coach/group-hub?group_id={esc(str(selected_group_id or ''))}&session_label={esc(selected_label or '')}&session_month={esc(selected_month or '')}&game_key={esc(selected_game_key or '')}" />
            <table style="width:100%;border-collapse:collapse;">
              <thead>
                <tr style="background:#2D323B;color:#fff;">
                  <th style="text-align:left;padding:8px 12px;min-width:160px;">Athlete</th>
                  {col_headers}
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            <div style="margin-top:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
              <button type="submit" class="btn btn-primary" style="font-size:15px;padding:10px 28px;">
                &#10003; Save All Results
              </button>
              <span style="font-size:13px;color:#6E737B;">Blank fields are skipped.</span>
            </div>
          </form>
        </div>"""

    elif selected_group_id and selected_label and selected_game_key and not athletes:
        entry_html = '<div class="card"><p class="muted">No athletes found in this group.</p></div>'

    # ── Session Sheet PDF panel ───────────────────────────────────────────────
    sheet_html = ""
    if selected_group_id and selected_label:
        # Embed completion data as JSON for "select only missing" JS
        import json as _json
        comp_json = _json.dumps({str(k): list(v) for k, v in completion_data.items()})

        game_blocks = ""
        for section in games_for_max_level(1):
            for g in section["games"]:
                gk = g["key"]
                # Work out if this game is fully done for all athletes
                n_done = sum(1 for vs in completion_data.values() if gk in vs)
                n_tot  = len(completion_data)
                badge  = ""
                if n_tot > 0:
                    if n_done == n_tot:
                        badge = f'<span style="font-size:11px;color:#065f46;background:#d1fae5;padding:1px 7px;border-radius:999px;font-weight:600;margin-left:6px;">✓ All done</span>'
                    elif n_done > 0:
                        badge = f'<span style="font-size:11px;color:#92400e;background:#fef3c7;padding:1px 7px;border-radius:999px;font-weight:600;margin-left:6px;">{n_done}/{n_tot}</span>'
                    else:
                        badge = f'<span style="font-size:11px;color:#9b1c1c;background:#fee2e2;padding:1px 7px;border-radius:999px;font-weight:600;margin-left:6px;">None done</span>'

                field_html_parts = []
                for f in g["fields"]:
                    unit = f.get("unit", "")
                    unit_span = (
                        '<span style="font-size:11px;color:#6E737B;margin-left:4px;">(' + esc(unit) + ')</span>'
                        if unit else ""
                    )
                    field_html_parts.append(
                        f'<label style="display:flex;align-items:center;gap:6px;font-size:13px;'
                        f'font-weight:400;margin:4px 0 4px 22px;cursor:pointer;">'
                        f'<input type="checkbox" name="fields" value="{esc(gk)}||{esc(f["key"])}" '
                        f'class="sheet-field-cb sheet-cb-{esc(gk)}" checked style="width:auto;margin:0;" />'
                        f'{esc(f["label"])}{unit_span}'
                        f'</label>'
                    )
                fields_html = "".join(field_html_parts)
                game_blocks += f"""
                <div style="margin-bottom:8px;">
                  <label style="display:flex;align-items:center;gap:6px;font-size:14px;
                                font-weight:700;cursor:pointer;">
                    <input type="checkbox" class="sheet-game-cb" data-game="{esc(gk)}"
                           checked style="width:auto;margin:0;"
                           onchange="toggleSheetGame(this)" />
                    {esc(g['name'])}{badge}
                  </label>
                  <div class="sheet-fields-{esc(gk)}">{fields_html}</div>
                </div>"""

        sheet_html = f"""
        <div class="card" style="margin-bottom:0;">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      flex-wrap:wrap;gap:10px;cursor:pointer;user-select:none;"
               onclick="toggleSheetPanel()">
            <span style="font-size:14px;font-weight:700;color:#2D323B;">
              &#128196; Download Session Sheet PDF
            </span>
            <span id="sheet-toggle-icon" style="font-size:11px;color:#F0A82E;font-weight:700;">
              &#9660; EXPAND
            </span>
          </div>
          <div id="sheet-panel" style="display:none;margin-top:16px;">
            <form method="post" action="/coach/session-sheet/pdf" target="_blank">
              <input type="hidden" name="group_id"       value="{esc(str(selected_group_id or ''))}" />
              <input type="hidden" name="session_label"  value="{esc(selected_label or '')}" />
              <input type="hidden" name="session_month"  value="{esc(selected_month or '')}" />
              <input type="hidden" name="include_names"  value="1" />
              <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
                <button type="button" onclick="sheetSelectAll()"
                        style="font-size:12px;padding:4px 12px;border-radius:999px;
                               border:1px solid #DDE0E3;background:#fff;cursor:pointer;font-weight:600;">
                  All games
                </button>
                <button type="button" onclick="sheetSelectMissing()"
                        style="font-size:12px;padding:4px 12px;border-radius:999px;
                               border:1px solid #F0A82E;background:#FFF8E7;cursor:pointer;
                               font-weight:600;color:#92400e;">
                  Only missing
                </button>
                <button type="button" onclick="sheetSelectNone()"
                        style="font-size:12px;padding:4px 12px;border-radius:999px;
                               border:1px solid #DDE0E3;background:#fff;cursor:pointer;font-weight:600;">
                  None
                </button>
              </div>
              <div style="columns:2;column-gap:24px;margin-bottom:16px;">{game_blocks}</div>
              <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;
                          padding-top:12px;border-top:1px solid #DDE0E3;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <label style="font-size:13px;font-weight:600;">Blank rows to add:</label>
                  <input type="number" name="blank_rows" value="0" min="0" max="20"
                         style="width:60px;padding:4px 8px;border:1px solid #DDE0E3;border-radius:5px;" />
                </div>
                <button type="submit" class="btn btn-primary" style="font-size:14px;padding:9px 24px;">
                  &#8681; Download PDF
                </button>
                <span style="font-size:12px;color:#6E737B;">Opens in a new tab.</span>
              </div>
            </form>
          </div>
        </div>
        <script>
        var _compData = {comp_json};
        function toggleSheetPanel() {{
          var p = document.getElementById('sheet-panel');
          var icon = document.getElementById('sheet-toggle-icon');
          var open = p.style.display !== 'none';
          p.style.display = open ? 'none' : 'block';
          icon.innerHTML = open ? '&#9660; EXPAND' : '&#9650; COLLAPSE';
        }}
        function toggleSheetGame(cb) {{
          var gk = cb.dataset.game;
          document.querySelectorAll('.sheet-cb-' + gk).forEach(function(el) {{
            el.checked = cb.checked;
          }});
        }}
        function sheetSelectAll() {{
          document.querySelectorAll('.sheet-game-cb,.sheet-field-cb').forEach(function(el) {{
            el.checked = true;
          }});
          document.querySelectorAll('[class^="sheet-fields-"]').forEach(function(el) {{
            el.style.display = '';
          }});
        }}
        function sheetSelectNone() {{
          document.querySelectorAll('.sheet-game-cb,.sheet-field-cb').forEach(function(el) {{
            el.checked = false;
          }});
        }}
        function sheetSelectMissing() {{
          // Uncheck games where every athlete already has results
          var totalAthletes = Object.keys(_compData).length;
          document.querySelectorAll('.sheet-game-cb').forEach(function(cb) {{
            var gk = cb.dataset.game;
            var doneCount = 0;
            Object.values(_compData).forEach(function(doneGames) {{
              if (doneGames.indexOf(gk) !== -1) doneCount++;
            }});
            var allDone = (totalAthletes > 0 && doneCount === totalAthletes);
            cb.checked = !allDone;
            document.querySelectorAll('.sheet-cb-' + gk).forEach(function(el) {{
              el.checked = !allDone;
            }});
          }});
        }}
        // Auto-open the sheet panel if no game is selected (nothing else to show)
        {'toggleSheetPanel();' if not selected_game_key and completion_data else ''}
        </script>"""

    # ── Assemble sections ─────────────────────────────────────────────────────
    sections = []
    if overview_html:
        sections.append(("Athletes", overview_html))
    if matrix_html:
        sections.append(("Completion Overview", matrix_html))
    if entry_html:
        sections.append(("Enter Results", entry_html))
    if sheet_html:
        sections.append(("Session Sheet", sheet_html))

    content_html = ""
    for section_label_txt, section_body in sections:
        content_html += f"""
        <div style="margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="width:4px;height:20px;background:#F0A82E;border-radius:2px;
                         display:inline-block;flex-shrink:0;"></span>
            <span style="font-size:12px;font-weight:700;color:#6E737B;
                         text-transform:uppercase;letter-spacing:0.06em;">{esc(section_label_txt)}</span>
          </div>
          {section_body}
        </div>"""

    if not content_html:
        content_html = '<p class="muted" style="margin-top:24px;">Select a group and phase above to get started.</p>'

    # ── Measurement Window panel (shown when a group is selected) ─────────────
    window_panel = ""
    if selected_group_id:
        recent_windows = recent_windows or []
        if active_window:
            wid = active_window["id"]
            label_txt = esc(active_window.get("session_label") or "")
            label_part = f' — <strong>{label_txt}</strong>' if label_txt else ''
            opened_at = esc(active_window.get("opened_at", "")[:16])
            window_panel = f"""
    <div style="background:#1EBE8B1A;border:1.5px solid #1EBE8B;border-radius:14px;
                padding:18px 20px;margin-bottom:20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
          <div style="font-weight:700;color:#065F46;font-size:15px;">
            🟢 Measurement Window Open{label_part}
          </div>
          <div style="color:#047857;font-size:13px;margin-top:3px;">
            Opened {opened_at} — athletes can self-score from their dashboard.
          </div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <a href="/coach/window/{wid}"
             style="background:#2D323B;color:#fff;font-weight:600;font-size:13px;
                    border-radius:8px;padding:8px 16px;text-decoration:none;">
            View Status
          </a>
          <form method="post" action="/coach/window/{wid}/close" style="margin:0;">
            <button type="submit"
                    onclick="return confirm('Close window? This commits all submitted scores and awards AXP. Athletes who haven\\'t submitted will be excluded (you can re-open later).')"
                    style="background:#F97316;color:#fff;font-weight:600;font-size:13px;
                           border:none;border-radius:8px;padding:8px 16px;cursor:pointer;">
              Close &amp; Commit
            </button>
          </form>
        </div>
      </div>
    </div>"""
        else:
            from constants import SESSION_TYPES
            label_options = "".join(
                f'<option value="{esc(t["key"])}">{esc(t["label"])}</option>'
                for t in SESSION_TYPES
            )
            recent_html = ""
            if recent_windows:
                rows = "".join(
                    f'<tr><td>{esc(w.get("session_label") or "—")}</td>'
                    f'<td>{esc((w.get("opened_at") or "")[:10])}</td>'
                    f'<td>{esc(w.get("status", ""))}</td>'
                    f'<td>{w.get("submission_count", 0)}</td>'
                    f'<td><a href="/coach/window/{w["id"]}" style="color:#2D323B;font-weight:600;">View</a></td></tr>'
                    for w in recent_windows
                )
                recent_html = f"""
        <div style="margin-top:16px;border-top:1px solid #E5E7EB;padding-top:12px;">
          <div style="font-size:12px;font-weight:700;color:#6E737B;text-transform:uppercase;
                      letter-spacing:0.06em;margin-bottom:8px;">Recent Windows</div>
          <table style="width:100%;font-size:13px;border-collapse:collapse;">
            <thead><tr style="color:#6E737B;">
              <th style="text-align:left;padding:4px 8px;">Phase</th>
              <th style="text-align:left;padding:4px 8px;">Opened</th>
              <th style="text-align:left;padding:4px 8px;">Status</th>
              <th style="text-align:left;padding:4px 8px;">Submitted</th>
              <th style="padding:4px 8px;"></th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""
            window_panel = f"""
    <div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:14px;
                padding:18px 20px;margin-bottom:20px;">
      <div style="font-weight:700;color:#2D323B;font-size:15px;margin-bottom:12px;">
        📋 Open a Measurement Window
      </div>
      <p style="font-size:13px;color:#6E737B;margin:0 0 14px;">
        Open a window so athletes can self-score from their dashboard.
        AXP is awarded when you close the window.
      </p>
      <form method="post" action="/coach/groups/{selected_group_id}/window/open"
            style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;">
        <div>
          <label style="font-size:12px;font-weight:600;color:#6E737B;display:block;margin-bottom:4px;">
            Phase label (optional)
          </label>
          <select name="session_label"
                  style="border:1px solid #DDE0E3;border-radius:8px;padding:8px 10px;
                         font-size:13px;color:#2D323B;background:#fff;">
            <option value="">— select —</option>
            {label_options}
          </select>
        </div>
        <button type="submit"
                style="background:#2D323B;color:#F0A82E;font-weight:700;font-size:13px;
                       border:none;border-radius:8px;padding:9px 20px;cursor:pointer;">
          Open Window
        </button>
      </form>
      {recent_html}
    </div>"""

    body = f"""
    <div class="page-head">
      <div>
        <h1>Group Hub</h1>
        <p class="muted">Completion overview · results entry · session sheet — all in one place.</p>
      </div>
    </div>
    <div class="card form-card" style="margin-bottom:20px;">{selector_form}</div>
    {window_panel}
    {content_html}
    <style>
      table td, table th {{ padding:8px 10px; }}
      table tbody tr:nth-child(even) {{ background:#f9fafb; }}
      table input[type=number] {{ border:1px solid #DDE0E3;border-radius:5px;
                                  padding:5px 8px;font-size:14px; }}
      table input[type=number]:focus {{ border-color:#2D323B;outline:none; }}
    </style>"""

    return layout("Group Hub", body, user=coach, active_nav="group_hub")


def session_sheet_pdf(label_display, month_str, group_name, athletes, games_fields,
                      prefilled=None):
    """Generate a per-athlete portrait PDF recording sheet — one page per athlete.
    games_fields: list of {{'game': game_dict, 'fields': [field_dict, ...]}}
    athletes:     list of name strings (may include empty strings for blank sheets)
    prefilled:    optional dict {{athlete_name: {{game_key: {{field_key: value}}}}}}
                  — existing values are printed in gold; blank fields stay empty.
    """
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, PageBreak)
    from reportlab.lib.styles import ParagraphStyle

    prefilled = prefilled or {}

    JAG_NAVY   = colors.HexColor("#2D323B")
    JAG_GOLD   = colors.HexColor("#F0A82E")
    JAG_BG     = colors.HexColor("#F3F4F5")
    JAG_BORDER = colors.HexColor("#DDE0E3")
    GOLD_LIGHT = colors.HexColor("#FFF8E7")
    GREEN_LIGHT= colors.HexColor("#D1FAE5")
    WHITE      = colors.white
    MUTED      = colors.HexColor("#6E737B")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=14*mm, rightMargin=14*mm,
                            topMargin=12*mm, bottomMargin=12*mm)

    page_w = A4[0] - 28*mm   # usable width

    hdr_title   = ParagraphStyle("ht",  fontSize=13, fontName="Helvetica-Bold", textColor=WHITE)
    hdr_sub     = ParagraphStyle("hs",  fontSize=9,  fontName="Helvetica",      textColor=JAG_GOLD)
    name_style  = ParagraphStyle("ns",  fontSize=18, fontName="Helvetica-Bold", textColor=JAG_NAVY,
                                  spaceBefore=6, spaceAfter=2)
    name_label  = ParagraphStyle("nl",  fontSize=9,  fontName="Helvetica",      textColor=MUTED,
                                  spaceAfter=8)
    game_hdr    = ParagraphStyle("gh",  fontSize=10, fontName="Helvetica-Bold", textColor=WHITE)
    game_done   = ParagraphStyle("gd",  fontSize=8,  fontName="Helvetica-Bold", textColor=JAG_GOLD)
    field_lbl   = ParagraphStyle("fl",  fontSize=9,  fontName="Helvetica",      textColor=JAG_NAVY)
    unit_lbl    = ParagraphStyle("ul",  fontSize=8,  fontName="Helvetica",      textColor=MUTED)
    val_filled  = ParagraphStyle("vf",  fontSize=11, fontName="Helvetica-Bold", textColor=JAG_NAVY,
                                  alignment=1)  # centred
    val_partial = ParagraphStyle("vp",  fontSize=8,  fontName="Helvetica",      textColor=MUTED,
                                  alignment=1)

    def _athlete_story(athlete_name):
        s = []
        athlete_data = prefilled.get(athlete_name, {})  # {game_key: {field_key: value}}

        # ---- Top header bar ----
        subtitle = f"{month_str}"
        if group_name:
            subtitle += f"  ·  {group_name}"
        hdr = Table([[
            Paragraph(label_display, hdr_title),
            Paragraph(subtitle, hdr_sub),
        ]], colWidths=[page_w * 0.6, page_w * 0.4])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), JAG_NAVY),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("ALIGN",         (1,0), (1,0),   "RIGHT"),
        ]))
        s.append(hdr)
        s.append(Spacer(1, 3*mm))

        # ---- Athlete name block ----
        display = athlete_name if athlete_name else "______________________________"
        s.append(Paragraph(display, name_style))
        s.append(Paragraph("Athlete Name", name_label))

        # ---- One table per game ----
        for gf in games_fields:
            game   = gf.get("game")
            fields = gf.get("fields", [])
            if not game or not fields:
                continue

            game_results = athlete_data.get(game["key"], {})
            filled_count = sum(1 for f in fields if game_results.get(f["key"], "") != "")
            all_done     = filled_count == len(fields)
            any_done     = filled_count > 0

            # Game name header — show "✓ Complete" badge when all fields filled
            if all_done and athlete_name:
                game_hdr_row = [[
                    Paragraph(game["name"], game_hdr),
                    Paragraph("✓  Complete", game_done),
                ]]
                game_tbl = Table(game_hdr_row, colWidths=[page_w * 0.75, page_w * 0.25])
                game_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0), (-1,-1), JAG_NAVY),
                    ("LEFTPADDING",   (0,0), (-1,-1), 8),
                    ("RIGHTPADDING",  (0,0), (-1,-1), 8),
                    ("TOPPADDING",    (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                    ("ALIGN",         (1,0), (1,0),   "RIGHT"),
                    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ]))
            else:
                game_tbl = Table([[Paragraph(game["name"], game_hdr)]], colWidths=[page_w])
                game_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0), (-1,-1), JAG_NAVY),
                    ("LEFTPADDING",   (0,0), (-1,-1), 8),
                    ("TOPPADDING",    (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ]))
            s.append(game_tbl)

            # Fields: label col | value col
            label_w = page_w * 0.55
            value_w = page_w * 0.45
            rows = []
            filled_flags = []   # parallel list: True if this row has a value
            for f in fields:
                unit_txt = (f" ({f['unit']})" if f.get("unit")
                            else (" (seconds)" if f.get("type") == "time" else ""))
                lbl_para = Paragraph(f["label"], field_lbl)
                if unit_txt:
                    lbl_cell = [lbl_para, Paragraph(unit_txt, unit_lbl)]
                else:
                    lbl_cell = lbl_para

                existing_val = game_results.get(f["key"], "")
                if existing_val != "" and athlete_name:
                    val_cell = Paragraph(str(existing_val), val_filled)
                    filled_flags.append(True)
                else:
                    val_cell = ""
                    filled_flags.append(False)

                rows.append([lbl_cell, val_cell])

            data_tbl = Table(rows, colWidths=[label_w, value_w],
                             rowHeights=[9*mm] * len(rows))
            style_cmds = [
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ("GRID",          (0,0), (-1,-1), 0.5, JAG_BORDER),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
                ("RIGHTPADDING",  (0,0), (-1,-1), 6),
                ("TOPPADDING",    (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("BACKGROUND",    (0,0), (0,-1),  JAG_BG),
            ]
            for i, is_filled in enumerate(filled_flags):
                if is_filled:
                    # Gold background for pre-filled values
                    style_cmds.append(("BACKGROUND", (1,i), (1,i), GOLD_LIGHT))
                elif i % 2 == 1:
                    style_cmds.append(("BACKGROUND", (1,i), (1,i), colors.HexColor("#FAFAFA")))

            data_tbl.setStyle(TableStyle(style_cmds))
            s.append(data_tbl)
            s.append(Spacer(1, 3*mm))

        # ---- Legend (only on pages with pre-filled data) ----
        if athlete_name and athlete_data:
            legend_style = ParagraphStyle("leg", fontSize=7, fontName="Helvetica",
                                           textColor=MUTED, spaceBefore=4)
            s.append(Paragraph(
                "<font color='#F0A82E'>■</font>  Gold = already recorded   "
                "□  White = still to complete",
                legend_style,
            ))

        return s

    story = []
    sheets = athletes if athletes else [""]
    for i, name in enumerate(sheets):
        story.extend(_athlete_story(name))
        if i < len(sheets) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buf.getvalue()


# Statistics & Reports landing page + printable reports
# ---------------------------------------------------------------------------

def reports_landing_page(coach, groups, orgs=None, sports=None):
    """Hub page: links to existing stats pages + new printable reports."""
    orgs = orgs or []
    sports = sports or []

    group_opts = '<option value="">— All groups in org —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )
    org_opts = '<option value="">— No org filter —</option>' + "".join(
        f'<option value="{o["id"]}">{esc(o["name"])}</option>' for o in orgs
    )
    sport_opts = '<option value="">— All sports —</option>' + "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>' for s in sports
    )

    def _report_card(icon, title, desc, report_type, btn_label="Generate Report"):
        return f"""
        <div style="background:var(--jag-card);border:1px solid var(--jag-border);border-radius:12px;padding:24px;display:flex;flex-direction:column;gap:12px;">
          <div style="font-size:32px;">{icon}</div>
          <h2 style="margin:0;font-size:17px;font-weight:700;color:var(--jag-navy);">{title}</h2>
          <p style="margin:0;font-size:13px;color:var(--jag-muted);line-height:1.5;">{desc}</p>
          <div style="margin-top:auto;">
            <button class="btn btn-primary" onclick="openReport('{report_type}')" style="width:100%;">{btn_label}</button>
          </div>
        </div>"""

    body = f"""
    <div class="page-head">
      <div>
        <h1>Statistics &amp; Reports</h1>
        <p class="muted">View live statistics or generate printable reports for coaches and organisations.</p>
      </div>
    </div>

    <div style="background:var(--jag-card);border:1px solid var(--jag-border);border-radius:10px;padding:20px;margin-bottom:32px;">
      <h3 style="margin:0 0 14px;font-size:14px;font-weight:700;color:var(--jag-navy);">Report Scope</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;align-items:end;">
        <div>
          <label style="font-size:12px;font-weight:700;color:var(--jag-muted);display:block;margin-bottom:4px;">Organisation</label>
          <select id="report-org" style="width:100%;" onchange="document.getElementById('report-group').value='';">{org_opts}</select>
        </div>
        <div>
          <label style="font-size:12px;font-weight:700;color:var(--jag-muted);display:block;margin-bottom:4px;">Group <span style="font-weight:400;">(overrides org)</span></label>
          <select id="report-group" style="width:100%;" onchange="if(this.value)document.getElementById('report-org').value='';">{group_opts}</select>
        </div>
        <div>
          <label style="font-size:12px;font-weight:700;color:var(--jag-muted);display:block;margin-bottom:4px;">Sport <span style="font-weight:400;">(optional)</span></label>
          <select id="report-sport" style="width:100%;">{sport_opts}</select>
        </div>
      </div>
      <p style="font-size:12px;color:var(--jag-muted);margin-top:12px;">Select an organisation OR a specific group, then optionally filter by sport. Click a report button below to generate.</p>
    </div>

    <h2 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--jag-muted);margin-bottom:16px;">Printable Reports</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-bottom:40px;">
      {_report_card("📋", "Athlete Baseline Report",
          "All athletes in the selected scope with their Round 1 (baseline) scores. Print and share at the start of a programme.",
          "baseline")}
      {_report_card("📈", "Round 2 Progress Report",
          "Side-by-side Round 1 vs Round 2 scores with % improvement, colour-coded green/red. Only athletes with 2+ sessions appear.",
          "progress")}
      {_report_card("✅", "Test Completion Sheet",
          "At-a-glance view of which measurement tests each athlete has completed. Shows a fraction (e.g. 4/6 fields) per game. Batch-printable by group or org.",
          "completion")}
    </div>

    <h2 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--jag-muted);margin-bottom:16px;">Live Statistics</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;">
      {_report_card("📊", "Achievement Statistics Overview",
          "Live view of group averages across all measurement rounds, with sport filter and admin overall table.",
          "stats", "View Statistics")}
    </div>

    <script>
    function openReport(type) {{
      if (type === 'stats') {{ window.location = '/coach/progress'; return; }}
      var group = document.getElementById('report-group').value;
      var org   = document.getElementById('report-org').value;
      var sport = document.getElementById('report-sport').value;
      if (!group && !org) {{ alert('Please select an organisation or group first.'); return; }}
      var params = [];
      if (group) params.push('group_id=' + group);
      else if (org) params.push('org_id=' + org);
      if (sport) params.push('sport=' + encodeURIComponent(sport));
      var url = '/coach/reports/' + type + '?' + params.join('&');
      if (type === 'completion') {{ window.location = url; }}
      else {{ window.open(url, '_blank'); }}
    }}
    </script>
    """
    return layout("Statistics & Reports", body, user=coach, active_nav="progress")


def completion_report_page(coach, group, athletes_data):
    """Printable test completion sheet — one row per athlete, one column per game."""
    from constants import games_for_max_level
    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group.get("name", "Group")

    # Build game list: (key, short_name, total_non_computed_fields) — Level 1 only
    games_info = []
    for section in games_for_max_level(1):
        for game in section["games"]:
            total = len(game.get("fields", []))
            # Abbreviate long names for column headers
            name = game["name"]
            games_info.append((game["key"], name, total))

    # Table header
    th_games = "".join(
        f'<th style="text-align:center;min-width:70px;font-size:9px;line-height:1.3;">{esc(n)}</th>'
        for _, n, _ in games_info
    )
    thead = (
        f'<tr>'
        f'<th class="left" style="min-width:36px;">#</th>'
        f'<th class="left" style="min-width:150px;">Athlete</th>'
        f'{th_games}'
        f'<th style="min-width:70px;">Games Done</th>'
        f'</tr>'
    )

    rows_html = ""
    for athlete, sessions in athletes_data:
        an = esc(athlete.get("athlete_number") or "—")
        name = esc(athlete.get("name") or "")

        # Aggregate all results across all sessions for this athlete
        recorded = {}  # game_key → set of field_keys with a value
        for s in sessions:
            for (gk, fk), val in s["results"].items():
                if val is not None:
                    recorded.setdefault(gk, set()).add(fk)

        game_tds = ""
        completed_count = 0
        for gk, gname, total_fields in games_info:
            n = len(recorded.get(gk, set()))
            if n > 0:
                completed_count += 1
                cell = f"{n}/{total_fields}" if total_fields > 1 else "✓"
                game_tds += f'<td style="text-align:center;color:#1a7a3a;font-weight:700;">{cell}</td>'
            else:
                game_tds += '<td style="text-align:center;color:#bbb;">—</td>'

        total_games = len(games_info)
        summary = f"{completed_count}/{total_games}"
        if completed_count == total_games:
            sc = "#1a7a3a"
        elif completed_count > 0:
            sc = "#e67e22"
        else:
            sc = "#c0392b"

        rows_html += (
            f'<tr>'
            f'<td style="color:#888;">{an}</td>'
            f'<td style="font-weight:600;">{name}</td>'
            f'{game_tds}'
            f'<td style="text-align:center;font-weight:700;color:{sc};">{summary}</td>'
            f'</tr>'
        )

    if not rows_html:
        colspan = 2 + len(games_info) + 1
        rows_html = f'<tr><td colspan="{colspan}" style="text-align:center;color:#888;padding:20px;">No athletes found.</td></tr>'

    table_html = f'<table><thead>{thead}</thead><tbody>{rows_html}</tbody></table>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Test Completion Sheet — {esc(group_name)}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;color-adjust:exact;}}
  body{{font-family:Arial,Helvetica,sans-serif;background:#fff;color:#2D323B;padding:20px;font-size:11px;}}
  .no-print{{margin-bottom:14px;}}
  .header{{display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:12px;border-bottom:3px solid #F0A82E;}}
  .header-logo{{background:#2D323B;border-radius:7px;padding:8px;flex-shrink:0;}}
  h1{{font-size:18px;font-weight:800;color:#2D323B;}}
  .sub{{font-size:11px;color:#888;margin-top:3px;}}
  table{{width:100%;border-collapse:collapse;margin-top:0;}}
  th{{background:#2D323B;color:#fff;padding:6px 8px;text-align:center;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;border:1px solid #444;}}
  th.left{{text-align:left;}}
  td{{padding:5px 8px;border:1px solid #ddd;vertical-align:middle;font-size:10px;}}
  tr:nth-child(even) td{{background:#F3F4F5;}}
  .done{{color:#1a7a3a;font-weight:700;text-align:center;}}
  .none{{color:#bbb;text-align:center;}}
  .sum-all{{color:#1a7a3a;font-weight:700;text-align:center;}}
  .sum-part{{color:#e67e22;font-weight:700;text-align:center;}}
  .sum-zero{{color:#c0392b;font-weight:700;text-align:center;}}
  @media print{{
    .no-print{{display:none!important;}}
    body{{
      padding:0;
      -webkit-transform:scale(0.48);
      transform:scale(0.48);
      -webkit-transform-origin:0 0;
      transform-origin:0 0;
      width:208%;
    }}
    tr{{page-break-inside:avoid;}}
    th{{background:#2D323B!important;color:#fff!important;-webkit-print-color-adjust:exact!important;}}
    tr:nth-child(even) td{{background:#f3f4f5!important;-webkit-print-color-adjust:exact!important;}}
  }}
</style>
</head>
<body>
  <div class="no-print">
    <button onclick="window.print()" style="background:#2D323B;color:#fff;border:none;border-radius:6px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;">&#128196; Print / Save as PDF</button>
    <button onclick="window.close()" style="background:#f3f4f5;border:1px solid #ddd;border-radius:6px;padding:8px 18px;font-size:13px;cursor:pointer;margin-left:6px;">Close</button>
    <span style="font-size:11px;color:#888;margin-left:10px;">Tip: select <strong>Landscape</strong> in your print dialog for best fit.</span>
  </div>
  <div class="header">
    <div class="header-logo">
      <svg width="22" height="22" fill="#F0A82E" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#F0A82E" stroke-width="1.5" fill="none"/></svg>
    </div>
    <div>
      <h1>Test Completion Sheet</h1>
      <div class="sub">{esc(group_name)} &nbsp;·&nbsp; Generated {today} &nbsp;·&nbsp; Just A Game</div>
    </div>
  </div>
  {table_html}
</body>
</html>"""


def completion_report_pdf(group, athletes_data):
    """Generate a landscape PDF of the test completion sheet using reportlab."""
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from constants import games_for_max_level

    JAG_NAVY  = colors.HexColor("#2D323B")
    JAG_GOLD  = colors.HexColor("#F0A82E")
    JAG_LIGHT = colors.HexColor("#F3F4F5")
    GREEN     = colors.HexColor("#1a7a3a")
    AMBER     = colors.HexColor("#e67e22")
    RED       = colors.HexColor("#c0392b")
    GREY      = colors.HexColor("#aaaaaa")

    buf = io.BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buf, pagesize=page_size,
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16, textColor=JAG_NAVY)
    sub_style   = ParagraphStyle("sub",   fontName="Helvetica",      fontSize=9,  textColor=colors.grey)
    hdr_style   = ParagraphStyle("hdr",   fontName="Helvetica-Bold", fontSize=7,  textColor=colors.white, alignment=TA_CENTER, leading=9)
    cell_style  = ParagraphStyle("cell",  fontName="Helvetica",      fontSize=8,  alignment=TA_CENTER)

    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group.get("name", "Group")

    # Build game info list (Level 1 only)
    games_info = []
    for section in games_for_max_level(1):
        for game in section["games"]:
            total = len(game.get("fields", []))
            games_info.append((game["key"], game["name"], total))

    # Build table data
    # Header row
    header = (
        [Paragraph("#", hdr_style), Paragraph("Athlete", hdr_style)] +
        [Paragraph(n, hdr_style) for _, n, _ in games_info] +
        [Paragraph("Done", hdr_style)]
    )
    table_data = [header]

    for athlete, sessions in athletes_data:
        an   = str(athlete.get("athlete_number") or "—")
        name = str(athlete.get("name") or "")

        recorded = {}
        for s in sessions:
            for (gk, fk), val in s["results"].items():
                if val is not None:
                    recorded.setdefault(gk, set()).add(fk)

        row = [an, name]
        completed_count = 0
        for gk, gname, total_fields in games_info:
            n = len(recorded.get(gk, set()))
            if n > 0:
                completed_count += 1
                cell = f"{n}/{total_fields}" if total_fields > 1 else "✓"
            else:
                cell = "—"
            row.append(cell)

        total_games = len(games_info)
        row.append(f"{completed_count}/{total_games}")
        table_data.append(row)

    # Column widths: #=10mm, Name=40mm, games share remaining, Done=16mm
    page_w = page_size[0] - 20*mm  # subtract margins
    fixed  = 10*mm + 40*mm + 16*mm
    game_w = max(14*mm, (page_w - fixed) / max(len(games_info), 1))
    col_widths = [10*mm, 40*mm] + [game_w]*len(games_info) + [16*mm]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Base style
    style_cmds = [
        ("BACKGROUND",    (0,0), (-1,0),  JAG_NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  7),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("ALIGN",         (1,0), (1,-1),  "LEFT"),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, JAG_LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 3),
        ("RIGHTPADDING",  (0,0), (-1,-1), 3),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("WORDWRAP",      (0,0), (-1,-1), "CJK"),
    ]

    # Colour the game cells per-row
    for ri, (athlete, sessions) in enumerate(athletes_data, start=1):
        recorded = {}
        for s in sessions:
            for (gk, fk), val in s["results"].items():
                if val is not None:
                    recorded.setdefault(gk, set()).add(fk)
        completed_count = sum(1 for gk,_,_ in games_info if recorded.get(gk))
        total_games = len(games_info)
        for ci, (gk, _, _) in enumerate(games_info, start=2):
            if recorded.get(gk):
                style_cmds.append(("TEXTCOLOR", (ci,ri), (ci,ri), GREEN))
                style_cmds.append(("FONTNAME",  (ci,ri), (ci,ri), "Helvetica-Bold"))
            else:
                style_cmds.append(("TEXTCOLOR", (ci,ri), (ci,ri), GREY))
        # Summary column colour
        sc_col = len(games_info) + 2
        if completed_count == total_games:
            style_cmds.append(("TEXTCOLOR", (sc_col,ri), (sc_col,ri), GREEN))
        elif completed_count > 0:
            style_cmds.append(("TEXTCOLOR", (sc_col,ri), (sc_col,ri), AMBER))
        else:
            style_cmds.append(("TEXTCOLOR", (sc_col,ri), (sc_col,ri), RED))
        style_cmds.append(("FONTNAME", (sc_col,ri), (sc_col,ri), "Helvetica-Bold"))

    tbl.setStyle(TableStyle(style_cmds))

    story = [
        Paragraph("Test Completion Sheet", title_style),
        Paragraph(f"{group_name}  ·  Generated {today}  ·  Just A Game", sub_style),
        Spacer(1, 4*mm),
        tbl,
    ]
    doc.build(story)
    return buf.getvalue()


_STOPWORDS = {"the", "and", "for", "with", "from", "into", "onto", "over",
              "under", "that", "this", "then", "than", "each", "your", "their"}

def _sig_words(text):
    """Return set of significant lowercase words (>2 chars, not stopwords)."""
    words = _re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}

def _build_game_so_map(resources):
    """
    Build a dict: game_key → self_organisation phrase, by loose-matching each
    resource name against every MEASUREMENT_GAMES game name.
    A match is declared when ≥1 significant word overlaps between the resource
    name and the game name (after normalisation).
    Resources without a self_organisation value are skipped.
    When multiple resources match the same game, the one with the most word
    overlap wins.
    """
    from constants import all_active_measurement_games, all_sport_games, SPORT_SPECIFIC_GAMES
    result = {}  # game_key → (overlap_count, self_org phrase)

    all_games = all_active_measurement_games()
    for sport_sections in SPORT_SPECIFIC_GAMES.values():
        for section in sport_sections:
            all_games.extend(section["games"])

    for r in resources:
        so = (r.get("self_organisation") or "").strip()
        if not so:
            continue
        res_words = _sig_words(r.get("name") or "")
        for game in all_games:
            game_words = _sig_words(game["name"])
            overlap = len(res_words & game_words)
            if overlap >= 1:
                prev_overlap, _ = result.get(game["key"], (0, ""))
                if overlap > prev_overlap:
                    result[game["key"]] = (overlap, so)

    return {gk: so for gk, (_, so) in result.items()}


def _report_html_shell(title, subtitle, group_name, body_content, today):
    """Shared outer HTML for printable reports."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} — {group_name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:Inter,system-ui,sans-serif;background:#fff;color:#2D323B;padding:24px;font-size:12px;}}
  h1{{font-size:20px;font-weight:800;}}
  table{{width:100%;border-collapse:collapse;margin-top:16px;}}
  th{{background:#2D323B;color:#fff;padding:7px 10px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;}}
  td{{padding:6px 10px;border-bottom:1px solid #e8e9ea;vertical-align:top;}}
  tr:nth-child(even) td{{background:#F3F4F5;}}
  .imp-pos{{color:#1a7a3a;font-weight:700;}}
  .imp-neg{{color:#c0392b;font-weight:700;}}
  .imp-zero{{color:#888;}}
  .no-print{{}}
  @media print{{
    *{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;}}
    .no-print{{display:none!important;}}
    body{{padding:10px;}}
    table{{page-break-inside:auto;}}
    tr{{page-break-inside:avoid;}}
    th{{background:#2D323B!important;color:#fff!important;}}
    tr:nth-child(even) td{{background:#F3F4F5!important;}}
  }}
</style>
</head>
<body>
  <div class="no-print" style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">
    <button onclick="window.print()" style="background:#2D323B;color:#fff;border:none;border-radius:6px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;">&#128196; Print / Save as PDF</button>
    <button onclick="window.close()" style="background:#F3F4F5;border:1px solid #ddd;border-radius:6px;padding:8px 18px;font-size:13px;cursor:pointer;">Close</button>
  </div>
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;padding-bottom:14px;border-bottom:3px solid #F0A82E;">
    <div style="background:#2D323B;border-radius:8px;padding:10px;flex-shrink:0;">
      <svg width="24" height="24" fill="#F0A82E" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
    </div>
    <div>
      <h1>{title}</h1>
      <p style="font-size:12px;color:#888;margin-top:3px;">{subtitle} &nbsp;·&nbsp; Generated {today} &nbsp;·&nbsp; Just A Game</p>
    </div>
  </div>
  {body_content}
</body>
</html>"""


def baseline_report_page(coach, group, athletes_data, resources=None):
    """
    athletes_data: list of (athlete_row, sessions_list) where sessions_list is
    ordered most-recent-first; we use sessions[-1] as the baseline.
    resources: list of resource rows (for self-organisation tag matching).
    """
    from constants import find_any_game

    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group["name"] if group else "All Athletes"
    so_map = _build_game_so_map(resources or [])

    # Collect all (game_key, field_key) pairs that appear in any baseline session
    used_cols = []  # ordered list of (game_key, field_key, label)
    seen = set()
    for athlete, sessions in athletes_data:
        if not sessions:
            continue
        baseline = sessions[-1]  # oldest
        for (gk, fk), val in baseline["results"].items():
            if (gk, fk) not in seen:
                seen.add((gk, fk))
                game = find_any_game(gk)
                if game:
                    all_fields = {f["key"]: f["label"] for f in game.get("fields", []) + game.get("computed", [])}
                    label = all_fields.get(fk, fk)
                    used_cols.append((gk, fk, f"{game['name']} — {label}"))

    # Sort used_cols by game order in MEASUREMENT_GAMES
    col_order = {}
    idx = 0
    for section in active_measurement_games():
        for game in section["games"]:
            for f in game.get("fields", []) + game.get("computed", []):
                col_order[(game["key"], f["key"])] = idx
                idx += 1
    used_cols.sort(key=lambda c: col_order.get((c[0], c[1]), 9999))

    if not used_cols:
        body_content = '<p style="color:#888;margin-top:20px;">No baseline scores recorded for any athletes in this group yet.</p>'
        return _report_html_shell("Athlete Baseline Report", group_name, group_name, body_content, today)

    def _th(gk, label):
        so = so_map.get(gk, "")
        so_line = f'<div style="font-size:9px;color:#F0A82E;font-weight:600;margin-top:3px;white-space:normal;line-height:1.3;">{esc(so)}</div>' if so else ""
        return f'<th style="white-space:nowrap;">{esc(label)}{so_line}</th>'

    th_cols = "".join(_th(gk, label) for gk, fk, label in used_cols)
    header = f'<tr><th>#</th><th>Athlete</th>{th_cols}<th>Date</th></tr>'

    rows = ""
    for athlete, sessions in athletes_data:
        if not sessions:
            continue
        baseline = sessions[-1]
        tds = "".join(
            f'<td>{baseline["results"].get((gk, fk), "")}</td>'
            for gk, fk, _ in used_cols
        )
        rows += f'<tr><td style="color:#888;">{esc(athlete.get("athlete_number") or "")}</td><td style="font-weight:600;">{esc(athlete["name"])}</td>{tds}<td style="color:#888;">{esc(baseline["date"])}</td></tr>'

    if not rows:
        body_content = '<p style="color:#888;margin-top:20px;">No athletes with baseline data found.</p>'
    else:
        so_note = ' <span style="color:#F0A82E;">Gold text under each column header = self-organisation focus for that activity.</span>' if so_map else ""
        body_content = f'<p style="font-size:12px;color:#555;margin-bottom:8px;">Round 1 (baseline) scores for <strong>{esc(group_name)}</strong>.{so_note}</p><div style="overflow-x:auto;"><table><thead>{header}</thead><tbody>{rows}</tbody></table></div>'

    return _report_html_shell("Athlete Baseline Report", group_name, group_name, body_content, today)


def progress_report_page(coach, group, athletes_data, resources=None):
    """
    athletes_data: list of (athlete_row, sessions_list) ordered most-recent-first.
    Uses sessions[-1] = R1 (baseline), sessions[-2] = R2 (second measurement).
    Only athletes with >= 2 sessions appear.
    resources: list of resource rows (for self-organisation tag matching).
    """
    from constants import find_any_game

    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group["name"] if group else "All Athletes"
    so_map = _build_game_so_map(resources or [])

    eligible = [(a, s) for a, s in athletes_data if len(s) >= 2]

    if not eligible:
        body_content = '<p style="color:#888;margin-top:20px;">No athletes with 2 or more test sessions found in this group.</p>'
        return _report_html_shell("Round 2 Progress Report", group_name, group_name, body_content, today)

    # Collect used columns from R1 or R2 of any eligible athlete
    used_cols = []
    seen = set()
    for athlete, sessions in eligible:
        r1 = sessions[-1]["results"]
        r2 = sessions[-2]["results"]
        for (gk, fk) in list(r1.keys()) + list(r2.keys()):
            if (gk, fk) not in seen:
                seen.add((gk, fk))
                game = find_any_game(gk)
                if game:
                    all_fields = {f["key"]: f for f in game.get("fields", []) + game.get("computed", [])}
                    field_def = all_fields.get(fk)
                    label = field_def["label"] if field_def else fk
                    ftype = field_def["type"] if field_def else "number"
                    used_cols.append((gk, fk, f"{game['name']} — {label}", ftype))

    col_order = {}
    idx = 0
    for section in active_measurement_games():
        for game in section["games"]:
            for f in game.get("fields", []) + game.get("computed", []):
                col_order[(game["key"], f["key"])] = idx
                idx += 1
    used_cols.sort(key=lambda c: col_order.get((c[0], c[1]), 9999))

    def pct_class(pct):
        if pct is None: return "imp-zero", "—"
        if pct > 0: return "imp-pos", f"+{pct:.1f}%"
        if pct < 0: return "imp-neg", f"{pct:.1f}%"
        return "imp-zero", "0.0%"

    # For each col: build 3 sub-columns R1 / R2 / Δ%
    def _progress_th(gk, label):
        so = so_map.get(gk, "")
        so_line = f'<div style="font-size:9px;color:#F0A82E;font-weight:600;margin-top:3px;white-space:normal;line-height:1.3;">{esc(so)}</div>' if so else ""
        return f'<th colspan="3" style="border-left:2px solid rgba(255,255,255,0.2);white-space:nowrap;">{esc(label)}{so_line}</th>'

    th_cols = "".join(
        _progress_th(gk, label)
        for gk, _, label, _ in used_cols
    )
    th_sub = "".join(
        '<th style="font-size:9px;background:#3d4451;border-left:2px solid rgba(255,255,255,0.15);">R1</th>'
        '<th style="font-size:9px;background:#3d4451;">R2</th>'
        '<th style="font-size:9px;background:#3d4451;">Δ%</th>'
        for _ in used_cols
    )
    header = f'<tr><th rowspan="2">#</th><th rowspan="2">Athlete</th>{th_cols}<th rowspan="2" style="border-left:2px solid rgba(255,255,255,0.2);">Overall Δ%</th></tr><tr>{th_sub}</tr>'

    rows = ""
    for athlete, sessions in eligible:
        r1 = sessions[-1]["results"]
        r2 = sessions[-2]["results"]
        field_pcts = []
        tds = ""
        for gk, fk, _, ftype in used_cols:
            v1 = r1.get((gk, fk))
            v2 = r2.get((gk, fk))
            v1_s = str(v1) if v1 is not None else "—"
            v2_s = str(v2) if v2 is not None else "—"
            pct = None
            if v1 is not None and v2 is not None and v1 != 0:
                raw = ((v2 - v1) / abs(v1)) * 100
                # For time fields, lower is better → flip sign
                pct = -raw if ftype == "time" else raw
                field_pcts.append(pct)
            css, pct_s = pct_class(pct)
            border = "border-left:2px solid #e0e0e0;"
            tds += (
                f'<td style="{border}">{v1_s}</td>'
                f'<td>{v2_s}</td>'
                f'<td class="{css}">{pct_s}</td>'
            )

        overall_pct = sum(field_pcts) / len(field_pcts) if field_pcts else None
        o_css, o_s = pct_class(overall_pct)
        rows += (
            f'<tr><td style="color:#888;">{esc(athlete.get("athlete_number") or "")}</td>'
            f'<td style="font-weight:600;">{esc(athlete["name"])}</td>'
            f'{tds}'
            f'<td class="{o_css}" style="font-size:13px;border-left:2px solid #ccc;">{o_s}</td></tr>'
        )

    r1_date = eligible[0][1][-1]["date"] if eligible else ""
    r2_date = eligible[0][1][-2]["date"] if eligible else ""
    so_note = ' <span style="color:#F0A82E;">Gold text under each column header = self-organisation focus.</span>' if so_map else ""
    body_content = f"""
    <p style="font-size:12px;color:#555;margin-bottom:8px;">
      Progress from Round 1 ({esc(r1_date)}) to Round 2 ({esc(r2_date)}) for <strong>{esc(group_name)}</strong>.
      <span style="color:#1a7a3a;font-weight:700;">Green</span> = improvement &nbsp;
      <span style="color:#c0392b;font-weight:700;">Red</span> = decline. Time fields: lower score = improvement.{so_note}
    </p>
    <div style="overflow-x:auto;"><table><thead>{header}</thead><tbody>{rows}</tbody></table></div>"""

    return _report_html_shell("Round 2 Progress Report", group_name, group_name, body_content, today)


def group_session_page(coach, participants, groups=None, session_types=None):
    """Rapid-fire session entry: select group → select athlete → select game → fields appear → quick-save.
    All saves for the same athlete+date land in one session (find-or-create).
    """
    import json as _json
    groups = groups or []

    # Group options
    group_opts = '<option value="">— All athletes —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )

    # Athlete options — each carries data-group attribute for JS filtering
    athlete_opts = '<option value="">— Select athlete —</option>' + "".join(
        f'<option value="{p["id"]}" data-group="{p.get("group_id") or ""}">{esc(p["name"])}</option>'
        for p in participants
    )

    # Field options: each individual field as its own option, grouped under the game name.
    # Option value = "game_key||field_key" so JS can split them apart.
    field_opts = '<option value="">— Select field —</option>'
    fields_data = {}   # composite_key -> {game_key, game_name, field_key, label, type}

    for section in active_measurement_games():
        for game in section["games"]:
            field_opts += f'<optgroup label="{esc(game["name"])}">'
            for f in game["fields"]:
                composite = f'{game["key"]}||{f["key"]}'
                field_opts += f'<option value="{esc(composite)}">{esc(f["label"])}</option>'
                fields_data[composite] = {
                    "game_key":   game["key"],
                    "game_name":  game["name"],
                    "field_key":  f["key"],
                    "label":      f["label"],
                    "type":       f["type"],
                }
            field_opts += '</optgroup>'

    # Sport-specific fields for JS (keyed by sport → flat list of composite-key entries)
    sport_fields_data = {}
    for sport, sport_sections in SPORT_SPECIFIC_GAMES.items():
        sport_fields_data[sport] = []
        for section in sport_sections:
            for game in section["games"]:
                for f in game["fields"]:
                    composite = f'{game["key"]}||{f["key"]}'
                    entry = {
                        "composite":  composite,
                        "game_key":   game["key"],
                        "game_name":  game["name"],
                        "field_key":  f["key"],
                        "label":      f["label"],
                        "type":       f["type"],
                    }
                    fields_data[composite] = entry
                    sport_fields_data[sport].append(entry)

    # Sport selector options for the checkbox UI
    qs_sport_opts = "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>'
        for s in SPORT_SPECIFIC_GAMES
    )

    fields_js      = _json.dumps(fields_data)
    sport_fields_js = _json.dumps(sport_fields_data)
    today = __import__("datetime").date.today().isoformat()
    show_group_filter = "block" if groups else "none"

    body = f"""
    <div class="page-head"><h1>Record Session</h1></div>

    <!-- Recording-for banner: hidden until athlete selected -->
    <div id="qs-banner" style="display:none;position:sticky;top:0;z-index:100;
         background:#2D323B;color:#F0A82E;padding:10px 20px;margin-bottom:16px;
         border-radius:8px;display:flex;align-items:center;justify-content:space-between;
         flex-wrap:wrap;gap:8px;font-size:14px;font-weight:700;">
      <span>&#128203; Recording for: <span id="qs-banner-name" style="color:#fff;"></span></span>
      <span id="qs-progress-badge"
            style="background:#F0A82E;color:#2D323B;border-radius:999px;
                   padding:3px 12px;font-size:12px;font-weight:800;">0 saved</span>
    </div>

    <div class="card form-card" style="max-width:560px;">
      {_session_label_pickers()}

      <div id="qs-group-wrap" style="display:{show_group_filter}; margin-bottom:16px;">
        <label for="qs-group">Group</label>
        <select id="qs-group">{group_opts}</select>
      </div>

      <label for="qs-athlete">Athlete</label>
      <select id="qs-athlete" style="margin-bottom:16px;">{athlete_opts}</select>

      <div style="padding-top:14px; border-top:1px solid var(--jag-border); margin-bottom:12px;">
        <label style="display:flex; align-items:center; gap:10px; cursor:pointer; margin:0 0 12px; font-size:14px; font-weight:600;">
          <input type="checkbox" id="qs-sport-check" style="width:auto; margin:0;" />
          Sport Specific Testing
        </label>
        <div id="qs-sport-wrap" style="display:none; margin-bottom:12px;">
          <label for="qs-sport-select" style="font-size:13px; font-weight:600; margin:0 0 6px;">Select Sport</label>
          <select id="qs-sport-select" style="max-width:220px;">
            <option value="">— Select sport —</option>
            {qs_sport_opts}
          </select>
        </div>
      </div>

      <label for="qs-field">Measurement Field</label>
      <select id="qs-field" style="margin-bottom:16px;">{field_opts}</select>

      <div id="qs-fields" style="margin-top:4px;"></div>
    </div>

    <div class="card" style="max-width:560px; margin-top:16px;">
      <h3 style="margin:0 0 10px; font-size:15px; color:#2D323B;">Session Log</h3>
      <div id="qs-log" style="font-size:13px; color:var(--jag-muted);">Nothing saved yet.</div>
    </div>

    <script>
    (function() {{
      var FIELDS        = {fields_js};
      var SPORT_FIELDS  = {sport_fields_js};
      var saveUrl = '/coach/session/save';

      var groupEl      = document.getElementById('qs-group');
      var athleteEl    = document.getElementById('qs-athlete');
      var fieldEl      = document.getElementById('qs-field');
      var fieldsEl     = document.getElementById('qs-fields');
      var logEl        = document.getElementById('qs-log');
      var logEmpty     = true;
      var savedCount   = 0;
      var sportCheckEl = document.getElementById('qs-sport-check');
      var sportWrapEl  = document.getElementById('qs-sport-wrap');
      var sportSelEl   = document.getElementById('qs-sport-select');
      var bannerEl     = document.getElementById('qs-banner');
      var bannerNameEl = document.getElementById('qs-banner-name');
      var progressEl   = document.getElementById('qs-progress-badge');

      // Cache original base field options (optgroups + options)
      var baseFieldOpts = Array.from(fieldEl.childNodes).map(function(n) {{ return n.cloneNode(true); }});

      // Cache all athlete options
      var allAthleteOpts = Array.from(athleteEl.querySelectorAll('option'));

      // Update "Recording for" banner when athlete changes
      function updateBanner() {{
        var idx  = athleteEl.selectedIndex;
        var name = idx >= 0 ? athleteEl.options[idx].text : '';
        if (athleteEl.value && bannerEl && bannerNameEl) {{
          bannerEl.style.display = 'flex';
          bannerNameEl.textContent = name;
        }} else if (bannerEl) {{
          bannerEl.style.display = 'none';
        }}
      }}
      athleteEl.addEventListener('change', updateBanner);

      function filterAthletes() {{
        if (!groupEl) return;
        var gid  = groupEl.value;
        var prev = athleteEl.value;
        athleteEl.innerHTML = '';
        allAthleteOpts.forEach(function(opt) {{
          if (!opt.value || !gid || opt.dataset.group === String(gid))
            athleteEl.appendChild(opt.cloneNode(true));
        }});
        if (Array.from(athleteEl.options).some(function(o) {{ return o.value === prev; }})) {{
          athleteEl.value = prev;
        }} else {{
          athleteEl.value = '';
          fieldsEl.innerHTML = '';
        }}
      }}

      function rebuildFieldDropdown() {{
        var prevVal = fieldEl.value;
        fieldEl.innerHTML = '';
        baseFieldOpts.forEach(function(n) {{ fieldEl.appendChild(n.cloneNode(true)); }});
        // Append sport-specific fields if checkbox is checked and sport is selected
        if (sportCheckEl && sportCheckEl.checked && sportSelEl && sportSelEl.value) {{
          var sport  = sportSelEl.value;
          var sfields = SPORT_FIELDS[sport] || [];
          if (sfields.length) {{
            var grp = document.createElement('optgroup');
            grp.label = sport + ' — Sport Specific';
            sfields.forEach(function(f) {{
              var opt = document.createElement('option');
              opt.value       = f.composite;
              opt.textContent = f.game_name + ' — ' + f.label;
              grp.appendChild(opt);
            }});
            fieldEl.appendChild(grp);
          }}
        }}
        if (Array.from(fieldEl.options).some(function(o) {{ return o.value === prevVal; }})) {{
          fieldEl.value = prevVal;
        }} else {{
          fieldEl.value = '';
          fieldsEl.innerHTML = '';
        }}
      }}

      // Sport toggle
      if (sportCheckEl) {{
        sportCheckEl.addEventListener('change', function() {{
          sportWrapEl.style.display = sportCheckEl.checked ? 'block' : 'none';
          if (!sportCheckEl.checked && sportSelEl) sportSelEl.value = '';
          rebuildFieldDropdown();
        }});
      }}
      if (sportSelEl) {{ sportSelEl.addEventListener('change', rebuildFieldDropdown); }}

      if (groupEl) groupEl.addEventListener('change', filterAthletes);

      function renderField(composite) {{
        fieldsEl.innerHTML = '';
        if (!composite || !FIELDS[composite]) return;
        var f    = FIELDS[composite];
        var step = (f.type === 'time') ? '0.01' : '1';
        var suffix = (f.type === 'time') ? ' (seconds)' : '';
        var div  = document.createElement('div');
        div.className = 'mg-field';
        div.style.marginBottom = '12px';
        div.innerHTML =
          '<label style="font-size:13px; font-weight:600; display:block; margin-bottom:4px;">' +
            f.label + suffix +
          '</label>' +
          '<div class="mg-field-row">' +
            '<input type="number" step="' + step + '" min="0" id="qs-single-input" style="max-width:160px;" />' +
            '<button type="button" class="mg-save-btn" id="qs-single-btn">&#10003; Save</button>' +
          '</div>';
        fieldsEl.appendChild(div);

        var btn = div.querySelector('.mg-save-btn');
        var inp = div.querySelector('input');
        inp.focus();

        btn.addEventListener('click', function() {{
          var athleteId = athleteEl.value;
          var value     = inp.value.trim();
          if (!athleteId) {{ alert('Please select an athlete first.'); return; }}
          if (!value)     {{ alert('Please enter a value first.'); return; }}
          doSave(athleteId, f.game_key, f.field_key, f.game_name, f.label, f.type, value, btn, inp);
        }});
        inp.addEventListener('keydown', function(e) {{
          if (e.key === 'Enter') {{ e.preventDefault(); btn.click(); }}
        }});
      }}

      function markBtn(btn, state) {{
        if (state === 'saving') {{
          btn.textContent = '...'; btn.disabled = true; btn.style.background = '';
        }} else if (state === 'ok') {{
          btn.textContent = '\\u2713 Saved'; btn.disabled = false;
          btn.style.background = '#F0A82E'; btn.style.color = '#2D323B'; btn.style.borderColor = '#F0A82E';
          setTimeout(function() {{
            btn.textContent = '\\u2713 Save';
            btn.style.background = ''; btn.style.color = ''; btn.style.borderColor = '';
          }}, 2000);
        }} else {{
          btn.textContent = '! Error'; btn.disabled = false;
          btn.style.background = '#9b1c1c'; btn.style.color = '#fff'; btn.style.borderColor = '#9b1c1c';
          setTimeout(function() {{
            btn.textContent = '\\u2713 Save';
            btn.style.background = ''; btn.style.color = ''; btn.style.borderColor = '';
          }}, 3000);
        }}
      }}

      async function doSave(athleteId, gameKey, fieldKey, gameName, fieldLabel, fieldType, value, btn, inp) {{
        markBtn(btn, 'saving');
        try {{
          var athleteName = athleteEl.options[athleteEl.selectedIndex].text;
          var sessionLabel = (document.getElementById('session_label') || {{}}).value || '';
          var sessionMonth = (document.getElementById('session_month') || {{}}).value || '';
          if (!sessionLabel) {{ alert('Please select a Test Phase before saving.'); markBtn(btn, 'error'); return; }}
          var body = 'athlete_id='     + encodeURIComponent(athleteId) +
                     '&session_label=' + encodeURIComponent(sessionLabel) +
                     '&session_month=' + encodeURIComponent(sessionMonth) +
                     '&game_key='      + encodeURIComponent(gameKey) +
                     '&field_key='     + encodeURIComponent(fieldKey) +
                     '&value='         + encodeURIComponent(value);
          var resp = await fetch(saveUrl, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
            body: body,
          }});
          var data = await resp.json();
          if (!resp.ok || !data.ok) throw new Error(data.error || 'Save failed');
          markBtn(btn, 'ok');
          // Update progress
          savedCount++;
          if (progressEl) progressEl.textContent = savedCount + ' saved';
          inp.value = '';
          inp.focus();
          // Styled log entry
          if (logEmpty) {{ logEl.innerHTML = ''; logEmpty = false; }}
          var now = new Date();
          var timeStr = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0');
          var displayVal = value + (fieldType === 'time' ? 's' : '');
          var entry = document.createElement('div');
          entry.style.cssText = 'padding:8px 12px;margin-bottom:8px;border-radius:6px;border-left:3px solid #F0A82E;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.06);';
          entry.innerHTML =
            '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px;">' +
              '<span style="font-weight:700;color:#2D323B;font-size:13px;">' + athleteName + '</span>' +
              '<span style="font-size:11px;color:#6E737B;">' + timeStr + '</span>' +
            '</div>' +
            '<div style="font-size:12px;color:#6E737B;margin-top:2px;">' + gameName + ' &mdash; ' + fieldLabel + '</div>' +
            '<div style="font-size:15px;font-weight:800;color:#2D323B;margin-top:4px;">' + displayVal + '</div>';
          logEl.insertBefore(entry, logEl.firstChild);
        }} catch(e) {{
          markBtn(btn, 'error');
        }}
      }}

      fieldEl.addEventListener('change', function() {{ renderField(fieldEl.value); }});
    }})();
    </script>
    """
    return layout("Record Session", body, user=coach, active_nav="session")


def help_page(user):
    """Role-aware help page. Shows sections appropriate to the user's role."""
    role = user["role"] if user else "participant"
    is_staff = role in ("practitioner", "org_admin", "system_admin")
    is_org_admin = role in ("org_admin", "system_admin")
    is_sys_admin = role == "system_admin"

    NAVY  = "#2D323B"
    GOLD  = "#F0A82E"

    role_labels = {
        "practitioner": "Practitioner",
        "org_admin":    "Organisation Admin",
        "system_admin": "System Admin",
        "participant":  "Athlete",
    }
    role_label = role_labels.get(role, "User")

    def section(icon, title, content_html, open_by_default=False):
        open_attr = " open" if open_by_default else ""
        return f"""
        <details class="help-section"{open_attr}>
          <summary class="help-section-summary">
            <span class="help-icon">{icon}</span>
            <span class="help-title">{title}</span>
            <span class="help-chevron">&#9660;</span>
          </summary>
          <div class="help-body">{content_html}</div>
        </details>"""

    def steps(items):
        rows = "".join(
            f'<li class="help-step"><span class="help-step-num">{i+1}</span><span>{item}</span></li>'
            for i, item in enumerate(items)
        )
        return f'<ol class="help-steps">{rows}</ol>'

    def tip(text):
        return f'<div class="help-tip"><span>&#128161;</span> {text}</div>'

    def note(text):
        return f'<div class="help-note"><span>&#9432;</span> {text}</div>'

    # ── Section content ────────────────────────────────────────────────────────

    s_login = section("&#128274;", "Logging In", (
        steps([
            "Open the portal in your browser (or from your phone's home screen).",
            "Enter your <strong>email address</strong> and <strong>password</strong>.",
            "Tap <strong>Log in</strong>.",
        ])
        + tip("If you've forgotten your password, click <em>Forgot your password?</em> on the login page.")
        + tip("Save the portal to your phone's home screen for one-tap access — see <em>Using the Portal on Your Phone</em> below.")
    ), open_by_default=True)

    s_password = section("&#128273;", "Changing Your Password", (
        steps([
            "Click <strong>My Account</strong> in the top-right corner.",
            "Scroll to the <em>Change Password</em> section.",
            "Enter your current password, then your new password twice.",
            "Click <strong>Change Password</strong> to save.",
        ])
        + tip("Choose a password that is at least 8 characters and easy for you to remember.")
    ))

    s_phone = section("&#128241;", "Using the Portal on Your Phone", (
        "<p>The portal works as a web app — you can add it to your home screen for quick access without opening a browser each time.</p>"
        + "<p><strong>iPhone / iPad (Safari only):</strong></p>"
        + steps([
            "Open the portal in <strong>Safari</strong>.",
            "Tap the <strong>Share</strong> button (the square with an arrow pointing up).",
            'Scroll down and tap <strong>"Add to Home Screen"</strong>.',
            'Tap <strong>Add</strong> in the top-right corner.',
        ])
        + "<p><strong>Android (Chrome only):</strong></p>"
        + steps([
            "Open the portal in <strong>Chrome</strong>.",
            "Tap the three-dot menu (&#8942;) in the top-right.",
            'Tap <strong>"Add to Home screen"</strong>.',
            'Tap <strong>Add</strong> to confirm.',
        ])
        + tip("A full setup guide PDF is available from your practitioner if you need one.")
    ))

    s_dashboard = section("&#128200;", "Your Dashboard", (
        "<p>Your dashboard shows your most recent results, level progress, and personal bests across all measurement games.</p>"
        "<ul class='help-list'>"
        "<li><strong>Level badge</strong> — your current adaptability level, based on your improvement across games.</li>"
        "<li><strong>Game cards</strong> — your latest score and personal best for each game.</li>"
        "<li><strong>Progress history</strong> — tap a game name to see your full result history over time.</li>"
        "</ul>"
        + note("Scores are entered by your practitioner after each session. Check back after a session to see your updated results.")
    ))

    sections_html = s_login + s_password + s_phone + s_dashboard

    if is_staff:
        s_add_athlete = section("&#128101;", "Adding an Athlete", (
            steps([
                "Click <strong>Add Participant</strong> in the navigation bar.",
                "Fill in the athlete's name and (optionally) email, sport, and group.",
                "Click <strong>Add Participant</strong> to save.",
            ])
            + tip("If you enter an email address, the athlete will automatically receive a welcome email with their login details.")
            + tip("Athlete numbers are assigned automatically — you can change them on the athlete's profile page.")
        ))

        s_record = section("&#127942;", "Recording a Session", (
            "<p>Use <strong>Record Session</strong> in the nav to record a one-off session for a single athlete.</p>"
            + steps([
                "Select the athlete from the dropdown.",
                "Choose the session type and month.",
                "Select which games were played using the chip panel.",
                "Enter the scores and click <strong>Save Session</strong>.",
            ])
            + tip("The system will warn you if a session already exists for that athlete in that month — you can choose to merge or replace.")
        ))

        s_group_hub = section("&#128203;", "Group Hub", (
            "<p>The <strong>Group Hub</strong> is your central workspace for group-based data entry and reporting. "
            "Select a group from the dropdown, then use the three panels:</p>"
            "<ul class='help-list'>"
            "<li><strong>Completion Matrix</strong> — shows which athletes have completed which games, colour-coded by session month. "
            "Click a game header to jump straight to that game's entry table.</li>"
            "<li><strong>Game Entry</strong> — enter or update results for the whole group at once for a selected game. "
            "Choose the game and month, fill in the table, and click <strong>Save All Results</strong>.</li>"
            "<li><strong>Session Recording Sheet</strong> — generate a printable PDF recording sheet for a session. "
            "Select athletes, session type, and month, then click <strong>Download PDF</strong>.</li>"
            "</ul>"
            + tip("Use the Completion Matrix to spot gaps — grey cells mean no data yet for that athlete/game combination.")
        ))

        s_resources = section("&#128218;", "Resources", (
            "<p>The <strong>Resources</strong> section holds shared files, links, and guides for your organisation.</p>"
            "<ul class='help-list'>"
            "<li>Resources are organised into folders.</li>"
            "<li>Each resource can have tags to help with searching and filtering.</li>"
            "<li>Click a resource tile to open it (external links open in a new tab).</li>"
            "</ul>"
            + note("Only practitioners and admins can add or edit resources. Contact your System Admin if you need something added.")
        ))

        s_reports = section("&#128202;", "Statistics &amp; Reports", (
            "<p>Access detailed analytics from <strong>Statistics &amp; Reports</strong> in the nav.</p>"
            "<ul class='help-list'>"
            "<li><strong>Group Progress</strong> — improvement trends for every athlete in a group, by game.</li>"
            "<li><strong>Achievement Summary</strong> — personal bests and level distribution across the group.</li>"
            "<li><strong>Scores Table</strong> — a flat table of all scores, exportable to PDF.</li>"
            "<li><strong>All Groups</strong> — cross-group overview (accessible from the main Reports landing page).</li>"
            "</ul>"
            + tip("Use the sport filter at the top of the Reports page to narrow down which groups are shown.")
        ))

        sections_html += s_add_athlete + s_record + s_group_hub + s_resources + s_reports

    if is_org_admin:
        s_practitioners = section("&#128101;", "Managing Practitioners", (
            "<p>As an Organisation Admin, you can view and manage practitioners in your organisation.</p>"
            + steps([
                "Go to <strong>Practitioners</strong> in the navigation.",
                "To add a new practitioner, click <strong>Add Practitioner</strong> and fill in their details.",
                "To reset a practitioner's password, click <strong>Reset Password</strong> on their row.",
                "To assign a practitioner to your organisation, use the <strong>Organisation</strong> dropdown on their entry.",
            ])
            + tip("When you create a practitioner account with an email address, they will receive a welcome email automatically.")
        ))

        s_org_admin = section("&#127970;", "Your Organisation", (
            "<p>Your Organisation Admin access lets you view all groups and athletes within your organisation, "
            "download reports, and review completion data across all practitioners you manage.</p>"
            "<ul class='help-list'>"
            "<li>Use the <strong>Group Hub</strong> to view any group in your organisation.</li>"
            "<li>Use <strong>Statistics &amp; Reports</strong> to access cross-group analytics.</li>"
            "<li>Contact your System Admin to update your organisation's name or logo.</li>"
            "</ul>"
        ))

        sections_html += s_practitioners + s_org_admin

    if is_sys_admin:
        s_orgs = section("&#127968;", "Managing Organisations", (
            "<p>As System Admin, you can create and manage organisations.</p>"
            + steps([
                "Go to <strong>Organisations</strong> in the navigation.",
                "Click <strong>Add Organisation</strong> to create a new one.",
                "Enter the name and optionally a logo URL.",
                "Use the Practitioners page to assign practitioners to organisations.",
            ])
            + tip("Organisations help scope data visibility — practitioners and athletes can only see data within their own organisation.")
        ))

        s_sys = section("&#9881;", "System Administration", (
            "<p>As System Admin you have unrestricted access to all data in the portal.</p>"
            "<ul class='help-list'>"
            "<li><strong>Practitioners page</strong> — add, edit, reset passwords, and set roles for any staff account.</li>"
            "<li><strong>Organisations page</strong> — create and edit organisations.</li>"
            "<li><strong>Resources</strong> — add and manage resources visible to all users.</li>"
            "<li><strong>CSV Import/Export</strong> — bulk import athletes (Practitioners list → Import CSV button).</li>"
            "</ul>"
            + note("Role changes take effect immediately. Be careful when demoting accounts — they will lose access to staff features straight away.")
        ))

        sections_html += s_orgs + s_sys

    body = f"""
    <style>
      .help-role-badge {{
        display: inline-block;
        background: {GOLD};
        color: {NAVY};
        font-weight: 700;
        font-size: 13px;
        padding: 3px 12px;
        border-radius: 20px;
        margin-bottom: 18px;
        letter-spacing: 0.03em;
      }}
      .help-intro {{
        color: #4B5563;
        margin-bottom: 28px;
        font-size: 15px;
      }}
      .help-section {{
        border: 1px solid #DDE0E3;
        border-radius: 10px;
        margin-bottom: 12px;
        background: #fff;
        overflow: hidden;
      }}
      .help-section[open] {{
        box-shadow: 0 2px 8px rgba(0,0,0,.06);
      }}
      .help-section-summary {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 15px 18px;
        cursor: pointer;
        list-style: none;
        user-select: none;
        background: #fff;
      }}
      .help-section-summary::-webkit-details-marker {{ display: none; }}
      .help-section[open] .help-section-summary {{
        background: {NAVY};
        color: #fff;
      }}
      .help-section[open] .help-title {{
        color: #fff;
      }}
      .help-section[open] .help-chevron {{
        transform: rotate(180deg);
        color: {GOLD};
      }}
      .help-icon {{
        font-size: 20px;
        flex-shrink: 0;
      }}
      .help-title {{
        font-weight: 700;
        font-size: 16px;
        color: {NAVY};
        flex: 1;
      }}
      .help-chevron {{
        font-size: 12px;
        color: #9CA3AF;
        transition: transform 0.2s;
        flex-shrink: 0;
      }}
      .help-body {{
        padding: 20px 22px 22px;
        border-top: 1px solid #DDE0E3;
        font-size: 15px;
        color: #374151;
        line-height: 1.7;
      }}
      .help-body p {{ margin: 0 0 14px; }}
      .help-steps {{
        list-style: none;
        padding: 0;
        margin: 12px 0 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }}
      .help-step {{
        display: flex;
        align-items: flex-start;
        gap: 12px;
      }}
      .help-step-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        min-width: 26px;
        background: {GOLD};
        color: {NAVY};
        font-weight: 800;
        font-size: 13px;
        border-radius: 50%;
        flex-shrink: 0;
        margin-top: 1px;
      }}
      .help-list {{
        margin: 10px 0 14px 18px;
        padding: 0;
      }}
      .help-list li {{ margin-bottom: 7px; }}
      .help-tip {{
        background: #FFFBEB;
        border-left: 3px solid {GOLD};
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 14px;
        color: #92400E;
        display: flex;
        gap: 8px;
        align-items: flex-start;
      }}
      .help-note {{
        background: #EFF6FF;
        border-left: 3px solid #3B82F6;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 14px;
        color: #1E40AF;
        display: flex;
        gap: 8px;
        align-items: flex-start;
      }}
    </style>

    <h1 style="margin-bottom:6px;">Help &amp; Guide</h1>
    <div class="help-role-badge">Viewing as: {esc(role_label)}</div>
    <p class="help-intro">
      Find answers to common questions below. Sections are shown based on your access level.
      Click a section heading to expand it.
    </p>

    {sections_html}

    <div style="margin-top:32px;padding:20px 22px;background:#F3F4F5;border-radius:10px;font-size:14px;color:#6E737B;">
      <strong style="color:{NAVY};">Need more help?</strong>
      Contact your practitioner or system administrator, or email
      <a href="mailto:info@justagame.co.nz">info@justagame.co.nz</a>.
    </div>
    """

    return layout("Help & Guide", body, user=user, active_nav="help")


def simple_message_page(title, message, user=None):
    body = f'<div class="card"><p>{esc(message)}</p></div>'
    return layout(title, body, user=user)


def admin_sessions_page(admin, groups, selected_group_id=None, athlete_sessions=None, flash=None, ungrouped=None):
    """System-admin tool: view and delete measurement sessions per group.
    athlete_sessions: list of (athlete_dict, sessions_list) for the selected group.
    """
    from constants import SESSION_LABEL_MAP

    group_opts = '<option value="">— Select a group —</option>' + "".join(
        f'<option value="{g["id"]}" {"selected" if selected_group_id and g["id"]==selected_group_id else ""}>'
        f'{esc(g["name"])}</option>'
        for g in groups
    )

    flash_html = ""
    if flash:
        flash_html = (f'<div style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:6px;'
                      f'padding:10px 14px;margin-bottom:16px;font-size:13px;font-weight:600;color:#065f46;">'
                      f'{esc(flash)}</div>')

    sessions_html = ""
    if athlete_sessions is not None:
        if not athlete_sessions:
            sessions_html = '<div class="card"><p class="muted">No athletes or sessions in this group.</p></div>'
        else:
            rows = ""
            for athlete, sessions in athlete_sessions:
                if not sessions:
                    rows += (f'<tr><td style="font-weight:600;">{esc(athlete["name"])}</td>'
                             f'<td colspan="5" class="muted" style="font-style:italic;">No sessions</td></tr>')
                    continue
                first = True
                for s in sessions:
                    label_disp = SESSION_LABEL_MAP.get(s.get("session_label") or "", s.get("session_label") or "—")
                    month_disp = s.get("session_month") or "—"
                    n_results  = len([v for v in (s.get("results") or {}).values() if v is not None])
                    name_cell  = (f'<td rowspan="{len(sessions)}" style="font-weight:600;vertical-align:top;'
                                  f'padding-top:10px;">{esc(athlete["name"])}</td>' if first else "")
                    rows += (
                        f'<tr style="border-bottom:1px solid #DDE0E3;">'
                        f'{name_cell}'
                        f'<td>{esc(str(s["id"]))}</td>'
                        f'<td>{esc(s["date"])}</td>'
                        f'<td><span style="font-size:12px;padding:2px 8px;border-radius:999px;background:#F3F4F5;'
                        f'font-weight:600;">{esc(label_disp)}</span></td>'
                        f'<td style="color:var(--jag-muted);font-size:12px;">{esc(month_disp)}</td>'
                        f'<td style="color:var(--jag-muted);font-size:12px;">{n_results} field{"s" if n_results!=1 else ""} recorded</td>'
                        f'<td>'
                        f'<form method="post" action="/coach/admin/sessions/delete" '
                        f'onsubmit="return confirm(\'Delete this session? This cannot be undone.\');">'
                        f'<input type="hidden" name="session_id" value="{s["id"]}" />'
                        f'<input type="hidden" name="group_id" value="{selected_group_id}" />'
                        f'<button type="submit" class="btn btn-sm" '
                        f'style="font-size:11px;background:#fee2e2;color:#9b1c1c;border:1px solid #fca5a5;">'
                        f'Delete</button>'
                        f'</form>'
                        f'</td>'
                        f'</tr>'
                    )
                    first = False

            sessions_html = f"""
            <div class="card" style="overflow-x:auto;padding:0;">
              <table class="table" style="width:100%;">
                <thead>
                  <tr style="background:#2D323B;color:#fff;">
                    <th>Athlete</th><th>Session ID</th><th>Date</th>
                    <th>Label</th><th>Month</th><th>Fields</th><th></th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

    # Ungrouped athletes panel
    ungrouped_html = ""
    if ungrouped is not None:
        if not ungrouped:
            ungrouped_html = '<div class="card"><p class="muted">No ungrouped athletes found.</p></div>'
        else:
            ug_rows = ""
            for a in ungrouped:
                n_sessions = a.get("_session_count", 0)
                aname = esc(a["name"])
                asport = esc(a.get("sport") or "—")
                aid = a["id"]
                ug_rows += (
                    f'<tr style="border-bottom:1px solid #DDE0E3;">'
                    f'<td style="font-weight:600;">{aname}</td>'
                    f'<td style="color:var(--jag-muted);font-size:12px;">{asport}</td>'
                    f'<td style="color:var(--jag-muted);font-size:12px;">{n_sessions} session{"s" if n_sessions!=1 else ""}</td>'
                    f'<td>'
                    f'<form method="post" action="/coach/admin/athletes/delete" '
                    f'onsubmit="return confirm(\'Permanently delete {aname} and all their data? This cannot be undone.\');">'
                    f'<input type="hidden" name="participant_id" value="{aid}" />'
                    f'<button type="submit" class="btn btn-sm" '
                    f'style="font-size:11px;background:#fee2e2;color:#9b1c1c;border:1px solid #fca5a5;">'
                    f'Delete</button>'
                    f'</form>'
                    f'</td>'
                    f'</tr>'
                )
            ungrouped_html = f"""
            <div style="margin-bottom:24px;">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                <h3 style="margin:0;font-size:16px;font-weight:700;color:var(--jag-navy);">
                  Ungrouped Athletes ({len(ungrouped)})
                </h3>
                <form method="post" action="/coach/admin/athletes/delete-ungrouped"
                      onsubmit="return confirm('Permanently delete ALL {len(ungrouped)} ungrouped athletes and all their data? This cannot be undone.');">
                  <button type="submit" class="btn btn-sm"
                          style="background:#fee2e2;color:#9b1c1c;border:1px solid #fca5a5;font-weight:700;">
                    &#128465; Delete All Ungrouped
                  </button>
                </form>
              </div>
              <div class="card" style="overflow-x:auto;padding:0;">
                <table class="table" style="width:100%;">
                  <thead>
                    <tr style="background:#2D323B;color:#fff;">
                      <th>Name</th><th>Sport</th><th>Sessions</th><th></th>
                    </tr>
                  </thead>
                  <tbody>{ug_rows}</tbody>
                </table>
              </div>
            </div>"""

    merge_panel = ""
    if selected_group_id and athlete_sessions:
        multi = sum(1 for _, s in athlete_sessions if len(s) > 1)
        if multi > 0:
            merge_panel = f"""
            <div style="background:#fffbeb;border:1px solid #F0A82E;border-left:4px solid #F0A82E;
                        border-radius:8px;padding:14px 18px;margin-bottom:20px;">
              <div style="font-weight:700;font-size:14px;color:#2D323B;margin-bottom:6px;">
                &#9889; Merge into Baseline
              </div>
              <p style="margin:0 0 12px;font-size:13px;color:#6E737B;">
                <strong>{multi} athlete{"s have" if multi!=1 else " has"}</strong> multiple sessions.
                This will combine all sessions per athlete into one, keeping the earliest date as the base
                and copying across any results that don't conflict. All surviving sessions will be labelled <strong>Baseline</strong>.
              </p>
              <form method="post" action="/coach/admin/sessions/merge"
                    onsubmit="return confirm('Merge all sessions for this group into one Baseline per athlete? This cannot be undone.');">
                <input type="hidden" name="group_id" value="{selected_group_id}" />
                <div style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;">
                  <label style="font-size:13px;font-weight:600;">
                    Baseline month (optional)
                    {_month_select("target_month")}
                  </label>
                  <button type="submit" class="btn btn-primary"
                          style="background:#F0A82E;color:#2D323B;border:none;font-weight:700;">
                    &#9889; Merge All into Baseline
                  </button>
                </div>
              </form>
            </div>"""

    body = f"""
    <div class="page-head">
      <div>
        <h1>Session Manager</h1>
        <p class="muted">System Admin &mdash; view and merge measurement sessions per group</p>
      </div>
      <a href="/coach/progress" class="btn btn-ghost">&larr; Back to Overview</a>
    </div>
    {flash_html}
    {ungrouped_html}
    <div class="card" style="margin-bottom:20px;">
      <form method="get" action="/coach/admin/sessions" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;">
        <label style="flex:1;min-width:200px;">Group
          <select name="group_id" required>{group_opts}</select>
        </label>
        <button type="submit" class="btn btn-primary">View Sessions</button>
      </form>
    </div>
    {merge_panel}
    {sessions_html}"""
    return layout("Session Manager", body, user=admin, active_nav="progress")


def confirm_replace_session_page(coach, participant, results, session_label, session_month,
                                  label_display, existing_month):
    """Warn the practitioner that a session with this label already exists, offer to merge new results in."""
    import datetime as _dt2
    try:
        em = _dt2.datetime.strptime(existing_month, "%Y-%m")
        existing_month_str = em.strftime("%B %Y")
    except Exception:
        existing_month_str = existing_month
    # Re-encode all results as hidden fields so they survive the round-trip
    hidden_results = "".join(
        f'<input type="hidden" name="mg__{gk}__{fk}" value="{v}" />'
        for gk, fk, v in results
    )
    pid = participant["id"]
    body = f"""
    <div class="card" style="max-width:540px;">
      <h2 style="margin-top:0;">&#9888; Session Already Recorded</h2>
      <p>A <strong>{esc(label_display)}</strong> session for <strong>{esc(participant['name'])}</strong>
         was already recorded in <strong>{esc(existing_month_str)}</strong>.</p>
      <p>The new results you just entered will be <strong>merged in</strong> — any fields you filled in
         will be updated, and any fields you left blank will keep their existing values.</p>
      <p style="font-size:0.85em;color:#6E737B;">This is useful when testing spans multiple sessions —
         just enter the new game results and confirm to add them alongside what's already there.</p>
      <form method="post" action="/coach/participants/{pid}/measurement/log">
        <input type="hidden" name="session_label" value="{esc(session_label)}" />
        <input type="hidden" name="session_month" value="{esc(session_month or '')}" />
        <input type="hidden" name="confirm_replace" value="1" />
        {hidden_results}
        <div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;">
          <button type="submit" class="btn btn-primary">Yes, Merge Results In</button>
          <a href="/coach/participants/{pid}" class="btn btn-ghost">Cancel — Keep Existing</a>
        </div>
      </form>
    </div>"""
    return layout(f"Merge Session — {participant['name']}", body, user=coach, active_nav="dashboard")


def edit_measurement_session_page(coach, participant, participant_id, selected_label, selected_month):
    """Standalone page for editing an existing measurement session — form is pre-filled via JS."""
    form_html = measurement_games_form(participant_id,
                                       selected_label=selected_label,
                                       selected_month=selected_month)
    back_url = f"/coach/participants/{participant_id}"
    body = f"""
    <div class="page-head" style="display:flex;align-items:center;gap:16px;">
      <a href="{back_url}" class="btn btn-ghost btn-sm">&#8592; Back</a>
      <h1 style="margin:0;">Edit Session &mdash; {esc(participant.get('name',''))}</h1>
    </div>
    <p class="muted">Existing values are loaded automatically. Update any field and click <strong>&#10003; Save</strong>
       — only the fields you save will be changed.</p>
    {form_html}
    """
    return layout(f"Edit Session — {participant.get('name','')}", body, user=coach, active_nav="dashboard")


def account_page(user, profile_error=None, profile_success=None, password_error=None, password_success=None):
    profile_error_html = f'<div class="alert">{esc(profile_error)}</div>' if profile_error else ""
    profile_success_html = f'<div class="flash">{esc(profile_success)}</div>' if profile_success else ""
    password_error_html = f'<div class="alert">{esc(password_error)}</div>' if password_error else ""
    password_success_html = f'<div class="flash">{esc(password_success)}</div>' if password_success else ""
    body = f"""
    <div class="page-head"><h1>My Account</h1></div>

    <h2 class="section-title">Your Details</h2>
    {profile_error_html}
    {profile_success_html}
    <div class="card form-card" style="max-width:420px">
      <form method="post" action="/account/profile">
        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required value="{esc(user['name'])}" />
        <label for="email">Email</label>
        <input type="email" id="email" name="email" required value="{esc(user['email'])}" />
        <label for="username">Username <span class="muted" style="font-weight:400;">(optional — can use instead of email to log in)</span></label>
        <input type="text" id="username" name="username" value="{esc(user['username'] or '' if 'username' in user.keys() else '')}" autocomplete="username" placeholder="e.g. coachsimon" />
        <button type="submit" class="btn btn-primary btn-block">Save Details</button>
      </form>
    </div>

    <h2 class="section-title">Change Password</h2>
    {password_error_html}
    {password_success_html}
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
    return layout("My Account", body, user=user, active_nav=None)


def coach_list_page(user, coaches, groups=None, coach_group_map=None, organisations=None, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    groups = groups or []
    coach_group_map = coach_group_map or {}
    organisations = organisations or []
    group_map = {g["id"]: g["name"] for g in groups}
    org_map = {o["id"]: o["name"] for o in organisations}

    # Collect unique organisations for filter bar (from the table, not free text)
    all_orgs = [o["name"] for o in organisations] if organisations else sorted(set(
        c["organisation"] for c in coaches if c["organisation"]
    ))

    rows = []
    for c in coaches:
        is_self = c["id"] == user["id"]
        status = "Active" if c["active"] else "Inactive"
        status_class = "tag-active" if c["active"] else "tag-inactive"
        admin_badge = ' <span class="tag tag-active" style="font-size:11px;">System Admin</span>' if c["is_admin"] else ""
        assigned_ids = coach_group_map.get(c["id"], [])
        assigned_names = [esc(group_map[gid]) for gid in assigned_ids if gid in group_map]
        group_badge = (" &middot; " + ", ".join(f'<span class="tag">{n}</span>' for n in assigned_names)) if assigned_names else ""
        org_text = esc(c["organisation"]) if c["organisation"] else ""
        org_pill = (f'<span style="font-size:11px;background:rgba(45,50,59,0.08);color:var(--jag-muted);'
                    f'border-radius:999px;padding:1px 8px;white-space:nowrap;">{org_text}</span> ') if org_text else ""

        c_org_attr = esc(c["organisation"] or "")
        c_admin_attr = "1" if c["is_admin"] else "0"
        c_active_attr = "1" if c["active"] else "0"

        if is_self:
            action_html = '<span class="muted">(you)</span>'
        else:
            toggle_label = "Deactivate" if c["active"] else "Reactivate"
            admin_toggle_label = "Remove System Admin" if c["is_admin"] else "Make System Admin"
            checkboxes = "".join(
                f'<label style="display:flex;align-items:center;gap:6px;font-size:12px;font-weight:normal;margin:2px 0;">'
                f'<input type="checkbox" name="group_id" value="{g["id"]}"'
                f'{" checked" if g["id"] in assigned_ids else ""}> {esc(g["name"])}</label>'
                for g in groups
            ) if groups else '<span class="muted" style="font-size:12px;">No groups yet</span>'
            org_opts = '<option value="">— No organisation —</option>' + "".join(
                f'<option value="{o["id"]}"{" selected" if o["id"] == c.get("organisation_id") else ""}>{esc(o["name"])}</option>'
                for o in organisations
            )
            org_form = (
                f'<form method="post" action="/coach/coaches/{c["id"]}/assign-org"'
                f' style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">'
                f'<select name="organisation_id"'
                f' style="font-size:12px;padding:3px 6px;border:1px solid var(--jag-border);border-radius:4px;flex:1;min-width:120px;">'
                f'{org_opts}</select>'
                f'<button type="submit" class="btn btn-ghost btn-sm">Set Org</button>'
                f'</form>'
            ) if organisations else ""
            action_html = f"""
            <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-start;min-width:180px;">
              <div style="display:flex;gap:6px;flex-wrap:wrap;">
                <form method="post" action="/coach/coaches/{c['id']}/reset-password" style="display:contents"
                      onsubmit="return confirm('Reset {esc(c['name'])}&#39;s password?');">
                  <button type="submit" class="btn btn-ghost btn-sm">Reset Password</button>
                </form>
                <form method="post" action="/coach/coaches/{c['id']}/toggle-admin" style="display:contents"
                      onsubmit="return confirm('{admin_toggle_label} for {esc(c['name'])}?');">
                  <button type="submit" class="btn btn-ghost btn-sm">{admin_toggle_label}</button>
                </form>
                <form method="post" action="/coach/coaches/{c['id']}/toggle" style="display:contents">
                  <button type="submit" class="btn btn-ghost btn-sm">{toggle_label}</button>
                </form>
              </div>
              {org_form}
              <details style="width:100%;">
                <summary style="font-size:12px;font-weight:600;color:var(--jag-muted);cursor:pointer;
                                list-style:none;display:flex;align-items:center;gap:4px;user-select:none;">
                  <span>&#9654;</span> Assign Groups
                </summary>
                <form method="post" action="/coach/coaches/{c['id']}/assign-group"
                      style="margin-top:6px;">
                  <div style="border:1px solid var(--jag-border);border-radius:6px;
                               padding:6px 10px;background:#FAFAFA;margin-bottom:6px;
                               max-height:140px;overflow-y:auto;">
                    {checkboxes}
                  </div>
                  <button type="submit" class="btn btn-ghost btn-sm">Save Groups</button>
                </form>
              </details>
            </div>"""
        rows.append(f"""<tr class="coach-row" data-org="{c_org_attr}" data-admin="{c_admin_attr}" data-active="{c_active_attr}">
          <td>{org_pill}{esc(c['name'])}{admin_badge}</td>
          <td>{esc(c['email'])}{group_badge}</td>
          <td><span class="tag {status_class}">{status}</span></td>
          <td>{action_html}</td>
        </tr>""")
    rows_html = "".join(rows)

    # Build filter bar
    org_btns = "".join(
        f'<button class="coach-filter-btn btn btn-ghost btn-sm" data-filter="org" data-value="{esc(o)}" '
        f'style="border-radius:999px;">{esc(o)}</button>'
        for o in all_orgs
    )
    filter_bar = f"""
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:16px;">
      <span style="font-size:12px;font-weight:600;color:var(--jag-muted);text-transform:uppercase;letter-spacing:.05em;">Filter:</span>
      <button class="coach-filter-btn btn btn-sm active-filter" data-filter="all" style="border-radius:999px;background:var(--jag-navy);color:#fff;border-color:var(--jag-navy);">All</button>
      <button class="coach-filter-btn btn btn-ghost btn-sm" data-filter="system_admin" style="border-radius:999px;">System Admins only</button>
      <button class="coach-filter-btn btn btn-ghost btn-sm" data-filter="active" style="border-radius:999px;">Active</button>
      <button class="coach-filter-btn btn btn-ghost btn-sm" data-filter="inactive" style="border-radius:999px;">Inactive</button>
      {(f'<span style="width:1px;height:18px;background:var(--jag-border);display:inline-block;margin:0 2px;"></span>' + org_btns) if org_btns else ""}
    </div>
    <div style="font-size:12px;color:var(--jag-muted);margin-bottom:10px;">
      Showing <strong id="coach-count">{len(coaches)}</strong> of {len(coaches)} coaches
    </div>"""

    filter_js = """
    <script>
    (function(){
      var active = 'all', activeOrg = null;
      var btns = document.querySelectorAll('.coach-filter-btn');
      var rows = document.querySelectorAll('.coach-row');
      var countEl = document.getElementById('coach-count');
      function applyFilter(){
        var shown = 0;
        rows.forEach(function(r){
          var show = true;
          if(active === 'system_admin') show = r.dataset.admin === '1';
          else if(active === 'active') show = r.dataset.active === '1';
          else if(active === 'inactive') show = r.dataset.active === '0';
          else if(active === 'org') show = r.dataset.org === activeOrg;
          r.style.display = show ? '' : 'none';
          if(show) shown++;
        });
        countEl.textContent = shown;
      }
      btns.forEach(function(btn){
        btn.addEventListener('click', function(){
          btns.forEach(function(b){
            b.classList.remove('active-filter');
            b.style.background = '';
            b.style.color = '';
            b.style.borderColor = '';
          });
          btn.classList.add('active-filter');
          btn.style.background = '#2D323B';
          btn.style.color = '#fff';
          btn.style.borderColor = '#2D323B';
          if(btn.dataset.filter === 'org'){
            active = 'org';
            activeOrg = btn.dataset.value;
          } else {
            active = btn.dataset.filter;
            activeOrg = null;
          }
          applyFilter();
        });
      });
    })();
    </script>"""

    body = f"""
    <div class="page-head">
      <h1>Practitioners</h1>
      <a class="btn btn-primary" href="/coach/coaches/new">Add Practitioner</a>
    </div>
    {message_html}
    {filter_bar}
    <div class="card">
      <table class="table">
        <thead><tr><th>Name</th><th>Email / Groups</th><th>Status</th><th></th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    {filter_js}
    """
    return layout("Practitioners", body, user=user, active_nav="coaches")


def new_coach_form(user, error=None, organisations=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    organisations = organisations or []
    org_opts = '<option value="">— No organisation —</option>' + "".join(
        f'<option value="{o["id"]}">{esc(o["name"])}</option>' for o in organisations
    )
    org_field = f"""
        <label for="organisation_id">Organisation <span style="font-weight:400;color:var(--jag-muted);">(optional — scopes coach to this org's groups)</span></label>
        <select id="organisation_id" name="organisation_id">{org_opts}</select>
        <p style="font-size:12px;color:var(--jag-muted);margin-top:-10px;">
          Don't see their organisation? <a href="/coach/organisations">Add it first</a>.
        </p>""" if organisations else """
        <label for="organisation_id">Organisation</label>
        <p style="font-size:12px;color:var(--jag-muted);">No organisations yet — <a href="/coach/organisations">create one first</a> to scope this coach.</p>"""
    body = f"""
    <div class="page-head"><h1>Add Practitioner</h1></div>
    {error_html}
    <div class="card form-card">
      <form method="post" action="/coach/coaches/new">
        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required />
        <label for="email">Email (used to log in)</label>
        <input type="email" id="email" name="email" required />
        {org_field}
        <label for="password">Temporary password</label>
        <input type="text" id="password" name="password" required value="CoachTemp123!" />
        <button type="submit" class="btn btn-primary">Create Practitioner</button>
      </form>
    </div>
    """
    return layout("Add Practitioner", body, user=user, active_nav="coaches")


def organisations_page(user, orgs_data, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    type_options = "".join(
        f'<option value="{t}">{t}</option>'
        for t in ["School", "Club", "Programme", "Other"]
    )

    rows = []
    for od in orgs_data:
        o = od["org"]
        type_badge = (f'<span style="font-size:11px;background:rgba(45,50,59,0.08);color:var(--jag-muted);'
                      f'border-radius:999px;padding:1px 8px;">{esc(o["type"])}</span> ') if o["type"] else ""
        logo_html = (
            f'<img src="{esc(o["icon_url"])}" alt="" '
            f'style="height:28px;width:auto;object-fit:contain;border-radius:3px;margin-right:8px;vertical-align:middle;" '
            f'onerror="this.style.display=\'none\'" />'
        ) if o["icon_url"] else ""
        rows.append(f"""
        <tr>
          <td>{logo_html}{type_badge}<strong>{esc(o["name"])}</strong></td>
          <td style="text-align:center;">{od["group_count"]}</td>
          <td style="text-align:center;">{od["coach_count"]}</td>
          <td>
            <a href="/coach/organisations/{o['id']}/edit" class="btn btn-ghost btn-sm">Edit</a>
            <form method="post" action="/coach/organisations/{o['id']}/delete" style="display:inline"
                  onsubmit="return confirm('Delete organisation \\'{esc(o['name'])}\\'? Groups and coaches will be unlinked.');">
              <button type="submit" class="btn btn-ghost btn-sm">Delete</button>
            </form>
          </td>
        </tr>""")

    rows_html = "".join(rows) if rows else '<tr><td colspan="4" class="muted" style="text-align:center;padding:24px;">No organisations yet.</td></tr>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>Organisations</h1>
        <p class="muted">Schools, clubs, and programmes — used to scope coaches to their own athletes.</p>
      </div>
    </div>
    {message_html}
    <div class="card" style="margin-bottom:24px;">
      <table class="table">
        <thead><tr><th>Name</th><th style="text-align:center;">Groups</th><th style="text-align:center;">Practitioners</th><th></th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <div class="card form-card" style="max-width:500px;">
      <h2 style="margin-bottom:16px;">Add Organisation</h2>
      <form method="post" action="/coach/organisations/new" style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <label for="new-org-name" style="margin-bottom:4px;">Name</label>
          <input type="text" id="new-org-name" name="name" placeholder="e.g. Makoura College" required />
        </div>
        <div>
          <label for="new-org-type" style="margin-bottom:4px;">Type <span style="font-weight:400;color:var(--jag-muted);">(optional)</span></label>
          <select id="new-org-type" name="type">
            <option value="">— Select type —</option>
            {type_options}
          </select>
        </div>
        <div>
          <label for="new-org-icon" style="margin-bottom:4px;">Logo URL <span style="font-weight:400;color:var(--jag-muted);">(optional — paste a public image link)</span></label>
          <input type="url" id="new-org-icon" name="icon_url" placeholder="https://…" />
          <p style="font-size:12px;color:var(--jag-muted);margin-top:4px;">Google Drive: open file → Share → Anyone with link → copy URL.</p>
        </div>
        <div><button type="submit" class="btn btn-primary">Create Organisation</button></div>
      </form>
    </div>
    """
    return layout("Organisations", body, user=user, active_nav="organisations")


def organisation_form(user, org=None, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    name_val = esc(org["name"]) if org else ""
    type_val = org["type"] if org else ""
    icon_val = esc(org["icon_url"]) if org and org["icon_url"] else ""
    type_options = "".join(
        f'<option value="{t}"{" selected" if type_val == t else ""}>{t}</option>'
        for t in ["School", "Club", "Programme", "Other"]
    )
    action = f"/coach/organisations/{org['id']}/edit" if org else "/coach/organisations/new"
    title = f"Edit Organisation — {org['name']}" if org else "Add Organisation"
    logo_preview = (
        f'<div style="margin-bottom:12px;"><img src="{icon_val}" alt="Current logo" '
        f'style="height:48px;width:auto;object-fit:contain;border-radius:4px;border:1px solid var(--jag-border);padding:4px;" '
        f'onerror="this.style.display=\'none\'" /></div>'
    ) if icon_val else ""
    body = f"""
    <div class="page-head">
      <h1>{esc(title)}</h1>
      <a class="btn btn-ghost" href="/coach/organisations">Back</a>
    </div>
    {error_html}
    <div class="card form-card">
      <form method="post" action="{action}">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" value="{name_val}" required />
        <label for="type">Type <span style="font-weight:400;color:var(--jag-muted);">(optional)</span></label>
        <select id="type" name="type">
          <option value="">— Select type —</option>
          {type_options}
        </select>
        <label for="icon_url">Logo URL <span style="font-weight:400;color:var(--jag-muted);">(optional — paste a public image link)</span></label>
        {logo_preview}
        <input type="url" id="icon_url" name="icon_url" value="{icon_val}" placeholder="https://…" />
        <p style="font-size:12px;color:var(--jag-muted);margin-top:-10px;">Google Drive: open file → Share → Anyone with link → copy the sharing URL.</p>
        <button type="submit" class="btn btn-primary" style="margin-top:8px;">{"Save Changes" if org else "Create"}</button>
      </form>
    </div>
    """
    return layout(title, body, user=user, active_nav="organisations")


def _gdrive_thumbnail(url):
    """Return a thumbnail URL for a Google Drive file link, or None if not GDrive."""
    if not url:
        return None
    m = _re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        # Also handle ?id= style links
        m = _re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if m:
        fid = m.group(1)
        return f"https://drive.google.com/thumbnail?id={fid}&sz=w400"
    return None


def _resource_tile(r, is_admin=False, tags=None):
    """Render a single resource as a link tile card."""
    # JAG brand palette: navy and gold alternating by id
    jag_palette = [
        ('#2D323B', '#F0A82E'),   # navy bg, gold icon
        ('#F0A82E', '#2D323B'),   # gold bg, navy icon
    ]
    bg_color, icon_color = jag_palette[r['id'] % len(jag_palette)]
    border_color = '#F0A82E' if bg_color == '#2D323B' else '#2D323B'

    name_q = esc(r['name']).replace("'", "\\'")
    desc = f'<span style="font-size:12px;color:var(--jag-muted);display:block;margin-top:4px;line-height:1.4;">{esc(r["description"])}</span>' if r['description'] else ''
    so_val = r['self_organisation'] if 'self_organisation' in r.keys() and r['self_organisation'] else None
    self_org_badge = (
        f'<div style="margin-top:6px;">'
        f'<span style="font-size:10px;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;'
        f'color:var(--jag-navy);opacity:0.5;">Self-organisation</span><br>'
        f'<span style="font-size:12px;font-weight:600;color:#F0A82E;">{esc(so_val)}</span>'
        f'</div>'
    ) if so_val else ''
    drag = '<span class="drag-handle" title="Drag to reorder" style="position:absolute;top:6px;left:8px;font-size:11px;color:#ccc;cursor:grab;z-index:1;">&#9776;</span>' if is_admin else ""
    admin_actions = f"""<div style="display:flex;gap:4px;margin-top:8px;padding-top:8px;border-top:1px solid var(--jag-border);">
        <a href="/coach/resources/{r['id']}/edit" class="btn btn-ghost btn-sm" style="font-size:11px;padding:2px 8px;">Edit</a>
        <form method="post" action="/coach/resources/{r['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete \\'{name_q}\\'?');">
          <button type="submit" class="btn btn-ghost btn-sm" style="font-size:11px;padding:2px 8px;">Delete</button>
        </form>
      </div>""" if is_admin else ""
    tag_names = [t["name"] for t in (tags or [])]
    tag_pills = "".join(
        f'<span style="font-size:10px;background:var(--jag-green);color:var(--jag-navy);border-radius:999px;padding:1px 7px;font-weight:600;white-space:nowrap;">{esc(t)}</span>'
        for t in tag_names
    )
    tags_html = f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:auto;padding-top:8px;">{tag_pills}</div>' if tag_pills else ''
    tag_data = ",".join(t.lower() for t in tag_names)
    search_data = (r['name'] + " " + (r['description'] or "")).lower()

    # SVG uses single quotes throughout so it embeds safely in JS strings
    placeholder_svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='36' height='36'"
        f" fill='{icon_color}' viewBox='0 0 24 24'>"
        f"<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z'/>"
        f"<path d='M14 2v6h6'/></svg>"
    )
    # Escape any single quotes in SVG for JS string embedding
    svg_js = placeholder_svg.replace("'", "\\'")
    fallback_style = (
        f"margin:-14px -14px 12px;height:100px;border-radius:8px 8px 0 0;"
        f"background:{bg_color};display:flex;align-items:center;justify-content:center;"
    ).replace("'", "\\'")

    # Google Drive thumbnail — or branded placeholder header
    thumb_url = _gdrive_thumbnail(r['url'] or '')
    if thumb_url:
        thumb_html = (
            f'<a href="{esc(r["url"])}" target="_blank" rel="noopener" tabindex="-1"'
            f' style="display:block;margin:-14px -14px 12px;border-radius:8px 8px 0 0;overflow:hidden;flex-shrink:0;">'
            f'<img src="{thumb_url}" alt="" loading="lazy"'
            f' style="width:100%;height:120px;object-fit:cover;display:block;"'
            f" onerror=\"this.parentElement.outerHTML='<div style=\\'{fallback_style}\\'>{svg_js}</div>';\">"
            f'</a>'
        )
    else:
        thumb_html = (
            f'<div style="margin:-14px -14px 12px;height:80px;border-radius:8px 8px 0 0;'
            f'background:{bg_color};display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
            f'{placeholder_svg}'
            f'</div>'
        )
    pad = '20px 14px 14px 28px' if is_admin else '14px'
    return (
        f'<div class="res-tile" data-id="{r["id"]}" data-tags="{esc(tag_data)}"'
        f' data-search="{esc(search_data)}"'
        f' style="position:relative;background:var(--jag-card);border:2px solid {border_color};'
        f'border-radius:10px;padding:{pad};display:flex;flex-direction:column;'
        f'word-break:break-word;overflow:hidden;transition:box-shadow 0.15s,transform 0.15s;"'
        f' onmouseover="this.style.boxShadow=\'0 4px 16px rgba(45,50,59,0.15)\';this.style.transform=\'translateY(-2px)\';"'
        f' onmouseout="this.style.boxShadow=\'\';this.style.transform=\'\';">'
        f'{drag}'
        f'{thumb_html}'
        f'<a href="{esc(r["url"])}" target="_blank" rel="noopener"'
        f' style="font-weight:700;font-size:14px;color:var(--jag-navy);text-decoration:none;line-height:1.3;"'
        f' onmouseover="this.style.textDecoration=\'underline\';" onmouseout="this.style.textDecoration=\'none\';">'
        f'{esc(r["name"])} <span style="font-size:11px;opacity:0.5;">&#8599;</span></a>'
        f'{desc}'
        f'{self_org_badge}'
        f'{tags_html}'
        f'{admin_actions}'
        f'</div>'
    )


def _resource_tile_wrap(tiles_html, list_id=None):
    """Wrap resource tiles in a CSS grid container."""
    list_attr = f' data-list-id="{list_id}"' if list_id is not None else ""
    return f'<div class="res-tiles-wrap" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px;padding:8px 0 12px;align-items:stretch;"{list_attr}>{tiles_html}</div>'


def resources_page(user, folder_groups, ungrouped, folders, tags=None, tags_by_resource=None, message=None, error=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    is_admin = user.get("is_admin")
    tags = tags or []
    tags_by_resource = tags_by_resource or {}

    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}">{esc(f["name"])}</option>' for f in folders
    )

    # Build folder sections — link tile layout
    folder_sections = ""
    for folder, resources in folder_groups:
        tiles_html = "".join(_resource_tile(r, is_admin=is_admin, tags=tags_by_resource.get(r['id'], [])) for r in resources)
        count = len(resources)
        count_text = f'<span class="muted" style="font-size:14px; font-weight:400;">&nbsp;({count} link{"s" if count != 1 else ""})</span>'
        list_content = _resource_tile_wrap(tiles_html, list_id=folder['id']) if tiles_html else '<p class="muted" style="margin:8px 0 0; font-size:13px;">No resources in this folder yet.</p>'
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder folders" style="cursor:grab; color:var(--jag-muted); font-size:16px;">&#9776;</span>' if is_admin else ""
        is_protected_folder = folder['name'].strip().lower() in (
            "measurement games",
            "general athleticism measurement games",
        )
        delete_btn = f"""<form method="post" action="/coach/resources/folders/{folder['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete folder \\'{esc(folder['name'])}\\'? Resources will move to Ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm" style="font-size:12px;">Delete folder</button>
            </form>""" if is_admin and not is_protected_folder else ""
        rename_html = f"""<button type="button" class="btn btn-ghost btn-sm" style="font-size:12px;"
              onclick="var w=document.getElementById('rename-wrap-{folder['id']}');w.style.display=w.style.display==='none'?'flex':'none';"
              title="Rename folder">&#9998; Rename</button>
            <span id="rename-wrap-{folder['id']}" style="display:none; align-items:center; gap:4px; margin-top:4px;">
              <form method="post" action="/coach/resources/folders/{folder['id']}/rename"
                    style="display:inline-flex; gap:4px; align-items:center;">
                <input type="text" name="folder_name" value="{esc(folder['name'])}"
                       style="padding:4px 8px; font-size:13px; width:200px; border-radius:6px; border:1px solid var(--jag-border);" />
                <button type="submit" class="btn btn-primary btn-sm">Save</button>
              </form>
            </span>""" if is_admin else ""
        admin_actions = f'<div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-left:auto;">{rename_html}{delete_btn}</div>' if is_admin else ""
        folder_sections += f"""
        <div class="res-section" data-folder-id="{folder['id']}" style="margin-bottom:44px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            {folder_handle}
            <div style="border-left:4px solid var(--jag-green);padding-left:12px;flex:1;min-width:0;">
              <h2 style="margin:0;font-size:20px;font-weight:700;color:var(--jag-navy);line-height:1.2;">{esc(folder['name'])}</h2>
              <span style="font-size:13px;color:var(--jag-muted);">{count} resource{"s" if count != 1 else ""}</span>
            </div>
            {admin_actions}
          </div>
          {list_content}
        </div>"""

    # Ungrouped section
    ug_tiles_html = "".join(_resource_tile(r, is_admin=is_admin, tags=tags_by_resource.get(r['id'], [])) for r in ungrouped)
    ug_count = len(ungrouped)
    ug_count_text = f'<span class="muted" style="font-size:14px; font-weight:400;">&nbsp;({ug_count} link{"s" if ug_count != 1 else ""})</span>'
    ungrouped_list_html = _resource_tile_wrap(ug_tiles_html, list_id="ungrouped") if ug_tiles_html else '<p class="muted" style="margin:8px 0 0; font-size:13px;">No ungrouped resources.</p>'
    ungrouped_section = f"""
    <div class="res-section" style="margin-bottom:44px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="border-left:4px solid var(--jag-border);padding-left:12px;">
          <h2 style="margin:0;font-size:20px;font-weight:700;color:var(--jag-muted);line-height:1.2;">Ungrouped</h2>
          <span style="font-size:13px;color:var(--jag-muted);">{ug_count} resource{"s" if ug_count != 1 else ""}</span>
        </div>
      </div>
      {ungrouped_list_html}
    </div>""" if ungrouped or is_admin else ""

    # Tag checkboxes for the Add Resource form
    tag_checkboxes_add = "".join(
        f'<label style="display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:400;margin:0 8px 4px 0;cursor:pointer;">'
        f'<input type="checkbox" name="tag_ids" value="{t["id"]}" style="width:auto;margin:0;" />{esc(t["name"])}</label>'
        for t in tags
    )
    tag_checkboxes_section = f'<label style="margin-top:10px;">Tags</label><div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{tag_checkboxes_add}</div>' if tags else ''

    # Manage Tags section (admin only)
    tag_rows = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;background:var(--jag-green);color:var(--jag-navy);border-radius:999px;padding:3px 10px;font-size:13px;font-weight:600;">'
        f'{esc(t["name"])}'
        f'<form method="post" action="/coach/resources/tags/{t["id"]}/delete" style="display:inline;margin:0;" onsubmit="return confirm(\'Delete tag \\\'{esc(t["name"])}\\\' ?\');">'
        f'<button type="submit" style="background:none;border:none;cursor:pointer;font-size:14px;line-height:1;color:var(--jag-navy);padding:0 0 0 4px;" title="Delete tag">&times;</button>'
        f'</form></span>'
        for t in tags
    ) if tags else '<span style="color:var(--jag-muted);font-size:13px;">No tags yet.</span>'

    manage_forms = f"""
    <div style="display:flex; gap:10px; margin-bottom:28px; flex-wrap:wrap;">
      <button type="button" class="btn btn-primary" onclick="var p=document.getElementById('res-add-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Add Resource</button>
      <button type="button" class="btn btn-ghost" onclick="var p=document.getElementById('folder-add-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Create Folder</button>
      <button type="button" class="btn btn-ghost" onclick="var p=document.getElementById('tags-panel');p.style.display=p.style.display==='none'?'block':'none';">&#127991; Manage Tags</button>
    </div>
    <div id="res-add-panel" style="display:none; margin-bottom:24px;">
      <div class="card form-card" style="max-width:480px;">
        <h2 style="margin-top:0; font-size:16px;">Add a resource</h2>
        <form method="post" action="/coach/resources/new">
          <label for="res_name">Name</label>
          <input type="text" id="res_name" name="name" required placeholder="e.g. Diamond Games Guide" />
          <label for="res_url">URL</label>
          <input type="url" id="res_url" name="url" required placeholder="https://..." />
          <label for="res_desc">Description (optional)</label>
          <input type="text" id="res_desc" name="description" placeholder="A short note" />
          <label for="res_so">Self-organisation focus (optional)</label>
          <input type="text" id="res_so" name="self_organisation" placeholder="e.g. Spatial awareness &amp; decision making" />
          <label for="res_folder">Folder (optional)</label>
          <select id="res_folder" name="folder_id">{folder_opts}</select>
          {tag_checkboxes_section}
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Add Resource</button>
        </form>
      </div>
    </div>
    <div id="folder-add-panel" style="display:none; margin-bottom:24px;">
      <div class="card form-card" style="max-width:360px;">
        <h2 style="margin-top:0; font-size:16px;">Create a folder</h2>
        <form method="post" action="/coach/resources/folders/new">
          <label for="folder_name">Folder name</label>
          <input type="text" id="folder_name" name="folder_name" required placeholder="e.g. Coaching Guides" />
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Create Folder</button>
        </form>
      </div>
    </div>
    <div id="tags-panel" style="display:none; margin-bottom:24px;">
      <div class="card form-card" style="max-width:520px;">
        <h2 style="margin-top:0; font-size:16px;">Manage Tags</h2>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;">{tag_rows}</div>
        <form method="post" action="/coach/resources/tags/new" style="display:flex;gap:8px;align-items:flex-end;">
          <div style="flex:1;">
            <label for="tag_name" style="font-size:13px;font-weight:600;">New tag name</label>
            <input type="text" id="tag_name" name="tag_name" required placeholder="e.g. Video" style="margin-top:4px;" />
          </div>
          <button type="submit" class="btn btn-primary">Add Tag</button>
        </form>
      </div>
    </div>""" if is_admin else ""

    sortable_js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.2/Sortable.min.js"></script>
    <script>
    function post(url, body) {
      fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: body,
      });
    }
    function postOrder(url, ids) { post(url, 'ids=' + ids.join(',')); }

    // Drag to reorder folders
    var foldersContainer = document.getElementById('folders-container');
    if (foldersContainer) {
      Sortable.create(foldersContainer, {
        handle: '.folder-handle',
        animation: 150,
        onEnd: function() {
          var ids = Array.from(foldersContainer.querySelectorAll('.res-section[data-folder-id]'))
                        .map(function(el) { return el.dataset.folderId; });
          postOrder('/coach/resources/folders/reorder', ids);
        }
      });
    }

    // Drag resources within and between lists
    document.querySelectorAll('.res-tiles-wrap[data-list-id]').forEach(function(list) {
      Sortable.create(list, {
        group: { name: 'resources', pull: true, put: true },
        handle: '.drag-handle:not(.folder-handle)',
        animation: 150,
        ghostClass: 'res-tile--ghost',
        onEnd: function(evt) {
          var fromList = evt.from;
          var toList   = evt.to;
          var itemId   = evt.item.dataset.id;
          if (fromList !== toList) {
            var newListId = toList.dataset.listId;
            var folderId  = (newListId === 'ungrouped') ? '' : newListId;
            post('/coach/resources/' + itemId + '/move', 'folder_id=' + folderId);
          }
          var destIds = Array.from(toList.querySelectorAll('.res-tile'))
                            .map(function(el) { return el.dataset.id; });
          postOrder('/coach/resources/reorder', destIds);
        }
      });
    });
    </script>""" if is_admin else ""

    # Search bar + tag filter buttons
    tag_filter_btns = "".join(
        f'<button type="button" class="res-tag-filter btn btn-ghost btn-sm" data-tag="{esc(t["name"].lower())}" '
        f'style="border-radius:999px;">{esc(t["name"])}</button>'
        for t in tags
    )
    search_bar = f"""
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:20px;">
      <input type="search" id="res-search" placeholder="Search resources…"
             style="max-width:260px;padding:8px 12px;border-radius:8px;border:1px solid var(--jag-border);font-size:14px;" />
      {tag_filter_btns}
      <button type="button" id="res-clear-filter" class="btn btn-ghost btn-sm" style="display:none;border-radius:999px;">&#10005; Clear</button>
    </div>
    <script>
    (function() {{
      var searchInput  = document.getElementById('res-search');
      var clearBtn     = document.getElementById('res-clear-filter');
      var activeTag    = null;

      function filterTiles() {{
        var query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        document.querySelectorAll('.res-tile').forEach(function(tile) {{
          var matchSearch = !query || (tile.dataset.search || '').indexOf(query) !== -1;
          var matchTag    = !activeTag || (tile.dataset.tags || '').split(',').indexOf(activeTag) !== -1;
          tile.style.display = (matchSearch && matchTag) ? '' : 'none';
        }});
        if (clearBtn) clearBtn.style.display = (query || activeTag) ? 'inline-block' : 'none';
      }}

      if (searchInput) searchInput.addEventListener('input', filterTiles);

      document.querySelectorAll('.res-tag-filter').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
          if (activeTag === btn.dataset.tag) {{
            activeTag = null;
            btn.style.background = '';
            btn.style.color = '';
          }} else {{
            activeTag = btn.dataset.tag;
            document.querySelectorAll('.res-tag-filter').forEach(function(b) {{
              b.style.background = '';
              b.style.color = '';
            }});
            btn.style.background = 'var(--jag-green)';
            btn.style.color = 'var(--jag-navy)';
          }}
          filterTiles();
        }});
      }});

      if (clearBtn) {{
        clearBtn.addEventListener('click', function() {{
          if (searchInput) searchInput.value = '';
          activeTag = null;
          document.querySelectorAll('.res-tag-filter').forEach(function(b) {{
            b.style.background = '';
            b.style.color = '';
          }});
          filterTiles();
        }});
      }}
    }})();
    </script>"""

    body = f"""
    <style>
    .res-tile {{ transition: box-shadow 0.18s ease, transform 0.18s ease; }}
    .res-tile:hover {{ box-shadow: 0 8px 28px rgba(0,0,0,0.14); transform: translateY(-3px); }}
    </style>
    <div style="max-width:1320px;">
    <div class="page-head">
      <h1>Resources</h1>
      <a href="/coach/resources/report" class="btn btn-ghost" target="_blank">&#128196; Print Report</a>
    </div>
    {message_html}{error_html}
    {manage_forms}
    {search_bar}
    <div id="folders-container">{folder_sections}</div>
    {ungrouped_section}
    </div>
    {sortable_js}
    """
    return layout("Resources", body, user=user, active_nav="resources")


def edit_resource_page(user, resource, folders, all_tags=None, selected_tag_ids=None, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}" {"selected" if resource["folder_id"] == f["id"] else ""}>{esc(f["name"])}</option>'
        for f in folders
    )
    all_tags = all_tags or []
    selected_tag_ids = selected_tag_ids or []
    tag_checkboxes = "".join(
        f'<label style="display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:400;margin:0 8px 4px 0;cursor:pointer;">'
        f'<input type="checkbox" name="tag_ids" value="{t["id"]}" {"checked" if t["id"] in selected_tag_ids else ""} style="width:auto;margin:0;" />{esc(t["name"])}</label>'
        for t in all_tags
    )
    tags_section = f'<label style="margin-top:10px;">Tags</label><div style="display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;">{tag_checkboxes}</div>' if all_tags else ''
    body = f"""
    <div class="page-head">
      <h1>Edit Resource</h1>
      <a class="btn btn-ghost" href="/coach/resources">&larr; Back</a>
    </div>
    {error_html}
    <div class="card form-card" style="max-width:520px;">
      <form method="post" action="/coach/resources/{resource['id']}/edit">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" required value="{esc(resource['name'])}" />
        <label for="url">URL</label>
        <input type="url" id="url" name="url" required value="{esc(resource['url'])}" />
        <label for="description">Description (optional)</label>
        <input type="text" id="description" name="description" value="{esc(resource['description'] or '')}" />
        <label for="self_organisation">Self-organisation focus (optional)</label>
        <input type="text" id="self_organisation" name="self_organisation" value="{esc(resource.get('self_organisation') or '')}" placeholder="e.g. Spatial awareness &amp; decision making" />
        <label for="folder_id">Folder</label>
        <select id="folder_id" name="folder_id">{folder_opts}</select>
        {tags_section}
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Save Changes</button>
      </form>
    </div>
    """
    return layout("Edit Resource", body, user=user, active_nav="resources")


def resources_report_page(user, all_folders, org=None, orgs=None):
    """Printable report of all resources with their self-organisation focus."""
    orgs = orgs or []
    org_opts = "".join(
        f'<option value="/coach/resources/report?org_id={o["id"]}"'
        f'{"selected" if org and o["id"] == org["id"] else ""}>{esc(o["name"])}</option>'
        for o in orgs
    )
    filter_bar = f"""
    <div class="no-print" style="margin-bottom:24px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <span style="font-size:13px;font-weight:600;color:var(--jag-muted);">Filter by organisation:</span>
      <select onchange="window.location=this.value" style="max-width:260px;">
        <option value="/coach/resources/report">All resources</option>
        {org_opts}
      </select>
      <button onclick="window.print()" class="btn btn-primary" style="margin-left:auto;">&#128196; Print / Save as PDF</button>
      <a href="/coach/resources" class="btn btn-ghost">← Back</a>
    </div>""" if orgs else f"""
    <div class="no-print" style="margin-bottom:24px;display:flex;gap:8px;justify-content:flex-end;">
      <button onclick="window.print()" class="btn btn-primary">&#128196; Print / Save as PDF</button>
      <a href="/coach/resources" class="btn btn-ghost">← Back</a>
    </div>"""

    org_title = f" — {esc(org['name'])}" if org else ""

    # Build report sections
    sections_html = ""
    has_so = any(
        (r.get("self_organisation") or "")
        for _, rs in all_folders
        for r in (rs if isinstance(rs, list) else [])
    )
    for folder, resources in all_folders:
        if not resources:
            continue
        folder_name = folder["name"] if isinstance(folder, dict) and folder != "__ungrouped__" else "Other Resources"
        rows = ""
        for r in resources:
            so = r.get("self_organisation") or ""
            desc = r.get("description") or ""
            rows += f"""
            <tr>
              <td style="padding:10px 12px;font-weight:600;font-size:13px;color:#2D323B;border-bottom:1px solid #e8e9ea;vertical-align:top;">
                <a href="{esc(r['url'])}" style="color:#2D323B;text-decoration:none;">{esc(r['name'])} <span style="font-size:10px;opacity:0.4;">&#8599;</span></a>
                {f'<div style="font-size:11px;color:#777;margin-top:2px;">{esc(desc)}</div>' if desc else ''}
              </td>
              <td style="padding:10px 12px;font-size:13px;color:#F0A82E;font-weight:600;border-bottom:1px solid #e8e9ea;vertical-align:top;">{esc(so) if so else '<span style="color:#ccc;font-weight:400;">—</span>'}</td>
            </tr>"""
        sections_html += f"""
        <div style="margin-bottom:32px;break-inside:avoid;">
          <h2 style="font-size:14px;font-weight:800;text-transform:uppercase;letter-spacing:0.08em;
                     color:#fff;background:#2D323B;padding:8px 14px;border-radius:6px 6px 0 0;margin:0;">
            {esc(folder_name)}
          </h2>
          <table style="width:100%;border-collapse:collapse;border:1px solid #e8e9ea;border-top:none;border-radius:0 0 6px 6px;overflow:hidden;">
            <thead>
              <tr style="background:#F3F4F5;">
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#666;width:60%;">Resource</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#666;width:40%;">Self-Organisation Focus</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    if not sections_html:
        sections_html = '<p style="color:#777;font-size:14px;">No resources found.</p>'

    today = _dt.date.today().strftime("%d %B %Y")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JAG Resources Report{org_title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Inter, system-ui, sans-serif; background: #fff; color: #2D323B; padding: 32px; max-width: 900px; margin: 0 auto; }}
  .no-print {{ }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ padding: 16px; }}
    a {{ color: inherit !important; }}
  }}
</style>
</head>
<body>
  <div class="no-print">{filter_bar}</div>
  <div style="display:flex;align-items:center;gap:16px;margin-bottom:28px;padding-bottom:16px;border-bottom:3px solid #F0A82E;">
    <div style="width:48px;height:48px;background:#2D323B;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
      <svg width="28" height="28" fill="#F0A82E" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
    </div>
    <div>
      <h1 style="font-size:22px;font-weight:800;color:#2D323B;line-height:1.1;">Measurement Games — Resource Guide{org_title}</h1>
      <p style="font-size:12px;color:#888;margin-top:4px;">Generated {today} &nbsp;·&nbsp; Just A Game</p>
    </div>
  </div>
  {'<p style="font-size:13px;color:#555;margin-bottom:24px;padding:10px 14px;background:#fffbe6;border-left:4px solid #F0A82E;border-radius:4px;"><strong>Self-organisation focus</strong> describes the adaptive and perceptual challenge each activity is designed to explore.</p>' if has_so else ''}
  {sections_html}
</body>
</html>"""
    # Return raw HTML — bypass the layout() wrapper so print CSS works cleanly
    return html


def scores_import_form(user, groups=None, orgs=None, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    groups = groups or []
    orgs = orgs or []

    group_opts = '<option value="">— No group filter —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )

    # Template download section — blank, by group, or by org
    group_template_opts = "".join(
        f'<option value="/coach/scores/import/template.csv?group_id={g["id"]}">{esc(g["name"])}</option>'
        for g in groups
    )
    org_template_opts = "".join(
        f'<option value="/coach/scores/import/template.csv?org_id={o["id"]}">{esc(o["name"])}</option>'
        for o in orgs
    )
    template_section = f"""
    <div style="background:var(--jag-card);border:1px solid var(--jag-border);border-radius:10px;padding:16px 20px;margin-bottom:24px;display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;">
      <div>
        <p style="margin:0 0 6px;font-size:13px;font-weight:600;">Download blank template</p>
        <a href="/coach/scores/import/template.csv" class="btn btn-ghost btn-sm">&#8681; All columns (no athletes)</a>
      </div>
      {'<div><p style="margin:0 0 6px;font-size:13px;font-weight:600;">Pre-filled by group</p><select id="tmpl-group" onchange="if(this.value)window.location=this.value" style="max-width:220px;"><option value="">Select group…</option>' + group_template_opts + '</select></div>' if groups else ''}
      {'<div><p style="margin:0 0 6px;font-size:13px;font-weight:600;">Pre-filled by organisation</p><select id="tmpl-org" onchange="if(this.value)window.location=this.value" style="max-width:220px;"><option value="">Select organisation…</option>' + org_template_opts + '</select></div>' if orgs else ''}
    </div>"""

    # Build a reference table of column names
    col_rows = ""
    for section in active_measurement_games():
        for game in section["games"]:
            for field in game.get("fields", []):
                col_rows += (
                    f'<tr><td style="font-family:monospace;font-size:12px;color:var(--jag-navy);padding:3px 10px 3px 0;">'
                    f'{esc(game["key"])}.{esc(field["key"])}</td>'
                    f'<td style="font-size:12px;color:var(--jag-muted);">{esc(game["name"])} — {esc(field["label"])}</td></tr>'
                )
            for field in game.get("computed", []):
                col_rows += (
                    f'<tr><td style="font-family:monospace;font-size:12px;color:#999;padding:3px 10px 3px 0;">'
                    f'{esc(game["key"])}.{esc(field["key"])}</td>'
                    f'<td style="font-size:12px;color:#bbb;">{esc(game["name"])} — {esc(field["label"])} <em>(auto-computed if omitted)</em></td></tr>'
                )

    body = f"""
    <div class="page-head">
      <div>
        <h1>Import Scores from CSV</h1>
        <p class="muted">Bulk-upload test scores for existing athletes. Each row becomes one measurement session on the selected date.</p>
      </div>
      <a href="/coach" class="btn btn-ghost">← Back</a>
    </div>
    {template_section}
    {error_html}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;max-width:1100px;align-items:start;">
      <div>
        <form method="post" action="/coach/scores/import" enctype="multipart/form-data">
          <div class="form-group">
            <label>Session Date <span style="color:red;">*</span></label>
            <input type="date" name="session_date" required style="max-width:220px;" />
            <small class="muted">All rows in this import are recorded on this date.</small>
          </div>
          <div class="form-group">
            <label>Group (optional)</label>
            <select name="group_id" style="max-width:300px;">{group_opts}</select>
            <small class="muted">Overrides each athlete's current group for the session snapshot. Leave blank to use their assigned group.</small>
          </div>
          <div class="form-group">
            <label>CSV File</label>
            <input type="file" name="csv_file" accept=".csv,.txt" />
            <small class="muted">Or paste CSV content below.</small>
          </div>
          <div class="form-group">
            <label>Paste CSV (optional)</label>
            <textarea name="csv_data" rows="8" placeholder="athlete_number,skipping_rope_sprint.time_1,balance_ball_catching.one_foot_balance_catch&#10;001,4.52,12&#10;002,5.10,9" style="font-family:monospace;font-size:13px;width:100%;"></textarea>
          </div>
          <button type="submit" class="btn btn-primary">Import Scores</button>
        </form>
      </div>
      <div>
        <h3 style="margin-top:0;font-size:15px;">CSV Format</h3>
        <p style="font-size:13px;color:var(--jag-muted);">First column must be <code>athlete_number</code>. Each additional column is named <code>game_key.field_key</code>. Blank cells are skipped — you don't need to include all games.</p>
        <p style="font-size:13px;color:var(--jag-muted);">Download the template above to get a pre-built header row with every available column.</p>
        <div style="max-height:400px;overflow-y:auto;border:1px solid var(--jag-border);border-radius:8px;padding:12px;">
          <table style="border-collapse:collapse;width:100%;">
            <thead><tr>
              <th style="font-size:11px;text-align:left;padding:3px 10px 6px 0;color:var(--jag-muted);border-bottom:1px solid var(--jag-border);">Column name</th>
              <th style="font-size:11px;text-align:left;padding:3px 0 6px;color:var(--jag-muted);border-bottom:1px solid var(--jag-border);">Field</th>
            </tr></thead>
            <tbody>
              <tr><td style="font-family:monospace;font-size:12px;color:var(--jag-green);padding:3px 10px 3px 0;font-weight:700;">athlete_number</td><td style="font-size:12px;">Athlete ID (required)</td></tr>
              {col_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>"""
    return layout("Import Scores", body, user=user, active_nav="dashboard")


def participant_import_form(user, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    body = f"""
    <div class="page-head">
      <div>
        <h1>Import Athletes from CSV</h1>
        <p class="muted">Paste CSV content below to bulk-create athletes. Existing athlete numbers are skipped (safe to re-run).</p>
      </div>
      <div><a class="btn btn-ghost" href="/coach">&larr; Back</a></div>
    </div>
    {error_html}

    <div class="card form-card" style="max-width:680px;">
      <h3 style="margin-top:0;font-size:14px;color:var(--jag-muted);text-transform:uppercase;letter-spacing:.04em;">CSV Format</h3>
      <p style="font-size:13px;margin:0 0 12px;">Use <code>First Name</code> and <code>Last Name</code> as separate columns, or a single <code>Name</code> column. All other columns are optional.</p>
      <pre style="background:var(--jag-bg);border:1px solid var(--jag-border);border-radius:8px;padding:12px;font-size:12px;overflow-x:auto;margin:0 0 16px;">First Name,Last Name,Organisation,Group,Gender,Sport
Jane,Smith,Masterton School,Under 12s,Female,Football
Tom,Brown,Wellington College,Under 14s,Male,Basketball
Alex,Lee,Masterton School,Under 12s,Male,Football</pre>
      <ul style="font-size:13px;color:var(--jag-muted);margin:0 0 20px;padding-left:18px;">
        <li>Column order doesn't matter — headers are matched by name.</li>
        <li>Groups are created automatically if they don't exist.</li>
        <li>Athletes without a login are created as data-only records — use Export CSV to get temp passwords.</li>
        <li>If <code>athlete_number</code> is provided and already exists, that row is skipped (safe to re-run).</li>
      </ul>

      <form method="post" action="/coach/participants/import" enctype="multipart/form-data">
        <label style="display:block;font-weight:600;margin-bottom:6px;">Upload CSV file</label>
        <input type="file" name="csv_file" accept=".csv,.txt"
               style="display:block;margin-bottom:16px;font-size:13px;" />
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
          <div style="flex:1;height:1px;background:var(--jag-border);"></div>
          <span style="font-size:12px;color:var(--jag-muted);white-space:nowrap;">or paste CSV below</span>
          <div style="flex:1;height:1px;background:var(--jag-border);"></div>
        </div>
        <textarea name="csv_data" rows="10" style="width:100%;box-sizing:border-box;font-family:monospace;font-size:13px;
          border:1px solid var(--jag-border);border-radius:8px;padding:10px;resize:vertical;"
          placeholder="First Name,Last Name,Organisation,Group,Gender,Sport&#10;Jane,Smith,Makoura College,Under 12s,Female,Football&#10;..."></textarea>
        <div style="margin-top:14px;display:flex;gap:8px;">
          <button type="submit" class="btn btn-primary">Import Athletes</button>
          <a class="btn btn-ghost" href="/coach">Cancel</a>
        </div>
      </form>
    </div>
    """
    return layout("Import Athletes", body, user=user, active_nav="dashboard")



# ══════════════════════════════════════════════════════════════════════════════
# XP ENGINE VIEWS
# ══════════════════════════════════════════════════════════════════════════════

_XP_TYPE_LABELS = {
    "formal_game":        "Formal session",
    "self_directed_game": "Self-directed session",
    "pb_formal":          "Personal best (formal)",
    "pb_self":            "Personal best (self-directed)",
    "ingame_formal":      "In-game score",
    "ingame_self":        "In-game score (self-directed)",
    "level_achievement":  "Level achieved",
    "breadth_first_game": "First time playing",
    "welcome_bonus":      "Welcome bonus",
    "streak_3":           "3-session streak",
    "streak_5":           "5-session streak",
    "all_8_session":      "All 8 games in one session",
    "all_8_l1":           "Level 1 in all 8 games",
}

_GAME_DISPLAY_NAMES = {
    "skipping_rope_sprint":  "Skipping Rope Sprint",
    "balance_ball_catching": "Balance Catching",
    "leap_catching_throwing": "Grid Leap",
    "split_step":            "Split Step",
    "diamond_games":         "Diamond Gates",
    "diamond_dribble":       "Diamond Dribble",
    "diamond_gym":           "Step Up",
    "lob_scotch":            "Lob Scotch",
}

_LEVEL_COLOURS = {
    1: ("#1EBE8B", "#fff"),
    2: ("#F0A82E", "#2D323B"),
    3: ("#2D323B", "#fff"),
    4: ("#F97316", "#fff"),
    5: ("#8B5CF6", "#fff"),
}


def _xp_event_row(event, i):
    xp_type = event.get("xp_type", "")
    label = _XP_TYPE_LABELS.get(xp_type, xp_type.replace("_", " ").title())
    game = _GAME_DISPLAY_NAMES.get(event.get("game_key"), event.get("game_key") or "")
    amount = int(event.get("amount", 0))
    created = (event.get("created_at") or "")[:10]
    shade = "#F3F4F5" if i % 2 == 0 else "#fff"
    game_chip = (
        f'<span style="font-size:11px;background:#2D323B;color:#fff;border-radius:999px;'
        f'padding:2px 8px;margin-left:6px;">{esc(game)}</span>'
        if game else ""
    )
    return f"""
    <tr style="background:{shade};">
      <td style="padding:9px 14px;font-size:13px;color:#2D323B;">{esc(label)}{game_chip}</td>
      <td style="padding:9px 14px;font-size:13px;color:#6E737B;">{esc(created)}</td>
      <td style="padding:9px 14px;font-size:13px;font-weight:700;color:#2D323B;text-align:right;">+{amount:,} AXP</td>
    </tr>"""


def athlete_xp_page(athlete, xp_data, levels, coach=None):
    """XP profile page — usable by both athletes (self-view) and coaches (viewing an athlete)."""
    name = esc(athlete.get("name", "Athlete"))
    total = xp_data.get("total", 0)
    tier = xp_data.get("tier", {})
    next_tier = xp_data.get("next_tier")
    progress = xp_data.get("progress", 0.0)
    events = xp_data.get("events", [])
    tier_label = tier.get("label", "Starter")
    tier_colour = tier.get("colour", "#6E737B")

    # ── Rank hero card ────────────────────────────────────────────────────────
    if next_tier:
        xp_to_next = next_tier["min_xp"] - total
        next_label = next_tier["label"]
        next_colour = next_tier["colour"]
        progress_bar = f"""
        <div style="margin-top:16px;">
          <div style="display:flex;justify-content:space-between;font-size:12px;color:rgba(255,255,255,0.75);margin-bottom:6px;">
            <span>{tier_label}</span><span>{esc(next_label)}</span>
          </div>
          <div style="background:rgba(255,255,255,0.25);border-radius:999px;height:10px;overflow:hidden;">
            <div style="width:{int(progress*100)}%;background:#fff;height:100%;border-radius:999px;transition:width 0.6s;"></div>
          </div>
          <div style="text-align:right;font-size:12px;color:rgba(255,255,255,0.75);margin-top:5px;">
            {xp_to_next:,} AXP to {esc(next_label)}
          </div>
        </div>"""
    else:
        progress_bar = f"""
        <div style="margin-top:16px;font-size:13px;color:rgba(255,255,255,0.8);">
          Maximum rank achieved — keep earning AXP!
        </div>"""

    hero = f"""
    <div style="background:{tier_colour};border-radius:16px;padding:28px 32px;margin-bottom:28px;color:#fff;">
      <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <div style="flex:1;min-width:200px;">
          <div style="font-size:13px;opacity:0.8;text-transform:uppercase;letter-spacing:0.08em;">Rank</div>
          <div style="font-size:36px;font-weight:800;line-height:1.1;">{esc(tier_label)}</div>
          <div style="font-size:14px;opacity:0.85;margin-top:4px;">{name}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:48px;font-weight:900;line-height:1;">{total:,}</div>
          <div style="font-size:14px;opacity:0.8;">AXP total</div>
        </div>
      </div>
      {progress_bar}
    </div>"""

    # ── Level achievements grid ───────────────────────────────────────────────
    level_chips = ""
    for game_key, display in _GAME_DISPLAY_NAMES.items():
        lvl = levels.get(game_key, 0)
        bg, fg = _LEVEL_COLOURS.get(lvl, ("#E5E7EB", "#6E737B")) if lvl else ("#F3F4F5", "#9CA3AF")
        label_text = f"L{lvl}" if lvl else "—"
        level_chips += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
          padding:10px 14px;background:#fff;border-radius:10px;border:1px solid #E5E7EB;">
          <span style="font-size:13px;color:#2D323B;font-weight:600;">{esc(display)}</span>
          <span style="font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;
            background:{bg};color:{fg};">{label_text}</span>
        </div>"""

    levels_section = f"""
    <div style="margin-bottom:32px;">
      <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:0 0 14px;">Level Achievements</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">
        {level_chips}
      </div>
    </div>"""

    # ── Recent XP events ──────────────────────────────────────────────────────
    rows = "".join(_xp_event_row(e, i) for i, e in enumerate(events))
    if not rows:
        rows = '<tr><td colspan="3" style="padding:20px;text-align:center;color:#9CA3AF;font-size:13px;">No AXP earned yet — complete a measurement session to get started.</td></tr>'

    events_section = f"""
    <div style="margin-bottom:32px;">
      <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:0 0 14px;">Recent AXP Events</h3>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;">
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;font-weight:600;">Event</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;font-weight:600;">Date</th>
              <th style="padding:10px 14px;text-align:right;font-size:12px;color:#fff;font-weight:600;">AXP</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""

    back_link = ""
    if coach:
        back_link = f'<a href="/coach/participants/{esc(str(athlete.get("id","")))}" class="btn btn-ghost btn-sm" style="margin-bottom:20px;">← Back to Profile</a>'

    body = f"""
    <div class="container" style="max-width:860px;padding-top:32px;">
      {back_link}
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 24px;">
        {"AAXP Profile — " + name if coach else "My AXP Profile"}
      </h2>
      {hero}
      {levels_section}
      {events_section}
    </div>"""

    user = coach if coach else athlete
    return layout("AXP Profile", body, user=user,
                  active_nav="dashboard" if coach else "dashboard")


def game_thresholds_page(coach, thresholds, core_games, xp_game_config):
    """System admin page for managing per-game level thresholds."""
    from constants import find_measurement_game, GAME_LEVEL_DESCRIPTIONS
    # Build a dict for easy lookup
    existing = {}
    for t in thresholds:
        existing[(t["game_key"], t["level"])] = dict(t)

    rows_html = ""
    for game_key in core_games:
        display = GAME_DISPLAY_NAMES.get(game_key, game_key)
        cfg = xp_game_config.get(game_key, {})
        primary_field = cfg.get("primary_field", "")
        lower = cfg.get("lower_is_better", False)
        game_def = find_measurement_game(game_key) or {}
        hint = game_def.get("level_threshold_hint", "")
        level_descs = GAME_LEVEL_DESCRIPTIONS.get(game_key, [])

        hint_html = (f'<div style="font-size:11px;color:#9CA3AF;margin-top:2px;">{esc(hint)}</div>'
                     if hint else "")

        rows_html += f"""
        <tr>
          <td colspan="5" style="padding:12px 14px 4px;background:#2D323B;">
            <div style="font-size:13px;font-weight:700;color:#F0A82E;letter-spacing:0.04em;">{esc(display)}</div>
            {hint_html}
          </td>
        </tr>"""

        for level in range(1, 6):
            bg, fg = _LEVEL_COLOURS.get(level, ("#E5E7EB", "#2D323B"))
            t = existing.get((game_key, level))
            curr_val = f'{t["threshold_value"]:g}' if t else ""
            curr_field = t["field_key"] if t else primary_field
            shade = "#F3F4F5" if level % 2 == 0 else "#fff"
            # Level description hint for practitioners
            lvl_desc = level_descs[level - 1] if level_descs and level <= len(level_descs) else ""
            desc_html = (f'<div style="font-size:11px;color:#6E737B;margin-top:2px;">{esc(lvl_desc)}</div>'
                         if lvl_desc else "")
            rows_html += f"""
            <tr style="background:{shade};">
              <td style="padding:8px 14px;vertical-align:top;">
                <span style="font-size:12px;font-weight:700;padding:2px 8px;border-radius:999px;
                  background:{bg};color:{fg};">L{level}</span>
                {desc_html}
              </td>
              <td style="padding:8px 14px;font-size:13px;color:#6E737B;vertical-align:middle;">{esc(curr_field)}</td>
              <td style="padding:8px 14px;font-size:13px;color:#2D323B;vertical-align:middle;">
                {f'<strong>{curr_val}</strong>' if curr_val else '<em style="color:#9CA3AF;">not set</em>'}
              </td>
              <td style="padding:8px 14px;vertical-align:middle;">
                <form method="post" action="/coach/admin/game-thresholds/set"
                      style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                  <input type="hidden" name="game_key" value="{esc(game_key)}" />
                  <input type="hidden" name="level" value="{level}" />
                  <input type="hidden" name="lower_is_better" value="{'1' if lower else '0'}" />
                  <input type="text" name="field_key" value="{esc(curr_field)}"
                         style="width:180px;font-size:12px;" placeholder="field key" />
                  <input type="number" name="threshold_value" value="{esc(curr_val)}"
                         step="0.01" style="width:90px;font-size:12px;" placeholder="value" />
                  <button type="submit" class="btn btn-primary btn-sm" style="font-size:12px;">Save</button>
                </form>
              </td>
              <td style="padding:8px 14px;vertical-align:middle;">
                {f'''<form method="post" action="/coach/admin/game-thresholds/delete">
                  <input type="hidden" name="game_key" value="{esc(game_key)}" />
                  <input type="hidden" name="level" value="{level}" />
                  <button class="btn btn-ghost btn-sm" style="font-size:12px;color:#DC2626;"
                    onclick="return confirm('Remove this threshold?')">Remove</button>
                </form>''' if t else ''}
              </td>
            </tr>"""

    body = f"""
    <div class="container" style="max-width:960px;padding-top:32px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:12px;">
        <div>
          <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 4px;">Game Level Thresholds</h2>
          <p style="font-size:13px;color:#6E737B;margin:0;">
            Set the score required for each level in each core game.
            Each game shows its threshold field and a plain-English description of what the level means.
            Thresholds can be updated at any time — once earned, an athlete's level is permanent.
          </p>
        </div>
        <form method="post" action="/coach/admin/xp-retroactive"
              onsubmit="return confirm('Run retroactive AXP pass over ALL existing sessions? This is safe to run multiple times but may take a moment.')">
          <button class="btn btn-primary">Run Retroactive AXP Pass</button>
        </form>
      </div>
      <div style="background:#EFF6FF;border-left:4px solid #2D323B;border-radius:8px;padding:12px 16px;
        margin-bottom:24px;font-size:13px;color:#2D323B;">
        <strong>How to set a threshold:</strong> enter the minimum score an athlete must reach on the
        listed field to earn that level. The field key is pre-filled from the game definition —
        only change it if you intentionally want a different field to drive the level check.
        For Skipping Rope Sprint, lower times are better (the system checks score ≤ threshold).
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;">
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Level</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Field</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Threshold</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Update</th>
              <th style="padding:10px 14px;font-size:12px;color:#fff;"></th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </div>"""

    return layout("Level Thresholds", body, user=coach, active_nav="dashboard")


# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE & SELF-DIRECTED VIEWS
# ══════════════════════════════════════════════════════════════════════════════

def attendance_list_page(coach, events):
    rows = ""
    for i, e in enumerate(events):
        shade = "#F3F4F5" if i % 2 == 0 else "#fff"
        date_str = e.get("date", "")[:10]
        group = esc(e.get("group_name") or "—")
        count = e.get("attendee_count", 0)
        notes = esc(e.get("notes") or "")
        rows += f"""
        <tr style="background:{shade};">
          <td style="padding:10px 14px;font-size:14px;color:#2D323B;">{esc(date_str)}</td>
          <td style="padding:10px 14px;font-size:14px;color:#2D323B;">{group}</td>
          <td style="padding:10px 14px;font-size:14px;color:#2D323B;text-align:center;">
            <span style="background:#1EBE8B;color:#fff;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;">{count}</span>
          </td>
          <td style="padding:10px 14px;font-size:13px;color:#6E737B;">{notes}</td>
          <td style="padding:10px 14px;white-space:nowrap;">
            <a href="/coach/attendance/{e['id']}/roll-call" class="btn btn-ghost btn-sm">Roll-Call</a>
            <a href="/coach/attendance/{e['id']}" class="btn btn-ghost btn-sm">View</a>
          </td>
        </tr>"""
    if not rows:
        rows = '<tr><td colspan="5" style="padding:24px;text-align:center;color:#9CA3AF;font-size:13px;">No sessions yet — create one to get started.</td></tr>'

    body = f"""
    <div class="container" style="max-width:900px;padding-top:32px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:12px;">
        <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0;">Session Attendance</h2>
        <a href="/coach/attendance/new" class="btn btn-primary">+ New Session</a>
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;">
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Date</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Group</th>
              <th style="padding:10px 14px;text-align:center;font-size:12px;color:#fff;">Present</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Notes</th>
              <th style="padding:10px 14px;font-size:12px;color:#fff;"></th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""
    return layout("Attendance", body, user=coach, active_nav="attendance")


def attendance_new_page(coach, groups):
    import datetime as _dt2
    today = _dt2.date.today().isoformat()
    group_opts = "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>'
        for g in groups
    )
    body = f"""
    <div class="container" style="max-width:560px;padding-top:32px;">
      <a href="/coach/attendance" class="btn btn-ghost btn-sm" style="margin-bottom:20px;">← Attendance</a>
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 24px;">New Session</h2>
      <form method="post" action="/coach/attendance/new">
        <div style="margin-bottom:16px;">
          <label style="display:block;font-weight:600;font-size:13px;margin-bottom:6px;">Group</label>
          <select name="group_id" style="width:100%;">
            <option value="">— All athletes —</option>
            {group_opts}
          </select>
        </div>
        <div style="margin-bottom:16px;">
          <label style="display:block;font-weight:600;font-size:13px;margin-bottom:6px;">Date</label>
          <input type="date" name="date" value="{today}" required style="width:100%;box-sizing:border-box;" />
        </div>
        <div style="margin-bottom:24px;">
          <label style="display:block;font-weight:600;font-size:13px;margin-bottom:6px;">Notes (optional)</label>
          <input type="text" name="notes" placeholder="e.g. Wet weather session" style="width:100%;box-sizing:border-box;" />
        </div>
        <div style="display:flex;gap:10px;">
          <button type="submit" class="btn btn-primary">Create & Take Roll-Call →</button>
          <a href="/coach/attendance" class="btn btn-ghost">Cancel</a>
        </div>
      </form>
    </div>"""
    return layout("New Session", body, user=coach, active_nav="attendance")


def roll_call_page(coach, event, athletes, already_marked):
    date_str = event.get("date", "")[:10]
    group_name = esc(event.get("group_name") or "All athletes")
    event_id = event["id"]

    athlete_checks = ""
    for a in athletes:
        pid = a["id"]
        checked = "checked" if pid in already_marked else ""
        name = esc(a.get("name", ""))
        num = esc(a.get("athlete_number") or "")
        athlete_checks += f"""
        <label style="display:flex;align-items:center;gap:12px;padding:11px 16px;
          cursor:pointer;border-radius:8px;transition:background 0.15s;"
          onmouseover="this.style.background='#F3F4F5'" onmouseout="this.style.background=''">
          <input type="checkbox" name="athlete_ids" value="{pid}" {checked}
            style="width:18px;height:18px;accent-color:#2D323B;cursor:pointer;" />
          <span style="flex:1;font-size:14px;color:#2D323B;font-weight:500;">{name}</span>
          {f'<span style="font-size:12px;color:#6E737B;">#{num}</span>' if num else ''}
        </label>"""

    if not athlete_checks:
        athlete_checks = '<p style="color:#9CA3AF;font-size:13px;padding:16px;">No athletes in this group.</p>'

    body = f"""
    <div class="container" style="max-width:600px;padding-top:32px;">
      <a href="/coach/attendance" class="btn btn-ghost btn-sm" style="margin-bottom:20px;">← Attendance</a>
      <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px;">
        <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0;">Roll-Call</h2>
        <span style="font-size:13px;color:#6E737B;">{group_name}</span>
      </div>
      <div style="font-size:15px;color:#2D323B;margin-bottom:24px;">
        <strong>{esc(date_str)}</strong>
        {f' — {esc(event.get("notes",""))}' if event.get("notes") else ""}
      </div>
      <form method="post" action="/coach/attendance/{event_id}/roll-call">
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;
          overflow:hidden;margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;align-items:center;
            padding:10px 16px;background:#F3F4F5;border-bottom:1px solid #E5E7EB;">
            <span style="font-size:12px;font-weight:600;color:#6E737B;text-transform:uppercase;letter-spacing:0.06em;">Athletes</span>
            <button type="button" onclick="toggleAll(this)"
              style="font-size:12px;color:#2D323B;background:none;border:none;cursor:pointer;font-weight:600;">
              Select all
            </button>
          </div>
          {athlete_checks}
        </div>
        <div style="display:flex;gap:10px;">
          <button type="submit" class="btn btn-primary">Save Attendance</button>
          <a href="/coach/attendance/{event_id}" class="btn btn-ghost">View</a>
        </div>
      </form>
    </div>
    <script>
    function toggleAll(btn) {{
      var boxes = document.querySelectorAll('input[name="athlete_ids"]');
      var allChecked = Array.from(boxes).every(b => b.checked);
      boxes.forEach(b => b.checked = !allChecked);
      btn.textContent = allChecked ? 'Select all' : 'Deselect all';
    }}
    </script>"""
    return layout("Roll-Call", body, user=coach, active_nav="attendance")


def attendance_view_page(coach, event, attendees):
    date_str = event.get("date", "")[:10]
    group_name = esc(event.get("group_name") or "All athletes")
    event_id = event["id"]
    rows = "".join(
        f'<tr style="background:{"#F3F4F5" if i%2==0 else "#fff"};">'
        f'<td style="padding:9px 14px;font-size:14px;color:#2D323B;">{esc(a.get("name",""))}</td>'
        f'<td style="padding:9px 14px;font-size:13px;color:#6E737B;">#{esc(a.get("athlete_number") or "")}</td>'
        f'<td style="padding:9px 14px;font-size:13px;color:#6E737B;">{esc((a.get("marked_at") or "")[:10])}</td>'
        f'</tr>'
        for i, a in enumerate(attendees)
    ) or '<tr><td colspan="3" style="padding:20px;text-align:center;color:#9CA3AF;font-size:13px;">No athletes marked present.</td></tr>'

    body = f"""
    <div class="container" style="max-width:700px;padding-top:32px;">
      <a href="/coach/attendance" class="btn btn-ghost btn-sm" style="margin-bottom:20px;">← Attendance</a>
      <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
        <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0;">
          Session — {esc(date_str)}
        </h2>
        <span style="font-size:13px;color:#6E737B;">{group_name}</span>
      </div>
      {f'<p style="font-size:13px;color:#6E737B;margin:0 0 20px;">{esc(event.get("notes",""))}</p>' if event.get("notes") else '<div style="margin-bottom:20px;"></div>'}
      <div style="display:flex;gap:10px;margin-bottom:24px;">
        <a href="/coach/attendance/{event_id}/roll-call" class="btn btn-primary btn-sm">Edit Roll-Call</a>
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;">
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Athlete</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">#</th>
              <th style="padding:10px 14px;text-align:left;font-size:12px;color:#fff;">Marked</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <p style="font-size:12px;color:#9CA3AF;margin-top:12px;text-align:right;">
        {len(attendees)} athlete{'s' if len(attendees) != 1 else ''} present
      </p>
    </div>"""
    return layout("Session Attendance", body, user=coach, active_nav="attendance")


def self_directed_home_page(athlete, pending_events, completed_sessions):
    name = esc(athlete.get("name", ""))

    pending_html = ""
    if pending_events:
        for e in pending_events:
            date_str = esc(e.get("date", "")[:10])
            group = esc(e.get("group_name") or "")
            pending_html += f"""
            <a href="/athlete/self-directed/{e['id']}"
               style="display:flex;align-items:center;justify-content:space-between;
                 padding:14px 18px;background:#fff;border:1px solid #E5E7EB;
                 border-radius:10px;text-decoration:none;margin-bottom:10px;
                 transition:box-shadow 0.15s;"
               onmouseover="this.style.boxShadow='0 2px 12px rgba(0,0,0,0.08)'"
               onmouseout="this.style.boxShadow=''">
              <div>
                <div style="font-size:15px;font-weight:600;color:#2D323B;">{date_str}</div>
                {f'<div style="font-size:12px;color:#6E737B;margin-top:2px;">{group}</div>' if group else ''}
              </div>
              <span style="font-size:13px;color:#F0A82E;font-weight:600;">Record scores →</span>
            </a>"""
    else:
        pending_html = '<p style="font-size:14px;color:#9CA3AF;padding:16px 0;">No sessions waiting to be scored.</p>'

    completed_html = ""
    if completed_sessions:
        for s in completed_sessions[:10]:
            date_str = esc(s.get("date", "")[:10])
            game_count = len({k[0] for k in s.get("results", {}).keys()})
            completed_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
              padding:10px 16px;background:#F3F4F5;border-radius:8px;margin-bottom:8px;">
              <span style="font-size:14px;color:#2D323B;">{date_str}</span>
              <span style="font-size:12px;color:#6E737B;">{game_count} game{'s' if game_count != 1 else ''} scored</span>
            </div>"""
    else:
        completed_html = '<p style="font-size:13px;color:#9CA3AF;">No self-directed scores recorded yet.</p>'

    body = f"""
    <div class="container" style="max-width:680px;padding-top:32px;">
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 6px;">Self-Directed Sessions</h2>
      <p style="font-size:14px;color:#6E737B;margin:0 0 28px;">
        After attending a training session, record your own scores here to earn AXP.
        Only sessions you were marked present for are available.
      </p>

      <h3 style="font-size:15px;font-weight:700;color:#2D323B;margin:0 0 12px;">
        Ready to score
        {f'<span style="font-size:12px;background:#F0A82E;color:#2D323B;border-radius:999px;padding:2px 8px;margin-left:8px;">{len(pending_events)}</span>' if pending_events else ''}
      </h3>
      {pending_html}

      <h3 style="font-size:15px;font-weight:700;color:#2D323B;margin:24px 0 12px;">Recent self-directed scores</h3>
      {completed_html}

      <div style="margin-top:28px;">
        <a href="/athlete/xp" class="btn btn-ghost btn-sm">View my AXP →</a>
      </div>
    </div>"""
    return layout("Self-Directed Sessions", body, user=athlete, active_nav="self_directed")


def self_directed_entry_page(athlete, event):
    date_str = esc(event.get("date", "")[:10])
    group = esc(event.get("group_name") or "")
    event_id = event["id"]

    # Build game entry cards — active games only (deprecated + hidden fields excluded)
    game_cards = ""
    for section in active_measurement_games():
        for game in section["games"]:
            fields_html = ""
            for field in game["fields"]:
                # active_measurement_games() already strips hidden fields
                ftype = field.get("type", "number")
                unit = esc(field.get("unit", ""))
                input_type = "number"
                step = "0.01" if ftype == "time" else "1"
                fields_html += f"""
                <div style="margin-bottom:12px;">
                  <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;color:#2D323B;">
                    {esc(field['label'])}
                    {f'<span style="font-size:11px;color:#6E737B;font-weight:400;"> {unit}</span>' if unit else ''}
                  </label>
                  <input type="{input_type}" step="{step}" min="0"
                    name="mg__{esc(game['key'])}__{esc(field['key'])}"
                    style="width:120px;font-size:14px;" placeholder="—" />
                </div>"""
            game_cards += f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;
              padding:16px 20px;margin-bottom:14px;">
              <div style="font-size:14px;font-weight:700;color:#2D323B;margin-bottom:12px;">
                {esc(GAME_DISPLAY_NAMES.get(game['key'], game['name']))}
              </div>
              {fields_html}
            </div>"""

    body = f"""
    <div class="container" style="max-width:640px;padding-top:32px;">
      <a href="/athlete/self-directed" class="btn btn-ghost btn-sm" style="margin-bottom:20px;">← Self-Directed</a>
      <h2 style="font-size:20px;font-weight:700;color:#2D323B;margin:0 0 4px;">Record Your Scores</h2>
      <p style="font-size:14px;color:#6E737B;margin:0 0 24px;">
        Session: <strong>{date_str}</strong>{f" · {group}" if group else ""}
        &nbsp;·&nbsp; Only fill in the games you actually played.
      </p>
      <form method="post" action="/athlete/self-directed/{event_id}">
        {game_cards}
        <div style="display:flex;gap:10px;margin-top:8px;">
          <button type="submit" class="btn btn-primary">Save & Earn AXP</button>
          <a href="/athlete/self-directed" class="btn btn-ghost">Cancel</a>
        </div>
      </form>
    </div>"""
    return layout("Self-Directed Entry", body, user=athlete, active_nav="self_directed")


# ══════════════════════════════════════════════════════════════════════════════
# GROUP LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════

def group_leaderboard_page(coach, groups, selected_group_id=None, ranked_athletes=None):
    """AXP leaderboard for a group — ranked by total AXP with rank badge and level count."""
    from constants import CORE_AAP_GAMES

    # Group selector
    _org_buckets = {}
    for g in groups:
        on = g.get("org_name") or "No Organisation"
        _org_buckets.setdefault(on, []).append(g)
    group_opts = '<option value="">— Select group —</option>'
    for on, glist in _org_buckets.items():
        group_opts += f'<optgroup label="{esc(on)}">'
        for g in glist:
            sel = "selected" if g["id"] == selected_group_id else ""
            group_opts += f'<option value="{g["id"]}" {sel}>{esc(g["name"])}</option>'
        group_opts += "</optgroup>"

    selector = f"""
    <form method="get" action="/coach/leaderboard"
          style="display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:28px;">
      <div>
        <label style="display:block;font-size:13px;font-weight:600;margin-bottom:5px;">Group</label>
        <select name="group_id" style="min-width:200px;">{group_opts}</select>
      </div>
      <button type="submit" class="btn btn-primary">Load</button>
    </form>"""

    # Podium + ranked list
    ranked_html = ""
    if ranked_athletes is not None:
        if not ranked_athletes:
            ranked_html = '<p style="color:#9CA3AF;font-size:14px;padding:16px 0;">No athletes with AXP in this group yet.</p>'
        else:
            LEVEL_COLOURS_LB = {
                0: ("#E5E7EB", "#6E737B"),
                1: ("#1EBE8B", "#fff"),
                2: ("#F0A82E", "#2D323B"),
                3: ("#2D323B", "#fff"),
                4: ("#F97316", "#fff"),
                5: ("#8B5CF6", "#fff"),
            }
            # Podium top-3
            podium_html = ""
            podium_order = [1, 0, 2]  # centre=1st, left=2nd, right=3rd
            podium_heights = {0: "90px", 1: "120px", 2: "70px"}
            podium_labels = {0: "2nd", 1: "1st", 2: "3rd"}
            podium_size = {0: "48px", 1: "64px", 2: "40px"}
            podium_font = {0: "16px", 1: "22px", 2: "14px"}
            podium_gold = {0: "#9CA3AF", 1: "#F0A82E", 2: "#CD7F32"}

            top3 = ranked_athletes[:3]
            if len(top3) >= 1:
                cols = ""
                for col_idx, rank_idx in enumerate(podium_order):
                    if rank_idx >= len(top3):
                        cols += '<div style="flex:1;"></div>'
                        continue
                    a = top3[rank_idx]
                    tier = a.get("tier") or {"label": "Starter", "colour": "#6E737B"}
                    name_parts = a["name"].strip().split()
                    inits = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else name_parts[0][0].upper()
                    av_size = podium_size[rank_idx]
                    av_font = podium_font[rank_idx]
                    medal_col = podium_gold[rank_idx]
                    pos_label = podium_labels[rank_idx]
                    bar_h = podium_heights[rank_idx]
                    cols += f"""
                    <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;">
                      <div style="width:{av_size};height:{av_size};border-radius:50%;background:#2D323B;
                                  display:flex;align-items:center;justify-content:center;
                                  font-weight:800;font-size:{av_font};color:{medal_col};
                                  box-shadow:0 4px 16px rgba(0,0,0,0.2);">{inits}</div>
                      <div style="font-size:12px;font-weight:700;color:#2D323B;text-align:center;
                                  max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                           title="{esc(a['name'])}">{esc(a['name'].split()[0])}</div>
                      <span style="font-size:10px;font-weight:700;background:{tier['colour']};color:#fff;
                                   border-radius:999px;padding:1px 7px;">{esc(tier['label'])}</span>
                      <div style="font-size:12px;font-weight:600;color:#6E737B;">{a['total_xp']:,} AXP</div>
                      <div style="width:100%;height:{bar_h};background:{medal_col};border-radius:8px 8px 0 0;
                                  display:flex;align-items:flex-start;justify-content:center;
                                  padding-top:6px;">
                        <span style="font-size:14px;font-weight:800;color:#fff;">{pos_label}</span>
                      </div>
                    </div>"""
                podium_html = f"""
                <div style="display:flex;align-items:flex-end;gap:8px;margin-bottom:32px;
                            max-width:340px;">
                  {cols}
                </div>"""

            # Full ranked list
            rows_html = ""
            for i, a in enumerate(ranked_athletes):
                tier = a.get("tier") or {"label": "Starter", "colour": "#6E737B"}
                levels = a.get("levels", {})
                games_at_l1 = sum(1 for gk in CORE_AAP_GAMES if levels.get(gk, 0) >= 1)
                name_parts = a["name"].strip().split()
                inits = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else name_parts[0][0].upper()
                pos = i + 1
                pos_style = ""
                if pos == 1:
                    pos_style = "color:#F0A82E;font-weight:800;"
                elif pos == 2:
                    pos_style = "color:#9CA3AF;font-weight:700;"
                elif pos == 3:
                    pos_style = "color:#CD7F32;font-weight:700;"

                # Mini level dots
                dots = ""
                for gk in CORE_AAP_GAMES:
                    lvl = levels.get(gk, 0)
                    bg, _ = LEVEL_COLOURS_LB.get(lvl, ("#E5E7EB", "#6E737B"))
                    dots += (f'<div style="width:8px;height:8px;border-radius:50%;'
                             f'background:{bg};flex-shrink:0;"></div>')

                shade = "#F9FAFB" if i % 2 == 0 else "#fff"
                rows_html += f"""
                <div style="display:flex;align-items:center;gap:14px;padding:12px 16px;
                            background:{shade};border-radius:8px;margin-bottom:4px;">
                  <div style="width:28px;text-align:right;font-size:14px;{pos_style}">
                    {pos}
                  </div>
                  <div style="width:40px;height:40px;border-radius:50%;background:#2D323B;
                              display:flex;align-items:center;justify-content:center;
                              font-weight:800;font-size:14px;color:#F0A82E;flex-shrink:0;">{inits}</div>
                  <div style="flex:1;min-width:0;">
                    <a href="/coach/participants/{a['id']}"
                       style="font-size:14px;font-weight:700;color:#2D323B;text-decoration:none;">
                      {esc(a['name'])}
                    </a>
                    <div style="display:flex;gap:3px;margin-top:4px;">{dots}</div>
                  </div>
                  <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:13px;font-weight:800;color:#2D323B;">{a['total_xp']:,}</div>
                    <div style="font-size:10px;color:#9CA3AF;">AXP</div>
                  </div>
                  <div style="flex-shrink:0;">
                    <span style="font-size:11px;font-weight:700;background:{tier['colour']};
                                 color:#fff;border-radius:999px;padding:2px 9px;">
                      {esc(tier['label'])}
                    </span>
                  </div>
                  <div style="flex-shrink:0;width:36px;text-align:center;">
                    <div style="font-size:13px;font-weight:700;color:#1EBE8B;">{games_at_l1}</div>
                    <div style="font-size:10px;color:#9CA3AF;">L1+</div>
                  </div>
                </div>"""

            ranked_html = f"""
            {podium_html}
            <div style="font-size:11px;color:#9CA3AF;margin-bottom:10px;padding:0 4px;">
              Dots = game levels (grey=none · green=L1 · gold=L2 · navy=L3 · orange=L4 · purple=L5)
            </div>
            {rows_html}"""

    body = f"""
    <div style="max-width:760px;padding-top:28px;">
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 20px;">Group Leaderboard</h2>
      {selector}
      {ranked_html}
    </div>"""
    return layout("Leaderboard", body, user=coach, active_nav="leaderboard")


# ══════════════════════════════════════════════════════════════════════════════
# ATHLETE-FACING GROUP LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════

def athlete_leaderboard_page(athlete, ranked_athletes, group_name=""):
    """Athlete-facing group leaderboard — only shown when group has show_leaderboard enabled."""
    from constants import CORE_AAP_GAMES
    LEVEL_COLOURS_ALB = {
        0: ("#E5E7EB", "#6E737B"),
        1: ("#1EBE8B", "#fff"),
        2: ("#F0A82E", "#2D323B"),
        3: ("#2D323B", "#fff"),
        4: ("#F97316", "#fff"),
        5: ("#8B5CF6", "#fff"),
    }

    if not ranked_athletes:
        rows_html = '<p style="color:#9CA3AF;font-size:14px;padding:16px 0;">No athletes with AXP yet — get scoring!</p>'
    else:
        rows_html = ""
        own_id = athlete["id"]
        for i, a in enumerate(ranked_athletes):
            pos = i + 1
            is_me = a["id"] == own_id
            tier = a.get("tier") or {"label": "Starter", "colour": "#6E737B"}
            levels = a.get("levels", {})
            name_parts = a["name"].strip().split()
            inits = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else name_parts[0][0].upper()
            pos_style = ""
            if pos == 1:
                pos_style = "color:#F0A82E;font-weight:800;"
            elif pos == 2:
                pos_style = "color:#9CA3AF;font-weight:700;"
            elif pos == 3:
                pos_style = "color:#CD7F32;font-weight:700;"
            dots = ""
            for gk in CORE_AAP_GAMES:
                lvl = levels.get(gk, 0)
                bg, _ = LEVEL_COLOURS_ALB.get(lvl, ("#E5E7EB", "#6E737B"))
                dots += f'<div style="width:8px;height:8px;border-radius:50%;background:{bg};flex-shrink:0;"></div>'
            me_border = "border:2px solid #F0A82E;" if is_me else "border:2px solid transparent;"
            me_bg = "#FFFBEB" if is_me else ("#F9FAFB" if i % 2 == 0 else "#fff")
            me_tag = '<span style="font-size:10px;font-weight:700;background:#F0A82E;color:#2D323B;border-radius:999px;padding:1px 7px;margin-left:6px;">You</span>' if is_me else ""
            rows_html += f"""
            <div style="display:flex;align-items:center;gap:14px;padding:12px 16px;
                        background:{me_bg};{me_border}border-radius:8px;margin-bottom:4px;">
              <div style="width:28px;text-align:right;font-size:14px;{pos_style}">{pos}</div>
              <div style="width:40px;height:40px;border-radius:50%;
                          background:{'#F0A82E' if is_me else '#2D323B'};
                          display:flex;align-items:center;justify-content:center;
                          font-weight:800;font-size:14px;
                          color:{'#2D323B' if is_me else '#F0A82E'};flex-shrink:0;">{inits}</div>
              <div style="flex:1;min-width:0;">
                <div style="font-size:14px;font-weight:700;color:#2D323B;">
                  {esc(a['name'])}{me_tag}
                </div>
                <div style="display:flex;gap:3px;margin-top:4px;">{dots}</div>
              </div>
              <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:13px;font-weight:800;color:#2D323B;">{a['total_xp']:,}</div>
                <div style="font-size:10px;color:#9CA3AF;">AXP</div>
              </div>
              <div style="flex-shrink:0;">
                <span style="font-size:11px;font-weight:700;background:{tier['colour']};
                             color:#fff;border-radius:999px;padding:2px 9px;">
                  {esc(tier['label'])}
                </span>
              </div>
            </div>"""

    group_label = f" — {esc(group_name)}" if group_name else ""
    body = f"""
    <div style="max-width:680px;padding-top:28px;">
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 4px;">
        Group Leaderboard{group_label}
      </h2>
      <p style="font-size:13px;color:#6E737B;margin:0 0 20px;">
        Ranked by total AXP earned — your position is highlighted.
      </p>
      <div style="font-size:11px;color:#9CA3AF;margin-bottom:10px;padding:0 4px;">
        Dots = game levels (grey=none · green=L1 · gold=L2 · navy=L3 · orange=L4 · purple=L5)
      </div>
      {rows_html}
    </div>"""
    return layout("Leaderboard", body, user=athlete, active_nav="leaderboard")


# ══════════════════════════════════════════════════════════════════════════════
# SCORE DISTRIBUTION REPORT  (system admin only)
# ══════════════════════════════════════════════════════════════════════════════

def score_distribution_page(coach, distributions):
    """
    distributions: list of dicts, one per core game:
      {
        game_key, display_name, field_key, lower_is_better,
        n, min_val, max_val, mean,
        p25, p50, p75, p90,
        suggested: {1: val, 2: val, 3: val, 4: val, 5: val}
      }
    """
    LEVEL_C = {1: ("#1EBE8B","#fff"), 2: ("#F0A82E","#2D323B"),
               3: ("#2D323B","#fff"), 4: ("#F97316","#fff"), 5: ("#8B5CF6","#fff")}

    def _fmt(v, lower=False):
        if v is None:
            return '<span style="color:#9CA3AF;">—</span>'
        if lower:
            return f'{v:.2f}s'
        return f'{v:g}'

    cards_html = ""
    for d in distributions:
        lower = d.get("lower_is_better", False)
        n = d.get("n", 0)
        if n == 0:
            cards_html += f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;
                        padding:20px 24px;margin-bottom:20px;opacity:0.6;">
              <div style="font-size:15px;font-weight:700;color:#2D323B;margin-bottom:4px;">
                {esc(d['display_name'])}
              </div>
              <div style="font-size:13px;color:#9CA3AF;">No scores recorded yet.</div>
            </div>"""
            continue

        # Distribution bar — visual spread
        mn, mx = d.get("min_val", 0), d.get("max_val", 1)
        rng = mx - mn or 1

        def _bar_pos(v):
            return max(0, min(100, round((v - mn) / rng * 100)))

        markers = [
            ("P25", d["p25"], "#9CA3AF"),
            ("Mean", d["mean"], "#2D323B"),
            ("P75", d["p75"], "#F0A82E"),
            ("P90", d["p90"], "#F97316"),
        ]
        marker_html = ""
        for label, val, col in markers:
            if val is None:
                continue
            pos = _bar_pos(val)
            marker_html += f"""
            <div style="position:absolute;left:{pos}%;top:0;height:100%;
                        border-left:2px solid {col};"></div>
            <div style="position:absolute;left:{pos}%;top:-18px;
                        transform:translateX(-50%);font-size:10px;font-weight:700;color:{col};
                        white-space:nowrap;">{label}: {_fmt(val, lower)}</div>"""

        bar_html = f"""
        <div style="position:relative;margin:28px 0 8px;">
          {marker_html}
          <div style="height:10px;background:#F3F4F5;border-radius:999px;overflow:visible;
                      border:1px solid #E5E7EB;position:relative;"></div>
          <div style="display:flex;justify-content:space-between;font-size:10px;
                      color:#9CA3AF;margin-top:4px;">
            <span>Min {_fmt(mn, lower)}</span>
            <span>Max {_fmt(mx, lower)}</span>
          </div>
        </div>"""

        # Stats row
        stats = [
            ("n", str(n), "#2D323B"),
            ("Min", _fmt(d.get("min_val"), lower), "#6E737B"),
            ("P25", _fmt(d.get("p25"), lower), "#9CA3AF"),
            ("Median", _fmt(d.get("p50"), lower), "#6E737B"),
            ("Mean", _fmt(d.get("mean"), lower), "#2D323B"),
            ("P75", _fmt(d.get("p75"), lower), "#F0A82E"),
            ("P90", _fmt(d.get("p90"), lower), "#F97316"),
            ("Max", _fmt(d.get("max_val"), lower), "#6E737B"),
        ]
        stats_html = "".join(
            f"""<div style="text-align:center;flex:1;min-width:56px;">
              <div style="font-size:14px;font-weight:800;color:{col};">{val}</div>
              <div style="font-size:10px;color:#9CA3AF;margin-top:2px;">{lbl}</div>
            </div>"""
            for lbl, val, col in stats
        )

        # Suggested thresholds badges
        sugg = d.get("suggested", {})
        sugg_html = ""
        for lvl in range(1, 6):
            sv = sugg.get(lvl)
            bg, fg = LEVEL_C.get(lvl, ("#E5E7EB", "#2D323B"))
            sv_str = _fmt(sv, lower) if sv is not None else "—"
            sugg_html += f"""
            <div style="display:flex;align-items:center;gap:8px;padding:5px 0;
                        border-bottom:1px solid #F3F4F5;">
              <span style="font-size:11px;font-weight:700;background:{bg};color:{fg};
                           border-radius:999px;padding:1px 8px;min-width:28px;text-align:center;">
                L{lvl}
              </span>
              <span style="font-size:13px;font-weight:600;color:#2D323B;">{sv_str}</span>
              {'<span style="font-size:10px;color:#9CA3AF;">(lower is better)</span>' if lower and sv is not None else ''}
            </div>"""

        lower_note = ' <span style="font-size:11px;color:#6E737B;font-weight:400;">(lower = better)</span>' if lower else ''
        cards_html += f"""
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;
                    padding:20px 24px;margin-bottom:20px;">
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:4px;flex-wrap:wrap;">
            <div style="font-size:16px;font-weight:800;color:#2D323B;">{esc(d['display_name'])}</div>
            <div style="font-size:12px;color:#9CA3AF;">field: <code>{esc(d['field_key'])}</code></div>
            {lower_note}
          </div>
          {bar_html}
          <div style="display:flex;flex-wrap:wrap;gap:4px;padding:14px 0;
                      border-top:1px solid #F3F4F5;border-bottom:1px solid #F3F4F5;
                      margin-bottom:14px;">
            {stats_html}
          </div>
          <div style="font-size:12px;font-weight:700;color:#2D323B;margin-bottom:6px;
                      text-transform:uppercase;letter-spacing:0.05em;">
            Suggested Thresholds
          </div>
          <div style="font-size:11px;color:#6E737B;margin-bottom:8px;">
            L1 ≈ just above mean &nbsp;·&nbsp;
            L2 ≈ P75 &nbsp;·&nbsp;
            L3 ≈ midpoint P75–P90 &nbsp;·&nbsp;
            L4 ≈ P90 &nbsp;·&nbsp;
            L5 ≈ beyond P90.
            These are starting points — set final values in
            <a href="/coach/admin/game-thresholds" style="color:#2D323B;font-weight:600;">
              AXP Thresholds</a>.
          </div>
          {sugg_html}
        </div>"""

    body = f"""
    <div style="max-width:800px;padding-top:28px;">
      <div style="margin-bottom:24px;">
        <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 4px;">
          Score Distribution Report
        </h2>
        <p style="font-size:13px;color:#6E737B;margin:0;">
          Percentiles calculated across all recorded scores for each core game's primary
          level-threshold field. Use these to set JAG Standard thresholds in
          <a href="/coach/admin/game-thresholds" style="color:#2D323B;font-weight:600;">
            AXP Thresholds</a>.
        </p>
      </div>
      <div style="background:#EFF6FF;border-left:4px solid #2D323B;border-radius:8px;
                  padding:12px 16px;margin-bottom:24px;font-size:13px;color:#2D323B;">
        <strong>Reading this report:</strong> P25 = 25th percentile (bottom quarter of athletes),
        P75 = top quarter threshold, P90 = top 10%. The bar shows relative spread —
        P75 (gold) and P90 (orange) markers indicate natural level break points.
        Suggested thresholds are computed automatically; always review against programme context.
      </div>
      {cards_html}
    </div>"""

    return layout("Score Distribution", body, user=coach, active_nav="dashboard")


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM ADMIN HUB  (system_admin only)
# ══════════════════════════════════════════════════════════════════════════════

def system_admin_hub_page(user):
    def _section(title, icon, cards_html):
        return f"""
        <div style="margin-bottom:36px;">
          <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.08em;color:#9CA3AF;margin:0 0 12px;">{icon} {esc(title)}</h3>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;">
            {cards_html}
          </div>
        </div>"""

    def _card(href, label, desc, colour="#2D323B", icon="→"):
        return f"""
        <a href="{href}" style="display:block;background:#fff;border:1px solid #E5E7EB;
                   border-radius:12px;padding:16px 18px;text-decoration:none;
                   transition:box-shadow 0.15s,transform 0.15s;"
           onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.10)';this.style.transform='translateY(-2px)'"
           onmouseout="this.style.boxShadow='';this.style.transform=''">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <span style="font-size:20px;">{icon}</span>
            <span style="font-size:14px;font-weight:700;color:{colour};">{esc(label)}</span>
          </div>
          <div style="font-size:12px;color:#6E737B;line-height:1.5;">{esc(desc)}</div>
        </a>"""

    thresholds = _section("JAG Standard — Thresholds & Standards", "🎯",
        _card("/coach/admin/score-distribution", "Score Distribution",
              "Percentile breakdown per game — P25, mean, P75, P90, max. Use to decide threshold values.",
              "#F0A82E", "📊") +
        _card("/coach/admin/game-thresholds", "AAXP Thresholds",
              "Set the official JAG Standard level thresholds (L1–L5) for all 8 core games.",
              "#2D323B", "⚙")
    )

    data_tools = _section("Data — Import & Export", "📁",
        _card("/coach/participants/import", "Import Athletes",
              "Bulk-upload athletes from a CSV file. Auto-assigns athlete numbers.",
              "#1EBE8B", "⬆") +
        _card("/coach/participants/export.csv", "Export Athletes",
              "Download all athletes with temporary passwords as a CSV.",
              "#6E737B", "⬇") +
        _card("/coach/scores/import", "Import Scores",
              "Bulk-upload measurement session scores from a CSV file.",
              "#1EBE8B", "⬆")
    )

    xp_tools = _section("AXP Engine", "⚡",
        _card("/coach/admin/game-thresholds#retroactive", "Retroactive AXP Pass",
              "Re-run the AXP engine across all historical sessions. Use after changing thresholds.",
              "#F97316", "🔄") +
        _card("/coach/leaderboard", "Group Leaderboard",
              "View AXP rankings within any group. Toggle per-group leaderboard visibility in group settings.",
              "#8B5CF6", "🏆")
    )

    people = _section("People & Organisations", "👥",
        _card("/coach/coaches", "Practitioners",
              "Manage practitioner accounts, roles, and school assignments.",
              "#2D323B", "👤") +
        _card("/coach/organisations", "Organisations",
              "Manage partner organisations and their branding.",
              "#2D323B", "🏢") +
        _card("/coach", "Practitioner Dashboard",
              "Main dashboard — groups, athletes, and session recording.",
              "#6E737B", "🏠")
    )

    reports = _section("Reports & Statistics", "📈",
        _card("/coach/reports", "Statistics & Reports",
              "All-groups progress overview, completion tracker, and achievement summaries.",
              "#2D323B", "📈") +
        _card("/coach/admin/sessions", "Session Browser",
              "Browse, merge, and manage all recorded measurement sessions.",
              "#6E737B", "📋")
    )

    body = f"""
    <div style="max-width:900px;padding-top:28px;">
      <div style="margin-bottom:28px;">
        <h2 style="font-size:24px;font-weight:800;color:#2D323B;margin:0 0 4px;">
          System Admin Hub
        </h2>
        <p style="font-size:13px;color:#6E737B;margin:0;">
          All admin tools in one place. These pages are only visible to system admins.
        </p>
      </div>
      {thresholds}
      {data_tools}
      {xp_tools}
      {people}
      {reports}
    </div>"""

    return layout("Admin Hub", body, user=user, active_nav="admin_hub")


# ── Measurement Window views ───────────────────────────────────────────────────

def measurement_window_status_page(coach, window, group, athletes, submissions, submitted_ids):
    """Practitioner live status view for an open/closed measurement window."""
    wid     = window["id"]
    status  = window.get("status", "open")
    gname   = esc(group.get("name", "Group"))
    label   = esc(window.get("session_label") or "—")
    opened  = esc((window.get("opened_at") or "")[:16])
    closed  = esc((window.get("closed_at") or "")[:16])
    opened_by = esc(window.get("opened_by_name", ""))

    is_open  = status == "open"
    status_chip = (
        '<span style="background:#1EBE8B;color:#fff;border-radius:999px;'
        'padding:3px 12px;font-size:12px;font-weight:700;">OPEN</span>'
        if is_open else
        '<span style="background:#6E737B;color:#fff;border-radius:999px;'
        'padding:3px 12px;font-size:12px;font-weight:700;">CLOSED</span>'
    )

    submitted_count = len(submitted_ids)
    total_count     = len(athletes)
    missing_count   = total_count - submitted_count

    # Athlete rows
    rows_html = ""
    for a in athletes:
        aid     = a["id"]
        aname   = esc(a["name"])
        anum    = esc(a.get("athlete_number") or "")
        done    = aid in submitted_ids
        dot     = ('<span style="color:#1EBE8B;font-size:18px;font-weight:700;">✓</span>'
                   if done else
                   '<span style="color:#DDE0E3;font-size:18px;">○</span>')
        status_txt = ('<span style="color:#1EBE8B;font-size:13px;font-weight:600;">Submitted</span>'
                      if done else
                      '<span style="color:#9CA3AF;font-size:13px;">Pending</span>')
        rows_html += f"""
        <tr>
          <td style="padding:10px 12px;">{dot}</td>
          <td style="padding:10px 12px;font-weight:600;color:#2D323B;">{aname}</td>
          <td style="padding:10px 12px;color:#6E737B;">{anum}</td>
          <td style="padding:10px 12px;">{status_txt}</td>
        </tr>"""

    # Action buttons
    if is_open:
        warning_js = ""
        if missing_count > 0:
            warning_js = f"return confirm('{missing_count} athlete(s) haven\\'t submitted yet. Close anyway and skip them? (You can re-open later for missing entries.)')"
        else:
            warning_js = "return confirm('All athletes have submitted. Close window and award AXP?')"
        actions = f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;">
          <form method="post" action="/coach/window/{wid}/close" style="margin:0;">
            <button type="submit" onclick="{warning_js}"
                    style="background:#F97316;color:#fff;font-weight:700;font-size:14px;
                           border:none;border-radius:10px;padding:11px 22px;cursor:pointer;">
              Close &amp; Award AXP
            </button>
          </form>
          <a href="/coach/group-hub?group_id={group['id']}"
             style="background:#F4F5F7;color:#2D323B;font-weight:600;font-size:14px;
                    border-radius:10px;padding:11px 22px;text-decoration:none;">
            ← Back to Group Hub
          </a>
        </div>"""
    else:
        actions = f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;">
          <form method="post" action="/coach/window/{wid}/reopen" style="margin:0;">
            <button type="submit"
                    style="background:#2D323B;color:#F0A82E;font-weight:700;font-size:14px;
                           border:none;border-radius:10px;padding:11px 22px;cursor:pointer;">
              Re-open for Missing Entries
            </button>
          </form>
          <a href="/coach/reports/completion?group_id={group['id']}"
             style="background:#1EBE8B;color:#fff;font-weight:600;font-size:14px;
                    border-radius:10px;padding:11px 22px;text-decoration:none;">
            📊 View Completion Report
          </a>
          <a href="/coach/group-hub?group_id={group['id']}"
             style="background:#F4F5F7;color:#2D323B;font-weight:600;font-size:14px;
                    border-radius:10px;padding:11px 22px;text-decoration:none;">
            ← Back to Group Hub
          </a>
        </div>"""

    missing_note = ""
    if is_open and missing_count > 0:
        missing_note = f"""
    <div style="background:#FEF3C7;border:1px solid #F0A82E;border-radius:10px;
                padding:12px 16px;margin-bottom:16px;font-size:13px;color:#92400E;">
      <strong>{missing_count} athlete{'' if missing_count == 1 else 's'} yet to submit.</strong>
      They will be excluded if you close now — you can re-open later to capture their scores.
    </div>"""

    body = f"""
    <div style="max-width:760px;">
      <div class="page-head" style="margin-bottom:16px;">
        <div>
          <h1 style="margin:0 0 4px;">Measurement Window — {gname}</h1>
          <p class="muted" style="margin:0;">
            Phase: <strong>{label}</strong> &nbsp;·&nbsp;
            Opened: {opened} by {opened_by} &nbsp;·&nbsp;
            {status_chip}
            {f'&nbsp;·&nbsp; Closed: {closed}' if closed else ''}
          </p>
        </div>
      </div>

      <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <div style="flex:1;min-width:120px;background:#1EBE8B1A;border:1px solid #1EBE8B;
                    border-radius:12px;padding:14px 16px;text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#065F46;">{submitted_count}</div>
          <div style="font-size:12px;color:#047857;font-weight:600;margin-top:2px;">Submitted</div>
        </div>
        <div style="flex:1;min-width:120px;background:#FEF3C71A;border:1px solid #F0A82E;
                    border-radius:12px;padding:14px 16px;text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#92400E;">{missing_count}</div>
          <div style="font-size:12px;color:#B45309;font-weight:600;margin-top:2px;">Pending</div>
        </div>
        <div style="flex:1;min-width:120px;background:#F4F5F7;
                    border-radius:12px;padding:14px 16px;text-align:center;">
          <div style="font-size:28px;font-weight:800;color:#2D323B;">{total_count}</div>
          <div style="font-size:12px;color:#6E737B;font-weight:600;margin-top:2px;">Total Athletes</div>
        </div>
      </div>

      {missing_note}

      <div class="card" style="padding:0;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;color:#fff;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;">
              <th style="padding:10px 12px;text-align:left;width:36px;"></th>
              <th style="padding:10px 12px;text-align:left;">Athlete</th>
              <th style="padding:10px 12px;text-align:left;">#</th>
              <th style="padding:10px 12px;text-align:left;">Status</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>

      {actions}
    </div>"""

    return layout(f"Window — {gname}", body, user=coach, active_nav="group_hub")


def athlete_window_submit_page(user, window, games, already_submitted=False):
    """Athlete self-score entry form for an open measurement window."""
    from constants import GAME_DISPLAY_NAMES
    wid      = window["id"]
    label    = esc(window.get("session_label") or "")
    label_h  = f' — <strong>{label}</strong>' if label else ''
    name     = esc(user.get("name", "Athlete").split()[0])

    if already_submitted:
        body = f"""
        <div style="max-width:640px;margin:40px auto;text-align:center;">
          <div style="font-size:48px;margin-bottom:16px;">✅</div>
          <h1 style="color:#2D323B;">Scores already submitted{label_h}</h1>
          <p style="color:#6E737B;font-size:15px;">
            Your scores have been recorded. AAXP will be awarded when your practitioner closes the session.
          </p>
          <a href="/dashboard"
             style="display:inline-block;margin-top:20px;background:#2D323B;color:#F0A82E;
                    font-weight:700;border-radius:10px;padding:12px 28px;text-decoration:none;">
            Back to Dashboard
          </a>
        </div>"""
        return layout("Scores Submitted", body, user=user, active_nav="dashboard")

    # Build game entry sections
    game_sections = ""
    for section in games:
        section_label = esc(section.get("section", ""))
        fields_html = ""
        for g in section.get("games", []):
            gkey  = g["key"]
            gname = esc(GAME_DISPLAY_NAMES.get(gkey, gkey.replace("_", " ").title()))
            visible_fields = [f for f in g.get("fields", []) if not f.get("hidden") and not f.get("computed")]
            if not visible_fields:
                continue
            field_inputs = ""
            for f in visible_fields:
                fkey   = f["key"]
                flabel = esc(f.get("label", fkey))
                funit  = esc(f.get("unit", ""))
                fmin   = f.get("min", 0)
                fmax   = f.get("max", "")
                fstep  = f.get("step", "any")
                field_inputs += f"""
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <label style="flex:1;font-size:13px;color:#6E737B;">{flabel}
                  {f'<span style="color:#9CA3AF;font-size:11px;"> ({funit})</span>' if funit else ''}
                </label>
                <input type="number" name="{gkey}.{fkey}"
                       min="{fmin}" {'max="'+str(fmax)+'"' if fmax else ''} step="{fstep}"
                       placeholder="—"
                       style="width:90px;border:1.5px solid #DDE0E3;border-radius:8px;
                              padding:7px 10px;font-size:15px;text-align:center;
                              color:#2D323B;font-weight:600;">
              </div>"""
            fields_html += f"""
          <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:12px;
                      padding:14px 16px;margin-bottom:12px;">
            <div style="font-weight:700;color:#2D323B;font-size:14px;margin-bottom:10px;">
              {gname}
            </div>
            {field_inputs}
          </div>"""
        if fields_html:
            game_sections += f"""
        <div style="margin-bottom:24px;">
          <div style="font-size:11px;font-weight:700;color:#9CA3AF;text-transform:uppercase;
                      letter-spacing:0.08em;margin-bottom:10px;">{section_label}</div>
          {fields_html}
        </div>"""

    body = f"""
    <div style="max-width:640px;">
      <div style="background:#2D323B;border-radius:16px;padding:20px 24px;margin-bottom:24px;">
        <h1 style="margin:0 0 4px;color:#fff;font-size:22px;">
          Hi {name} — enter your scores{label_h}
        </h1>
        <p style="margin:0;color:#9CA3AF;font-size:13px;">
          Enter the score for each game you completed today. You only submit once — take your time.
        </p>
      </div>

      <form id="windowForm">
        {game_sections}
        <div style="position:sticky;bottom:0;background:#fff;padding:16px 0;
                    border-top:1px solid #E5E7EB;margin-top:8px;">
          <button type="submit" id="submitBtn"
                  style="width:100%;background:#1EBE8B;color:#fff;font-weight:700;font-size:16px;
                         border:none;border-radius:12px;padding:14px;cursor:pointer;">
            Submit My Scores
          </button>
          <p id="submitMsg" style="text-align:center;font-size:13px;color:#6E737B;
                                   margin:8px 0 0;display:none;"></p>
        </div>
      </form>
    </div>

    <script>
    document.getElementById('windowForm').addEventListener('submit', async function(e) {{
      e.preventDefault();
      const btn = document.getElementById('submitBtn');
      const msg = document.getElementById('submitMsg');
      btn.disabled = true;
      btn.textContent = 'Submitting…';
      const data = {{}};
      new FormData(this).forEach((v, k) => {{ if (v !== '') data[k] = parseFloat(v); }});
      if (Object.keys(data).length === 0) {{
        msg.textContent = 'Please enter at least one score before submitting.';
        msg.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Submit My Scores';
        return;
      }}
      try {{
        const r = await fetch('/athlete/window/{wid}/submit', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify(data),
        }});
        const j = await r.json();
        if (j.ok) {{
          btn.style.background = '#065F46';
          btn.textContent = '✓ Scores Submitted!';
          msg.textContent = 'Your scores have been saved. AAXP will be awarded when the session closes.';
          msg.style.display = 'block';
          setTimeout(() => window.location.href = '/dashboard', 2000);
        }} else if (j.error === 'already_submitted') {{
          msg.textContent = 'You have already submitted scores for this session.';
          msg.style.display = 'block';
          btn.disabled = false;
          btn.textContent = 'Submit My Scores';
        }} else {{
          throw new Error(j.error || 'Server error');
        }}
      }} catch(err) {{
        msg.textContent = 'Something went wrong — please try again. (' + err.message + ')';
        msg.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Submit My Scores';
      }}
    }});
    </script>"""

    return layout(f"Score Entry{' — ' + label if label else ''}", body, user=user, active_nav="dashboard")
