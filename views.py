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
                ("/coach",            "Home",         "home"),
                ("/coach/groups",     "Groups",       "dashboard"),
                ("/coach/session",    "Record",       "session"),
                ("/coach/attendance", "Attendance",   "attendance"),
                ("/coach/group-hub",  "Group Hub",    "group_hub"),
                ("/coach/leaderboard","Leaderboard",  "leaderboard"),
                ("/coach/progress",   "Reports",      "progress"),
                ("/coach/resources",  "Resources",    "resources"),
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

                def _drop_item(href, label, sym, sym_col="#F0A82E"):
                    return (
                        f'<a class="nav-dropdown-item" href="{href}">'
                        f'<span style="width:24px;height:24px;border-radius:6px;'
                        f'background:rgba(255,255,255,0.09);display:inline-flex;flex-shrink:0;'
                        f'align-items:center;justify-content:center;font-size:12px;'
                        f'color:{sym_col};font-weight:700;">{sym}</span>'
                        f'{label}</a>'
                    )

                def _drop_divider(label=""):
                    if label:
                        return (f'<div style="padding:6px 10px 2px;font-size:10px;font-weight:700;'
                                f'text-transform:uppercase;letter-spacing:0.08em;'
                                f'color:rgba(255,255,255,0.30);">{label}</div>')
                    return '<div style="height:1px;background:rgba(255,255,255,0.10);margin:4px 8px;"></div>'

                dropdown_links = (
                    _drop_item("/coach/participants/new", "Add Participant", "+") +
                    _drop_item("/coach/coaches",          "Practitioners",   "◉") +
                    _drop_item("/coach/organisations",    "Organisations",   "▣")
                )
                if is_sys:
                    dropdown_links += (
                        _drop_divider("System Admin") +
                        _drop_item("/coach/admin/hub",               "Admin Hub",         "⚙", "#F0A82E") +
                        _drop_item("/coach/admin/score-distribution", "Score Distribution","▦", "#F0A82E") +
                        _drop_item("/coach/admin/game-thresholds",    "AXP Thresholds",   "◎", "#F0A82E")
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
                     ("/athlete/xp", "My AXP", "xp")]
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
            position: absolute; top: calc(100% + 10px); left: 0;
            background: #2D323B;
            border: 1.5px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.28);
            min-width: 220px;
            z-index: 999; padding: 8px;
          }}
          .nav-dropdown-item {{
            display: flex; align-items: center; gap: 10px;
            padding: 8px 10px; border-radius: 8px;
            font-size: 13px; font-weight: 600;
            color: rgba(255,255,255,0.78); text-decoration: none; white-space: nowrap;
            transition: background 0.12s, color 0.12s;
          }}
          .nav-dropdown-item:hover {{
            background: rgba(240,168,46,0.15);
            color: #F0A82E;
          }}
          .nav-dropdown-item:hover span {{ background: rgba(240,168,46,0.25) !important; }}
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

    if user and user.get("role") != "participant" and active_nav != "home":
        home_btn = ('<div style="margin-bottom:16px;">'
                    '<a href="/coach" class="return-home-btn">'
                    '&larr; Home'
                    '</a></div>')
    else:
        home_btn = ""

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
    .return-home-btn {{
      display: inline-flex; align-items: center; gap: 6px;
      font-size: 13px; font-weight: 700; color: #7A5800;
      text-decoration: none; padding: 6px 14px; border-radius: 20px;
      background: rgba(240,168,46,0.12); border: 1.5px solid #F0A82E;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
    }}
    .return-home-btn:hover {{
      background: #F0A82E !important;
      color: #2D323B !important;
      border-color: #F0A82E !important;
    }}
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
  {f'''<div style="background:#1B2E4B;border-bottom:3px solid #F0A82E;padding:9px 20px;
              display:flex;align-items:center;justify-content:space-between;
              position:sticky;top:60px;z-index:900;gap:12px;">
    <span style="font-size:13px;color:#fff;line-height:1.4;">
      &#128065; <strong style="color:#F0A82E;">Viewing as {esc(user.get("name","Athlete"))}</strong>
      &nbsp;&mdash;&nbsp;you are seeing their screen. Actions are read-only.
    </span>
    <a href="/coach/exit-view-as"
       style="font-size:12px;font-weight:700;color:#F0A82E;text-decoration:none;white-space:nowrap;
              background:rgba(240,168,46,0.15);padding:5px 14px;border-radius:20px;
              border:1px solid rgba(240,168,46,0.4);">
      &larr; Exit View
    </a>
  </div>''' if user and user.get("_view_as") else ""}
  <main class="container">
    {flash_html}
    {home_btn}
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
    """

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
        f'{esc(g["name"])}</button>'
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

    sections_html = completion_strip_html + chip_panel_html + "".join(f"""
    <div class="mg-section" style="margin-bottom:24px;">
      <div style="border-left:4px solid #F0A82E;padding-left:10px;margin-bottom:12px;">
        <h4 style="margin:0;font-size:15px;font-weight:700;color:var(--jag-navy);">{esc(section['section'])}</h4>
      </div>
      {''.join(_measurement_game_fieldset(g) for g in section['games'])}
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
                           xp_data=None, levels=None, levels_by_area=None,
                           pending_self_directed=None, thresholds=None,
                           resources=None, attendance_count=None,
                           active_window=None, already_submitted=False):
    """Full athlete dashboard: rank hero, XP progress, game level grid, guided steps, nudge."""
    from constants import CORE_AAP_GAMES, XP_GAME_CONFIG, find_measurement_game, SCORING_AREAS, threshold_field_key

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
        xp_next_label = (f'<span style="font-size:12px;color:#9CA3AF;">'
                         f'{xp_to_next:,} AXP to {esc(next_tier["label"])}</span>')
    else:
        xp_next_label = '<span style="font-size:12px;color:#1EBE8B;font-weight:700;">Max rank reached!</span>'

    # ── AXP journey line ──────────────────────────────────────────────────────
    from constants import XP_RANK_TIERS
    _jl_max = XP_RANK_TIERS[-1]["min_xp"]  # 25000 (Titanium)
    _jl_fill = min(100.0, (total_xp / _jl_max * 100)) if _jl_max else 100.0
    _jl_dots = ""
    _jl_labels = ""
    for _t in XP_RANK_TIERS:
        _pos = (_t["min_xp"] / _jl_max * 100) if _jl_max else 0
        _achieved = total_xp >= _t["min_xp"]
        _is_cur = _t["label"] == tier["label"]
        if _is_cur:
            _dot = (f'width:14px;height:14px;background:#fff;'
                    f'border:2px solid {_t["colour"]};'
                    f'box-shadow:0 0 0 3px rgba(255,255,255,0.25);top:-4px;')
        elif _achieved:
            _dot = 'width:10px;height:10px;background:#fff;top:-2px;'
        else:
            _dot = ('width:10px;height:10px;'
                    'background:rgba(255,255,255,0.15);'
                    'border:1.5px solid rgba(255,255,255,0.3);top:-2px;')
        _jl_dots += (
            f'<div style="position:absolute;left:{_pos:.1f}%;'
            f'transform:translateX(-50%);{_dot}'
            f'border-radius:50%;z-index:2;"></div>'
        )
        _fw = "700" if _is_cur else "400"
        _op = "1" if _achieved else "0.4"
        _jl_labels += (
            f'<div style="position:absolute;left:{_pos:.1f}%;'
            f'transform:translateX(-50%);text-align:center;width:52px;margin-left:-26px;">'
            f'<div style="font-size:10px;font-weight:{_fw};'
            f'color:rgba(255,255,255,{_op});white-space:nowrap;">{esc(_t["label"])}</div>'
            f'<div style="font-size:9px;color:rgba(255,255,255,0.35);">{_t["min_xp"]:,}</div>'
            f'</div>'
        )
    _journey_line = f"""
      <div style="position:relative;padding-bottom:38px;">
        <div style="position:relative;height:6px;background:rgba(255,255,255,0.12);border-radius:999px;">
          <div style="width:{_jl_fill:.1f}%;height:100%;background:#fff;border-radius:999px;
                      position:absolute;top:0;left:0;transition:width 0.8s ease;"></div>
          {_jl_dots}
        </div>
        <div style="position:relative;height:34px;margin-top:8px;">
          {_jl_labels}
        </div>
      </div>"""

    # ── Active testing round banner ────────────────────────────────────────────
    window_banner = ""
    if active_window:
        wid    = active_window["id"]
        lvl    = active_window.get("level", "")
        rtype  = active_window.get("round_type", "")
        seq    = active_window.get("retest_sequence")
        rlabel = f"Level {lvl} {rtype.title()}" + (f" #{seq}" if seq else "")
        LEVEL_COLOURS = {1:"#1EBE8B", 2:"#3B82F6", 3:"#F3AA33", 4:"#F97316", 5:"#8B5CF6"}
        clr = LEVEL_COLOURS.get(lvl, "#F0A82E")
        if already_submitted:
            window_banner = f"""
    <div style="background:linear-gradient(135deg,#064E3B 0%,#065F46 100%);border-radius:16px;
                padding:20px 24px;margin-bottom:20px;
                border:1.5px solid rgba(30,190,139,0.40);">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:44px;height:44px;border-radius:12px;background:rgba(30,190,139,0.20);
                    display:flex;align-items:center;justify-content:center;font-size:22px;
                    flex-shrink:0;color:#1EBE8B;">&#10003;</div>
        <div>
          <div style="font-size:12px;font-weight:700;color:#1EBE8B;letter-spacing:0.05em;
                      text-transform:uppercase;margin-bottom:2px;">{esc(rlabel)}</div>
          <div style="font-weight:800;color:#FFFFFF;font-size:16px;">Scores submitted!</div>
          <div style="color:rgba(255,255,255,0.60);font-size:13px;margin-top:2px;">
            AXP will be awarded when your practitioner closes the round.
          </div>
        </div>
      </div>
      <a href="/athlete/round/{wid}"
         style="display:block;text-align:center;margin-top:14px;background:rgba(255,255,255,0.12);
                color:#FFFFFF;font-weight:700;font-size:13px;border-radius:10px;
                padding:10px 20px;text-decoration:none;">
        Review / Update My Scores &#8250;
      </a>
    </div>"""
        else:
            window_banner = f"""
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:22px 24px;margin-bottom:20px;
                border:2px solid {clr};
                box-shadow:0 0 0 4px {clr}22;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">
        <div style="width:8px;height:8px;border-radius:50%;background:{clr};
                    animation:pulse 1.5s infinite;"></div>
        <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.08em;color:{clr};">Testing Round Open</span>
      </div>
      <div style="font-size:20px;font-weight:800;color:#FFFFFF;margin-bottom:4px;">
        {esc(rlabel)} &#8212; enter your scores!
      </div>
      <div style="font-size:13px;color:rgba(255,255,255,0.55);margin-bottom:18px;">
        Use your <strong style="color:rgba(255,255,255,0.80);">Level {lvl} game cards</strong>.
        Submit your results to earn AXP.
      </div>
      <a href="/athlete/round/{wid}"
         style="display:block;text-align:center;background:{clr};color:#2D323B;
                font-weight:800;font-size:16px;border-radius:12px;padding:14px 24px;
                text-decoration:none;letter-spacing:0.02em;">
        Enter My Scores &#8250;
      </a>
    </div>
    <style>
      @keyframes pulse {{
        0%,100% {{ opacity:1; transform:scale(1); }}
        50% {{ opacity:0.4; transform:scale(1.4); }}
      }}
    </style>"""

    # ── Hero card ─────────────────────────────────────────────────────────────
    hero = f"""
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);
                border-radius:20px;padding:28px 24px 20px;margin-bottom:16px;
                position:relative;overflow:hidden;">
      <!-- Decorative circle -->
      <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;
                  border-radius:50%;background:rgba(240,168,46,0.06);pointer-events:none;"></div>
      <!-- Top row: avatar + name -->
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <div style="width:64px;height:64px;border-radius:50%;background:#F0A82E;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;font-size:24px;color:#2D323B;flex-shrink:0;
                    box-shadow:0 4px 20px rgba(240,168,46,0.40);">{inits}</div>
        <div>
          <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-bottom:1px;">Welcome back</div>
          <div style="font-size:28px;font-weight:900;color:#FFFFFF;line-height:1.1;">{first_name}!</div>
          <span style="font-size:12px;font-weight:700;background:{tier_colour};color:#fff;
                       border-radius:999px;padding:3px 12px;display:inline-block;margin-top:5px;">{tier_label}</span>
        </div>
      </div>
      <!-- Big AXP number -->
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:64px;font-weight:900;color:#F0A82E;line-height:1;
                    letter-spacing:-2px;">{total_xp:,}</div>
        <div style="font-size:13px;font-weight:700;color:rgba(255,255,255,0.50);
                    text-transform:uppercase;letter-spacing:0.10em;margin-top:4px;">Total AXP</div>
        <div style="margin-top:6px;">{xp_next_label}</div>
      </div>
      <!-- AXP journey line -->
      <div style="background:rgba(255,255,255,0.07);border-radius:12px;padding:12px 14px 2px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <span style="font-size:10px;font-weight:700;text-transform:uppercase;
                       letter-spacing:0.08em;color:#F0A82E;">AXP Journey</span>
          <a href="/athlete/axp-info"
             style="font-size:11px;color:rgba(255,255,255,0.45);text-decoration:none;">
            What is AXP? ›
          </a>
        </div>
        {_journey_line}
      </div>
    </div>"""

    # ── Pending self-directed count (used in nav card badge) ─────────────────
    levels = levels or {}

    # ── Big action nav cards ──────────────────────────────────────────────────
    def _nav_card(href, icon, title, subtitle, badge=None):
        badge_html = (f'<span style="font-size:11px;font-weight:700;background:#F0A82E;color:#2D323B;'
                      f'border-radius:999px;padding:2px 9px;margin-left:8px;">{badge}</span>') if badge else ''
        return f"""
        <a href="{href}" style="display:flex;align-items:center;gap:16px;
                  background:#2D323B;border-radius:16px;padding:20px 20px;
                  text-decoration:none;border-left:4px solid #F0A82E;
                  transition:background 0.15s,transform 0.1s;margin-bottom:12px;"
           onmouseover="this.style.background='#383E49';this.style.transform='translateX(2px)'"
           onmouseout="this.style.background='#2D323B';this.style.transform=''">
          <div style="width:52px;height:52px;border-radius:14px;background:rgba(240,168,46,0.15);
                      border:1.5px solid rgba(240,168,46,0.30);display:flex;align-items:center;
                      justify-content:center;font-size:24px;flex-shrink:0;">{icon}</div>
          <div style="flex:1;">
            <div style="font-size:16px;font-weight:800;color:#FFFFFF;margin-bottom:3px;">
              {title}{badge_html}
            </div>
            <div style="font-size:13px;color:rgba(255,255,255,0.55);line-height:1.4;">{subtitle}</div>
          </div>
          <div style="font-size:20px;color:#F0A82E;font-weight:700;flex-shrink:0;">›</div>
        </a>"""

    pending_count = len(pending_self_directed) if pending_self_directed else 0
    sd_badge = str(pending_count) if pending_count else None

    nav_cards = (
        _nav_card("/athlete/report", "&#9654;", "My Movement Report",
                  "See what you&rsquo;re tracking well and where to focus next") +
        _nav_card("/athlete/self-directed", "&#9650;", "Self-Directed Sessions",
                  "Record your own scores and earn AXP",
                  badge=sd_badge) +
        _nav_card("/athlete/xp", "&#9733;", "My Levels &amp; AXP",
                  "Track your progress across all 8 games") +
        (_nav_card("/athlete/leaderboard", "&#9670;", "Group Leaderboard",
                  "See how you rank in your group")
         if user.get("show_leaderboard") else "")
    )

    # ── Recent results summary ────────────────────────────────────────────────
    history_html = ""
    if measurement_sessions:
        history_html = f"""
        <div style="margin-top:8px;">
          <div style="display:flex;align-items:center;gap:0;margin-bottom:12px;">
            <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
            <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Recent Test Results</span>
          </div>
          {measurement_games_history(measurement_sessions)}
        </div>"""

    body = f"""
    <div style="max-width:520px;margin:0 auto;">
      {window_banner}
      {hero}
      {nav_cards}
      {history_html}
    </div>"""
    return layout("My Dashboard", body, user=user, active_nav="dashboard")


def athlete_resources_page(athlete, folder_groups, ungrouped, all_tags=None, tags_by_resource=None):
    """Athlete-facing resource browser — grouped by folder with tag filter bar."""
    all_tags = all_tags or []
    tags_by_resource = tags_by_resource or {}

    # ── Tag filter bar ────────────────────────────────────────────────────────
    if all_tags:
        chip_all = (
            '<button onclick="jagFilter(\'all\',this)" '
            'class="jag-tag-chip jag-tag-active" data-tag="all">'
            'All</button>'
        )
        chips = "".join(
            f'<button onclick="jagFilter(\'{esc(t["name"])}\',this)" '
            f'class="jag-tag-chip" data-tag="{esc(t["name"])}">'
            f'{esc(t["name"])}</button>'
            for t in all_tags
        )
        filter_bar = f"""
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6E737B;text-transform:uppercase;
                       letter-spacing:.06em;margin-right:4px;">Filter:</span>
          {chip_all}{chips}
        </div>
        <style>
          .jag-tag-chip {{
            font-size:12px;font-weight:700;border:1.5px solid #E5E7EB;border-radius:999px;
            padding:5px 14px;background:#fff;color:#6E737B;cursor:pointer;transition:.15s;
          }}
          .jag-tag-chip:hover {{ border-color:#F0A82E;color:#2D323B; }}
          .jag-tag-chip.jag-tag-active {{ background:#F0A82E;border-color:#F0A82E;color:#2D323B; }}
          .jag-res-tile[data-hidden="1"] {{ display:none !important; }}
        </style>
        <script>
          function jagFilter(tag, btn) {{
            document.querySelectorAll('.jag-tag-chip').forEach(function(b){{b.classList.remove('jag-tag-active');}});
            btn.classList.add('jag-tag-active');
            document.querySelectorAll('.jag-res-tile').forEach(function(tile){{
              if (tag === 'all') {{ tile.dataset.hidden = '0'; return; }}
              var tags = (tile.dataset.tags || '').split(',').map(function(s){{return s.trim().toLowerCase();}});
              tile.dataset.hidden = tags.indexOf(tag.toLowerCase()) === -1 ? '1' : '0';
            }});
            // Show "no results" message
            var sections = document.querySelectorAll('.jag-res-section');
            sections.forEach(function(sec){{
              var visible = sec.querySelectorAll('.jag-res-tile:not([data-hidden="1"])').length;
              sec.querySelector('.jag-res-grid').style.display = visible ? '' : 'none';
              var empty = sec.querySelector('.jag-res-empty');
              if (empty) empty.style.display = visible ? 'none' : '';
            }});
            var totalVisible = document.querySelectorAll('.jag-res-tile:not([data-hidden="1"])').length;
            var noRes = document.getElementById('jag-no-results');
            if (noRes) noRes.style.display = totalVisible ? 'none' : '';
          }}
        </script>"""
    else:
        filter_bar = ""

    # ── Resource sections ─────────────────────────────────────────────────────
    content_html = ""
    for folder, items in folder_groups:
        if not items:
            continue
        tiles = _athlete_resource_tiles(items, tags_by_resource)
        content_html += f"""
        <div class="jag-res-section" style="margin-bottom:28px;">
          <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:0 0 10px;
                     padding-left:12px;border-left:4px solid #F0A82E;">{esc(folder["name"])}</h3>
          <div class="jag-res-grid"
               style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;">
            {tiles}
          </div>
          <p class="jag-res-empty" style="display:none;font-size:13px;color:#9CA3AF;padding:12px 0;">
            No resources match this filter in this section.
          </p>
        </div>"""
    if ungrouped:
        tiles = _athlete_resource_tiles(list(ungrouped), tags_by_resource)
        label = "Other" if folder_groups else ""
        header = (f'<h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:0 0 10px;'
                  f'padding-left:12px;border-left:4px solid #E5E7EB;">{label}</h3>') if label else ''
        content_html += f"""
        <div class="jag-res-section" style="margin-bottom:28px;">
          {header}
          <div class="jag-res-grid"
               style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;">
            {tiles}
          </div>
          <p class="jag-res-empty" style="display:none;font-size:13px;color:#9CA3AF;padding:12px 0;">
            No resources match this filter in this section.
          </p>
        </div>"""
    if not content_html:
        content_html = '<p style="color:#9CA3AF;font-size:14px;padding:32px 0;text-align:center;">No resources have been shared yet.</p>'

    body = f"""
    <div style="max-width:900px;padding-top:28px;">
      <h2 style="font-size:22px;font-weight:700;color:#2D323B;margin:0 0 16px;">Resources</h2>
      {filter_bar}
      {content_html}
      <p id="jag-no-results" style="display:none;color:#9CA3AF;font-size:14px;
         padding:32px 0;text-align:center;">No resources match this filter.</p>
    </div>"""
    return layout("Resources", body, user=athlete, active_nav="resources")


def _athlete_resource_tiles(items, tags_by_resource=None):
    tags_by_resource = tags_by_resource or {}
    html = ""
    for r in items:
        r_name = esc(r.get("name", ""))
        r_url = r.get("url", "")
        r_notes = esc(r.get("notes") or r.get("description") or "")
        thumb = _gdrive_thumbnail(r_url) if "drive.google.com" in r_url else None
        img_html = (f'<img src="{thumb}" alt="" style="width:100%;height:100px;'
                    f'object-fit:cover;border-radius:8px 8px 0 0;display:block;">'
                    if thumb else '')
        # Tags for this resource
        res_tags = tags_by_resource.get(r["id"], [])
        tag_names = ",".join(t["name"] for t in res_tags)
        tag_chips = "".join(
            f'<span style="font-size:10px;font-weight:700;background:rgba(240,168,46,0.12);'
            f'color:#CF8F1F;border-radius:999px;padding:2px 8px;">{esc(t["name"])}</span>'
            for t in res_tags
        )
        tag_chips_html = (f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;">'
                          f'{tag_chips}</div>') if tag_chips else ''
        html += f"""
        <a href="{esc(r_url)}" target="_blank" rel="noopener"
           class="jag-res-tile" data-tags="{esc(tag_names)}" data-hidden="0"
           style="display:flex;flex-direction:column;background:#fff;
                  border:1px solid #E5E7EB;border-radius:12px;text-decoration:none;
                  overflow:hidden;transition:box-shadow 0.15s,border-color 0.15s;"
           onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.1)';this.style.borderColor='#F0A82E'"
           onmouseout="this.style.boxShadow='';this.style.borderColor='#E5E7EB'">
          {img_html}
          <div style="padding:12px 14px;flex:1;">
            <div style="font-size:13px;font-weight:700;color:#2D323B;line-height:1.3;">{r_name}</div>
            {f'<div style="font-size:12px;color:#6E737B;margin-top:4px;">{r_notes}</div>' if r_notes else ''}
            {tag_chips_html}
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


def practitioner_home_page(coach, show_onboarding=False):
    """Landing page for practitioners — large card links to each main area."""
    name = coach.get("name", "").split()[0] if coach.get("name") else "there"
    is_admin = coach.get("role") in {"org_admin", "system_admin"}

    _G = "#F0A82E"  # gold
    _S = 'stroke="#F0A82E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    CARDS = [
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
            "title": "View Groups &amp; Athletes",
            "sub":   "Browse your groups and individual athlete profiles",
            "href":  "/coach/groups",
            "color": _G,
        },
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><polyline points="20 6 9 17 4 12"/></svg>',
            "title": "Record Attendance",
            "sub":   "Mark attendance and open self-test exploration",
            "href":  "/coach/attendance/new",
            "color": _G,
        },
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>',
            "title": "Group Testing",
            "sub":   "Record measurement sessions and review game scores",
            "href":  "/coach/group-hub",
            "color": _G,
        },
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            "title": "Reports",
            "sub":   "Progress reports, group next steps, and adaptability snapshots",
            "href":  "/coach/progress",
            "color": _G,
        },
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><path d="M6 9H4a2 2 0 0 0 0 4h2"/><path d="M18 9h2a2 2 0 0 1 0 4h-2"/><path d="M6 3h12v9a6 6 0 0 1-12 0V3z"/><line x1="9" y1="21" x2="15" y2="21"/><line x1="12" y1="18" x2="12" y2="21"/></svg>',
            "title": "Group Leaderboard",
            "sub":   "AXP rankings within your groups",
            "href":  "/coach/leaderboard",
            "color": _G,
        },
        {
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="10" y1="8" x2="16" y2="8"/><line x1="10" y1="12" x2="16" y2="12"/></svg>',
            "title": "Go To Resources",
            "sub":   "Guides and reference materials for your programme",
            "href":  "/coach/resources",
            "color": _G,
        },
    ]
    if is_admin:
        CARDS.append({
            "icon": f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" {_S}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
            "title": "Admin Hub",
            "sub":   "Manage athletes, practitioners, games, thresholds and organisations",
            "href":  "/coach/admin/hub",
            "color": _G,
        })

    cards_html = ""
    for c in CARDS:
        cards_html += f"""
        <a href="{c['href']}" class="prac-card" style="--card-accent:{c['color']};">
          <div class="prac-card-icon">{c['icon']}</div>
          <div class="prac-card-body">
            <div class="prac-card-title">{c['title']}</div>
            <div class="prac-card-sub">{c['sub']}</div>
          </div>
          <div class="prac-card-arrow">&#8250;</div>
        </a>"""

    if show_onboarding:
        onboarding_callout = (
            '<div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);'
            'border:2px solid #F0A82E;border-radius:16px;padding:20px 22px;'
            'margin-bottom:24px;display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;">'
            '<div style="width:44px;height:44px;border-radius:12px;background:rgba(240,168,46,0.18);'
            'border:1px solid rgba(240,168,46,0.35);display:flex;align-items:center;'
            'justify-content:center;font-size:22px;flex-shrink:0;">&#9733;</div>'
            '<div style="flex:1;min-width:0;">'
            '<div style="font-size:15px;font-weight:800;color:#FFFFFF;margin-bottom:4px;">'
            'Welcome to JAG! Let&rsquo;s get you set up.</div>'
            '<div style="font-size:13px;color:rgba(255,255,255,0.60);margin-bottom:14px;line-height:1.5;">'
            'It only takes a few minutes to create your first group, add athletes, and run your first session.</div>'
            '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
            '<a href="/coach/getting-started" '
            'style="font-size:13px;font-weight:700;background:#F0A82E;color:#2D323B;'
            'border-radius:8px;padding:8px 18px;text-decoration:none;">'
            'View Getting Started Guide &#8250;</a>'
            '<form method="post" action="/coach/getting-started/dismiss" style="margin:0;">'
            '<button type="submit" '
            'style="font-size:13px;color:rgba(255,255,255,0.45);background:none;border:none;'
            'cursor:pointer;padding:8px 4px;font-weight:600;">Dismiss</button>'
            '</form></div></div></div>'
        )
    else:
        onboarding_callout = ""

    body = f"""
    <style>
      .prac-home {{
        max-width: 680px;
        margin: 0 auto;
        padding: 32px 16px 48px;
      }}
      .prac-welcome {{
        text-align: center;
        margin-bottom: 36px;
      }}
      .prac-welcome h1 {{
        font-size: 22px;
        font-weight: 700;
        color: #2D323B;
        margin: 0 0 6px;
      }}
      .prac-welcome h1 span {{
        color: #F0A82E;
      }}
      .prac-welcome p {{
        font-size: 14px;
        color: #64748B;
        margin: 0;
      }}
      .prac-cards {{
        display: flex;
        flex-direction: column;
        gap: 12px;
      }}
      .prac-card {{
        display: flex;
        align-items: center;
        gap: 18px;
        background: #2D323B;
        border-left: 5px solid var(--card-accent);
        border-radius: 14px;
        padding: 18px 20px;
        text-decoration: none;
        color: inherit;
        transition: background 0.18s, transform 0.15s, box-shadow 0.18s;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
      }}
      .prac-card:hover {{
        background: #1E252C;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.20);
      }}
      .prac-card:active {{
        transform: translateY(0);
      }}
      .prac-card-icon {{
        font-size: 28px;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(240,168,46,0.18);
        border: 1px solid rgba(240,168,46,0.30);
        border-radius: 12px;
        flex-shrink: 0;
      }}
      .prac-card-body {{
        flex: 1;
        min-width: 0;
      }}
      .prac-card-title {{
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
      }}
      .prac-card-sub {{
        font-size: 12px;
        color: rgba(255,255,255,0.60);
        line-height: 1.4;
      }}
      .prac-card-arrow {{
        font-size: 26px;
        color: var(--card-accent);
        flex-shrink: 0;
      }}
      @media (min-width: 520px) {{
        .prac-card-title {{ font-size: 16px; }}
        .prac-card-icon  {{ font-size: 30px; width: 54px; height: 54px; }}
      }}
    </style>

    <div class="prac-home">
      <div class="prac-welcome">
        <h1>What are you keen to do today, <span>{esc(name)}</span>?</h1>
        <p>Choose an area to get started</p>
      </div>
      {onboarding_callout}
      <div class="prac-cards">
        {cards_html}
      </div>
    </div>"""

    return layout("Home", body, user=coach, active_nav="home")


def getting_started_page(coach):
    """Step-by-step onboarding guide for new practitioners."""
    is_admin = coach.get("role") in {"org_admin", "system_admin"}

    STEPS = [
        {
            "num": "1",
            "title": "Create a Group",
            "body": (
                "Groups are how you organise your athletes — typically a class, team, or training cohort. "
                "Go to <strong>Groups &amp; Athletes</strong> and click <strong>+ New Group</strong>. "
                "Give it a name, assign a sport, and it&rsquo;s ready to use."
            ),
            "href": "/coach/groups",
            "cta": "Go to Groups",
        },
        {
            "num": "2",
            "title": "Add Your Athletes",
            "body": (
                "From your group page, use <strong>Add Athlete</strong> to create individual accounts, "
                "or use the CSV import to onboard everyone at once. "
                "Each athlete gets a login so they can access their own dashboard and self-test."
            ),
            "href": "/coach/groups",
            "cta": "Go to Groups",
        },
        {
            "num": "3",
            "title": "Record Attendance &amp; Open a Session",
            "body": (
                "When your group meets, go to <strong>Record Attendance</strong>, select the group and date, "
                "and mark who&rsquo;s present. Then hit <strong>Open Session</strong> to allow athletes "
                "to submit their own self-test scores from their devices during the session."
            ),
            "href": "/coach/attendance/new",
            "cta": "Record Attendance",
        },
        {
            "num": "4",
            "title": "Record Measurement Games Scores",
            "body": (
                "Go to <strong>Group Testing</strong>, choose your group, select which games were played, "
                "and enter each athlete&rsquo;s scores. The system calculates derived scores automatically "
                "and updates each athlete&rsquo;s level and AXP in real time."
            ),
            "href": "/coach/group-hub",
            "cta": "Go to Group Testing",
        },
        {
            "num": "5",
            "title": "View Reports",
            "body": (
                "Head to <strong>Reports</strong> to see group-level progress and individual athlete snapshots. "
                "Click any athlete to open their full <strong>CLA Movement Report</strong> — this shows "
                "their current gaps framed as game environment constraints, with suggested games to target each area."
            ),
            "href": "/coach/progress",
            "cta": "Go to Reports",
        },
        {
            "num": "6",
            "title": "Set Up the Resource Library",
            "body": (
                "Add guides, videos, and links that athletes can access from their dashboard. "
                "Create tags (e.g. <em>balance</em>, <em>agility</em>, <em>reaction</em>) in the Admin Hub, "
                "assign them to resources, and athletes can filter the library by their focus area."
            ),
            "href": "/coach/resources",
            "cta": "Go to Resources",
        },
    ]

    if is_admin:
        STEPS.insert(0, {
            "num": "0",
            "title": "Set Up Your Organisation",
            "body": (
                "As an admin, start by going to <strong>Admin Hub &rarr; Organisations</strong> to create "
                "your organisation and add its logo URL. This branding appears across the portal for your "
                "practitioners and athletes."
            ),
            "href": "/coach/admin/hub",
            "cta": "Go to Admin Hub",
        })
        for i, s in enumerate(STEPS):
            s["num"] = str(i)

    steps_html = ""
    for s in STEPS:
        steps_html += f"""
        <div style="display:flex;gap:18px;margin-bottom:28px;align-items:flex-start;">
          <div style="width:36px;height:36px;border-radius:50%;background:#F0A82E;color:#2D323B;
                      font-size:15px;font-weight:800;display:flex;align-items:center;
                      justify-content:center;flex-shrink:0;margin-top:2px;">{esc(s['num'])}</div>
          <div style="flex:1;border-bottom:1px solid #F3F4F5;padding-bottom:24px;">
            <div style="font-size:16px;font-weight:800;color:#2D323B;margin-bottom:6px;">{s['title']}</div>
            <div style="font-size:14px;color:#374151;line-height:1.65;margin-bottom:12px;">{s['body']}</div>
            <a href="{s['href']}"
               style="font-size:12px;font-weight:700;color:#F0A82E;text-decoration:none;
                      border:1.5px solid #F0A82E;border-radius:8px;padding:5px 14px;
                      display:inline-block;"
               onmouseover="this.style.background='#F0A82E';this.style.color='#2D323B';"
               onmouseout="this.style.background='';this.style.color='#F0A82E';">
              {esc(s['cta'])} &#8250;
            </a>
          </div>
        </div>"""

    body = f"""
    <style>
      @media print {{
        nav, .nav, header, .site-header, .mobile-nav, .desktop-nav,
        .print-hide, form[action*="dismiss"] {{ display: none !important; }}
        body {{ font-size: 13px; }}
        .gs-print-btn {{ display: none !important; }}
        a {{ color: #2D323B !important; text-decoration: none !important; }}
        .gs-hero {{ border: 2px solid #2D323B !important; background: #fff !important; }}
        .gs-hero * {{ color: #2D323B !important; }}
      }}
    </style>

    <div style="max-width:720px;margin:0 auto;padding:32px 16px 64px;">

      <!-- Hero -->
      <div class="gs-hero" style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);
           border-radius:16px;padding:28px 32px;margin-bottom:36px;">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    gap:16px;flex-wrap:wrap;margin-bottom:8px;">
          <div>
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.09em;
                        color:rgba(240,168,46,0.85);margin-bottom:6px;">JAG Portal</div>
            <h1 style="margin:0;font-size:26px;font-weight:900;color:#FFFFFF;line-height:1.2;">
              Getting Started Guide
            </h1>
          </div>
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <button class="gs-print-btn" onclick="window.print()"
                    style="font-size:13px;font-weight:700;background:rgba(255,255,255,0.10);
                           color:#FFFFFF;border:1.5px solid rgba(255,255,255,0.25);
                           border-radius:8px;padding:7px 16px;cursor:pointer;">
              &#128438; Print / Save PDF
            </button>
            <a href="/coach" style="font-size:13px;font-weight:700;color:rgba(255,255,255,0.55);
                                    text-decoration:none;">&larr; Back</a>
          </div>
        </div>
        <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.60);line-height:1.55;">
          Follow these steps to get your programme up and running. Each step links directly to the
          relevant part of the portal.
        </p>
      </div>

      <!-- Steps -->
      <div style="padding:0 4px;">
        {steps_html}
      </div>

      <!-- Footer note -->
      <div style="background:rgba(240,168,46,0.08);border-left:4px solid #F0A82E;border-radius:8px;
                  padding:14px 18px;font-size:13px;color:#7A5800;margin-top:8px;">
        <strong>Tip:</strong> This guide is always available from the <strong>Help</strong> link
        in the nav menu. You can print it or save it as a PDF using the button above.
      </div>

      <!-- Dismiss -->
      <div style="margin-top:32px;text-align:center;" class="print-hide">
        <form method="post" action="/coach/getting-started/dismiss">
          <button type="submit"
                  style="font-size:13px;color:#9CA3AF;background:none;border:none;
                         cursor:pointer;text-decoration:underline;">
            Got it &mdash; don&rsquo;t show the welcome banner again
          </button>
        </form>
      </div>

    </div>"""
    return layout("Getting Started", body, user=coach, active_nav="home")


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
        next_steps_cta = f"""
        <a href="/coach/groups/{group['id']}/next-steps"
           style="display:flex;align-items:center;gap:14px;
                  background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);
                  border-radius:12px;padding:14px 18px;margin-bottom:12px;
                  text-decoration:none;box-shadow:0 2px 8px rgba(45,50,59,0.12);"
           onmouseover="this.style.boxShadow='0 6px 20px rgba(240,168,46,0.22)'"
           onmouseout="this.style.boxShadow='0 2px 8px rgba(45,50,59,0.12)'">
          <div style="width:36px;height:36px;border-radius:10px;flex-shrink:0;
                      background:rgba(240,168,46,0.18);border:1px solid rgba(240,168,46,0.38);
                      display:flex;align-items:center;justify-content:center;
                      font-size:16px;color:#F0A82E;">&#9654;</div>
          <div style="flex:1;min-width:0;">
            <div style="font-size:14px;font-weight:800;color:#FFFFFF;line-height:1.2;">Next Steps</div>
            <div style="font-size:11px;color:rgba(255,255,255,0.45);margin-top:1px;">Programme Progress Design</div>
          </div>
          <div style="font-size:18px;color:#F0A82E;font-weight:700;">&#8594;</div>
        </a>"""
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
        admin_btns = f"""
            <div style="position:relative;display:inline-block;">
              <button type="button" class="btn btn-ghost btn-sm" id="more-btn-{gkey}"
                      onclick="var m=document.getElementById('more-menu-{gkey}');m.style.display=m.style.display==='none'?'block':'none';"
                      style="font-size:12px;padding:4px 10px;">⋯ More</button>
              <div id="more-menu-{gkey}" style="display:none;position:absolute;top:calc(100% + 4px);right:0;
                   background:#fff;border:1px solid #E5E7EB;border-radius:10px;
                   box-shadow:0 8px 24px rgba(0,0,0,.10);min-width:160px;z-index:100;padding:6px 0;">
                <a href="/coach/groups/{group['id']}/edit"
                   style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
                   onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">✏️ Edit Group</a>
                <button onclick="var el=document.getElementById('relabel-{gkey}');el.style.display=el.style.display==='none'?'block':'none';document.getElementById('more-menu-{gkey}').style.display='none';"
                        style="display:block;width:100%;text-align:left;padding:9px 16px;font-size:13px;
                               color:#2D323B;background:none;border:none;cursor:pointer;"
                        onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">🏷️ Tag Sessions</button>
                <div style="border-top:1px solid #F3F4F6;margin:4px 0;"></div>
                <form method="post" action="/coach/groups/{group['id']}/delete" style="margin:0;"
                      onsubmit="return confirm('Delete group \\'{esc(group['name'])}\\'? Participants move to ungrouped.');">
                  <button type="submit"
                          style="display:block;width:100%;text-align:left;padding:9px 16px;font-size:13px;
                                 color:#EF4444;background:none;border:none;cursor:pointer;"
                          onmouseover="this.style.background='#FEF2F2'" onmouseout="this.style.background=''">🗑 Delete Group</button>
                </form>
              </div>
            </div>
            <script>
              document.addEventListener('click', function(e) {{
                var btn = document.getElementById('more-btn-{gkey}');
                var menu = document.getElementById('more-menu-{gkey}');
                if (menu && btn && !btn.contains(e.target) && !menu.contains(e.target)) {{
                  menu.style.display = 'none';
                }}
              }});
            </script>""" if is_admin else ""
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
          {next_steps_cta}
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
        <div id="sport-filter" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
          <span style="font-size:12px;color:var(--jag-muted);font-weight:600;margin-right:2px;">Sport:</span>
          <button onclick="filterSport(this, '')" class="filter-active"
            style="padding:4px 12px;border-radius:999px;border:1px solid var(--jag-green);
                   background:var(--jag-green);color:var(--jag-navy);font-size:12px;cursor:pointer;font-weight:600;">All</button>
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

    admin_dropdown = """
      <div style="position:relative;display:inline-block;">
        <button type="button" class="btn btn-ghost" id="admin-menu-btn"
                onclick="var m=document.getElementById('admin-menu');m.style.display=m.style.display==='none'?'block':'none';"
                style="display:flex;align-items:center;gap:5px;">
          ⚙ Admin <span style="font-size:10px;margin-top:1px;">▾</span>
        </button>
        <div id="admin-menu" style="display:none;position:absolute;top:calc(100% + 4px);right:0;
             background:#fff;border:1px solid #E5E7EB;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.10);
             min-width:200px;z-index:200;padding:6px 0;">
          <a href="/coach/participants/import" style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
             onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">&#8679; Import Athletes</a>
          <a href="/coach/participants/export.csv" style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
             onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">&#8681; Export Athletes</a>
          <a href="/coach/scores/import" style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
             onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">&#8679; Import Scores</a>
          <div style="border-top:1px solid #F3F4F6;margin:4px 0;"></div>
          <a href="/coach/admin/game-thresholds" style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
             onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">&#9881; AXP Thresholds</a>
          <a href="/coach/admin/score-distribution" style="display:block;padding:9px 16px;font-size:13px;color:#2D323B;text-decoration:none;"
             onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background=''">&#128202; Score Distribution</a>
        </div>
      </div>
      <script>
        document.addEventListener('click', function(e) {
          var btn = document.getElementById('admin-menu-btn');
          var menu = document.getElementById('admin-menu');
          if (menu && btn && !btn.contains(e.target) && !menu.contains(e.target)) {
            menu.style.display = 'none';
          }
        });
      </script>""" if is_admin else ""

    action_btns = f"""
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px;">
      <a class="btn btn-primary" href="/coach/participants/new">+ Add Participant</a>
      <button type="button" class="btn btn-primary" onclick="var p=document.getElementById('create-group-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Create Group</button>
      <a class="btn btn-primary" href="/coach/session">Record Session</a>
      {admin_dropdown}
      {'<div style="flex:1;min-width:0;"></div>' + filter_bar if filter_bar else ''}
    </div>
    {create_group_form}""" if is_admin else (f"""
    <div style="margin-bottom:12px;">{filter_bar}</div>""" if filter_bar else "")

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
        untested_color = "color:#92400E;" if untested > 0 else "color:var(--jag-navy);"

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
            <div class="stat-label">Pending Baseline</div>
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
    <style>
      .form-section-label {{
        font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
        color:var(--jag-muted);margin-bottom:14px;display:flex;align-items:center;gap:8px;
      }}
      .form-section-label::after {{
        content:'';flex:1;height:1px;background:var(--jag-border);
      }}
      .login-toggle-card {{
        border:1.5px solid var(--jag-border);border-radius:12px;padding:16px 18px;
        cursor:pointer;transition:border-color 0.15s,background 0.15s;
        display:flex;align-items:flex-start;gap:14px;
      }}
      .login-toggle-card:hover {{ border-color:#F0A82E;background:rgba(240,168,46,0.04); }}
      .login-toggle-card.active {{ border-color:#F0A82E;background:rgba(240,168,46,0.07); }}
    </style>

    <!-- Hero banner -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:28px 28px 24px;margin-bottom:28px;display:flex;align-items:center;gap:18px;">
      <div style="width:52px;height:52px;border-radius:14px;background:rgba(240,168,46,0.18);
                  border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                  justify-content:center;font-size:24px;flex-shrink:0;">&#43;&#128100;</div>
      <div>
        <div style="font-size:22px;font-weight:800;color:#FFFFFF;line-height:1.2;">Add Participant</div>
        <div style="font-size:13px;color:rgba(255,255,255,0.55);margin-top:4px;">
          Register a new athlete and optionally set up their login access.
        </div>
      </div>
    </div>

    {error_html}

    <div class="card form-card">
      <form method="post" action="/coach/participants/new">

        <!-- Section 1: Athlete Details -->
        <div class="form-section-label">Athlete Details</div>

        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required placeholder="e.g. Alex Johnson" />

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;">
          <div>
            <label for="gender">Gender</label>
            <select id="gender" name="gender">
              <option value="">— Not specified —</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Non-binary">Non-binary</option>
              <option value="Prefer not to say">Prefer not to say</option>
            </select>
          </div>
          <div>
            <label for="sport">Sport</label>
            <select id="sport" name="sport">{sport_options}</select>
          </div>
        </div>

        <!-- Section 2: Programme & Group -->
        <div class="form-section-label" style="margin-top:24px;">Programme &amp; Group</div>

        <label for="programme">Programme / notes</label>
        <input type="text" id="programme" name="programme"
               placeholder="e.g. Athlete Adaptability Programme - Masterton 2026" />

        <label for="group_id">Group <span style="font-weight:400;color:var(--jag-muted);">(optional)</span></label>
        <select id="group_id" name="group_id">{group_opts}</select>

        <!-- Section 3: Account Access -->
        <div class="form-section-label" style="margin-top:24px;">Account Access</div>

        <div class="login-toggle-card" id="login-toggle-card"
             onclick="var cb=document.getElementById('setup-login');cb.checked=!cb.checked;
                      this.classList.toggle('active',cb.checked);
                      document.getElementById('login-fields').style.display=cb.checked?'block':'none';">
          <div style="width:36px;height:36px;border-radius:10px;background:#2D323B;
                      display:flex;align-items:center;justify-content:center;
                      font-size:17px;flex-shrink:0;color:#F0A82E;">&#128273;</div>
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-weight:700;font-size:14px;color:var(--jag-navy);">Set up login account</span>
              <input type="checkbox" id="setup-login" name="setup_login" value="1"
                     style="width:16px;height:16px;margin:0;accent-color:#F0A82E;"
                     onclick="event.stopPropagation();
                              document.getElementById('login-toggle-card').classList.toggle('active',this.checked);
                              document.getElementById('login-fields').style.display=this.checked?'block':'none';" />
            </div>
            <p style="margin:4px 0 0;font-size:13px;color:var(--jag-muted);line-height:1.5;">
              Gives the athlete access to their own dashboard — XP progress, level tracking, and guided training steps.
            </p>
          </div>
        </div>

        <div id="login-fields" style="display:none;margin-top:16px;
             padding:16px 18px;background:rgba(240,168,46,0.06);
             border:1.5px solid rgba(240,168,46,0.25);border-radius:10px;">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div>
              <label for="email" style="margin-top:0;">Email <span style="font-weight:400;color:var(--jag-muted);">(used to log in)</span></label>
              <input type="email" id="email" name="email" placeholder="athlete@example.com" />
            </div>
            <div>
              <label for="password" style="margin-top:0;">Temporary password</label>
              <input type="text" id="password" name="password" value="Athlete123!" />
            </div>
          </div>
          <p style="margin:10px 0 0;font-size:12px;color:var(--jag-muted);">
            &#9432;&nbsp; The athlete should change their password after first login.
          </p>
        </div>

        <!-- Submit -->
        <div style="margin-top:28px;padding-top:20px;border-top:1px solid var(--jag-border);
                    display:flex;align-items:center;gap:12px;">
          <button type="submit" class="btn btn-primary" style="padding:10px 28px;font-size:15px;">
            &#43; Add Participant
          </button>
          <a href="/coach" class="btn btn-ghost" style="padding:10px 20px;">Cancel</a>
        </div>

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
    # AXP journey line for coach view
    from constants import XP_RANK_TIERS
    _cj_max = XP_RANK_TIERS[-1]["min_xp"]
    _cj_fill = min(100.0, (total_xp / _cj_max * 100)) if _cj_max else 100.0
    _cj_dots = ""
    _cj_lbls = ""
    _next_tier_c = xp_data.get("next_tier")
    for _ct in XP_RANK_TIERS:
        _cp = (_ct["min_xp"] / _cj_max * 100) if _cj_max else 0
        _ca = total_xp >= _ct["min_xp"]
        _cc = _ct["label"] == tier["label"]
        if _cc:
            _cds = ('width:12px;height:12px;background:#fff;'
                    f'border:2px solid {_ct["colour"]};'
                    'box-shadow:0 0 0 2px rgba(255,255,255,0.2);top:-3px;')
        elif _ca:
            _cds = 'width:8px;height:8px;background:#fff;top:-1px;'
        else:
            _cds = ('width:8px;height:8px;background:rgba(255,255,255,0.15);'
                    'border:1px solid rgba(255,255,255,0.3);top:-1px;')
        _cj_dots += (f'<div style="position:absolute;left:{_cp:.1f}%;transform:translateX(-50%);'
                     f'{_cds}border-radius:50%;z-index:2;"></div>')
        _cfw = "700" if _cc else "400"
        _cop = "1" if _ca else "0.4"
        _cj_lbls += (f'<div style="position:absolute;left:{_cp:.1f}%;transform:translateX(-50%);'
                     f'text-align:center;width:48px;margin-left:-24px;">'
                     f'<div style="font-size:9px;font-weight:{_cfw};color:rgba(255,255,255,{_cop});white-space:nowrap;">'
                     f'{esc(_ct["label"])}</div>'
                     f'<div style="font-size:8px;color:rgba(255,255,255,0.3);">{_ct["min_xp"]:,}</div>'
                     f'</div>')
    if _next_tier_c:
        _xtn = _next_tier_c["min_xp"] - total_xp
        _cnote = (f'<div style="font-size:10px;color:#9CA3AF;margin-top:2px;">'
                  f'{_xtn:,} AXP to {esc(_next_tier_c["label"])}</div>')
    else:
        _cnote = '<div style="font-size:10px;color:#1EBE8B;margin-top:2px;font-weight:700;">Max rank!</div>'

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

    # Inline group-assign form for the hero (admin only)
    group_assign_inline = ""
    if is_admin and groups:
        group_assign_inline = f"""
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.10);
                    display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
          <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                       letter-spacing:0.07em;color:rgba(255,255,255,0.40);white-space:nowrap;">Group</span>
          <form method="post" action="/coach/participants/{participant['id']}/assign-group"
                style="display:flex;gap:8px;align-items:center;flex:1;min-width:200px;">
            <select name="group_id"
                    style="flex:1;font-size:12px;padding:5px 8px;border-radius:7px;
                           border:1px solid rgba(255,255,255,0.20);
                           background:rgba(255,255,255,0.08);color:#fff;">
              {group_opts}
            </select>
            <button type="submit" class="btn btn-primary btn-sm"
                    style="font-size:12px;padding:5px 14px;white-space:nowrap;">Save</button>
          </form>
        </div>"""

    pid = participant['id']

    def _pnav(href, icon, title, subtitle, new_tab=False):
        target = ' target="_blank"' if new_tab else ''
        return f"""<a href="{href}"{target}
          style="display:flex;align-items:center;gap:16px;background:#2D323B;border-radius:16px;
                 padding:18px 20px;text-decoration:none;border-left:4px solid #F0A82E;
                 margin-bottom:10px;transition:opacity 0.15s;"
          onmouseover="this.style.opacity='0.88';" onmouseout="this.style.opacity='1';">
          <div style="width:48px;height:48px;border-radius:12px;background:rgba(240,168,46,0.15);
                      display:flex;align-items:center;justify-content:center;font-size:22px;
                      color:#F0A82E;flex-shrink:0;">{icon}</div>
          <div style="flex:1;">
            <div style="font-size:15px;font-weight:800;color:#FFFFFF;margin-bottom:2px;">{title}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.50);">{subtitle}</div>
          </div>
          <div style="font-size:20px;color:#F0A82E;font-weight:300;">&#8250;</div>
        </a>"""

    nav_cards = (
        _pnav(f"/coach/participants/{pid}/progress",   "&#9650;",  "Achievement Statistics",
              "Game-by-game progress, personal bests and improvements") +
        _pnav(f"/coach/participants/{pid}/report",     "&#9654;",  "Movement Report",
              "Full printable athlete progress report", new_tab=True) +
        _pnav(f"/coach/participants/{pid}/xp",         "&#9733;",  "AXP Profile",
              "XP history, level achievements and rank journey") +
        _pnav(f"/coach/participants/{pid}/quickstart.pdf", "&#9670;", "Quick-Start Card",
              "Printable game guide personalised for this athlete", new_tab=True) +
        _pnav(f"/coach/participants/{pid}/view-as",    "&#9673;",  "View as Athlete",
              "See the athlete dashboard through their eyes")
    )

    reset_inline = ""
    if reset_btn:
        reset_inline = f"""
        <form method="post" action="/coach/participants/{pid}/reset-password"
              onsubmit="return confirm('Reset {esc(participant['name'])}&#39;s password?');"
              style="margin-top:8px;">
          <button type="submit"
                  style="font-size:12px;color:rgba(255,255,255,0.40);background:none;border:none;
                         cursor:pointer;font-weight:600;padding:0;text-decoration:underline;">
            Reset Password
          </button>
        </form>"""

    body = f"""
    <div style="max-width:560px;margin:0 auto;padding-bottom:48px;">

    <!-- Athlete hero -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:24px 28px;margin-bottom:20px;">
      <div style="display:flex;align-items:flex-start;gap:14px;">
        <!-- Avatar -->
        <div style="width:60px;height:60px;border-radius:50%;background:rgba(240,168,46,0.18);
                    border:2px solid rgba(240,168,46,0.40);display:flex;align-items:center;
                    justify-content:center;font-weight:800;font-size:20px;color:#F0A82E;
                    flex-shrink:0;">{inits}</div>
        <!-- Identity -->
        <div style="flex:1;min-width:0;">
          <h1 style="margin:0 0 6px;font-size:22px;font-weight:800;color:#FFFFFF;line-height:1.2;">
            {esc(participant['name'])}
          </h1>
          <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
            {number_pill}{sport_pill}{gender_pill}{group_pill}
          </div>
          {f'<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.40);word-break:break-all;">{esc(participant["email"] or "")}</p>' if participant.get("email") else ""}
          {f'<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.45);">{esc(participant["programme"])}</p>' if participant.get("programme") else ""}
        </div>
        <!-- AXP snapshot -->
        <div style="text-align:right;flex-shrink:0;">
          <div style="font-size:32px;font-weight:800;color:#F0A82E;line-height:1;">{total_xp:,}</div>
          <div style="font-size:10px;color:rgba(255,255,255,0.40);letter-spacing:0.06em;margin-bottom:4px;">AXP</div>
          <span style="font-size:11px;font-weight:700;background:{tier_colour};color:#fff;
                       border-radius:999px;padding:2px 10px;">{tier_label}</span>
        </div>
      </div>
      <!-- Stats row -->
      <div style="display:flex;flex-wrap:wrap;gap:12px 20px;margin-top:14px;padding-top:12px;
                  border-top:1px solid rgba(255,255,255,0.09);">
        <div style="font-size:12px;color:rgba(255,255,255,0.50);">
          <span style="font-weight:700;color:#FFFFFF;">{session_count}</span> test sessions
        </div>
        <div style="font-size:12px;color:rgba(255,255,255,0.50);">
          <span style="font-weight:700;color:#FFFFFF;">{att_count}</span> sessions attended
        </div>
        <a href="/coach" style="margin-left:auto;font-size:12px;color:rgba(255,255,255,0.35);
                                text-decoration:none;align-self:center;"
           onmouseover="this.style.color='rgba(255,255,255,0.70)';"
           onmouseout="this.style.color='rgba(255,255,255,0.35)';">&larr; Back</a>
      </div>
      {reset_inline}
      {group_assign_inline}
    </div>

    {message_html}
    {transfer_notice}

    <!-- Nav cards -->
    <div style="margin-bottom:24px;">
      {nav_cards}
    </div>

    {measurement_games_form(pid)}

    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
      <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;"></div>
      <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                   color:#2D323B;">Measurement Games History</span>
    </div>
    {measurement_games_history(measurement_sessions, show_delete=True, participant_id=pid)}

    </div>"""
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
          <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
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
                <details open style="margin-bottom:12px;">
                  <summary style="list-style:none;cursor:pointer;display:flex;align-items:center;
                                  justify-content:space-between;padding:13px 18px;
                                  background:var(--jag-card);border:1.5px solid var(--jag-border);
                                  border-radius:12px;font-weight:700;font-size:15px;
                                  color:var(--jag-navy);user-select:none;">
                    {esc(game['name'])}
                    <span class="acc-chev" style="font-size:12px;color:var(--jag-muted);
                                                  transition:transform 0.2s;display:inline-block;">▼</span>
                  </summary>
                  <div style="background:var(--jag-card);border:1.5px solid var(--jag-border);
                              border-top:none;border-radius:0 0 12px 12px;
                              padding:4px 18px 18px;overflow-x:auto;">
                    <table class="table" style="width:100%;margin-top:12px;">
                      <thead><tr>
                        <th>Measurement</th>
                        <th>Group avg</th>
                        <th>By athlete &mdash; click to view profile</th>
                      </tr></thead>
                      <tbody>{rows}</tbody>
                    </table>
                  </div>
                </details>"""

        if game_cards:
            sections_html += f'<h2 class="section-title">{esc(section["section"])}</h2>{game_cards}'

    if not sections_html:
        sections_html = '<div class="card"><p class="muted">No measurements recorded yet.</p></div>'

    prog_link = f'/coach/groups/{group_id}/progress' if group_id else '/coach'
    body = f"""
    <style>
      details summary::-webkit-details-marker {{ display:none; }}
      details[open] summary .acc-chev {{ transform:rotate(180deg); }}
    </style>
    <div class="page-head">
      <div>
        <h1>{gname} &mdash; Achievement Summary</h1>
        <p class="muted">First session to most recent &mdash; {athlete_count} athlete{"s" if athlete_count != 1 else ""} with 2+ sessions</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <a class="btn btn-ghost" href="{prog_link}">Individual stats &rarr;</a>
        <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
      </div>
    </div>
    {level_bar}
    {hero_card}
    {athlete_grid}
    <div style="border-left:4px solid var(--jag-green);padding-left:12px;margin-bottom:20px;">
      <h2 style="margin:0 0 2px;font-size:17px;font-weight:700;">Measurement Breakdown</h2>
      <p class="muted" style="margin:0;">Group average per field with individual athlete results — click any game to expand or collapse</p>
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
          <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
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
          <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
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
        <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
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
            <a href="/coach/groups/{gid}/next-steps" class="btn btn-ghost btn-sm" style="font-size:11px;">&#128161; Next Steps</a>
          </div>
        </div>"""

    group_cards = f'<div class="jag-group-cards-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:32px;">{group_cards_html}</div>' if group_cards_html else ""

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
                     f'<a href="/coach/groups/{gid}/next-steps" class="btn btn-ghost btn-sm" style="font-size:12px;">&#128161; Next Steps</a>'
                     f'<a href="/coach/progress/pdf?scope=group&group_id={gid}" class="btn btn-ghost btn-sm no-print" style="font-size:12px;">&#128196; PDF</a>')

        group_sections_html += f"""
        <details style="margin-bottom:12px;">
          <summary style="list-style:none;cursor:pointer;display:flex;align-items:center;
                          gap:12px;padding:14px 18px;
                          background:var(--jag-card);border:1.5px solid var(--jag-border);
                          border-radius:12px;user-select:none;flex-wrap:wrap;">
            <div style="border-left:4px solid var(--jag-green);padding-left:12px;flex:1;min-width:0;">
              <div style="font-size:16px;font-weight:700;color:var(--jag-navy);">{gname}</div>
              <div style="font-size:12px;color:var(--jag-muted);">Group averages{filter_note}</div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;" onclick="event.stopPropagation();">{links}</div>
            <span class="acc-chev" style="font-size:12px;color:var(--jag-muted);
                                          transition:transform 0.2s;display:inline-block;flex-shrink:0;">▼</span>
          </summary>
          <div style="background:var(--jag-card);border:1.5px solid var(--jag-border);
                      border-top:none;border-radius:0 0 12px 12px;padding:20px 18px;">
            {tables_html}
          </div>
        </details>"""

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
    <style>
      details summary::-webkit-details-marker {{ display:none; }}
      details[open] summary .acc-chev {{ transform:rotate(180deg); }}
      @media (max-width: 640px) {{
        .jag-group-cards-grid {{ display:none !important; }}
      }}
    </style>
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
    <div style="border-left:4px solid var(--jag-green);padding-left:12px;margin-bottom:16px;">
      <h2 style="margin:0 0 2px;font-size:17px;font-weight:700;">Group Measurement Tables</h2>
      <p class="muted" style="margin:0;">Click a group to expand its round-by-round averages</p>
    </div>
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
    t_style      = ParagraphStyle("t",  fontName="Helvetica-Bold", fontSize=16, textColor=JAG_NAVY)
    s_style      = ParagraphStyle("s",  fontName="Helvetica",      fontSize=9,  textColor=JAG_GREY)
    hero_title_s = ParagraphStyle("ht", fontName="Helvetica-Bold", fontSize=20, textColor=colors.white, leading=26)
    hero_sub_s   = ParagraphStyle("hs", fontName="Helvetica",      fontSize=9,  textColor=JAG_GOLD,     leading=13)
    g_style      = ParagraphStyle("g",  fontName="Helvetica-Bold", fontSize=11, textColor=colors.white)
    gm_style     = ParagraphStyle("gm", fontName="Helvetica-Bold", fontSize=9,  textColor=JAG_NAVY)
    hdr_s        = ParagraphStyle("hd", fontName="Helvetica-Bold", fontSize=7,  textColor=colors.white,
                                   alignment=TA_CENTER, leading=9)
    fld_s        = ParagraphStyle("fl", fontName="Helvetica-Bold", fontSize=7,  textColor=JAG_NAVY,
                                   alignment=TA_LEFT, leading=9)
    val_s        = ParagraphStyle("vl", fontName="Helvetica",      fontSize=8,  alignment=TA_CENTER)
    pct_s        = ParagraphStyle("pc", fontName="Helvetica-Bold", fontSize=8,  alignment=TA_CENTER)
    pct_g        = ParagraphStyle("pg", fontName="Helvetica-Bold", fontSize=8,  textColor=JAG_GREEN, alignment=TA_CENTER)
    pct_r        = ParagraphStyle("pr", fontName="Helvetica-Bold", fontSize=8,  textColor=JAG_RED,   alignment=TA_CENTER)
    sec_s        = ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=7,  textColor=JAG_NAVY,
                                   alignment=TA_LEFT, leading=9)

    today = _dt.date.today().strftime("%d %B %Y")
    story = []

    # Hero banner
    hero_tbl = Table(
        [[Paragraph(title, hero_title_s)],
         [Paragraph(f"{subtitle} &nbsp;&middot;&nbsp; Generated {today} &nbsp;&middot;&nbsp; Just A Game", hero_sub_s)]],
        colWidths=[page_w],
    )
    hero_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), JAG_NAVY),
        ("TOPPADDING",    (0, 0), (0,  0),  12),
        ("BOTTOMPADDING", (0, 0), (0,  0),  4),
        ("TOPPADDING",    (0, 1), (0,  1),  0),
        ("BOTTOMPADDING", (0, 1), (0,  1),  12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("LINEBELOW",     (0, 1), (-1, 1),  2.5, JAG_GOLD),
    ]))
    story.append(hero_tbl)
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
                    sec_tbl = Table(
                        [[Paragraph(section["section"].upper(), sec_s)]],
                        colWidths=[page_w]
                    )
                    sec_tbl.setStyle(TableStyle([
                        ("LINEBEFORE",    (0, 0), (0, -1), 3, JAG_GOLD),
                        ("TOPPADDING",    (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                    ]))
                    story.append(sec_tbl)
                    story.append(Spacer(1, 2*mm))
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
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;max-width:820px;">
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
        content_html = """
    <div style="margin-top:8px;">

      <!-- ── How it works strip ─────────────────────────────────────── -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px;">

        <div style="background:#fff;border:1.5px solid #E5E7EB;border-radius:14px;
                    padding:20px 18px;display:flex;gap:14px;align-items:flex-start;">
          <div style="width:40px;height:40px;border-radius:10px;background:#2D323B;
                      display:flex;align-items:center;justify-content:center;
                      font-size:18px;color:#F0A82E;flex-shrink:0;font-weight:700;">◎</div>
          <div>
            <div style="font-weight:700;color:#2D323B;font-size:14px;margin-bottom:4px;">
              Athlete Overview
            </div>
            <div style="font-size:13px;color:#6E737B;line-height:1.5;">
              See every athlete's XP tier and level progress across all core measurement games at a glance.
            </div>
          </div>
        </div>

        <div style="background:#fff;border:1.5px solid #E5E7EB;border-radius:14px;
                    padding:20px 18px;display:flex;gap:14px;align-items:flex-start;">
          <div style="width:40px;height:40px;border-radius:10px;background:#2D323B;
                      display:flex;align-items:center;justify-content:center;
                      font-size:18px;color:#F0A82E;flex-shrink:0;font-weight:700;">✓</div>
          <div>
            <div style="font-weight:700;color:#2D323B;font-size:14px;margin-bottom:4px;">
              Completion Matrix
            </div>
            <div style="font-size:13px;color:#6E737B;line-height:1.5;">
              Track which athletes have been scored for each game. Click any gap to jump straight to data entry.
            </div>
          </div>
        </div>

        <div style="background:#fff;border:1.5px solid #E5E7EB;border-radius:14px;
                    padding:20px 18px;display:flex;gap:14px;align-items:flex-start;">
          <div style="width:40px;height:40px;border-radius:10px;background:#2D323B;
                      display:flex;align-items:center;justify-content:center;
                      font-size:18px;color:#F0A82E;flex-shrink:0;font-weight:700;">▤</div>
          <div>
            <div style="font-weight:700;color:#2D323B;font-size:14px;margin-bottom:4px;">
              Session Sheet
            </div>
            <div style="font-size:13px;color:#6E737B;line-height:1.5;">
              Download a printable PDF recording sheet for your group — blank or pre-filled with existing scores.
            </div>
          </div>
        </div>

      </div>

      <!-- ── Quick-start prompt ─────────────────────────────────────── -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d434d 100%);
                  border-radius:16px;padding:28px 32px;
                  display:flex;align-items:center;gap:24px;">
        <div style="width:52px;height:52px;border-radius:12px;background:rgba(240,168,46,0.15);
                    display:flex;align-items:center;justify-content:center;
                    font-size:26px;color:#F0A82E;font-weight:700;flex-shrink:0;">▲</div>
        <div style="flex:1;">
          <div style="font-size:17px;font-weight:700;color:#fff;margin-bottom:6px;">
            Select a group and test phase to get started
          </div>
          <div style="font-size:13px;color:#adb3bb;line-height:1.6;">
            Choose your group, the test phase, and optionally a month using the form above,
            then click <strong style="color:#F0A82E;">Load</strong> to see your full session hub.
          </div>
        </div>
        <div style="background:#F0A82E;border-radius:10px;padding:10px 20px;
                    font-weight:700;font-size:13px;color:#2D323B;white-space:nowrap;flex-shrink:0;">
          ↑ Start above
        </div>
      </div>

    </div>"""

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
    <div class="card form-card" style="margin-bottom:20px;">
      <div style="font-size:11px;font-weight:700;color:#6E737B;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:10px;">Load Session</div>
      {selector_form}
    </div>
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

def reports_landing_page(coach, groups, orgs=None, sports=None, active_windows=None):
    """Hub page: links to existing stats pages + new printable reports."""
    orgs = orgs or []
    sports = sports or []
    active_windows = active_windows or []

    group_opts = '<option value="">— All groups in org —</option>' + "".join(
        f'<option value="{g["id"]}">{esc(g["name"])}</option>' for g in groups
    )
    org_opts = '<option value="">— No org filter —</option>' + "".join(
        f'<option value="{o["id"]}">{esc(o["name"])}</option>' for o in orgs
    )
    sport_opts = '<option value="">— All sports —</option>' + "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>' for s in sports
    )

    # ── Measurement window status widget ────────────────────────────────────
    def _window_widget(windows):
        if not windows:
            return ""
        cards = ""
        for w in windows:
            try:
                dt = _dt.datetime.fromisoformat(w["opened_at"])
                opened_fmt = dt.strftime("%-d %b %Y")
            except Exception:
                opened_fmt = (w["opened_at"] or "")[:10]
            sub_count = w["submission_count"] or 0
            sub_label = f'{sub_count} submission{"s" if sub_count != 1 else ""}'
            session_lbl = esc(w["session_label"] or "Untitled Session")
            grp_name    = esc(w["group_name"])
            opened_by   = esc(w["opened_by_name"] or "")
            win_id      = w["id"]
            cards += f"""
            <div style="background:var(--jag-card);border:1px solid rgba(30,190,139,0.25);border-left:4px solid #1EBE8B;border-radius:8px;padding:16px 20px;display:flex;align-items:center;gap:16px;">
              <div style="flex:1;min-width:0;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
                  <span style="background:rgba(30,190,139,0.12);color:#1EBE8B;font-size:10px;font-weight:700;letter-spacing:0.07em;padding:2px 9px;border-radius:20px;text-transform:uppercase;">OPEN</span>
                  <span style="font-weight:700;font-size:14px;color:var(--jag-navy);">{grp_name}</span>
                  <span style="font-size:13px;color:var(--jag-text);">— {session_lbl}</span>
                </div>
                <div style="font-size:12px;color:var(--jag-muted);">Opened {opened_fmt} by {opened_by} &nbsp;·&nbsp; {sub_label}</div>
              </div>
              <a href="/coach/window/{win_id}" class="btn btn-ghost" style="white-space:nowrap;font-size:13px;flex-shrink:0;">Manage &rarr;</a>
            </div>"""
        return f"""
        <div style="margin-bottom:28px;">
          <h2 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--jag-muted);margin-bottom:12px;">Active Measurement Windows</h2>
          <div style="display:flex;flex-direction:column;gap:10px;">{cards}</div>
        </div>"""

    windows_widget = _window_widget(active_windows)

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

    {windows_widget}

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
      {_report_card("📈", "Athlete Progress Report",
          "Baseline vs latest session scores with % improvement and AAP Level for each athlete. Colour-coded green/red. Only athletes with 2+ sessions appear.",
          "progress")}
      {_report_card("✅", "Test Completion Sheet",
          "At-a-glance view of which measurement tests each athlete has completed across all active games. Shows a fraction (e.g. 4/6 fields) per game. Batch-printable by group or org.",
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
    """Printable test completion sheet — one row per athlete, one column per active game."""
    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group.get("name", "Group")

    # Build game list: (key, short_name, total_non_computed_fields) — all active games
    games_info = []
    for section in active_measurement_games():
        for game in section["games"]:
            total = len(game.get("fields", []))
            games_info.append((game["key"], game["name"], total))

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
    Compares sessions[-1] = baseline (oldest) vs sessions[0] = latest.
    Only athletes with >= 2 sessions appear.
    resources: list of resource rows (for self-organisation tag matching).
    """
    from constants import find_any_game, IMPROVEMENT_LEVELS

    today = _dt.date.today().strftime("%d %B %Y")
    group_name = group["name"] if group else "All Athletes"
    so_map = _build_game_so_map(resources or [])

    eligible = [(a, s) for a, s in athletes_data if len(s) >= 2]

    if not eligible:
        body_content = '<p style="color:#888;margin-top:20px;">No athletes with 2 or more test sessions found in this group.</p>'
        return _report_html_shell("Athlete Progress Report", group_name, group_name, body_content, today)

    def _aap_level_label(pct):
        """Map improvement % to the highest matching IMPROVEMENT_LEVELS label."""
        if pct is None:
            return "—"
        label = IMPROVEMENT_LEVELS[0][1]
        for threshold, name in IMPROVEMENT_LEVELS:
            if pct >= threshold:
                label = name
        return label

    # Collect used columns from baseline or latest of any eligible athlete
    used_cols = []
    seen = set()
    for athlete, sessions in eligible:
        r_base = sessions[-1]["results"]  # oldest = baseline
        r_latest = sessions[0]["results"]  # most recent
        for (gk, fk) in list(r_base.keys()) + list(r_latest.keys()):
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

    # For each col: 3 sub-columns Base / Latest / Δ%
    def _progress_th(gk, label):
        so = so_map.get(gk, "")
        so_line = f'<div style="font-size:9px;color:#F0A82E;font-weight:600;margin-top:3px;white-space:normal;line-height:1.3;">{esc(so)}</div>' if so else ""
        return f'<th colspan="3" style="border-left:2px solid rgba(255,255,255,0.2);white-space:nowrap;">{esc(label)}{so_line}</th>'

    th_cols = "".join(
        _progress_th(gk, label)
        for gk, _, label, _ in used_cols
    )
    th_sub = "".join(
        '<th style="font-size:9px;background:#3d4451;border-left:2px solid rgba(255,255,255,0.15);">Base</th>'
        '<th style="font-size:9px;background:#3d4451;">Latest</th>'
        '<th style="font-size:9px;background:#3d4451;">Δ%</th>'
        for _ in used_cols
    )
    header = (
        f'<tr><th rowspan="2">#</th><th rowspan="2">Athlete</th>{th_cols}'
        f'<th rowspan="2" style="border-left:2px solid rgba(255,255,255,0.2);">Overall Δ%</th>'
        f'<th rowspan="2" style="border-left:2px solid rgba(255,255,255,0.2);">AAP Level</th></tr>'
        f'<tr>{th_sub}</tr>'
    )

    rows = ""
    for athlete, sessions in eligible:
        r_base   = sessions[-1]["results"]  # oldest = baseline
        r_latest = sessions[0]["results"]   # most recent
        field_pcts = []
        tds = ""
        for gk, fk, _, ftype in used_cols:
            v1 = r_base.get((gk, fk))
            v2 = r_latest.get((gk, fk))
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
        aap_label = _aap_level_label(overall_pct)
        session_count = len(sessions)
        rows += (
            f'<tr><td style="color:#888;">{esc(athlete.get("athlete_number") or "")}</td>'
            f'<td style="font-weight:600;">{esc(athlete["name"])}'
            f'<div style="font-size:9px;color:#888;font-weight:400;">{session_count} session{"s" if session_count != 1 else ""}</div></td>'
            f'{tds}'
            f'<td class="{o_css}" style="font-size:13px;border-left:2px solid #ccc;">{o_s}</td>'
            f'<td style="font-size:11px;font-weight:600;color:#2D323B;border-left:2px solid #ccc;white-space:nowrap;">{esc(aap_label)}</td></tr>'
        )

    base_date   = eligible[0][1][-1]["date"] if eligible else ""
    latest_date = eligible[0][1][0]["date"]  if eligible else ""
    so_note = ' <span style="color:#F0A82E;">Gold text under each column header = self-organisation focus.</span>' if so_map else ""
    body_content = f"""
    <p style="font-size:12px;color:#555;margin-bottom:8px;">
      Baseline ({esc(base_date)}) vs latest session ({esc(latest_date)}) for <strong>{esc(group_name)}</strong>.
      <span style="color:#1a7a3a;font-weight:700;">Green</span> = improvement &nbsp;
      <span style="color:#c0392b;font-weight:700;">Red</span> = decline. Time fields: lower score = improvement.{so_note}
    </p>
    <div style="overflow-x:auto;"><table><thead>{header}</thead><tbody>{rows}</tbody></table></div>"""

    return _report_html_shell("Athlete Progress Report", group_name, group_name, body_content, today)


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

    has_sport_specific = bool(SPORT_SPECIFIC_GAMES)
    sport_section = f"""
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
      </div>""" if has_sport_specific else ""

    body = f"""
    <!-- Recording-for banner: hidden until athlete selected -->
    <div id="qs-banner" style="display:none;position:sticky;top:0;z-index:100;
         background:#2D323B;padding:12px 20px;margin-bottom:20px;
         border-radius:10px;flex-direction:row;align-items:center;justify-content:space-between;
         flex-wrap:wrap;gap:8px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:36px;height:36px;border-radius:50%;background:#F0A82E;
                    display:flex;align-items:center;justify-content:center;
                    font-size:16px;flex-shrink:0;">📋</div>
        <div>
          <div style="font-size:11px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:.06em;">Recording for</div>
          <div id="qs-banner-name" style="font-size:16px;font-weight:800;color:#fff;line-height:1.2;"></div>
        </div>
      </div>
      <span id="qs-progress-badge"
            style="background:#F0A82E;color:#2D323B;border-radius:999px;
                   padding:5px 16px;font-size:13px;font-weight:800;">0 saved</span>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;max-width:900px;align-items:start;">

      <!-- LEFT: Setup card -->
      <div class="card" style="padding:0;overflow:hidden;">
        <div style="background:#2D323B;padding:14px 18px;">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#F0A82E;margin-bottom:2px;">Step 1</div>
          <div style="font-size:15px;font-weight:700;color:#fff;">Session Setup</div>
        </div>
        <div style="padding:18px;">
          {_session_label_pickers()}
          <div id="qs-group-wrap" style="display:{show_group_filter}; margin-bottom:16px;">
            <label for="qs-group">Group</label>
            <select id="qs-group">{group_opts}</select>
          </div>
          <label for="qs-athlete">Athlete</label>
          <select id="qs-athlete" style="margin-bottom:0;">{athlete_opts}</select>
        </div>
      </div>

      <!-- RIGHT: Score entry card -->
      <div class="card" style="padding:0;overflow:hidden;">
        <div style="background:#2D323B;padding:14px 18px;">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#F0A82E;margin-bottom:2px;">Step 2</div>
          <div style="font-size:15px;font-weight:700;color:#fff;">Enter Score</div>
        </div>
        <div style="padding:18px;">
          {sport_section}
          <label for="qs-field">Measurement Field</label>
          <select id="qs-field" style="margin-bottom:16px;">{field_opts}</select>
          <div id="qs-fields" style="margin-top:4px;"></div>
          <div id="qs-score-hint" style="color:var(--jag-muted);font-size:13px;margin-top:8px;">
            Select an athlete and a measurement field to enter a score.
          </div>
        </div>
      </div>

    </div>

    <!-- Session Log -->
    <div style="max-width:900px;margin-top:16px;">
      <div class="card" style="padding:0;overflow:hidden;">
        <div style="background:#F9FAFB;border-bottom:1px solid #E5E7EB;padding:12px 18px;
                    display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:13px;font-weight:700;color:#2D323B;">Session Log</span>
          <span id="qs-log-count" style="font-size:12px;color:var(--jag-muted);">Nothing saved yet</span>
        </div>
        <div id="qs-log" style="padding:12px 18px;font-size:13px;color:var(--jag-muted);min-height:60px;"></div>
      </div>
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
      var scoreHintEl  = document.getElementById('qs-score-hint');
      var logCountEl   = document.getElementById('qs-log-count');

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
        if (scoreHintEl) {{
          scoreHintEl.style.display = athleteEl.value ? 'none' : 'block';
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
          '<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px;">' +
            '<div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#9CA3AF;margin-bottom:6px;">' + f.game_name + '</div>' +
            '<label style="font-size:14px; font-weight:700; display:block; margin-bottom:10px;color:#2D323B;">' +
              f.label + suffix +
            '</label>' +
            '<div class="mg-field-row" style="display:flex;gap:8px;align-items:center;">' +
              '<input type="number" step="' + step + '" min="0" id="qs-single-input" style="max-width:140px;font-size:20px;font-weight:700;text-align:center;padding:8px 12px;" />' +
              '<button type="button" class="mg-save-btn btn btn-primary" id="qs-single-btn" style="white-space:nowrap;padding:8px 20px;">&#10003; Save</button>' +
            '</div>' +
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
          entry.style.cssText = 'padding:10px 14px;margin-bottom:8px;border-radius:8px;border-left:3px solid #F0A82E;background:#FFFBEB;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;';
          entry.innerHTML =
            '<div>' +
              '<div style="font-weight:700;color:#2D323B;font-size:13px;">' + athleteName + '</div>' +
              '<div style="font-size:12px;color:#6E737B;margin-top:1px;">' + gameName + ' — ' + fieldLabel + '</div>' +
            '</div>' +
            '<div style="display:flex;align-items:center;gap:10px;">' +
              '<span style="font-size:18px;font-weight:800;color:#2D323B;">' + displayVal + '</span>' +
              '<span style="font-size:11px;color:#9CA3AF;">' + timeStr + '</span>' +
            '</div>';
          logEl.insertBefore(entry, logEl.firstChild);
          if (logCountEl) logCountEl.textContent = savedCount + ' score' + (savedCount !== 1 ? 's' : '') + ' saved';
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
            <div class="help-icon-box">{icon}</div>
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

    s_login = section("&#9654;", "Logging In", (
        steps([
            "Open the portal in your browser (or from your phone's home screen).",
            "Enter your <strong>email address</strong> and <strong>password</strong>.",
            "Tap <strong>Log in</strong>.",
        ])
        + tip("If you've forgotten your password, click <em>Forgot your password?</em> on the login page.")
        + tip("Save the portal to your phone's home screen for one-tap access — see <em>Using the Portal on Your Phone</em> below.")
    ), open_by_default=True)

    s_password = section("&#10033;", "Changing Your Password", (
        steps([
            "Click <strong>My Account</strong> in the top-right corner.",
            "Scroll to the <em>Change Password</em> section.",
            "Enter your current password, then your new password twice.",
            "Click <strong>Change Password</strong> to save.",
        ])
        + tip("Choose a password that is at least 8 characters and easy for you to remember.")
    ))

    s_phone = section("&#9990;", "Using the Portal on Your Phone", (
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

    s_dashboard = section("&#9650;", "Your Dashboard", (
        "<p>Your dashboard shows your most recent results, level progress, and personal bests across all measurement games.</p>"
        "<ul class='help-list'>"
        "<li><strong>Level badge</strong> — your current adaptability level, based on your improvement across games.</li>"
        "<li><strong>Game cards</strong> — your latest score and personal best for each game.</li>"
        "<li><strong>Progress history</strong> — tap a game name to see your full result history over time.</li>"
        "</ul>"
        + note("Scores are entered by your practitioner after each session. Check back after a session to see your updated results.")
    ))

    sections_html = s_login + s_password + s_phone + s_dashboard

    # ── System Map (staff only) ────────────────────────────────────────────────
    if is_staff:
        def _map_area(accent, icon, title, links):
            """One area card: coloured left bar, title, bullet link list."""
            link_rows = "".join(
                f'<a href="{href}" style="display:block;font-size:12px;font-weight:600;'
                f'color:#2D323B;text-decoration:none;padding:5px 8px;border-radius:6px;'
                f'margin-bottom:2px;background:#F4F5F7;"'
                f' onmouseover="this.style.background=\'#EEF0F2\';this.style.color=\'{accent}\';"'
                f' onmouseout="this.style.background=\'#F4F5F7\';this.style.color=\'#2D323B\';">'
                f'{label}</a>'
                for href, label in links
            )
            return (
                f'<div style="background:#fff;border-radius:10px;border:1px solid #E5E7EB;'
                f'border-left:4px solid {accent};padding:14px 16px;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
                f'<span style="font-size:16px;">{icon}</span>'
                f'<span style="font-size:13px;font-weight:800;color:#2D323B;">{title}</span>'
                f'</div>'
                f'{link_rows}'
                f'</div>'
            )

        def _flow_label(txt):
            return (f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.08em;color:#9CA3AF;margin:18px 0 8px;">{txt}</div>')

        prac_map = (
            _flow_label("Daily workflows") +
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;">' +
            _map_area("#F0A82E", "&#9654;", "Practitioner Hub", [
                ("/coach", "Home — all nav cards"),
            ]) +
            _map_area("#F0A82E", "&#128101;", "Groups &amp; Athletes", [
                ("/coach/groups",           "Groups list &amp; athlete tiles"),
                ("/coach/participants/new", "Add new athlete"),
            ]) +
            _map_area("#F0A82E", "&#9651;", "Athlete Profile", [
                ("/coach/participants/{id}",          "Profile &amp; recording form"),
                ("/coach/participants/{id}/progress", "Achievement statistics"),
                ("/coach/participants/{id}/report",   "Movement report"),
                ("/coach/participants/{id}/xp",       "AXP profile"),
                ("/coach/participants/{id}/quickstart.pdf", "Quick-start card (PDF)"),
                ("/coach/participants/{id}/view-as",  "View as athlete"),
            ]) +
            '</div>' +

            _flow_label("Official testing") +
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;">' +
            _map_area("#1EBE8B", "&#9632;", "Group Hub", [
                ("/coach/group-hub",       "Open measurement window"),
                ("/coach/window/{id}",     "Live window status &amp; close"),
                ("/coach/session-sheet",   "Session sheet PDF"),
                ("/coach/group-testing",   "Group score entry table"),
            ]) +
            _map_area("#1EBE8B", "&#9679;", "Attendance", [
                ("/coach/attendance",          "Attendance history"),
                ("/coach/attendance/new",      "New attendance event"),
                ("/coach/attendance/{id}/roll-call", "Roll call (unlocks self-directed)"),
            ]) +
            _map_area("#1EBE8B", "&#9733;", "Post-Session", [
                ("/coach/session/success/{id}", "Session success &amp; AXP summary"),
                ("/coach/session",              "Record single session"),
            ]) +
            '</div>' +

            _flow_label("Reports &amp; analytics") +
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;">' +
            _map_area("#6366F1", "&#9650;", "Reports", [
                ("/coach/reports",                           "Reports landing"),
                ("/coach/progress",                          "All-groups progress"),
                ("/coach/reports/baseline",                  "Baseline report"),
                ("/coach/reports/progress",                  "Progress report"),
                ("/coach/reports/completion",                "Completion report"),
                ("/coach/groups/{id}/achievement-summary",   "Group achievement summary"),
                ("/coach/groups/{id}/next-steps",            "Group next steps"),
                ("/coach/groups/{id}/scores",                "Group scores table"),
            ]) +
            _map_area("#6366F1", "&#9670;", "Leaderboard &amp; Resources", [
                ("/coach/leaderboard",   "Group AXP leaderboard"),
                ("/coach/resources",     "Resource library (manage)"),
                ("/athlete/resources",   "Resource library (athlete view)"),
            ]) +
            _map_area("#6366F1", "&#9636;", "Data Tools", [
                ("/coach/participants/import", "Import athletes (CSV)"),
                ("/coach/participants/export.csv", "Export athletes (CSV)"),
                ("/coach/scores/import",       "Import scores (CSV)"),
            ]) +
            '</div>'
        )

        admin_map = ""
        if is_org_admin:
            admin_map = (
                _flow_label("Admin-only areas") +
                f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;">' +
                _map_area("#8B5CF6", "&#9881;", "Admin Hub", [
                    ("/coach/admin/hub", "All admin tools in one place"),
                ]) +
                _map_area("#8B5CF6", "&#9651;", "People", [
                    ("/coach/coaches",           "Manage practitioners"),
                    ("/coach/coaches/new",       "Add practitioner"),
                    ("/coach/organisations",     "Manage organisations"),
                ]) +
                _map_area("#8B5CF6", "&#9670;", "Game Config", [
                    ("/coach/admin/score-distribution", "Score distribution report"),
                    ("/coach/admin/game-thresholds",    "Set level thresholds"),
                ]) +
                _map_area("#8B5CF6", "&#9632;", "Data &amp; Sessions", [
                    ("/coach/admin/sessions",            "Session browser &amp; merge"),
                    ("/coach/completion-tracker",        "Completion tracker"),
                    ("/coach/admin/game-thresholds#retroactive", "Retroactive AXP pass"),
                ]) +
                '</div>'
            )

        s_system_map = section(
            "&#9670;", "System Map — All Pages &amp; Features",
            f'<p style="margin-bottom:16px;font-size:14px;color:#6E737B;">'
            f'Every page in the portal you can access, organised by workflow. Click any link to go there.</p>'
            f'{prac_map}{admin_map}',
            open_by_default=True
        )
        sections_html = s_system_map + sections_html

    if is_staff:
        s_add_athlete = section("&#43;", "Adding an Athlete", (
            steps([
                "Click <strong>Add Participant</strong> in the navigation bar.",
                "Fill in the athlete's name and (optionally) email, sport, and group.",
                "Click <strong>Add Participant</strong> to save.",
            ])
            + tip("If you enter an email address, the athlete will automatically receive a welcome email with their login details.")
            + tip("Athlete numbers are assigned automatically — you can change them on the athlete's profile page.")
        ))

        s_record = section("&#9679;", "Recording a Session", (
            "<p>Use <strong>Record Session</strong> in the nav to record a one-off session for a single athlete.</p>"
            + steps([
                "Select the athlete from the dropdown.",
                "Choose the session type and month.",
                "Select which games were played using the chip panel.",
                "Enter the scores and click <strong>Save Session</strong>.",
            ])
            + tip("The system will warn you if a session already exists for that athlete in that month — you can choose to merge or replace.")
        ))

        s_group_hub = section("&#9632;", "Group Hub", (
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

        s_resources = section("&#9636;", "Resources", (
            "<p>The <strong>Resources</strong> section holds shared files, links, and guides for your organisation.</p>"
            "<ul class='help-list'>"
            "<li>Resources are organised into folders.</li>"
            "<li>Each resource can have tags to help with searching and filtering.</li>"
            "<li>Click a resource tile to open it (external links open in a new tab).</li>"
            "</ul>"
            + note("Only practitioners and admins can add or edit resources. Contact your System Admin if you need something added.")
        ))

        s_reports = section("&#9650;", "Statistics &amp; Reports", (
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
        s_practitioners = section("&#9651;", "Managing Practitioners", (
            "<p>As an Organisation Admin, you can view and manage practitioners in your organisation.</p>"
            + steps([
                "Go to <strong>Practitioners</strong> in the navigation.",
                "To add a new practitioner, click <strong>Add Practitioner</strong> and fill in their details.",
                "To reset a practitioner's password, click <strong>Reset Password</strong> on their row.",
                "To assign a practitioner to your organisation, use the <strong>Organisation</strong> dropdown on their entry.",
            ])
            + tip("When you create a practitioner account with an email address, they will receive a welcome email automatically.")
        ))

        s_org_admin = section("&#9670;", "Your Organisation", (
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
        s_orgs = section("&#9670;", "Managing Organisations", (
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

    if is_staff:
        guide_card = (
            '<a href="/coach/getting-started" style="display:flex;align-items:center;gap:16px;'
            'background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border:1.5px solid ' + GOLD + ';'
            'border-radius:14px;padding:18px 22px;text-decoration:none;margin-bottom:20px;">'
            '<div style="width:44px;height:44px;border-radius:12px;background:rgba(240,168,46,0.18);'
            'border:1px solid rgba(240,168,46,0.35);display:flex;align-items:center;'
            'justify-content:center;font-size:22px;flex-shrink:0;">&#9733;</div>'
            '<div style="flex:1;">'
            '<div style="font-size:15px;font-weight:800;color:#FFFFFF;margin-bottom:3px;">Getting Started Guide</div>'
            '<div style="font-size:13px;color:rgba(255,255,255,0.55);">Step-by-step setup — groups, athletes, sessions, reports. Printable.</div>'
            '</div>'
            '<div style="font-size:24px;color:' + GOLD + ';font-weight:300;">&#8250;</div>'
            '</a>'
        )
    else:
        guide_card = ""

    body = f"""
    <style>
      .help-section {{
        border: 1px solid #DDE0E3;
        border-left: 3px solid rgba(240,168,46,0.35);
        border-radius: 10px;
        margin-bottom: 10px;
        background: #fff;
        overflow: hidden;
        transition: border-color 0.15s;
      }}
      .help-section[open] {{
        border-left-color: {GOLD};
        box-shadow: 0 2px 10px rgba(45,50,59,0.10);
      }}
      .help-section-summary {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 18px;
        cursor: pointer;
        list-style: none;
        user-select: none;
        background: #fff;
        transition: background 0.15s;
      }}
      .help-section-summary::-webkit-details-marker {{ display: none; }}
      .help-section[open] .help-section-summary {{
        background: {NAVY};
        color: #fff;
      }}
      .help-section[open] .help-title {{ color: #fff; }}
      .help-section[open] .help-chevron {{
        transform: rotate(180deg);
        color: {GOLD};
      }}
      .help-icon-box {{
        width: 34px; height: 34px; min-width: 34px;
        border-radius: 9px;
        background: rgba(240,168,46,0.14);
        border: 1px solid rgba(240,168,46,0.30);
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; font-weight: 700; color: #F0A82E;
        flex-shrink: 0;
        transition: background 0.15s, border-color 0.15s;
      }}
      .help-section[open] .help-icon-box {{
        background: rgba(240,168,46,0.22);
        border-color: rgba(240,168,46,0.50);
        color: #F0A82E;
      }}
      .help-title {{
        font-weight: 700;
        font-size: 15px;
        color: {NAVY};
        flex: 1;
      }}
      .help-chevron {{
        font-size: 11px;
        color: #9CA3AF;
        transition: transform 0.2s, color 0.15s;
        flex-shrink: 0;
      }}
      .help-body {{
        padding: 20px 22px 22px;
        border-top: 1px solid rgba(240,168,46,0.20);
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
        width: 26px; height: 26px; min-width: 26px;
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
        background: rgba(240,168,46,0.08);
        border-left: 3px solid {GOLD};
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 14px;
        color: #7A5800;
        display: flex;
        gap: 8px;
        align-items: flex-start;
      }}
      .help-note {{
        background: rgba(45,50,59,0.05);
        border-left: 3px solid {NAVY};
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin: 12px 0;
        font-size: 14px;
        color: {NAVY};
        display: flex;
        gap: 8px;
        align-items: flex-start;
      }}
    </style>

    <div style="background:linear-gradient(135deg,{NAVY} 0%,#3d4350 100%);
                border-radius:16px;padding:24px 28px;margin-bottom:24px;">
      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
        <div style="width:46px;height:46px;border-radius:13px;flex-shrink:0;
                    background:rgba(240,168,46,0.18);border:1px solid rgba(240,168,46,0.38);
                    display:flex;align-items:center;justify-content:center;
                    font-size:26px;font-weight:900;color:#F0A82E;">?</div>
        <div style="flex:1;min-width:0;">
          <h1 style="margin:0 0 2px;font-size:22px;font-weight:800;color:#fff;line-height:1.2;">Help &amp; Guide</h1>
          <div style="font-size:13px;color:rgba(255,255,255,0.55);">
            Sections shown for your access level — click a heading to expand
          </div>
        </div>
        <div style="background:{GOLD};color:{NAVY};font-weight:700;font-size:12px;
                    padding:4px 14px;border-radius:20px;letter-spacing:0.04em;white-space:nowrap;">
          {esc(role_label)}
        </div>
      </div>
    </div>

    {guide_card}

    {sections_html}

    <div style="margin-top:24px;padding:18px 22px;
                background:linear-gradient(135deg,{NAVY} 0%,#3d4350 100%);
                border-radius:12px;font-size:14px;color:rgba(255,255,255,0.70);">
      <strong style="color:#fff;display:block;margin-bottom:4px;">Need more help?</strong>
      Contact your practitioner or system administrator, or email
      <a href="mailto:info@justagame.co.nz" style="color:{GOLD};text-decoration:none;">info@justagame.co.nz</a>.
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


def session_success_page(coach, participant, session, results, xp_events, level_ups):
    """Confirmation screen shown to a practitioner after saving a formal measurement session."""
    from constants import GAME_DISPLAY_NAMES as _GDN
    name = esc(participant.get("name", "Athlete"))
    pid  = participant.get("id", "")
    label = esc(session.get("session_label") or "")
    date_str = esc((session.get("date") or "")[:10])
    total_xp = sum(e.get("amount", 0) for e in xp_events)

    _XP_LABELS = {
        "session": "Session completed",
        "self_directed": "Self-directed session",
        "first_game": "First game recorded",
        "level_up": "Level achieved",
        "streak_3": "3-session streak",
        "streak_5": "5-session streak",
        "personal_best": "Personal best",
        "welcome": "Welcome bonus",
    }

    # ── Scores recorded ──────────────────────────────────────────────────────
    # Group by game
    games_seen = {}
    for (gk, fk, val) in results:
        if gk not in games_seen:
            games_seen[gk] = []
        games_seen[gk].append((fk, val))

    score_rows = ""
    for gk, fields in games_seen.items():
        game_label = esc(_GDN.get(gk, gk))
        field_strs = ", ".join(f"{v:g}" for _, v in fields)
        score_rows += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:9px 14px;border-bottom:1px solid #F0F1F3;">
          <span style="font-size:13px;color:#2D323B;font-weight:500;">{game_label}</span>
          <span style="font-size:13px;font-weight:700;color:#2D323B;">{field_strs}</span>
        </div>"""
    if not score_rows:
        score_rows = '<div style="padding:12px 14px;font-size:13px;color:#9CA3AF;">No scores recorded.</div>'

    # ── Level-ups ─────────────────────────────────────────────────────────────
    level_up_html = ""
    if level_ups:
        pills = ""
        for lu in level_ups:
            game_lbl = esc(_GDN.get(lu.get("game_key", ""), lu.get("game_key", "")))
            lvl = lu.get("level", "")
            pills += (f'<span style="font-size:12px;font-weight:700;padding:4px 14px;'
                      f'background:#F0A82E;color:#2D323B;border-radius:999px;'
                      f'white-space:nowrap;">&#9650; {game_lbl} → L{lvl}</span> ')
        level_up_html = f"""
        <div style="background:rgba(240,168,46,0.10);border:1px solid rgba(240,168,46,0.30);
                    border-radius:10px;padding:12px 16px;margin-bottom:16px;">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                      color:#7A5800;margin-bottom:8px;">&#127881; Level-ups this session</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;">{pills}</div>
        </div>"""

    # ── XP breakdown ─────────────────────────────────────────────────────────
    xp_rows = ""
    for e in xp_events:
        xp_type = e.get("xp_type", "")
        label_e = esc(e.get("notes") or _XP_LABELS.get(xp_type, xp_type))
        xp_rows += f"""
        <div style="display:flex;justify-content:space-between;padding:7px 0;
                    border-bottom:1px solid rgba(255,255,255,0.10);">
          <span style="font-size:12px;color:rgba(255,255,255,0.75);">{label_e}</span>
          <span style="font-size:12px;font-weight:700;color:#F0A82E;">+{e.get('amount',0):,}</span>
        </div>"""

    xp_block = ""
    if xp_events:
        xp_block = f"""
        <div style="margin-top:14px;background:rgba(255,255,255,0.07);border-radius:10px;padding:12px 16px;">
          <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                      color:rgba(240,168,46,0.80);margin-bottom:6px;">AXP awarded to {name}</div>
          {xp_rows}
          <div style="display:flex;justify-content:space-between;padding-top:8px;margin-top:4px;">
            <span style="font-size:12px;font-weight:700;color:#fff;">Total</span>
            <span style="font-size:14px;font-weight:900;color:#F0A82E;">+{total_xp:,} AXP</span>
          </div>
        </div>"""

    session_meta = label if label else date_str

    body = f"""
    <div class="container" style="max-width:600px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:20px;color:#fff;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:14px;">
            <div style="width:48px;height:48px;border-radius:13px;background:rgba(30,190,139,0.18);
                        border:1.5px solid rgba(30,190,139,0.35);display:flex;align-items:center;
                        justify-content:center;font-size:22px;flex-shrink:0;">&#10003;</div>
            <div>
              <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                          color:rgba(30,190,139,0.85);margin-bottom:2px;">Session Saved</div>
              <div style="font-size:20px;font-weight:800;line-height:1.2;">{name}</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:2px;">{session_meta}</div>
            </div>
          </div>
          <a href="/coach/participants/{pid}"
             style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.65);text-decoration:none;
                    padding:5px 12px;border-radius:20px;border:1px solid rgba(255,255,255,0.20);
                    background:rgba(255,255,255,0.08);white-space:nowrap;align-self:flex-start;"
             onmouseover="this.style.background='rgba(255,255,255,0.15)'"
             onmouseout="this.style.background='rgba(255,255,255,0.08)'">&larr; Athlete Profile</a>
        </div>
        {xp_block}
      </div>

      {level_up_html}

      <!-- Scores recorded -->
      <div style="display:flex;align-items:center;gap:0;margin-bottom:12px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Scores Recorded</span>
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;margin-bottom:24px;background:#fff;">
        {score_rows}
      </div>

      <!-- Actions -->
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <a href="/coach/participants/{pid}/report"
           style="flex:1;text-align:center;padding:12px 16px;background:#F0A82E;color:#2D323B;
                  font-weight:700;font-size:13px;border-radius:10px;text-decoration:none;">
          View Progress Report &#8594;
        </a>
        <a href="/coach/participants/{pid}"
           style="flex:1;text-align:center;padding:12px 16px;background:rgba(45,50,59,0.06);
                  color:#2D323B;font-weight:600;font-size:13px;border-radius:10px;
                  text-decoration:none;border:1px solid #E5E7EB;">
          Athlete Profile
        </a>
      </div>
    </div>"""
    return layout("Session Saved", body, user=coach, active_nav="participants")


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
            deactivate_color = "color:#c0392b;" if c["active"] else ""
            action_html = f"""
            <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-start;min-width:200px;">
              <!-- Row 1: role + status actions -->
              <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
                <form method="post" action="/coach/coaches/{c['id']}/toggle-admin" style="display:contents"
                      onsubmit="return confirm('{admin_toggle_label} for {esc(c['name'])}?');">
                  <button type="submit" class="btn btn-ghost btn-sm"
                          style="font-size:11px;">{admin_toggle_label}</button>
                </form>
                <form method="post" action="/coach/coaches/{c['id']}/toggle" style="display:contents">
                  <button type="submit" class="btn btn-ghost btn-sm"
                          style="font-size:11px;{deactivate_color}">{toggle_label}</button>
                </form>
              </div>
              <!-- Row 2: password reset (secondary) -->
              <form method="post" action="/coach/coaches/{c['id']}/reset-password"
                    onsubmit="return confirm('Reset {esc(c['name'])}&#39;s password?');">
                <button type="submit" class="btn btn-ghost btn-sm"
                        style="font-size:11px;color:var(--jag-muted);">&#128273; Reset Password</button>
              </form>
              <!-- Row 3: org assignment -->
              {org_form}
              <!-- Row 4: group assignment accordion -->
              <details style="width:100%;">
                <summary style="font-size:12px;font-weight:600;color:var(--jag-muted);cursor:pointer;
                                list-style:none;display:flex;align-items:center;gap:4px;user-select:none;">
                  <span class="acc-chev" style="font-size:10px;transition:transform 0.15s;display:inline-block;">&#9654;</span> Assign Groups
                </summary>
                <form method="post" action="/coach/coaches/{c['id']}/assign-group"
                      style="margin-top:8px;">
                  <div style="border:1px solid var(--jag-border);border-radius:8px;
                               padding:8px 12px;background:#FAFAFA;margin-bottom:8px;
                               max-height:140px;overflow-y:auto;">
                    {checkboxes}
                  </div>
                  <button type="submit" class="btn btn-ghost btn-sm"
                          style="font-size:11px;">Save Groups</button>
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
    <!-- Hero banner -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;
                justify-content:space-between;gap:16px;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:16px;">
        <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                    border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                    justify-content:center;font-size:22px;flex-shrink:0;color:#F0A82E;font-weight:700;">&#128101;</div>
        <div>
          <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Practitioners</div>
          <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:3px;">
            Manage accounts, roles, and organisation assignments.
          </div>
        </div>
      </div>
      <a class="btn btn-primary" href="/coach/coaches/new"
         style="white-space:nowrap;">+ Add Practitioner</a>
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
    <!-- Hero banner -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;gap:18px;">
      <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                  border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                  justify-content:center;font-size:22px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9962;</div>
      <div>
        <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Organisations</div>
        <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:3px;">
          Schools, clubs, and programmes — scope practitioners to their own athletes.
        </div>
      </div>
    </div>

    {message_html}

    <!-- Two-column layout: table + form -->
    <div style="display:flex;flex-wrap:wrap;gap:24px;align-items:start;">

      <!-- Left: org table -->
      <div class="card" style="flex:1;min-width:0;overflow-x:auto;">
        <table class="table">
          <thead><tr><th>Name</th><th style="text-align:center;">Groups</th><th style="text-align:center;">Practitioners</th><th></th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>

      <!-- Right: add form -->
      <div class="card form-card" style="width:320px;min-width:280px;flex-shrink:0;flex-grow:1;max-width:380px;">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                    color:var(--jag-muted);margin-bottom:16px;display:flex;align-items:center;gap:8px;">
          Add Organisation
          <div style="flex:1;height:1px;background:var(--jag-border);"></div>
        </div>
        <form method="post" action="/coach/organisations/new">
          <label for="new-org-name">Name</label>
          <input type="text" id="new-org-name" name="name" placeholder="e.g. Makoura College" required />
          <label for="new-org-type">Type <span style="font-weight:400;color:var(--jag-muted);">(optional)</span></label>
          <select id="new-org-type" name="type">
            <option value="">— Select type —</option>
            {type_options}
          </select>
          <label for="new-org-icon">Logo URL <span style="font-weight:400;color:var(--jag-muted);">(optional)</span></label>
          <input type="url" id="new-org-icon" name="icon_url" placeholder="https://…" />
          <p style="font-size:11px;color:var(--jag-muted);margin-top:4px;line-height:1.4;">
            Google Drive: Share → Anyone with link → copy URL.
          </p>
          <div style="margin-top:16px;">
            <button type="submit" class="btn btn-primary btn-block">Create Organisation</button>
          </div>
        </form>
      </div>

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
    # Alternating accent colour: gold for even ids, navy for odd
    accent   = '#F0A82E' if r['id'] % 2 == 0 else '#2D323B'
    icon_col = '#2D323B' if accent == '#F0A82E' else '#F0A82E'

    name_q = esc(r['name']).replace("'", "\\'")
    desc = f'<span style="font-size:12px;color:var(--jag-muted);display:block;margin-top:5px;line-height:1.5;">{esc(r["description"])}</span>' if r['description'] else ''
    so_val = r['self_organisation'] if 'self_organisation' in r.keys() and r['self_organisation'] else None
    self_org_badge = (
        f'<div style="margin-top:8px;padding:5px 10px;background:rgba(240,168,46,0.10);border-radius:8px;">'
        f'<span style="font-size:10px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;color:var(--jag-muted);">Self-organisation</span><br>'
        f'<span style="font-size:12px;font-weight:600;color:#C98B00;">{esc(so_val)}</span>'
        f'</div>'
    ) if so_val else ''
    drag = '<span class="drag-handle" title="Drag to reorder" style="position:absolute;top:10px;left:10px;font-size:12px;color:rgba(255,255,255,0.55);cursor:grab;z-index:2;">&#9776;</span>' if is_admin else ""
    admin_actions = f"""<div style="display:flex;gap:6px;margin-top:auto;padding-top:10px;border-top:1px solid #F0F0F0;">
        <a href="/coach/resources/{r['id']}/edit" class="btn btn-ghost btn-sm" style="flex:1;text-align:center;font-size:11px;padding:3px 0;">&#9998; Edit</a>
        <form method="post" action="/coach/resources/{r['id']}/delete" style="flex:1;"
              onsubmit="return confirm('Delete \\'{name_q}\\'?');">
          <button type="submit" class="btn btn-ghost btn-sm" style="width:100%;font-size:11px;padding:3px 0;color:#c0392b;">&#10005; Delete</button>
        </form>
      </div>""" if is_admin else ""

    tag_names = [t["name"] for t in (tags or [])]
    tag_data  = ",".join(t.lower() for t in tag_names)
    if tag_names:
        chips = ''.join(
            f'<span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;'
            f'padding:2px 8px;border-radius:20px;background:rgba(240,168,46,0.15);color:#9a6c00;">{esc(t)}</span>'
            for t in tag_names[:4]
        )
        tags_html = f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;">{chips}</div>'
    else:
        tags_html = ''
    search_data = (r['name'] + " " + (r['description'] or "")).lower()

    # SVG document icon — uses single quotes for safe JS embedding
    placeholder_svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='42' height='42'"
        f" viewBox='0 0 24 24' fill='{icon_col}'>"
        f"<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/>"
        f"<polyline points='14 2 14 8 20 8' fill='none' stroke='{icon_col}' stroke-width='1.5'/>"
        f"<line x1='8' y1='13' x2='16' y2='13' stroke='{'#2D323B' if icon_col != '#2D323B' else '#F0A82E'}' stroke-width='1.5' stroke-linecap='round'/>"
        f"<line x1='8' y1='17' x2='14' y2='17' stroke='{'#2D323B' if icon_col != '#2D323B' else '#F0A82E'}' stroke-width='1.5' stroke-linecap='round'/>"
        f"</svg>"
    )
    svg_js = placeholder_svg.replace("'", "\\'")
    fallback_style = (
        f"margin:-14px -14px 14px;height:110px;border-radius:8px 8px 0 0;"
        f"background:{accent};display:flex;align-items:center;justify-content:center;"
    ).replace("'", "\\'")

    # Google Drive thumbnail — or branded placeholder header
    thumb_url = _gdrive_thumbnail(r['url'] or '')
    if thumb_url:
        thumb_html = (
            f'<a href="{esc(r["url"])}" target="_blank" rel="noopener" tabindex="-1"'
            f' style="display:block;margin:-14px -14px 14px;border-radius:8px 8px 0 0;overflow:hidden;flex-shrink:0;">'
            f'<img src="{thumb_url}" alt="" loading="lazy"'
            f' style="width:100%;height:140px;object-fit:cover;display:block;"'
            f" onerror=\"this.parentElement.outerHTML='<div style=\\'{fallback_style}\\'>{svg_js}</div>';\">"
            f'</a>'
        )
    else:
        thumb_html = (
            f'<div style="margin:-14px -14px 14px;height:110px;border-radius:8px 8px 0 0;'
            f'background:{accent};display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
            f'{placeholder_svg}'
            f'</div>'
        )
    pad = '14px 14px 14px 28px' if is_admin else '14px'
    return (
        f'<div class="res-tile" data-id="{r["id"]}" data-tags="{esc(tag_data)}"'
        f' data-search="{esc(search_data)}"'
        f' style="position:relative;background:var(--jag-card);'
        f'border:1.5px solid #E8E9EB;border-top:4px solid {accent};'
        f'border-radius:10px;padding:{pad};display:flex;flex-direction:column;'
        f'word-break:break-word;overflow:hidden;transition:box-shadow 0.18s,transform 0.15s;"'
        f' onmouseover="this.style.boxShadow=\'0 6px 22px rgba(240,168,46,0.20)\';this.style.transform=\'translateY(-3px)\';"'
        f' onmouseout="this.style.boxShadow=\'\';this.style.transform=\'\';">'
        f'{drag}'
        f'{thumb_html}'
        f'<a href="{esc(r["url"])}" target="_blank" rel="noopener"'
        f' style="font-weight:700;font-size:14px;color:var(--jag-navy);text-decoration:none;line-height:1.3;"'
        f' onmouseover="this.style.textDecoration=\'underline\';" onmouseout="this.style.textDecoration=\'none\';">'
        f'{esc(r["name"])} <span style="font-size:11px;color:#F0A82E;">&#8599;</span></a>'
        f'{desc}'
        f'{self_org_badge}'
        f'{tags_html}'
        f'<div style="flex:1;min-height:6px;"></div>'
        f'{admin_actions}'
        f'</div>'
    )


def _resource_tile_wrap(tiles_html, list_id=None):
    """Wrap resource tiles in a CSS grid container."""
    list_attr = f' data-list-id="{list_id}"' if list_id is not None else ""
    return f'<div class="res-tiles-wrap" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px;padding:10px 0 14px;align-items:stretch;"{list_attr}>{tiles_html}</div>'


def resources_page(user, folder_groups, ungrouped, folders, message=None, error=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    is_admin = user.get("is_admin")

    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}">{esc(f["name"])}</option>' for f in folders
    )

    # Build folder sections — link tile layout
    folder_sections = ""
    for folder, resources in folder_groups:
        tiles_html = "".join(_resource_tile(r, is_admin=is_admin) for r in resources)
        count = len(resources)
        count_text = f'<span class="muted" style="font-size:14px; font-weight:400;">&nbsp;({count} link{"s" if count != 1 else ""})</span>'
        list_content = _resource_tile_wrap(tiles_html, list_id=folder['id']) if tiles_html else '<p class="muted" style="margin:8px 0 0; font-size:13px;">No resources in this folder yet.</p>'
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder folders" style="cursor:grab; color:rgba(255,255,255,0.45); font-size:16px;">&#9776;</span>' if is_admin else ""
        is_protected_folder = folder['name'].strip().lower() in (
            "measurement games",
            "general athleticism measurement games",
        )
        delete_btn = f"""<form method="post" action="/coach/resources/folders/{folder['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete folder \\'{esc(folder['name'])}\\'? Resources will move to Ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm" style="font-size:12px;color:rgba(255,255,255,0.70);border-color:rgba(255,255,255,0.25);">&#10005; Delete</button>
            </form>""" if is_admin and not is_protected_folder else ""
        rename_html = f"""<button type="button" class="btn btn-ghost btn-sm" style="font-size:12px;color:rgba(255,255,255,0.70);border-color:rgba(255,255,255,0.25);"
              onclick="var w=document.getElementById('rename-wrap-{folder['id']}');w.style.display=w.style.display==='none'?'flex':'none';"
              title="Rename folder">&#9998; Rename</button>
            <span id="rename-wrap-{folder['id']}" style="display:none; align-items:center; gap:4px; margin-top:4px;">
              <form method="post" action="/coach/resources/folders/{folder['id']}/rename"
                    style="display:inline-flex; gap:4px; align-items:center;">
                <input type="text" name="folder_name" value="{esc(folder['name'])}"
                       style="padding:4px 8px; font-size:13px; width:200px; border-radius:6px; border:1px solid rgba(255,255,255,0.3);background:rgba(255,255,255,0.10);color:#fff;" />
                <button type="submit" class="btn btn-primary btn-sm">Save</button>
              </form>
            </span>""" if is_admin else ""
        admin_actions = f'<div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-left:auto;">{rename_html}{delete_btn}</div>' if is_admin else ""
        folder_sections += f"""
        <div class="res-section" data-folder-id="{folder['id']}" style="margin-bottom:44px;">
          <div style="background:#2D323B;border-radius:12px;padding:14px 18px;margin-bottom:16px;
                      display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            {folder_handle}
            <div style="flex:1;min-width:0;">
              <h2 style="margin:0;font-size:17px;font-weight:700;color:#FFFFFF;line-height:1.2;">{esc(folder['name'])}</h2>
              <span style="font-size:12px;color:rgba(255,255,255,0.50);">{count} resource{"s" if count != 1 else ""}</span>
            </div>
            {admin_actions}
          </div>
          {list_content}
        </div>"""

    # Ungrouped section
    ug_tiles_html = "".join(_resource_tile(r, is_admin=is_admin) for r in ungrouped)
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

    manage_forms = f"""
    <div style="display:flex; gap:10px; margin-bottom:28px; flex-wrap:wrap;">
      <button type="button" class="btn btn-primary" onclick="var p=document.getElementById('res-add-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Add Resource</button>
      <button type="button" class="btn btn-ghost" onclick="var p=document.getElementById('folder-add-panel');p.style.display=p.style.display==='none'?'block':'none';">+ Create Folder</button>
      <form method="post" action="/admin/sync-card-taxonomy" style="margin:0;">
        <button type="submit" class="btn btn-ghost" title="Re-apply taxonomy tags from CARD_TAXONOMY for all resources that have a card_slug set">⟳ Sync Card Taxonomy</button>
      </form>
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

    # Search bar (tag filter removed — taxonomy is now hidden)
    search_bar = """
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:20px;">
      <input type="search" id="res-search" placeholder="Search resources…"
             style="max-width:260px;padding:8px 12px;border-radius:8px;border:1px solid var(--jag-border);font-size:14px;" />
    </div>
    <script>
    (function() {
      var searchInput = document.getElementById('res-search');
      if (searchInput) {
        searchInput.addEventListener('input', function() {
          var query = searchInput.value.toLowerCase().trim();
          document.querySelectorAll('.res-tile').forEach(function(tile) {
            tile.style.display = (!query || (tile.dataset.search || '').indexOf(query) !== -1) ? '' : 'none';
          });
        });
      }
    })();
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


def edit_resource_page(user, resource, folders, selected_game_keys=None,
                       taxonomy_tags=None, error=None):
    from constants import CORE_AAP_GAMES, find_measurement_game
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}" {"selected" if resource["folder_id"] == f["id"] else ""}>{esc(f["name"])}</option>'
        for f in folders
    )
    selected_game_keys = set(selected_game_keys or [])
    taxonomy_tags = taxonomy_tags or {}

    # ── Helper: render a group of checkboxes for one dimension ────────────
    def _tax_checkboxes(dim, options, selected_set):
        html = ""
        for val, label in options:
            chk = "checked" if val in selected_set else ""
            html += (
                f'<label style="display:inline-flex;align-items:center;gap:5px;font-size:12px;'
                f'font-weight:400;margin:0 10px 5px 0;cursor:pointer;">'
                f'<input type="checkbox" name="tax_{dim}" value="{esc(val)}" {chk} style="width:auto;margin:0;" />'
                f'{esc(label)}</label>'
            )
        return html

    # ── D10: Test Linkage (measurement game checkboxes) ──────────────────
    game_html = ""
    for gk in CORE_AAP_GAMES:
        gdef = find_measurement_game(gk)
        gname = gdef["name"] if gdef else gk
        chk = "checked" if gk in selected_game_keys else ""
        game_html += (
            f'<label style="display:inline-flex;align-items:center;gap:5px;font-size:12px;'
            f'font-weight:400;margin:0 10px 5px 0;cursor:pointer;">'
            f'<input type="checkbox" name="game_keys" value="{esc(gk)}" {chk} style="width:auto;margin:0;" />'
            f'{esc(gname)}</label>'
        )

    # ── D9: Programme Level (single-select) ──────────────────────────────
    current_range = resource.get("level_range") or "multi_level"
    range_opts = ""
    for val, label in [
        ("multi_level", "Multi-level — constraint adjustable, suits any level"),
        ("level_1",     "Level 1 — athlete working toward Level 1"),
        ("level_2",     "Level 2 — athlete at Level 1, moving to Level 2"),
        ("level_3",     "Level 3 — athlete at Level 2 and above"),
    ]:
        sel = "selected" if current_range == val else ""
        range_opts += f'<option value="{val}" {sel}>{label}</option>'

    # ── D7: Space Requirement (single-select) ─────────────────────────────
    current_space = resource.get("space_requirement") or "unspecified"
    space_opts = ""
    for val, label in [
        ("unspecified", "Not specified"),
        ("minimal",     "Minimal — < 5m × 5m (classroom or corridor)"),
        ("medium",      "Medium — 5–15m (half gym or small outdoor area)"),
        ("large",       "Large — 15m+ (full gymnasium or outdoor field)"),
    ]:
        sel = "selected" if current_space == val else ""
        space_opts += f'<option value="{val}" {sel}>{label}</option>'

    # ── D1: Measurement Family ────────────────────────────────────────────
    D1 = [
        ("balance_postural",      "Balance & Postural Control"),
        ("explosive_landing",     "Explosive & Landing"),
        ("dynamic_locomotor",     "Dynamic Locomotor"),
        ("perceptual_motor_speed","Perceptual-Motor Speed"),
    ]
    # ── D2: Physical Quality (S&C Language) ──────────────────────────────
    D2 = [
        ("bilateral_balance",        "Bilateral balance"),
        ("unilateral_balance",       "Unilateral balance"),
        ("proprioception",           "Proprioception"),
        ("core_stability",           "Core stability"),
        ("plyometric_power",         "Plyometric power"),
        ("landing_mechanics",        "Landing mechanics"),
        ("horizontal_power",         "Horizontal power"),
        ("vertical_power",           "Vertical power"),
        ("linear_speed",             "Linear speed"),
        ("change_of_direction",      "Change of direction speed"),
        ("reactive_agility",         "Reactive agility"),
        ("rhythmic_coordination",    "Rhythmic coordination"),
        ("hand_eye_coordination",    "Hand-eye coordination"),
        ("foot_eye_coordination",    "Foot-eye coordination"),
        ("ball_manipulation",        "Ball manipulation / dribbling"),
    ]
    # ── D3: EcoD Construct (CLA Language) ────────────────────────────────
    D3 = [
        ("perception_action",        "Perception-action coupling"),
        ("postural_attunement",      "Postural attunement"),
        ("metastability",            "Metastability"),
        ("ballistic_force_landing",  "Ballistic force production with landing control"),
        ("functional_locomotion",    "Functional locomotion"),
        ("attunement_calibration",   "Attunement & calibration"),
        ("info_predictable",         "Informational constraint — predictable (wall / set feed)"),
        ("info_unpredictable",       "Informational constraint — unpredictable (reflex ball / opponent)"),
        ("self_organisation",        "Self-organisation"),
        ("functional_variability",   "Functional variability"),
        ("constrain_to_afford",      "Constrain to afford"),
        ("constrain_to_potentiate",  "Constrain to potentiate"),
        ("representative_task",      "Representative task design"),
        ("repetition_without",       "Repetition without repetition"),
    ]
    # ── D4: Laterality ───────────────────────────────────────────────────
    D4 = [
        ("bilateral",    "Bilateral"),
        ("unilateral",   "Unilateral"),
        ("alternating",  "Alternating (bilateral ↔ unilateral)"),
        ("asymmetric",   "Asymmetric (different demand each side)"),
        ("not_applicable","Not applicable"),
    ]
    # ── D6: Equipment / Tool ─────────────────────────────────────────────
    D6 = [
        ("large_ball",       "Large ball"),
        ("small_ball",       "Small ball"),
        ("reflex_ball",      "Reflex / reaction ball"),
        ("standard_rope",    "Standard rope (single rotation)"),
        ("rope_double",      "Rope (double rotation)"),
        ("wall",             "Wall (hard surface)"),
        ("step_box",         "Step / box"),
        ("gate_cone",        "Gate / cone"),
        ("bosu",             "Bosu / balance ball"),
        ("no_equipment",     "No equipment"),
    ]
    # ── D8: Group Format ─────────────────────────────────────────────────
    D8 = [
        ("individual",   "Individual (1 person)"),
        ("pair",         "Pair (2 people)"),
        ("small_group",  "Small group (3–5)"),
        ("large_group",  "Large group (6+)"),
        ("adaptable",    "Adaptable (works across group sizes)"),
    ]

    def _dim_section(dim_id, title, options):
        sel = set(taxonomy_tags.get(dim_id, []))
        return (
            f'<div style="margin-bottom:12px;">'
            f'<div style="font-size:11px;font-weight:700;color:#6E737B;text-transform:uppercase;'
            f'letter-spacing:0.06em;margin-bottom:5px;">{esc(title)}</div>'
            f'<div style="display:flex;flex-wrap:wrap;">{_tax_checkboxes(dim_id, options, sel)}</div>'
            f'</div>'
        )

    taxonomy_section = f"""
    <div style="margin-top:18px;padding:16px 18px;background:#F8F9FA;border-radius:10px;
                border:1px solid #E5E7EB;">
      <div style="font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:14px;padding-bottom:8px;
                  border-bottom:1px solid #E5E7EB;">
        Hidden Taxonomy
        <span style="font-weight:400;font-size:11px;text-transform:none;color:#6E737B;">
          — practitioner recommendation engine, not shown to athletes
        </span>
      </div>

      <div style="margin-bottom:12px;">
        <div style="font-size:11px;font-weight:700;color:#6E737B;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:5px;">D10 · Test Linkage
          <span style="font-weight:400;text-transform:none;color:#9CA3AF;">(highest weight in scoring)</span>
        </div>
        <div style="display:flex;flex-wrap:wrap;">{game_html}</div>
      </div>

      {_dim_section("D1", "D1 · Measurement Family", D1)}
      {_dim_section("D2", "D2 · Physical Quality (S&C Language)", D2)}
      {_dim_section("D3", "D3 · EcoD Construct (CLA Language)", D3)}
      {_dim_section("D4", "D4 · Laterality", D4)}
      {_dim_section("D6", "D6 · Equipment / Tool", D6)}
      {_dim_section("D8", "D8 · Group Format", D8)}

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:4px;">
        <div>
          <label for="level_range" style="font-size:11px;font-weight:700;color:#6E737B;
                  text-transform:uppercase;letter-spacing:0.06em;">D9 · Programme Level</label>
          <select id="level_range" name="level_range" style="margin-top:4px;font-size:13px;">
            {range_opts}
          </select>
        </div>
        <div>
          <label for="space_requirement" style="font-size:11px;font-weight:700;color:#6E737B;
                  text-transform:uppercase;letter-spacing:0.06em;">D7 · Space Requirement</label>
          <select id="space_requirement" name="space_requirement" style="margin-top:4px;font-size:13px;">
            {space_opts}
          </select>
        </div>
      </div>
    </div>"""

    body = f"""
    <div class="page-head">
      <h1>Edit Resource</h1>
      <a class="btn btn-ghost" href="/coach/resources">&larr; Back</a>
    </div>
    {error_html}
    <div class="card form-card" style="max-width:560px;">
      <form method="post" action="/coach/resources/{resource['id']}/edit">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" required value="{esc(resource['name'])}" />
        <label for="url">URL</label>
        <input type="url" id="url" name="url" required value="{esc(resource['url'])}" />
        <label for="description">Description (optional)</label>
        <input type="text" id="description" name="description" value="{esc(resource['description'] or '')}" />
        <label for="self_organisation">Self-organisation focus (optional)</label>
        <input type="text" id="self_organisation" name="self_organisation" value="{esc(resource.get('self_organisation') or '')}" placeholder="e.g. Spatial awareness &amp; decision making" />
        <label for="card_slug" style="margin-top:14px;">Card Slug (auto-taxonomy)</label>
        <input type="text" id="card_slug" name="card_slug"
               value="{esc(resource.get('card_slug') or '')}"
               placeholder="e.g. lob-scotch  (leave blank to set tags manually below)"
               style="font-family:monospace;font-size:12px;" />
        <p style="font-size:11px;color:#6E737B;margin-top:3px;margin-bottom:10px;">
          Match a slug from the card library (e.g. <code>lob-scotch</code>, <code>grid-leap</code>).
          When set, saving will auto-fill all taxonomy dimensions from the card definition — no manual ticking needed.
        </p>
        <label for="folder_id">Folder</label>
        <select id="folder_id" name="folder_id">{folder_opts}</select>
        {taxonomy_section}
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
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;max-width:1100px;align-items:start;">
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
    "diamond_gates":         "Diamond Gates",
    "diamond_dribble":       "Diamond Dribble",
    "step_up":               "Step Up",
    "lob_scotch":            "Lob Scotch",
    "lateral_ladder":        "Lateral Ladder",
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
    notes = event.get("notes") or ""
    amount = int(event.get("amount", 0))
    created = (event.get("created_at") or "")[:10]
    is_level = (xp_type == "level_achievement")

    if is_level:
        # Extract level number from notes e.g. "Earned Level 1 in Skipping Rope Sprint"
        import re as _re
        lvl_match = _re.search(r"Level\s+(\d)", notes)
        lvl_num = int(lvl_match.group(1)) if lvl_match else 0
        bg, fg = _LEVEL_COLOURS.get(lvl_num, ("#F0A82E", "#2D323B"))
        # Highlighted row using the level's colour
        shade = "#FFFBEB"
        border = f"border-left:4px solid {bg};"
        level_badge = (
            f'<span style="font-size:11px;font-weight:800;background:{bg};color:{fg};'
            f'border-radius:999px;padding:2px 8px;margin-left:6px;">L{lvl_num}</span>'
            if lvl_num else ""
        )
        icon = '🏆 '
        game_chip = (
            f'<span style="font-size:11px;background:#2D323B;color:#fff;border-radius:999px;'
            f'padding:2px 8px;margin-left:6px;">{esc(game)}</span>'
            if game else ""
        )
        return f"""
    <tr style="background:{shade};{border}">
      <td style="padding:9px 14px;font-size:13px;color:#2D323B;font-weight:600;">{icon}{esc(label)}{level_badge}{game_chip}</td>
      <td style="padding:9px 14px;font-size:13px;color:#6E737B;">{esc(created)}</td>
      <td style="padding:9px 14px;font-size:13px;font-weight:800;color:{bg};text-align:right;">+{amount:,} AXP</td>
    </tr>"""
    else:
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
    from constants import XP_RANK_TIERS
    _max_xp = XP_RANK_TIERS[-1]["min_xp"]
    _fill = min(100.0, (total / _max_xp * 100)) if _max_xp else 100.0
    _dots = ""
    _lbls = ""
    for _t in XP_RANK_TIERS:
        _p = (_t["min_xp"] / _max_xp * 100) if _max_xp else 0
        _ach = total >= _t["min_xp"]
        _cur = _t["label"] == tier_label
        if _cur:
            _ds = ('width:14px;height:14px;background:#fff;'
                   f'border:2px solid rgba(0,0,0,0.2);'
                   'box-shadow:0 0 0 3px rgba(255,255,255,0.3);top:-4px;')
        elif _ach:
            _ds = 'width:10px;height:10px;background:#fff;top:-2px;'
        else:
            _ds = ('width:10px;height:10px;background:rgba(255,255,255,0.2);'
                   'border:1.5px solid rgba(255,255,255,0.4);top:-2px;')
        _dots += (f'<div style="position:absolute;left:{_p:.1f}%;transform:translateX(-50%);'
                  f'{_ds}border-radius:50%;z-index:2;"></div>')
        _fw = "700" if _cur else "400"
        _op = "1" if _ach else "0.45"
        _lbls += (f'<div style="position:absolute;left:{_p:.1f}%;transform:translateX(-50%);'
                  f'text-align:center;width:52px;margin-left:-26px;">'
                  f'<div style="font-size:10px;font-weight:{_fw};color:rgba(255,255,255,{_op});white-space:nowrap;">'
                  f'{esc(_t["label"])}</div>'
                  f'<div style="font-size:9px;color:rgba(255,255,255,0.45);">{_t["min_xp"]:,}</div>'
                  f'</div>')

    if next_tier:
        xp_to_next = next_tier["min_xp"] - total
        _next_note = (f'<div style="text-align:right;font-size:12px;color:rgba(255,255,255,0.8);margin-top:2px;">'
                      f'{xp_to_next:,} AXP to {esc(next_tier["label"])}</div>')
    else:
        _next_note = '<div style="text-align:center;font-size:12px;color:rgba(255,255,255,0.85);margin-top:2px;">Maximum rank achieved — keep earning AXP!</div>'

    _journey = f"""
      <div style="margin-top:18px;background:rgba(16,185,129,0.15);
                  border:1.5px solid rgba(16,185,129,0.5);border-radius:14px;
                  padding:14px 16px 6px;">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.07em;color:#6EE7B7;margin-bottom:10px;">AXP Journey</div>
        <div style="position:relative;padding-bottom:36px;">
          <div style="position:relative;height:6px;background:rgba(255,255,255,0.2);border-radius:999px;">
            <div style="width:{_fill:.1f}%;height:100%;background:#fff;border-radius:999px;
                        position:absolute;top:0;left:0;transition:width 0.8s ease;"></div>
            {_dots}
          </div>
          <div style="position:relative;height:32px;margin-top:9px;">
            {_lbls}
          </div>
        </div>
        {_next_note}
      </div>"""

    _back_href = f'/coach/participants/{esc(str(athlete.get("id","")))}' if coach else '/athlete/dashboard'
    _back_label = "&larr; Back to Profile" if coach else "&larr; Dashboard"

    hero = f"""
    <div style="background:{tier_colour};border-radius:16px;padding:24px 28px;margin-bottom:28px;color:#fff;">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:14px;">
          <div style="width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,0.18);
                      border:1.5px solid rgba(255,255,255,0.30);display:flex;align-items:center;
                      justify-content:center;font-size:22px;font-weight:800;flex-shrink:0;">&#9650;</div>
          <div>
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                        color:rgba(255,255,255,0.70);margin-bottom:2px;">AXP Profile</div>
            <div style="font-size:22px;font-weight:800;line-height:1.1;">{name}</div>
            <div style="font-size:13px;opacity:0.75;margin-top:2px;">{esc(tier_label)}</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
          <div style="font-size:42px;font-weight:900;line-height:1;">{total:,}</div>
          <div style="font-size:12px;opacity:0.75;">AXP total</div>
          <a href="{_back_href}"
             style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.65);text-decoration:none;
                    padding:5px 12px;border-radius:20px;border:1px solid rgba(255,255,255,0.25);
                    background:rgba(255,255,255,0.10);white-space:nowrap;
                    transition:background 0.15s;"
             onmouseover="this.style.background='rgba(255,255,255,0.20)'"
             onmouseout="this.style.background='rgba(255,255,255,0.10)'">{_back_label}</a>
        </div>
      </div>
      {_journey}
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
      <div style="display:flex;align-items:center;gap:0;margin-bottom:14px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Level Achievements</span>
      </div>
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
      <div style="display:flex;align-items:center;gap:0;margin-bottom:14px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Recent AXP Events</span>
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;border-bottom:2px solid #F0A82E;">
              <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Event</th>
              <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Date</th>
              <th style="padding:10px 14px;text-align:right;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">AXP</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""

    if coach:
        back_href = f'/coach/participants/{esc(str(athlete.get("id","")))}'
        back_label = "&larr; Back to Profile"
    else:
        back_href = "/athlete/dashboard"
        back_label = "&larr; Dashboard"

    body = f"""
    <div class="container" style="max-width:860px;">
      {hero}
      {levels_section}
      {events_section}
    </div>"""

    user = coach if coach else athlete
    return layout("AXP Profile", body, user=user,
                  active_nav="dashboard" if coach else "dashboard")


def game_thresholds_page(coach, thresholds, scoring_areas, xp_game_config, threshold_field_key_fn=None):
    """System admin page for managing per-scoring-area level thresholds."""
    from constants import find_measurement_game, GAME_LEVEL_DESCRIPTIONS
    if threshold_field_key_fn is None:
        from constants import threshold_field_key as threshold_field_key_fn

    # Build a dict for easy lookup keyed by (game_key, field_key, level)
    existing = {}
    for t in thresholds:
        existing[(t["game_key"], t["field_key"] or "", t["level"])] = dict(t)

    rows_html = ""
    for area in scoring_areas:
        game_key = area["game_key"]
        area_field_key = area["field_key"]  # None = pooled
        lower = area["lower_is_better"]
        stored_fk = threshold_field_key_fn(area)  # field_key stored in DB

        display = esc(area["display_name"])
        pooled_note = ' <span style="font-size:10px;color:#9CA3AF;">(combined groups)</span>' if area_field_key is None else ""
        game_def = find_measurement_game(game_key) or {}
        hint = game_def.get("level_threshold_hint", "")
        level_descs = GAME_LEVEL_DESCRIPTIONS.get(game_key, [])

        hint_html = (f'<div style="font-size:11px;color:#9CA3AF;margin-top:2px;">{esc(hint)}</div>'
                     if hint else "")

        rows_html += f"""
        <tr>
          <td colspan="4" style="padding:14px 16px 10px;background:#2D323B;
                                  border-bottom:2px solid rgba(240,168,46,0.30);">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <span style="font-size:14px;font-weight:800;color:#F0A82E;letter-spacing:0.02em;">{display}</span>
              {pooled_note}
              <span style="font-size:11px;color:rgba(255,255,255,0.40);background:rgba(255,255,255,0.10);
                           border-radius:999px;padding:1px 8px;">field: {esc(stored_fk)}</span>
            </div>
            {hint_html}
          </td>
        </tr>"""

        for level in range(1, 6):
            bg, fg = _LEVEL_COLOURS.get(level, ("#E5E7EB", "#2D323B"))
            t = existing.get((game_key, stored_fk, level))
            curr_val = f'{t["threshold_value"]:g}' if t else ""
            shade = "#F3F4F5" if level % 2 == 0 else "#fff"
            lvl_desc = level_descs[level - 1] if level_descs and level <= len(level_descs) else ""
            desc_html = (f'<div style="font-size:11px;color:#6E737B;margin-top:2px;">{esc(lvl_desc)}</div>'
                         if lvl_desc else "")
            rows_html += f"""
            <tr style="background:{shade};border-bottom:1px solid #F0F1F3;">
              <td style="padding:10px 16px;vertical-align:middle;">
                <div style="display:flex;align-items:flex-start;gap:8px;">
                  <span style="font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;
                                background:{bg};color:{fg};white-space:nowrap;flex-shrink:0;">L{level}</span>
                  <div style="font-size:12px;color:#6E737B;line-height:1.4;padding-top:2px;">{esc(lvl_desc) if lvl_desc else ""}</div>
                </div>
              </td>
              <td style="padding:10px 16px;vertical-align:middle;">
                {f'<span style="font-size:14px;font-weight:800;color:#2D323B;">{curr_val}</span>' if curr_val else '<span style="font-size:13px;color:#C4C7CC;font-style:italic;">not set</span>'}
              </td>
              <td style="padding:10px 16px;vertical-align:middle;">
                <form method="post" action="/coach/admin/game-thresholds/set"
                      style="display:flex;gap:6px;align-items:center;">
                  <input type="hidden" name="game_key" value="{esc(game_key)}" />
                  <input type="hidden" name="field_key" value="{esc(stored_fk)}" />
                  <input type="hidden" name="level" value="{level}" />
                  <input type="hidden" name="lower_is_better" value="{'1' if lower else '0'}" />
                  <input type="number" name="threshold_value" value="{esc(curr_val)}"
                         step="0.01" style="width:90px;font-size:12px;" placeholder="value" />
                  <button type="submit" class="btn btn-primary btn-sm" style="font-size:12px;">Save</button>
                </form>
              </td>
              <td style="padding:10px 16px;vertical-align:middle;">
                {f'''<form method="post" action="/coach/admin/game-thresholds/delete">
                  <input type="hidden" name="game_key" value="{esc(game_key)}" />
                  <input type="hidden" name="field_key" value="{esc(stored_fk)}" />
                  <input type="hidden" name="level" value="{level}" />
                  <button class="btn btn-ghost btn-sm" style="font-size:11px;color:#DC2626;"
                    onclick="return confirm('Remove this threshold?')">&#10005; Remove</button>
                </form>''' if t else ''}
              </td>
            </tr>"""

    body = f"""
    <div class="container" style="max-width:960px;">

      <!-- Hero banner with utility actions embedded -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;
                  justify-content:space-between;gap:16px;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                      border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                      justify-content:center;font-size:22px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9881;</div>
          <div>
            <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">AXP Thresholds</div>
            <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:3px;">
              Set the score required for L1–L5 in each core game. Once earned, levels are permanent.
            </div>
          </div>
        </div>
        <!-- Utility actions: secondary, embedded in hero -->
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <form method="post" action="/coach/admin/xp-retroactive"
                onsubmit="return confirm('Run retroactive AXP pass over ALL existing sessions? This is safe to run multiple times but may take a moment.')">
            <button style="background:rgba(240,168,46,0.18);border:1px solid rgba(240,168,46,0.40);
                           color:#F0A82E;border-radius:8px;padding:7px 14px;font-size:12px;
                           font-weight:700;cursor:pointer;letter-spacing:0.02em;">
              &#8635; Re-run AXP Pass
            </button>
          </form>
          <form method="post" action="/coach/admin/level-retroactive"
                onsubmit="return confirm('Re-check level thresholds across ALL sessions? Run this after setting thresholds for the first time. Safe to run multiple times.')">
            <button style="background:rgba(30,190,139,0.18);border:1px solid rgba(30,190,139,0.40);
                           color:#1EBE8B;border-radius:8px;padding:7px 14px;font-size:12px;
                           font-weight:700;cursor:pointer;letter-spacing:0.02em;">
              &#10003; Re-check Levels
            </button>
          </form>
        </div>
      </div>

      <!-- Reading guide — JAG gold-tinted -->
      <div style="background:rgba(240,168,46,0.08);border-left:4px solid #F0A82E;border-radius:10px;
                  padding:14px 18px;margin-bottom:24px;font-size:13px;color:#2D323B;line-height:1.6;">
        <strong>How to set a threshold:</strong> enter the minimum score an athlete must reach on the
        listed field to earn that level. The field key is pre-filled from the game definition —
        only change it if you intentionally want a different field to drive the level check.
        For timed games (lower = better), the system checks score &#8804; threshold.
      </div>

      <!-- Threshold table -->
      <div style="border:1.5px solid #E8E9EB;border-radius:14px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;">
              <th style="padding:12px 16px;text-align:left;font-size:11px;font-weight:700;
                         color:rgba(255,255,255,0.60);text-transform:uppercase;letter-spacing:0.06em;">Level</th>
              <th style="padding:12px 16px;text-align:left;font-size:11px;font-weight:700;
                         color:rgba(255,255,255,0.60);text-transform:uppercase;letter-spacing:0.06em;">Current</th>
              <th style="padding:12px 16px;text-align:left;font-size:11px;font-weight:700;
                         color:rgba(255,255,255,0.60);text-transform:uppercase;letter-spacing:0.06em;">Update</th>
              <th style="padding:12px 16px;font-size:11px;color:rgba(255,255,255,0.30);"></th>
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
    for e in events:
        date_str = e.get("date", "")[:10]
        group = esc(e.get("group_name") or "—")
        count = e.get("attendee_count", 0)
        notes = esc(e.get("notes") or "")
        rows += f"""
        <tr style="border-bottom:1px solid #F3F4F5;">
          <td style="padding:12px 16px;font-size:14px;font-weight:600;color:#2D323B;">{esc(date_str)}</td>
          <td style="padding:12px 16px;font-size:13px;color:#6E737B;">{group}</td>
          <td style="padding:12px 16px;text-align:center;">
            <span style="background:#1EBE8B;color:#fff;border-radius:999px;padding:2px 10px;
                         font-size:12px;font-weight:700;">{count}</span>
          </td>
          <td style="padding:12px 16px;font-size:13px;color:#6E737B;">{notes}</td>
          <td style="padding:12px 16px;white-space:nowrap;text-align:right;">
            <a href="/coach/attendance/{e['id']}/roll-call"
               style="font-size:12px;font-weight:600;color:#2D323B;text-decoration:none;
                      padding:4px 12px;border:1px solid #DDE0E3;border-radius:6px;margin-right:6px;">Roll-Call</a>
            <a href="/coach/attendance/{e['id']}"
               style="font-size:12px;font-weight:600;color:#F0A82E;text-decoration:none;
                      padding:4px 12px;border:1px solid #F0A82E;border-radius:6px;">View</a>
          </td>
        </tr>"""
    if not rows:
        rows = '<tr><td colspan="5" style="padding:28px;text-align:center;color:#9CA3AF;font-size:13px;">No sessions yet — create one to get started.</td></tr>'

    body = f"""
    <div class="container" style="max-width:900px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;
                  justify-content:space-between;gap:16px;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                      border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                      justify-content:center;font-size:22px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9632;</div>
          <div>
            <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Session Attendance</div>
            <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:3px;">
              Create sessions, take roll-call, and track self-directed completion.
            </div>
          </div>
        </div>
        <a href="/coach/attendance/new" class="btn btn-primary">+ New Session</a>
      </div>
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;background:#fff;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;border-bottom:2px solid #F0A82E;">
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Date</th>
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Group</th>
              <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Present</th>
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Notes</th>
              <th style="padding:10px 16px;"></th>
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
    <div class="container" style="max-width:580px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:44px;height:44px;border-radius:12px;background:rgba(240,168,46,0.18);
                      border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                      justify-content:center;font-size:20px;color:#F0A82E;flex-shrink:0;font-weight:700;">+</div>
          <div>
            <div style="font-size:18px;font-weight:800;color:#FFFFFF;line-height:1.2;">New Session</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:3px;">
              Create a session then take roll-call to mark attendance.
            </div>
          </div>
        </div>
      </div>
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:24px 28px;">
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
            <button type="submit" class="btn btn-primary">Create &amp; Take Roll-Call →</button>
            <a href="/coach/attendance" class="btn btn-ghost">Cancel</a>
          </div>
        </form>
      </div>
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
        <label style="display:flex;align-items:center;gap:12px;padding:12px 16px;
                       cursor:pointer;border-bottom:1px solid #F3F4F5;transition:background 0.12s;"
               onmouseover="this.style.background='rgba(240,168,46,0.04)'"
               onmouseout="this.style.background=''">
          <input type="checkbox" name="athlete_ids" value="{pid}" {checked}
                 style="width:18px;height:18px;accent-color:#F0A82E;cursor:pointer;flex-shrink:0;" />
          <span style="flex:1;font-size:14px;color:#2D323B;font-weight:500;">{name}</span>
          {f'<span style="font-size:11px;color:#9CA3AF;background:#F3F4F5;border-radius:999px;padding:1px 8px;">#{num}</span>' if num else ''}
        </label>"""

    if not athlete_checks:
        athlete_checks = '<p style="color:#9CA3AF;font-size:13px;padding:20px 16px;">No athletes in this group.</p>'

    body = f"""
    <div class="container" style="max-width:600px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div>
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
                        color:rgba(240,168,46,0.80);margin-bottom:3px;">Roll-Call</div>
            <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">{esc(date_str)}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:4px;">
              {group_name}{f" &nbsp;·&nbsp; {esc(event.get('notes',''))}" if event.get('notes') else ""}
            </div>
          </div>
          <a href="/coach/attendance" style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.70);
             text-decoration:none;padding:6px 14px;border:1px solid rgba(255,255,255,0.20);border-radius:20px;">
            &larr; Attendance</a>
        </div>
      </div>
      <form method="post" action="/coach/attendance/{event_id}/roll-call">
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;align-items:center;
                      padding:10px 16px;background:#F8F9FA;border-bottom:1px solid #E5E7EB;">
            <span style="font-size:11px;font-weight:700;color:#6E737B;text-transform:uppercase;letter-spacing:0.06em;">
              Athletes — {len(athletes)} total
            </span>
            <button type="button" onclick="toggleAll(this)"
                    style="font-size:12px;color:#2D323B;background:none;border:none;cursor:pointer;font-weight:700;">
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


def attendance_view_page(coach, event, attendees, submitted_ids=None):
    date_str = event.get("date", "")[:10]
    group_name = esc(event.get("group_name") or "All athletes")
    event_id = event["id"]
    is_open = bool(event.get("is_open"))
    opened_at = event.get("opened_at") or ""
    submitted_ids = submitted_ids or set()
    submitted_count = sum(1 for a in attendees if a["id"] in submitted_ids)

    rows = ""
    for a in attendees:
        pid = a["id"]
        done = pid in submitted_ids
        sd_cell = (
            '<span style="font-size:11px;font-weight:700;color:#065F46;background:rgba(30,190,139,0.12);'
            'border:1px solid rgba(30,190,139,0.28);border-radius:999px;padding:2px 10px;">&#10003; Done</span>'
            if done else
            ('<span style="font-size:11px;font-weight:600;color:#7A5800;background:rgba(240,168,46,0.10);'
             'border:1px solid rgba(240,168,46,0.28);border-radius:999px;padding:2px 10px;">Pending</span>'
             if is_open else
             '<span style="font-size:11px;color:#9CA3AF;">—</span>')
        )
        rows += (
            f'<tr style="border-bottom:1px solid #F3F4F5;">'
            f'<td style="padding:10px 16px;font-size:14px;font-weight:500;color:#2D323B;">{esc(a.get("name",""))}</td>'
            f'<td style="padding:10px 16px;font-size:12px;color:#9CA3AF;">'
            f'{"#" + esc(a.get("athlete_number") or "") if a.get("athlete_number") else "—"}</td>'
            f'<td style="padding:10px 16px;font-size:12px;color:#6E737B;">{esc((a.get("marked_at") or "")[:10])}</td>'
            f'<td style="padding:10px 16px;">{sd_cell}</td>'
            f'</tr>'
        )
    if not rows:
        rows = '<tr><td colspan="4" style="padding:28px;text-align:center;color:#9CA3AF;font-size:13px;">No athletes marked present.</td></tr>'

    # Session status control
    if is_open:
        status_badge = ('<div style="display:flex;align-items:center;gap:6px;">'
                        '<div style="width:8px;height:8px;border-radius:50%;background:#1EBE8B;'
                        'animation:pulse 1.5s infinite;flex-shrink:0;"></div>'
                        '<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
                        'letter-spacing:0.07em;color:#1EBE8B;">Self-Test Open</span>'
                        '</div>')
        session_ctrl = f"""
        <form method="POST" action="/coach/attendance/{event_id}/close" style="display:inline;">
          <button type="submit"
                  style="font-size:12px;font-weight:700;color:#fff;background:#D4622F;
                         border:none;border-radius:20px;padding:6px 16px;cursor:pointer;">
            &#9632; End Session</button>
        </form>"""
    else:
        status_badge = ('<span style="font-size:11px;font-weight:700;text-transform:uppercase;'
                        'letter-spacing:0.07em;color:#9CA3AF;">Self-Test Closed</span>')
        session_ctrl = f"""
        <form method="POST" action="/coach/attendance/{event_id}/open" style="display:inline;">
          <button type="submit"
                  style="font-size:12px;font-weight:700;color:#2D323B;background:#1EBE8B;
                         border:none;border-radius:20px;padding:6px 16px;cursor:pointer;">
            &#9654; Open Session</button>
        </form>"""

    # Summary stats
    n = len(attendees)
    pending_count = n - submitted_count
    stats_html = f"""
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;">
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#2D323B;">{n}</div>
        <div style="font-size:11px;color:#6E737B;margin-top:2px;">Present</div>
      </div>
      <div style="background:#fff;border:1px solid rgba(30,190,139,0.30);border-radius:10px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#1EBE8B;">{submitted_count}</div>
        <div style="font-size:11px;color:#6E737B;margin-top:2px;">Self-directed done</div>
      </div>
      <div style="background:#fff;border:1px solid rgba(240,168,46,0.30);border-radius:10px;padding:12px 20px;text-align:center;min-width:100px;">
        <div style="font-size:22px;font-weight:800;color:#F0A82E;">{pending_count}</div>
        <div style="font-size:11px;color:#6E737B;margin-top:2px;">Still pending</div>
      </div>
    </div>"""

    # 1-hour warning modal (only injected when session is open and has an opened_at stamp)
    timer_js = ""
    if is_open and opened_at:
        timer_js = f"""
    <div id="session-timer-modal"
         style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.55);
                z-index:9999;align-items:center;justify-content:center;">
      <div style="background:#fff;border-radius:16px;padding:32px 28px;max-width:400px;
                  width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);text-align:center;">
        <div style="font-size:32px;margin-bottom:12px;">&#9201;</div>
        <div style="font-size:18px;font-weight:800;color:#2D323B;margin-bottom:8px;">
          Session has been open for 1 hour
        </div>
        <div style="font-size:13px;color:#6E737B;margin-bottom:24px;line-height:1.6;">
          Are athletes still self-testing? You can end the session now or keep it open.
        </div>
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
          <form method="POST" action="/coach/attendance/{event_id}/close">
            <button type="submit"
                    style="font-size:14px;font-weight:700;color:#fff;background:#D4622F;
                           border:none;border-radius:12px;padding:12px 24px;cursor:pointer;
                           min-width:140px;">
              &#9632; End Session</button>
          </form>
          <button onclick="dismissTimer()"
                  style="font-size:14px;font-weight:700;color:#2D323B;background:#F0A82E;
                         border:none;border-radius:12px;padding:12px 24px;cursor:pointer;
                         min-width:140px;">
            Continue &#8250;</button>
        </div>
      </div>
    </div>
    <script>
      (function() {{
        var openedAt = new Date("{esc(opened_at)}");
        var ONE_HOUR = 60 * 60 * 1000;
        var SNOOZE_KEY = "jag_session_{event_id}_snoozed";
        var modal = document.getElementById("session-timer-modal");

        function showModal() {{
          modal.style.display = "flex";
        }}

        function dismissTimer() {{
          modal.style.display = "none";
          sessionStorage.setItem(SNOOZE_KEY, Date.now().toString());
        }}
        window.dismissTimer = dismissTimer;

        function check() {{
          var now = Date.now();
          var elapsed = now - openedAt.getTime();
          if (elapsed < ONE_HOUR) {{
            setTimeout(check, ONE_HOUR - elapsed + 1000);
            return;
          }}
          var snoozed = parseInt(sessionStorage.getItem(SNOOZE_KEY) || "0");
          // Re-show after snooze of 30 minutes
          if (snoozed && (now - snoozed) < 30 * 60 * 1000) {{
            setTimeout(check, 30 * 60 * 1000 - (now - snoozed) + 1000);
            return;
          }}
          showModal();
        }}
        check();
      }})();
    </script>
    <style>
      @keyframes pulse {{ 0%,100% {{ opacity:1;transform:scale(1); }} 50% {{ opacity:0.4;transform:scale(1.4); }} }}
    </style>"""

    body = f"""
    {timer_js}
    <div class="container" style="max-width:760px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div>
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
                        color:rgba(240,168,46,0.80);margin-bottom:3px;">Session</div>
            <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">{group_name} &nbsp;·&nbsp; {esc(date_str)}</div>
            {f'<div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:4px;">{esc(event.get("notes",""))}</div>' if event.get("notes") else ""}
            <div style="margin-top:10px;">{status_badge}</div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            {session_ctrl}
            <a href="/coach/attendance/{event_id}/roll-call"
               style="font-size:12px;font-weight:700;color:#2D323B;background:#F0A82E;
                      text-decoration:none;padding:6px 16px;border-radius:20px;">Edit Roll-Call</a>
            <a href="/coach/attendance"
               style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.70);text-decoration:none;
                      padding:6px 14px;border:1px solid rgba(255,255,255,0.20);border-radius:20px;">
              &larr; Attendance</a>
          </div>
        </div>
      </div>
      {stats_html}
      <div style="border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;background:#fff;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#2D323B;border-bottom:2px solid #F0A82E;">
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Athlete</th>
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">#</th>
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Marked</th>
              <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;
                          text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Self-Directed</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""
    return layout("Session Attendance", body, user=coach, active_nav="attendance")


def self_directed_home_page(athlete, pending_events, completed_sessions):
    pending_html = ""
    if pending_events:
        for e in pending_events:
            date_str = esc(e.get("date", "")[:10])
            group = esc(e.get("group_name") or "")
            pending_html += f"""
            <a href="/athlete/self-directed/{e['id']}"
               style="display:flex;align-items:center;justify-content:space-between;gap:12px;
                      padding:14px 18px;background:#fff;border:1px solid #E5E7EB;
                      border-left:3px solid #F0A82E;border-radius:10px;text-decoration:none;
                      margin-bottom:10px;transition:box-shadow 0.15s,border-color 0.15s;"
               onmouseover="this.style.boxShadow='0 2px 12px rgba(0,0,0,0.08)'"
               onmouseout="this.style.boxShadow=''">
              <div>
                <div style="font-size:14px;font-weight:700;color:#2D323B;">{date_str}</div>
                {f'<div style="font-size:12px;color:#6E737B;margin-top:2px;">{group}</div>' if group else ''}
              </div>
              <span style="font-size:12px;font-weight:700;color:#7A5800;background:rgba(240,168,46,0.12);
                           border:1px solid rgba(240,168,46,0.30);border-radius:999px;
                           padding:4px 14px;white-space:nowrap;flex-shrink:0;">Record scores →</span>
            </a>"""
    else:
        pending_html = ('<div style="background:rgba(30,190,139,0.06);border-left:3px solid #1EBE8B;'
                        'border-radius:8px;padding:14px 18px;font-size:13px;color:#065F46;">'
                        '&#10003; You\'re all caught up — no sessions waiting to be scored.</div>')

    completed_html = ""
    if completed_sessions:
        for s in completed_sessions[:10]:
            date_str = esc(s.get("date", "")[:10])
            game_count = len({k[0] for k in s.get("results", {}).keys()})
            completed_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:10px 16px;background:#F8F9FA;border-radius:8px;margin-bottom:8px;
                        border:1px solid #F0F1F3;">
              <span style="font-size:13px;font-weight:500;color:#2D323B;">{date_str}</span>
              <span style="font-size:12px;color:#6E737B;">{game_count} game{'s' if game_count != 1 else ''} scored</span>
            </div>"""
    else:
        completed_html = '<p style="font-size:13px;color:#9CA3AF;margin:0;">No self-directed scores recorded yet.</p>'

    pending_badge = (f'<span style="font-size:11px;font-weight:700;background:#F0A82E;color:#2D323B;'
                     f'border-radius:999px;padding:1px 8px;margin-left:8px;">{len(pending_events)}</span>'
                     if pending_events else '')

    body = f"""
    <div class="container" style="max-width:680px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                      border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                      justify-content:center;font-size:20px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9654;</div>
          <div>
            <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Self-Directed Sessions</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:3px;">
              Record your own scores after training to earn AXP.
            </div>
          </div>
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:0;margin-bottom:12px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">
          Ready to score{pending_badge}
        </span>
      </div>
      {pending_html}

      <div style="display:flex;align-items:center;gap:0;margin:24px 0 12px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">
          Recent scores
        </span>
      </div>
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
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:3px solid #2D323B;
                        border-radius:10px;padding:16px 20px;margin-bottom:12px;">
              <div style="font-size:13px;font-weight:800;color:#2D323B;margin-bottom:12px;
                          text-transform:uppercase;letter-spacing:0.04em;">
                {esc(GAME_DISPLAY_NAMES.get(game['key'], game['name']))}
              </div>
              {fields_html}
            </div>"""

    body = f"""
    <div class="container" style="max-width:640px;">
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                        border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                        justify-content:center;font-size:20px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9654;</div>
            <div>
              <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                          color:rgba(240,168,46,0.80);margin-bottom:2px;">Self-Directed Session</div>
              <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Record Your Scores</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:3px;">
                {date_str}{f" &middot; {group}" if group else ""}
              </div>
            </div>
          </div>
          <a href="/athlete/self-directed"
             style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.65);text-decoration:none;
                    padding:6px 14px;border-radius:20px;border:1px solid rgba(255,255,255,0.20);
                    background:rgba(255,255,255,0.08);white-space:nowrap;align-self:flex-start;
                    transition:background 0.15s;"
             onmouseover="this.style.background='rgba(255,255,255,0.15)'"
             onmouseout="this.style.background='rgba(255,255,255,0.08)'">&larr; Self-Directed</a>
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:0;margin-bottom:16px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Games</span>
        <span style="font-size:12px;color:#6E737B;margin-left:8px;font-weight:400;">— only fill in games you played</span>
      </div>

      <form method="post" action="/athlete/self-directed/{event_id}">
        {game_cards}
        <div style="display:flex;gap:10px;margin-top:20px;">
          <button type="submit" class="btn btn-primary">Save &amp; Earn AXP</button>
          <a href="/athlete/self-directed" class="btn btn-ghost">Cancel</a>
        </div>
      </form>
    </div>"""
    return layout("Self-Directed Entry", body, user=athlete, active_nav="self_directed")


def self_directed_success_page(athlete, xp_events, session_date, group_name):
    """Shown immediately after an athlete submits self-directed scores."""
    total_earned = sum(e.get("amount", 0) for e in xp_events)
    session_date_str = esc((session_date or "")[:10])
    group_str = esc(group_name or "")

    # XP type display names
    _XP_LABELS = {
        "session": "Session completed",
        "self_directed": "Self-directed session",
        "first_game": "First game recorded",
        "level_up": "Level achieved",
        "streak_3": "3-session streak",
        "streak_5": "5-session streak",
        "personal_best": "Personal best",
        "welcome": "Welcome bonus",
    }

    # XP breakdown rows
    breakdown_rows = ""
    for e in xp_events:
        xp = e.get("amount", 0)
        xp_type = e.get("xp_type", "")
        label = esc(e.get("notes") or _XP_LABELS.get(xp_type, xp_type))
        breakdown_rows += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.10);">
          <span style="font-size:13px;color:rgba(255,255,255,0.80);">{label}</span>
          <span style="font-size:13px;font-weight:700;color:#F0A82E;">+{xp:,} AXP</span>
        </div>"""
    if not breakdown_rows:
        breakdown_rows = ('<div style="font-size:13px;color:rgba(255,255,255,0.60);padding:8px 0;">'
                          'No new XP events — you may have already scored this session.</div>')

    body = f"""
    <div class="container" style="max-width:520px;padding-top:40px;">
      <!-- Success hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:28px 28px 24px;margin-bottom:20px;text-align:center;">
        <div style="font-size:44px;margin-bottom:10px;">&#9650;</div>
        <div style="font-size:28px;font-weight:900;color:#F0A82E;line-height:1.1;">+{total_earned:,} AXP</div>
        <div style="font-size:14px;color:rgba(255,255,255,0.70);margin-top:6px;">Scores saved — great work!</div>
        {f'<div style="font-size:12px;color:rgba(255,255,255,0.45);margin-top:4px;">{session_date_str}{" · " + group_str if group_str else ""}</div>' if session_date_str else ""}

        <!-- XP breakdown inside hero -->
        <div style="margin-top:20px;background:rgba(255,255,255,0.06);border-radius:10px;
                    padding:12px 16px;text-align:left;">
          <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                      color:rgba(240,168,46,0.80);margin-bottom:6px;">AXP earned</div>
          {breakdown_rows}
        </div>
      </div>

      <!-- Actions -->
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <a href="/athlete/self-directed"
           style="flex:1;text-align:center;padding:12px 16px;background:#F0A82E;color:#2D323B;
                  font-weight:700;font-size:14px;border-radius:10px;text-decoration:none;
                  transition:opacity 0.15s;"
           onmouseover="this.style.opacity='0.88'" onmouseout="this.style.opacity='1'">
          &#8592; Self-Directed Home
        </a>
        <a href="/athlete/xp"
           style="flex:1;text-align:center;padding:12px 16px;background:rgba(45,50,59,0.06);
                  color:#2D323B;font-weight:600;font-size:14px;border-radius:10px;
                  text-decoration:none;border:1px solid #E5E7EB;transition:background 0.15s;"
           onmouseover="this.style.background='rgba(45,50,59,0.10)'"
           onmouseout="this.style.background='rgba(45,50,59,0.06)'">
          View AXP Profile &#8594;
        </a>
      </div>
    </div>"""
    return layout("Scores Saved", body, user=athlete, active_nav="self_directed")


# ══════════════════════════════════════════════════════════════════════════════
# GROUP LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════

def group_leaderboard_page(coach, groups, selected_group_id=None, ranked_athletes=None, all_ranked=None):
    """AXP leaderboard for a group — ranked by total AXP with rank badge and level count.
    all_ranked: programme-wide list (org_admin / system_admin only), each entry includes group_name."""
    from constants import CORE_AAP_GAMES

    LEVEL_COLOURS_LB = {
        0: ("#E5E7EB", "#6E737B"),
        1: ("#1EBE8B", "#fff"),
        2: ("#F0A82E", "#2D323B"),
        3: ("#2D323B", "#fff"),
        4: ("#F97316", "#fff"),
        5: ("#8B5CF6", "#fff"),
    }
    MEDAL = {1: "#F0A82E", 2: "#9CA3AF", 3: "#CD7F32"}
    MEDAL_BG = {1: "rgba(240,168,46,0.08)", 2: "rgba(156,163,175,0.06)", 3: "rgba(205,127,50,0.06)"}

    def _inits(name):
        parts = name.strip().split()
        return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else (parts[0][0].upper() if parts else "?")

    def _dots(levels):
        return "".join(
            f'<div style="width:8px;height:8px;border-radius:50%;background:{LEVEL_COLOURS_LB.get(levels.get(gk,0),("#E5E7EB",""))[0]};flex-shrink:0;"></div>'
            for gk in CORE_AAP_GAMES
        )

    def _podium(athletes_list):
        top3 = athletes_list[:3]
        if not top3:
            return ""
        podium_order = [1, 0, 2]
        bar_h     = {0: "110px", 1: "80px",  2: "60px"}
        av_size   = {0: "68px",  1: "52px",  2: "44px"}
        av_font   = {0: "24px",  1: "18px",  2: "15px"}
        label_txt = {0: "1st",   1: "2nd",   2: "3rd"}
        cols = ""
        for rank_idx in podium_order:
            if rank_idx >= len(top3):
                cols += '<div style="flex:1;"></div>'
                continue
            a = top3[rank_idx]
            tier = a.get("tier") or {"label": "Starter", "colour": "#6E737B"}
            mc = MEDAL.get(rank_idx + 1, "#9CA3AF")
            pos_label = label_txt[rank_idx]
            inits = _inits(a["name"])
            first = esc(a["name"].split()[0])
            cols += f"""
            <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;">
              <div style="width:{av_size[rank_idx]};height:{av_size[rank_idx]};border-radius:50%;
                          background:#2D323B;border:3px solid {mc};
                          display:flex;align-items:center;justify-content:center;
                          font-weight:800;font-size:{av_font[rank_idx]};color:{mc};
                          box-shadow:0 4px 20px rgba(0,0,0,0.25);">{inits}</div>
              <div style="font-size:12px;font-weight:700;color:#fff;text-align:center;
                          max-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                   title="{esc(a['name'])}">{first}</div>
              <span style="font-size:10px;font-weight:700;background:{tier['colour']};color:#fff;
                           border-radius:999px;padding:2px 8px;">{esc(tier['label'])}</span>
              <div style="font-size:11px;font-weight:600;color:rgba(255,255,255,0.6);">{a['total_xp']:,} AXP</div>
              <div style="width:100%;height:{bar_h[rank_idx]};background:{mc};border-radius:8px 8px 0 0;
                          display:flex;align-items:flex-start;justify-content:center;padding-top:8px;">
                <span style="font-size:15px;font-weight:900;color:#fff;opacity:0.9;">{pos_label}</span>
              </div>
            </div>"""
        return f"""
        <div style="background:linear-gradient(135deg,#2D323B 0%,#3d434d 100%);
                    border-radius:16px;padding:28px 24px 0;margin-bottom:4px;">
          <div style="display:flex;align-items:flex-end;gap:8px;max-width:360px;margin:0 auto;">
            {cols}
          </div>
        </div>"""

    def _ranked_rows(athletes_list, show_group=False):
        if not athletes_list:
            return '<p style="color:#9CA3AF;font-size:14px;padding:16px 0;">No athletes ranked yet.</p>'
        rows = ""
        for i, a in enumerate(athletes_list):
            pos = i + 1
            tier = a.get("tier") or {"label": "Starter", "colour": "#6E737B"}
            levels = a.get("levels", {})
            games_at_l1 = sum(1 for gk in CORE_AAP_GAMES if levels.get(gk, 0) >= 1)
            inits = _inits(a["name"])
            mc = MEDAL.get(pos)
            row_bg = MEDAL_BG.get(pos, ("#F9FAFB" if i % 2 == 0 else "#fff"))
            left_border = f"border-left:3px solid {mc};" if mc else "border-left:3px solid transparent;"
            pos_colour = mc or "#9CA3AF"
            pos_fw = "800" if pos <= 3 else "600"
            group_line = f'<div style="font-size:11px;color:#9CA3AF;">{esc(a.get("group_name",""))}</div>' if show_group else ""
            rows += f"""
            <div style="display:flex;align-items:center;gap:14px;padding:11px 16px;
                        background:{row_bg};border-radius:8px;margin-bottom:3px;
                        {left_border}transition:box-shadow 0.15s;">
              <div style="width:26px;text-align:center;font-size:14px;
                          font-weight:{pos_fw};color:{pos_colour};flex-shrink:0;">{pos}</div>
              <div style="width:40px;height:40px;border-radius:50%;background:#2D323B;
                          display:flex;align-items:center;justify-content:center;
                          font-weight:800;font-size:14px;color:#F0A82E;flex-shrink:0;">{inits}</div>
              <div style="flex:1;min-width:0;">
                <a href="/coach/participants/{a['id']}"
                   style="font-size:14px;font-weight:700;color:#2D323B;text-decoration:none;">
                  {esc(a['name'])}
                </a>
                {group_line}
                <div style="display:flex;gap:3px;margin-top:4px;">{_dots(levels)}</div>
              </div>
              <div style="text-align:right;flex-shrink:0;min-width:52px;">
                <div style="font-size:16px;font-weight:900;color:#2D323B;line-height:1;">{a['total_xp']:,}</div>
                <div style="font-size:10px;color:#9CA3AF;font-weight:600;letter-spacing:0.04em;">AXP</div>
              </div>
              <div style="flex-shrink:0;">
                <span style="font-size:11px;font-weight:700;background:{tier['colour']};
                             color:#fff;border-radius:999px;padding:2px 10px;">
                  {esc(tier['label'])}
                </span>
              </div>
              <div style="flex-shrink:0;width:36px;text-align:center;">
                <div style="font-size:13px;font-weight:700;color:#1EBE8B;">{games_at_l1}</div>
                <div style="font-size:10px;color:#9CA3AF;">L1+</div>
              </div>
            </div>"""
        return rows

    # ── Group selector ─────────────────────────────────────────────────────────
    _org_buckets = {}
    for g in groups:
        on = g.get("org_name") or "No Organisation"
        _org_buckets.setdefault(on, []).append(g)
    group_opts = '<option value="">— All groups —</option>'
    for on, glist in _org_buckets.items():
        group_opts += f'<optgroup label="{esc(on)}">'
        for g in glist:
            sel = "selected" if g["id"] == selected_group_id else ""
            group_opts += f'<option value="{g["id"]}" {sel}>{esc(g["name"])}</option>'
        group_opts += "</optgroup>"

    selector = f"""
    <div style="background:#fff;border:1.5px solid #E5E7EB;border-radius:12px;
                padding:16px 20px;margin-bottom:24px;">
      <div style="font-size:11px;font-weight:700;color:#6E737B;text-transform:uppercase;
                  letter-spacing:0.07em;margin-bottom:10px;">Filter by Group</div>
      <form method="get" action="/coach/leaderboard"
            style="display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;">
        <select name="group_id" style="min-width:220px;">{group_opts}</select>
        <button type="submit" class="btn btn-primary">Load</button>
      </form>
    </div>"""

    # ── Hero banner ────────────────────────────────────────────────────────────
    total_athletes = len(all_ranked) if all_ranked is not None else ""
    hero_sub = f"{total_athletes} athletes across all groups" if total_athletes else "Ranked by AXP earned in sessions"
    hero = f"""
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d434d 100%);
                border-radius:20px;padding:28px 32px;margin-bottom:28px;
                display:flex;align-items:center;gap:24px;">
      <div style="width:60px;height:60px;border-radius:14px;background:rgba(240,168,46,0.18);
                  border:1.5px solid rgba(240,168,46,0.35);
                  display:flex;align-items:center;justify-content:center;
                  font-size:28px;color:#F0A82E;font-weight:900;flex-shrink:0;">▲</div>
      <div>
        <div style="font-size:24px;font-weight:900;color:#fff;letter-spacing:-0.01em;">Leaderboard</div>
        <div style="font-size:13px;color:rgba(255,255,255,0.55);margin-top:4px;">{hero_sub}</div>
      </div>
    </div>"""

    # ── Programme-wide section ─────────────────────────────────────────────────
    all_ranked_section = ""
    if all_ranked is not None:
        legend = '<div style="font-size:11px;color:#9CA3AF;padding:8px 4px 4px;">Dots = game levels &nbsp;·&nbsp; grey=none · green=L1 · gold=L2 · navy=L3</div>'
        all_ranked_section = f"""
        <div style="margin-bottom:36px;">
          <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:16px;">
            <h2 style="font-size:17px;font-weight:700;color:#2D323B;margin:0;">Programme-Wide</h2>
            <span style="font-size:12px;color:#9CA3AF;">{len(all_ranked)} athletes</span>
          </div>
          {_podium(all_ranked)}
          {legend}
          {_ranked_rows(all_ranked, show_group=True)}
        </div>
        <div style="border-top:1.5px solid #E5E7EB;margin-bottom:32px;"></div>"""

    # ── Group-specific section ─────────────────────────────────────────────────
    ranked_html = ""
    if ranked_athletes is not None:
        legend = '<div style="font-size:11px;color:#9CA3AF;padding:8px 4px 4px;">Dots = game levels &nbsp;·&nbsp; grey=none · green=L1 · gold=L2 · navy=L3</div>'
        ranked_html = f"""
        {_podium(ranked_athletes)}
        {legend}
        {_ranked_rows(ranked_athletes)}"""

    body = f"""
    <div style="max-width:780px;">
      {hero}
      {all_ranked_section}
      <h3 style="font-size:16px;font-weight:700;color:#2D323B;margin:0 0 16px;">Group Leaderboard</h3>
      {selector}
      {ranked_html}
    </div>"""
    return layout("Leaderboard", body, user=coach, active_nav="leaderboard")


# ══════════════════════════════════════════════════════════════════════════════
# AXP INFO PAGE
# ══════════════════════════════════════════════════════════════════════════════

def axp_info_page(user):
    """Plain-English explainer of the AXP points system for athletes."""
    from constants import (XP_RANK_TIERS, XP_PARTICIPATION,
                           ROUND_XP_BASELINE_PER_GAME, ROUND_XP_COMPLETION_BONUS,
                           ROUND_XP_IMPROVEMENT_FACTOR, ROUND_XP_IMPROVEMENT_CAP)

    tier_rows = ""
    for t in XP_RANK_TIERS:
        tier_rows += f"""
        <div style="display:flex;align-items:center;gap:14px;padding:10px 0;
                    border-bottom:1px solid #F3F4F6;">
          <span style="display:inline-block;width:12px;height:12px;border-radius:50%;
                       background:{t['colour']};flex-shrink:0;"></span>
          <span style="font-weight:700;font-size:14px;color:#2D323B;min-width:80px;">{esc(t['label'])}</span>
          <span style="font-size:13px;color:#6B7280;">{t['min_xp']:,} AXP{' +' if t['min_xp'] > 0 else ''}</span>
        </div>"""

    # Testing round AXP
    testing_rows = [
        (f"&#9654; Each game completed in a Baseline round", f"{ROUND_XP_BASELINE_PER_GAME} AXP"),
        (f"&#9654; Finishing all games in a Baseline round", f"+{ROUND_XP_COMPLETION_BONUS} AXP bonus"),
        (f"&#9654; Each game in a Re-Test (based on improvement)", f"Up to {ROUND_XP_IMPROVEMENT_CAP} AXP"),
        (f"&#9654; Completing all games in a Re-Test round", f"+{ROUND_XP_COMPLETION_BONUS} AXP bonus"),
    ]
    testing_html = ""
    for label, pts in testing_rows:
        testing_html += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:9px 0;border-bottom:1px solid #F3F4F6;gap:12px;">
          <span style="font-size:13px;color:#374151;">{label}</span>
          <span style="font-size:13px;font-weight:700;color:#F0A82E;white-space:nowrap;">{pts}</span>
        </div>"""

    # Other AXP
    other_rows = [
        ("&#9733; Completing a game in a regular session", "50 AXP"),
        ("&#9733; Personal best in a regular session", "50 AXP"),
        ("&#9733; Completing a self-directed session game", "25 AXP"),
        ("&#9733; Personal best in a self-directed session", "25 AXP"),
        ("&#9733; First ever session (Welcome Bonus)", "100 AXP"),
        ("&#9733; First time playing a new game", "20 AXP"),
        ("&#9733; All 8 games in one session", "100 AXP"),
        ("&#9733; 3-session attendance streak", "30 AXP"),
        ("&#9733; 5-session attendance streak", "75 AXP"),
        ("&#9733; 10th session milestone", "150 AXP"),
        ("&#9733; 25th session milestone", "300 AXP"),
        ("&#9733; 50th session milestone", "600 AXP"),
    ]
    other_html = ""
    for label, pts in other_rows:
        other_html += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:9px 0;border-bottom:1px solid #F3F4F6;gap:12px;">
          <span style="font-size:13px;color:#374151;">{label}</span>
          <span style="font-size:13px;font-weight:700;color:#2D323B;white-space:nowrap;">{pts}</span>
        </div>"""

    body = f"""
    <div style="max-width:680px;margin:0 auto;padding:24px 16px 48px;">
      <a href="/dashboard" style="font-size:13px;color:#6B7280;text-decoration:none;">&larr; Back to Dashboard</a>

      <div style="background:#2D323B;border-radius:20px;padding:28px;margin:20px 0 28px;color:#fff;">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                    color:#F0A82E;margin-bottom:6px;">Points System</div>
        <h1 style="font-size:26px;font-weight:800;margin:0 0 10px;">What is AXP?</h1>
        <p style="font-size:14px;color:rgba(255,255,255,0.8);line-height:1.7;margin:0;">
          <strong style="color:#F0A82E;">AXP (Adaptability Experience Points)</strong> is how we track
          your effort and progress in the Athlete Adaptability Programme. Every time you show up,
          test yourself, or improve your scores — you earn AXP.
          It&rsquo;s not just about how good you are; it&rsquo;s about how much you&rsquo;re
          putting in and growing.
        </p>
      </div>

      <div class="card" style="margin-bottom:20px;">
        <h2 style="font-size:15px;font-weight:700;color:#2D323B;margin:0 0 4px;">AXP from Testing Rounds</h2>
        <p style="font-size:13px;color:#6B7280;margin:0 0 4px;">
          The biggest AXP comes from testing rounds opened by your practitioner.
        </p>
        <p style="font-size:13px;color:#6B7280;margin:0 0 12px;">
          <strong>Re-Test AXP</strong> is based on how much you improved since your last test.
          The formula is: <em>improvement % &times; {ROUND_XP_IMPROVEMENT_FACTOR}</em>, capped at {ROUND_XP_IMPROVEMENT_CAP} AXP per game.
          A 20% improvement earns 120 AXP per game — so the harder you work between tests, the more you earn.
        </p>
        {testing_html}
      </div>

      <div class="card" style="margin-bottom:20px;">
        <h2 style="font-size:15px;font-weight:700;color:#2D323B;margin:0 0 4px;">Other ways to earn AXP</h2>
        <p style="font-size:13px;color:#6B7280;margin:0 0 12px;">
          You also earn AXP for regular sessions, streaks, and milestones.
        </p>
        {other_html}
      </div>

      <div class="card">
        <h2 style="font-size:15px;font-weight:700;color:#2D323B;margin:0 0 4px;">Ranks</h2>
        <p style="font-size:13px;color:#6B7280;margin:0 0 12px;">
          Your rank shows how much AXP you&rsquo;ve earned overall. Keep showing up and it keeps climbing.
        </p>
        {tier_rows}
      </div>
    </div>"""

    return layout("What is AXP?", body, user=user, active_nav="xp")


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
            <div style="background:#fff;border:1.5px solid #E8E9EB;border-left:4px solid #E8E9EB;
                        border-radius:12px;padding:20px 24px;margin-bottom:20px;opacity:0.55;">
              <div style="font-size:15px;font-weight:700;color:#2D323B;margin-bottom:4px;">
                {esc(d['display_name'])}
              </div>
              <div style="font-size:13px;color:#9CA3AF;">No scores recorded yet.</div>
            </div>"""
            continue

        mn, mx = d.get("min_val", 0), d.get("max_val", 1)
        rng = mx - mn or 1

        def _bar_pos(v):
            return max(0, min(100, round((v - mn) / rng * 100)))

        # Coloured fill strips on the track
        p25_pct = _bar_pos(d["p25"]) if d.get("p25") is not None else 0
        p75_pct = _bar_pos(d["p75"]) if d.get("p75") is not None else 0
        p90_pct = _bar_pos(d["p90"]) if d.get("p90") is not None else 0
        fill_iq  = f'<div style="position:absolute;left:{p25_pct}%;width:{max(0,p75_pct-p25_pct)}%;height:100%;background:rgba(240,168,46,0.35);border-radius:3px;"></div>' if d.get("p25") and d.get("p75") else ""
        fill_top = f'<div style="position:absolute;left:{p75_pct}%;width:{max(0,p90_pct-p75_pct)}%;height:100%;background:rgba(249,115,22,0.28);border-radius:3px;"></div>' if d.get("p75") and d.get("p90") else ""

        markers = [
            ("P25", d.get("p25"), "#9CA3AF"),
            ("Mean", d.get("mean"), "#2D323B"),
            ("P75", d.get("p75"), "#F0A82E"),
            ("P90", d.get("p90"), "#F97316"),
        ]
        marker_html = ""
        for label, val, col in markers:
            if val is None:
                continue
            pos = _bar_pos(val)
            marker_html += (
                f'<div style="position:absolute;left:{pos}%;top:0;height:100%;'
                f'border-left:2px solid {col};z-index:1;"></div>'
                f'<div style="position:absolute;left:{pos}%;top:-20px;'
                f'transform:translateX(-50%);font-size:10px;font-weight:700;color:{col};'
                f'white-space:nowrap;">{label}: {_fmt(val, lower)}</div>'
            )

        bar_html = f"""
        <div style="position:relative;margin:32px 0 10px;">
          {marker_html}
          <div style="height:12px;background:#F0F1F3;border-radius:999px;overflow:hidden;
                      border:1px solid #E5E7EB;position:relative;">
            {fill_iq}{fill_top}
          </div>
          <div style="display:flex;justify-content:space-between;font-size:10px;
                      color:#9CA3AF;margin-top:5px;">
            <span>Min {_fmt(mn, lower)}</span>
            <span>Max {_fmt(mx, lower)}</span>
          </div>
        </div>"""

        # Stats row — key stats highlighted, secondary muted
        stats = [
            ("n",      str(n),                    "#2D323B", False),
            ("Min",    _fmt(d.get("min_val"),lower), "#9CA3AF", False),
            ("P25",    _fmt(d.get("p25"),lower),   "#6E737B", False),
            ("Median", _fmt(d.get("p50"),lower),   "#6E737B", False),
            ("Mean",   _fmt(d.get("mean"),lower),  "#2D323B", True),
            ("P75",    _fmt(d.get("p75"),lower),   "#F0A82E", True),
            ("P90",    _fmt(d.get("p90"),lower),   "#F97316", True),
            ("Max",    _fmt(d.get("max_val"),lower),"#9CA3AF", False),
        ]
        stats_html = "".join(
            f'<div style="text-align:center;flex:1;min-width:52px;'
            f'{"background:rgba(240,168,46,0.07);border-radius:8px;padding:6px 4px;" if bold else "padding:6px 4px;"}">'
            f'<div style="font-size:{"16" if bold else "13"}px;font-weight:{"900" if bold else "700"};color:{col};">{val}</div>'
            f'<div style="font-size:10px;color:#9CA3AF;margin-top:2px;">{lbl}</div>'
            f'</div>'
            for lbl, val, col, bold in stats
        )

        # Suggested thresholds — horizontal row
        sugg = d.get("suggested", {})
        sugg_badges = ""
        for lvl in range(1, 6):
            sv = sugg.get(lvl)
            bg, fg = LEVEL_C.get(lvl, ("#E5E7EB", "#2D323B"))
            sv_str = _fmt(sv, lower) if sv is not None else "—"
            sugg_badges += (
                f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px;'
                f'padding:10px 14px;background:#FAFAFA;border:1.5px solid #EFEFEF;border-radius:10px;min-width:64px;">'
                f'<span style="font-size:11px;font-weight:700;background:{bg};color:{fg};'
                f'border-radius:999px;padding:1px 10px;">L{lvl}</span>'
                f'<span style="font-size:13px;font-weight:800;color:#2D323B;">{sv_str}</span>'
                f'</div>'
            )

        lower_note = (' <span style="font-size:11px;font-weight:600;color:#6E737B;'
                      'background:#F3F4F5;border-radius:999px;padding:1px 8px;">lower = better</span>') if lower else ''
        cards_html += f"""
        <div style="background:#fff;border:1.5px solid #E8E9EB;border-left:4px solid #2D323B;
                    border-radius:12px;overflow:hidden;margin-bottom:20px;">
          <!-- Card header -->
          <div style="padding:16px 20px 14px;border-bottom:1px solid #F3F4F5;">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <span style="font-size:16px;font-weight:800;color:#2D323B;">{esc(d['display_name'])}</span>
              <span style="font-size:11px;color:#9CA3AF;background:#F3F4F5;border-radius:999px;
                           padding:1px 8px;">field: {esc(d['field_key'])}</span>
              {lower_note}
              <span style="margin-left:auto;font-size:12px;color:#9CA3AF;font-weight:600;">n = {n}</span>
            </div>
            {bar_html}
          </div>
          <!-- Stats row -->
          <div style="display:flex;flex-wrap:wrap;gap:0;padding:4px 12px;">
            {stats_html}
          </div>
          <!-- Suggested thresholds -->
          <div style="padding:14px 20px 18px;border-top:1px solid #F3F4F5;">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.06em;color:var(--jag-muted);margin-bottom:10px;
                        display:flex;align-items:center;gap:8px;">
              Suggested Thresholds
              <span style="font-weight:400;text-transform:none;letter-spacing:0;">
                — <a href="/coach/admin/game-thresholds" style="color:#2D323B;">set final values in AXP Thresholds &#8599;</a>
              </span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              {sugg_badges}
            </div>
          </div>
        </div>"""

    body = f"""
    <!-- Hero banner -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;
                justify-content:space-between;gap:16px;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:16px;">
        <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                    border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                    justify-content:center;font-size:22px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9698;</div>
        <div>
          <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">Score Distribution Report</div>
          <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:3px;">
            Percentile breakdown per game — use to set thresholds in
            <a href="/coach/admin/game-thresholds" style="color:#F0A82E;font-weight:600;">AXP Thresholds &#8599;</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Reading guide -->
    <div style="background:rgba(240,168,46,0.08);border-left:4px solid #F0A82E;border-radius:10px;
                padding:14px 18px;margin-bottom:24px;font-size:13px;color:#2D323B;line-height:1.6;">
      <strong>Reading this report:</strong> P25 = 25th percentile (bottom quarter of athletes),
      P75 = top quarter threshold, P90 = top 10%. The
      <span style="display:inline-block;width:14px;height:8px;background:rgba(240,168,46,0.45);
                   border-radius:2px;vertical-align:middle;margin:0 2px;"></span> gold bar = interquartile range (P25→P75),
      <span style="display:inline-block;width:14px;height:8px;background:rgba(249,115,22,0.35);
                   border-radius:2px;vertical-align:middle;margin:0 2px;"></span> orange = P75→P90.
      Key stats (Mean, P75, P90) are highlighted in each row.
      Suggested thresholds are computed automatically — always review against programme context.
    </div>

    <div style="max-width:800px;">
      {cards_html}
    </div>"""

    return layout("Score Distribution", body, user=coach, active_nav="dashboard")


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM ADMIN HUB  (system_admin only)
# ══════════════════════════════════════════════════════════════════════════════

def system_admin_hub_page(user):
    def _section(title, sym, cards_html):
        return f"""
        <div style="margin-bottom:36px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
            <div style="width:28px;height:28px;border-radius:8px;background:#2D323B;
                        display:flex;align-items:center;justify-content:center;
                        font-size:13px;color:#F0A82E;font-weight:700;flex-shrink:0;">{sym}</div>
            <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                         letter-spacing:0.08em;color:var(--jag-muted);">{esc(title)}</span>
            <div style="flex:1;height:1px;background:var(--jag-border);"></div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;">
            {cards_html}
          </div>
        </div>"""

    def _card(href, label, desc, icon_sym="▶", icon_bg="#2D323B", icon_col="#F0A82E", label_col="#2D323B"):
        return f"""
        <a href="{href}" style="display:flex;gap:14px;align-items:flex-start;
                   background:#fff;border:1.5px solid #E8E9EB;
                   border-radius:12px;padding:16px 18px;text-decoration:none;
                   transition:box-shadow 0.18s,transform 0.15s,border-color 0.15s;"
           onmouseover="this.style.boxShadow='0 6px 20px rgba(240,168,46,0.15)';this.style.transform='translateY(-2px)';this.style.borderColor='#F0A82E';"
           onmouseout="this.style.boxShadow='';this.style.transform='';this.style.borderColor='#E8E9EB';">
          <div style="width:36px;height:36px;border-radius:10px;background:{icon_bg};
                      display:flex;align-items:center;justify-content:center;
                      font-size:15px;color:{icon_col};flex-shrink:0;font-weight:700;">{icon_sym}</div>
          <div>
            <div style="font-size:14px;font-weight:700;color:{label_col};margin-bottom:4px;">{esc(label)}</div>
            <div style="font-size:12px;color:#6E737B;line-height:1.5;">{esc(desc)}</div>
          </div>
        </a>"""

    thresholds = _section("JAG Standard — Thresholds &amp; Standards", "◎",
        _card("/coach/admin/score-distribution", "Score Distribution",
              "Percentile breakdown per game — P25, mean, P75, P90, max. Use to decide threshold values.",
              "▦", "#F0A82E", "#2D323B", "#B07800") +
        _card("/coach/admin/game-thresholds", "AXP Thresholds",
              "Set the official JAG Standard level thresholds (L1–L5) for all 8 core games.",
              "⚙", "#2D323B", "#F0A82E", "#2D323B")
    )

    data_tools = _section("Data — Import &amp; Export", "↕",
        _card("/coach/participants/import", "Import Athletes",
              "Bulk-upload athletes from a CSV file. Auto-assigns athlete numbers.",
              "▲", "#1EBE8B", "#fff", "#0d7a5a") +
        _card("/coach/participants/export.csv", "Export Athletes",
              "Download all athletes with temporary passwords as a CSV.",
              "▼", "#6E737B", "#fff", "#4a5057") +
        _card("/coach/scores/import", "Import Scores",
              "Bulk-upload measurement session scores from a CSV file.",
              "▲", "#1EBE8B", "#fff", "#0d7a5a")
    )

    xp_tools = _section("AXP Engine", "★",
        _card("/coach/admin/game-thresholds#retroactive", "Retroactive AXP Pass",
              "Re-run the AXP engine across all historical sessions. Use after changing thresholds.",
              "↺", "#F97316", "#fff", "#c05a0a") +
        _card("/coach/leaderboard", "Group Leaderboard",
              "View AXP rankings within any group. Toggle per-group leaderboard visibility in group settings.",
              "▲", "#8B5CF6", "#fff", "#5b2fc9")
    )

    people = _section("People &amp; Organisations", "◈",
        _card("/coach/coaches", "Practitioners",
              "Manage practitioner accounts, roles, and organisation assignments.",
              "◉", "#2D323B", "#F0A82E", "#2D323B") +
        _card("/coach/organisations", "Organisations",
              "Manage partner organisations and their branding.",
              "▣", "#2D323B", "#F0A82E", "#2D323B") +
        _card("/coach", "Practitioner Dashboard",
              "Main dashboard — groups, athletes, and session recording.",
              "⌂", "#6E737B", "#fff", "#4a5057")
    )

    reports = _section("Reports &amp; Statistics", "▤",
        _card("/coach/reports", "Statistics &amp; Reports",
              "All-groups progress overview, completion tracker, and achievement summaries.",
              "▤", "#2D323B", "#F0A82E", "#2D323B") +
        _card("/coach/admin/sessions", "Session Browser",
              "Browse, merge, and manage all recorded measurement sessions.",
              "≡", "#6E737B", "#fff", "#4a5057")
    )

    system_map = _section("System Map &amp; Help", "?",
        _card("/help", "Portal System Map",
              "Full map of every page and feature in the portal, with direct links. Role-aware — shows practitioner and admin areas.",
              "◈", "#6366F1", "#fff", "#3730a3")
    )

    body = f"""
    <!-- Hero banner -->
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                padding:24px 28px;margin-bottom:32px;display:flex;align-items:center;gap:18px;">
      <div style="width:52px;height:52px;border-radius:14px;background:rgba(240,168,46,0.18);
                  border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                  justify-content:center;font-size:24px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9881;</div>
      <div>
        <div style="font-size:22px;font-weight:800;color:#FFFFFF;line-height:1.2;">System Admin Hub</div>
        <div style="font-size:13px;color:rgba(255,255,255,0.50);margin-top:4px;">
          All admin tools in one place — only visible to system admins.
        </div>
      </div>
    </div>
    <div style="max-width:900px;">
      {thresholds}
      {data_tools}
      {xp_tools}
      {people}
      {reports}
      {system_map}
    </div>"""

    return layout("Admin Hub", body, user=user, active_nav="admin_hub")


# ── Athlete Quick-Start Card PDF ──────────────────────────────────────────────

def athlete_quickstart_card_pdf(participant, xp_data, levels):
    """Generate a personalised single-page A4 Quick-Start Card PDF for an athlete."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from constants import XP_RANK_TIERS, XP_PARTICIPATION, CORE_AAP_GAMES, find_measurement_game

    NAVY   = colors.HexColor("#2D323B")
    GOLD   = colors.HexColor("#F0A82E")
    GREEN  = colors.HexColor("#1EBE8B")
    WHITE  = colors.white
    LIGHT  = colors.HexColor("#F4F5F7")
    MUTED  = colors.HexColor("#6E737B")
    BORDER = colors.HexColor("#E5E7EB")

    name       = participant.get("name", "Athlete")
    email      = participant.get("email", "")
    an         = participant.get("athlete_number") or ""
    total_xp   = (xp_data or {}).get("total", 0)
    tier       = (xp_data or {}).get("tier") or XP_RANK_TIERS[0]
    tier_label = tier["label"]
    tier_col   = colors.HexColor(tier["colour"])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=16*mm, rightMargin=16*mm,
                            topMargin=0, bottomMargin=14*mm)
    W = A4[0] - 32*mm

    # ── Styles ─────────────────────────────────────────────────────────────────
    S = lambda name, **kw: ParagraphStyle(name, **kw)
    hdr_name  = S("hn", fontSize=20, fontName="Helvetica-Bold", textColor=WHITE, leading=24)
    hdr_sub   = S("hs", fontSize=10, fontName="Helvetica",      textColor=GOLD)
    body      = S("b",  fontSize=9,  fontName="Helvetica",      textColor=NAVY, leading=13)
    body_mute = S("bm", fontSize=8,  fontName="Helvetica",      textColor=MUTED, leading=12)
    sec_head  = S("sh", fontSize=8,  fontName="Helvetica-Bold", textColor=NAVY,
                  spaceBefore=10, spaceAfter=4,
                  textTransform="uppercase", letterSpacing=1.0)
    tier_sty  = S("ts", fontSize=11, fontName="Helvetica-Bold", textColor=WHITE,
                  alignment=TA_CENTER)
    xp_big    = S("xb", fontSize=22, fontName="Helvetica-Bold", textColor=GOLD,
                  alignment=TA_CENTER)
    xp_lbl    = S("xl", fontSize=8,  fontName="Helvetica",      textColor=MUTED,
                  alignment=TA_CENTER)
    cell_sty  = S("cs", fontSize=8,  fontName="Helvetica",      textColor=NAVY, leading=11)
    cell_bold = S("cb", fontSize=8,  fontName="Helvetica-Bold", textColor=NAVY, leading=11)
    cell_gold = S("cg", fontSize=8,  fontName="Helvetica-Bold", textColor=GOLD, leading=11,
                  alignment=TA_CENTER)
    step_num  = S("sn", fontSize=10, fontName="Helvetica-Bold", textColor=WHITE,
                  alignment=TA_CENTER)
    step_txt  = S("st", fontSize=8,  fontName="Helvetica",      textColor=NAVY, leading=12)
    footer_s  = S("fs", fontSize=7,  fontName="Helvetica",      textColor=MUTED,
                  alignment=TA_CENTER)

    story = []

    # ── Header banner ──────────────────────────────────────────────────────────
    an_str = f"  ·  #{an}" if an else ""
    hdr_table = Table(
        [[Paragraph(name, hdr_name)],
         [Paragraph(f"Athlete Quick-Start Card{an_str}", hdr_sub)]],
        colWidths=[W]
    )
    hdr_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 8))

    # ── XP hero + tier ────────────────────────────────────────────────────────
    DARK_DIV = colors.HexColor("#3D4350")   # subtle divider on navy bg
    PALE     = colors.HexColor("#9CA3AF")   # muted text on navy bg

    # Find next tier
    next_tier = None
    for t in XP_RANK_TIERS:
        if total_xp < t["min_xp"]:
            next_tier = t
            break
    next_str = (f"{next_tier['min_xp'] - total_xp:,} AXP to {next_tier['label']}"
                if next_tier else "Maximum rank achieved!")

    # LEFT: number block — explicit rowHeights prevent the overlap bug
    num_block = Table(
        [[Paragraph(f"{total_xp:,}", S("xb2", fontSize=26, fontName="Helvetica-Bold",
                                        textColor=GOLD, alignment=TA_CENTER, leading=30))],
         [Paragraph("YOUR AXP", S("xl2", fontSize=8,  fontName="Helvetica",
                                   textColor=PALE, alignment=TA_CENTER))]],
        colWidths=[W * 0.28],
        rowHeights=[32, 14],
    )
    num_block.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    # MIDDLE: tier badge + progress note
    tier_chip = Table(
        [[Paragraph(tier_label, S("tc2", fontSize=10, fontName="Helvetica-Bold",
                                   textColor=WHITE, alignment=TA_CENTER))]],
        colWidths=[34*mm]
    )
    tier_chip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), tier_col),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    mid_cell = [
        tier_chip,
        Spacer(1, 5),
        Paragraph(next_str, S("ns2", fontSize=8, fontName="Helvetica",
                               textColor=PALE, leading=11)),
    ]

    # RIGHT: tier ladder with coloured dots
    DIM_NAVY = colors.HexColor("#3A404B")
    tier_rows = []
    for t in XP_RANK_TIERS:
        tc       = colors.HexColor(t["colour"])
        achieved = total_xp >= t["min_xp"]
        current  = (t["label"] == tier_label)
        dot_bg   = tc if achieved else DIM_NAVY
        dot = Table([[""]], colWidths=[3.5*mm], rowHeights=[3.5*mm])
        dot.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), dot_bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        name_style = S("tl2", fontSize=8,
                       fontName="Helvetica-Bold" if current else "Helvetica",
                       textColor=tc if achieved else PALE)
        val_style  = S("tv2", fontSize=7, fontName="Helvetica", textColor=PALE)
        tier_rows.append([dot,
                          Paragraph(t["label"], name_style),
                          Paragraph(f"{t['min_xp']:,} AXP", val_style)])
    ladder = Table(tier_rows, colWidths=[5*mm, 26*mm, 24*mm])
    ladder.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    xp_section = Table(
        [[num_block, mid_cell, ladder]],
        colWidths=[W * 0.28, W * 0.38, W * 0.34]
    )
    xp_section.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEAFTER",     (0, 0), (0, -1), 0.5, DARK_DIV),
        ("LINEAFTER",     (1, 0), (1, -1), 0.5, DARK_DIV),
    ]))
    story.append(xp_section)
    story.append(Spacer(1, 8))

    # ── How to earn AXP ───────────────────────────────────────────────────────
    story.append(Paragraph("How You Earn AXP", sec_head))
    earn_rows = [
        [Paragraph("Activity", cell_bold), Paragraph("AXP", cell_gold)],
        [Paragraph("Attending a measurement session", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['formal_game']} per game", cell_gold)],
        [Paragraph("Personal best in a formal session", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['pb_formal']} per PB", cell_gold)],
        [Paragraph("Self-directed session (self-test)", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['self_directed_game']} per game", cell_gold)],
        [Paragraph("First ever session — welcome bonus", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['welcome_bonus']}", cell_gold)],
        [Paragraph("Attendance streak (3 sessions)", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['streak_3']}", cell_gold)],
        [Paragraph("Attendance streak (5 sessions)", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['streak_5']}", cell_gold)],
        [Paragraph("Complete all 8 games in one session", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['all_8_session']}", cell_gold)],
        [Paragraph("Reach L1 in all 8 core games", cell_sty),
         Paragraph(f"+{XP_PARTICIPATION['all_8_l1']}", cell_gold)],
    ]
    earn_table = Table(earn_rows, colWidths=[W * 0.78, W * 0.22])
    earn_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("BACKGROUND",    (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(earn_table)
    story.append(Spacer(1, 8))

    # ── Game levels ───────────────────────────────────────────────────────────
    story.append(Paragraph("Your Game Levels", sec_head))
    level_cols = []
    LEVEL_LABELS = {0: "—", 1: "L1", 2: "L2", 3: "L3", 4: "L4", 5: "L5"}
    LEVEL_COLOURS_RL = {
        0: (colors.HexColor("#E5E7EB"), MUTED),
        1: (GREEN, WHITE),
        2: (GOLD, NAVY),
        3: (NAVY, WHITE),
        4: (colors.HexColor("#F97316"), WHITE),
        5: (colors.HexColor("#8B5CF6"), WHITE),
    }
    badge_rows = []
    row = []
    for i, gk in enumerate(CORE_AAP_GAMES):
        gdef = find_measurement_game(gk)
        gname = (gdef["name"][:18] + "…" if gdef and len(gdef["name"]) > 18
                 else (gdef["name"] if gdef else gk))
        lvl = (levels or {}).get(gk, 0)
        bg, fg = LEVEL_COLOURS_RL.get(lvl, (LIGHT, MUTED))
        lbl = LEVEL_LABELS.get(lvl, "—")
        badge = Table(
            [[Paragraph(lbl, S("lv", fontSize=9, fontName="Helvetica-Bold",
                               textColor=fg, alignment=TA_CENTER))],
             [Paragraph(gname, S("gn", fontSize=7, fontName="Helvetica",
                                  textColor=MUTED, alignment=TA_CENTER, leading=9))]],
            colWidths=[(W / 4) - 2*mm]
        )
        badge.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), bg),
            ("BACKGROUND",    (0, 1), (0, 1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ]))
        row.append(badge)
        if len(row) == 4 or i == len(CORE_AAP_GAMES) - 1:
            while len(row) < 4:
                row.append("")
            badge_rows.append(row)
            row = []

    badge_grid = Table(badge_rows,
                       colWidths=[(W / 4) - 1*mm] * 4,
                       hAlign="LEFT")
    badge_grid.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1),
    ]))
    story.append(badge_grid)
    story.append(Spacer(1, 8))

    # ── Getting started steps ─────────────────────────────────────────────────
    story.append(Paragraph("Getting Started", sec_head))
    steps = [
        ("1", "Log in", f"Use your email: {email or 'ask your practitioner'}"),
        ("2", "Check your dashboard", "See your current level, AXP total, and recent sessions"),
        ("3", "Attend sessions", "Your practitioner will record your scores and you'll earn AXP"),
        ("4", "Try self-directed", "Practise games on your own from the Self-Directed section"),
    ]
    step_cells = []
    for num, title, desc in steps:
        num_cell = Table([[Paragraph(num, step_num)]], colWidths=[7*mm])
        num_cell.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GOLD),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        txt_cell = [
            Paragraph(title, S("st", fontSize=8, fontName="Helvetica-Bold", textColor=NAVY)),
            Paragraph(desc,  S("sd", fontSize=7, fontName="Helvetica",      textColor=MUTED, leading=10)),
        ]
        step_cells.append([num_cell, txt_cell])

    steps_table = Table(step_cells, colWidths=[10*mm, W - 10*mm])
    steps_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, BORDER),
    ]))
    story.append(steps_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width=W, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Just A Game  ·  Adaptability Assessment Programme  ·  justagame.co.nz",
        footer_s
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Measurement Window views ───────────────────────────────────────────────────

def testing_hub_page(coach, group, rounds, options, open_rnd, athletes):
    """Practitioner testing hub: round history + open next round."""
    gid   = group["id"]
    gname = esc(group.get("name", "Group"))

    # Level callout colours
    LEVEL_COLOURS = {1:"#1EBE8B", 2:"#3B82F6", 3:"#F3AA33", 4:"#F97316", 5:"#8B5CF6"}

    # ── Options panel ────────────────────────────────────────────────────────
    if open_rnd:
        rtype  = open_rnd["round_type"].title()
        rlabel = f"Level {open_rnd['level']} {rtype}"
        if open_rnd["retest_sequence"]:
            rlabel += f" #{open_rnd['retest_sequence']}"
        clr = LEVEL_COLOURS.get(open_rnd["level"], "#6E737B")
        options_html = f"""
        <div style="background:#FEF3C7;border:1.5px solid #F3AA33;border-radius:14px;
                    padding:18px 20px;margin-bottom:20px;">
          <p style="margin:0 0 4px;font-size:12px;font-weight:700;color:#92400E;
                    text-transform:uppercase;letter-spacing:0.06em;">Round in Progress</p>
          <div style="font-size:18px;font-weight:800;color:#2D323B;margin-bottom:12px;">
            {esc(rlabel)}
          </div>
          <a href="/coach/round/{open_rnd['id']}"
             style="display:inline-block;background:#2D323B;color:#F3AA33;font-weight:700;
                    font-size:14px;border-radius:10px;padding:10px 20px;text-decoration:none;">
            Enter / Review Scores →
          </a>
        </div>"""
    elif options:
        btns = ""
        for opt in options:
            lvl   = opt["level"]
            rtype = opt["round_type"]
            clr   = LEVEL_COLOURS.get(lvl, "#6E737B")
            btns += f"""
          <button type="submit" name="round_type" value="{rtype}"
                  onclick="this.form.elements['level'].value='{lvl}'"
                  style="flex:1;min-width:160px;background:{clr};color:#fff;
                         font-weight:700;font-size:14px;border:none;border-radius:10px;
                         padding:12px 16px;cursor:pointer;">
            {esc(opt['label'])}
          </button>"""
        options_html = f"""
        <div style="background:#EEF3F5;border:1.5px solid #BDC4CA;border-radius:14px;
                    padding:18px 20px;margin-bottom:20px;">
          <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#6E737B;
                    text-transform:uppercase;letter-spacing:0.06em;">Open Next Round</p>

          <div style="background:#FFF8E7;border:1.5px solid #F3AA33;border-radius:10px;
                      padding:12px 14px;margin-bottom:14px;font-size:13px;color:#92400E;">
            <strong>Before opening:</strong> Confirm all athletes will use the correct level game cards.
            All games must be completed at the same level across the group.
          </div>

          <form method="post" action="/coach/groups/{gid}/testing/open" style="margin:0;">
            <input type="hidden" name="level" value="">
            <div style="display:flex;flex-wrap:wrap;gap:10px;">
              {btns}
            </div>
          </form>
        </div>"""
    else:
        options_html = """
        <div style="background:#F4F5F7;border-radius:14px;padding:16px 20px;
                    margin-bottom:20px;color:#6E737B;font-size:14px;">
          All 5 levels complete — no further testing rounds available for this group.
        </div>"""

    # ── Round history table ──────────────────────────────────────────────────
    if rounds:
        rows = ""
        for r in rounds:
            lvl   = r["level"]
            rtype = r["round_type"].title()
            seq   = r.get("retest_sequence")
            rlbl  = f"Level {lvl} {rtype}" + (f" #{seq}" if seq else "")
            clr   = LEVEL_COLOURS.get(lvl, "#6E737B")
            stat  = r["status"]
            stat_chip = (
                f'<span style="background:#1EBE8B;color:#fff;border-radius:999px;'
                f'padding:2px 10px;font-size:11px;font-weight:700;">OPEN</span>'
                if stat == "open" else
                f'<span style="background:#E5E7EB;color:#6E737B;border-radius:999px;'
                f'padding:2px 10px;font-size:11px;font-weight:600;">Closed</span>'
            )
            opened  = esc((r.get("opened_at") or "")[:10])
            closed  = esc((r.get("closed_at") or "—")[:10])
            link    = f'<a href="/coach/round/{r["id"]}" style="color:#2D323B;font-weight:600;text-decoration:none;">View →</a>'
            rows += f"""
          <tr>
            <td style="padding:10px 12px;">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                           background:{clr};margin-right:6px;"></span>
              <strong>{esc(rlbl)}</strong>
            </td>
            <td style="padding:10px 12px;">{stat_chip}</td>
            <td style="padding:10px 12px;color:#6E737B;font-size:13px;">{opened}</td>
            <td style="padding:10px 12px;color:#6E737B;font-size:13px;">{closed}</td>
            <td style="padding:10px 12px;">{link}</td>
          </tr>"""
        history_html = f"""
        <div class="card" style="padding:0;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#2D323B;color:#fff;font-size:11px;
                         text-transform:uppercase;letter-spacing:0.06em;">
                <th style="padding:10px 12px;text-align:left;">Round</th>
                <th style="padding:10px 12px;text-align:left;">Status</th>
                <th style="padding:10px 12px;text-align:left;">Opened</th>
                <th style="padding:10px 12px;text-align:left;">Closed</th>
                <th style="padding:10px 12px;"></th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""
    else:
        history_html = """
        <div style="background:#F4F5F7;border-radius:12px;padding:16px 20px;
                    color:#9CA3AF;font-size:14px;text-align:center;">
          No testing rounds yet. Open the first round above to begin.
        </div>"""

    body = f"""
    <div style="max-width:820px;">
      <div class="page-head" style="margin-bottom:20px;">
        <div>
          <h1 style="margin:0 0 4px;">Testing Rounds — {gname}</h1>
          <p class="muted" style="margin:0;">{len(athletes)} athlete(s) in this group</p>
        </div>
        <a href="/coach/group-hub?group_id={gid}"
           style="background:#F4F5F7;color:#2D323B;font-weight:600;font-size:14px;
                  border-radius:10px;padding:10px 18px;text-decoration:none;">
          ← Group Hub
        </a>
      </div>

      {options_html}

      <h2 style="font-size:14px;font-weight:700;color:#6E737B;text-transform:uppercase;
                 letter-spacing:0.06em;margin:0 0 10px;">Round History</h2>
      {history_html}
    </div>"""

    return layout(f"Testing — {gname}", body, user=coach, active_nav="group_hub")


def testing_round_page(coach, rnd, athletes, scores_by_athlete, games):
    """Practitioner score-entry grid for an open (or closed) testing round."""
    from constants import GAME_DISPLAY_NAMES, XP_GAME_CONFIG
    rid    = rnd["id"]
    lvl    = rnd["level"]
    rtype  = rnd["round_type"]
    seq    = rnd.get("retest_sequence")
    is_open = rnd["status"] == "open"
    gid    = rnd["group_id"]
    rlabel = f"Level {lvl} {rtype.title()}" + (f" #{seq}" if seq else "")
    LEVEL_COLOURS = {1:"#1EBE8B", 2:"#3B82F6", 3:"#F3AA33", 4:"#F97316", 5:"#8B5CF6"}
    clr = LEVEL_COLOURS.get(lvl, "#6E737B")

    # Callout banner
    callout = f"""
    <div style="background:#FFF8E7;border:2px solid #F3AA33;border-radius:14px;
                padding:14px 18px;margin-bottom:20px;">
      <p style="margin:0;font-size:13px;color:#92400E;">
        <strong>⚠ Level {lvl} Testing.</strong>
        Before recording any scores, confirm all athletes are using
        <strong>Level {lvl} game cards</strong>.
        All games must be completed at Level {lvl} across the whole group —
        do not mix levels within a round.
      </p>
    </div>"""

    if not is_open:
        callout = f"""
    <div style="background:#F4F5F7;border-radius:14px;padding:12px 18px;margin-bottom:20px;
                font-size:13px;color:#6E737B;">
      This round is <strong>closed</strong>. Scores are read-only.
    </div>"""

    # Build athlete tabs / score grids
    if not athletes:
        athlete_html = '<div style="color:#9CA3AF;padding:20px;">No athletes in this group.</div>'
    else:
        tabs = ""
        panels = ""
        for i, a in enumerate(athletes):
            aid   = a["id"]
            aname = esc(a["name"])
            anum  = esc(a.get("athlete_number") or "")
            active_cls = "active" if i == 0 else ""
            tabs += f"""
          <button class="rtab {active_cls}" data-aid="{aid}"
                  onclick="switchTab({aid})"
                  style="padding:9px 16px;font-size:13px;font-weight:600;border:none;
                         border-bottom:3px solid transparent;background:transparent;
                         cursor:pointer;color:#6E737B;white-space:nowrap;">
            {aname}{(' <span style="color:#BDC4CA;font-size:11px;">#' + anum + '</span>') if anum else ''}
          </button>"""
            # Score fields for this athlete
            fields_html = ""
            for section in games:
                for g in section.get("games", []):
                    gkey  = g["key"]
                    gdisp = esc(GAME_DISPLAY_NAMES.get(gkey, gkey.replace("_", " ").title()))
                    visible = [f for f in g.get("fields", []) if not f.get("hidden") and not f.get("computed")]
                    if not visible:
                        continue
                    inputs = ""
                    for f in visible:
                        fkey   = f["key"]
                        flabel = esc(f.get("label", fkey))
                        funit  = esc(f.get("unit", ""))
                        val    = scores_by_athlete.get(aid, {}).get(gkey, {}).get(fkey, "")
                        val_s  = str(val) if val != "" else ""
                        ro     = 'readonly style="background:#F4F5F7;color:#9CA3AF;"' if not is_open else ""
                        inputs += f"""
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <label style="flex:1;font-size:12px;color:#6E737B;">{flabel}
                      {f'<span style="color:#BDC4CA;font-size:10px;">({funit})</span>' if funit else ''}
                    </label>
                    <input type="number" step="any" placeholder="—"
                           class="score-field" data-game="{gkey}" data-field="{fkey}"
                           value="{val_s}" {ro}
                           style="width:80px;border:1.5px solid #DDE0E3;border-radius:8px;
                                  padding:6px 8px;font-size:14px;text-align:center;
                                  font-weight:600;color:#2D323B;">
                  </div>"""
                    fields_html += f"""
              <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;
                          padding:12px 14px;margin-bottom:10px;">
                <div style="font-weight:700;color:#2D323B;font-size:13px;margin-bottom:8px;">
                  {gdisp}
                </div>
                {inputs}
              </div>"""
            save_btn = ""
            if is_open:
                save_btn = f"""
            <div style="margin-top:14px;">
              <button onclick="saveScores({aid})"
                      id="saveBtn_{aid}"
                      style="background:{clr};color:#fff;font-weight:700;font-size:14px;
                             border:none;border-radius:10px;padding:11px 24px;cursor:pointer;">
                Save {aname.split()[0] if aname else 'Athlete'}'s Scores
              </button>
              <span id="saveMsg_{aid}" style="margin-left:12px;font-size:13px;color:#6E737B;"></span>
            </div>"""
            panels += f"""
          <div class="rpanel" data-aid="{aid}"
               style="display:{'block' if i == 0 else 'none'};padding:16px 0;">
            {fields_html}
            {save_btn}
          </div>"""
        athlete_html = f"""
        <div style="border-bottom:2px solid #E5E7EB;display:flex;gap:0;overflow-x:auto;
                    margin-bottom:0;">
          {tabs}
        </div>
        {panels}"""

    # Close button
    close_btn = ""
    if is_open:
        close_btn = f"""
    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #E5E7EB;">
      <form method="post" action="/coach/round/{rid}/close" style="display:inline;">
        <button type="submit"
                onclick="return confirm('Close this round and award AXP to all athletes?')"
                style="background:#2D323B;color:#F3AA33;font-weight:700;font-size:14px;
                       border:none;border-radius:10px;padding:12px 24px;cursor:pointer;">
          Close Round &amp; Award AXP
        </button>
      </form>
      <a href="/coach/groups/{gid}/testing"
         style="margin-left:12px;color:#6E737B;font-size:13px;text-decoration:none;">
        ← Testing Hub
      </a>
    </div>"""

    body = f"""
    <div style="max-width:860px;">
      <div class="page-head" style="margin-bottom:16px;">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <span style="display:inline-block;width:12px;height:12px;border-radius:50%;
                         background:{clr};"></span>
            <h1 style="margin:0;font-size:20px;">{esc(rlabel)}</h1>
            {'<span style="background:#1EBE8B;color:#fff;border-radius:999px;padding:2px 10px;font-size:11px;font-weight:700;">OPEN</span>' if is_open else '<span style="background:#E5E7EB;color:#6E737B;border-radius:999px;padding:2px 10px;font-size:11px;">Closed</span>'}
          </div>
          <p class="muted" style="margin:0;">
            {esc(rnd.get('group_name',''))} &nbsp;·&nbsp;
            Opened: {esc((rnd.get('opened_at') or '')[:10])}
            {f"&nbsp;·&nbsp; Closed: {esc((rnd.get('closed_at') or '')[:10])}" if rnd.get('closed_at') else ''}
          </p>
        </div>
      </div>

      {callout}

      <div class="card" style="padding:16px 20px 20px;">
        {athlete_html}
      </div>

      {close_btn}
    </div>

    <script>
    function switchTab(aid) {{
      document.querySelectorAll('.rtab').forEach(b => {{
        b.style.borderBottomColor = b.dataset.aid == aid ? '#F3AA33' : 'transparent';
        b.style.color = b.dataset.aid == aid ? '#2D323B' : '#6E737B';
      }});
      document.querySelectorAll('.rpanel').forEach(p => {{
        p.style.display = p.dataset.aid == aid ? 'block' : 'none';
      }});
    }}

    async function saveScores(aid) {{
      const panel = document.querySelector(`.rpanel[data-aid="${{aid}}"]`);
      const scores = {{}};
      panel.querySelectorAll('.score-field').forEach(inp => {{
        if (inp.value !== '') scores[inp.dataset.game + '.' + inp.dataset.field] = parseFloat(inp.value);
      }});
      const btn = document.getElementById('saveBtn_' + aid);
      const msg = document.getElementById('saveMsg_' + aid);
      btn.disabled = true;
      btn.textContent = 'Saving…';
      try {{
        const r = await fetch('/coach/round/{rid}/score', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{ athlete_id: aid, scores }}),
        }});
        const j = await r.json();
        if (j.ok) {{
          msg.textContent = '✓ Saved';
          msg.style.color = '#1EBE8B';
        }} else {{
          msg.textContent = 'Error — try again';
          msg.style.color = '#EF4444';
        }}
      }} catch(e) {{
        msg.textContent = 'Network error';
        msg.style.color = '#EF4444';
      }}
      btn.disabled = false;
      btn.textContent = "Save Scores";
      setTimeout(() => {{ msg.textContent = ''; }}, 3000);
    }}

    // Highlight active tab on load
    switchTab(document.querySelector('.rtab')?.dataset.aid);
    </script>"""

    return layout(f"{rlabel} — Scores", body, user=coach, active_nav="group_hub")


def athlete_round_page(athlete, rnd, games, existing_scores):
    """Athlete self-entry page for an open testing round."""
    from constants import GAME_DISPLAY_NAMES, XP_GAME_CONFIG, ROUND_XP_BASELINE_PER_GAME, ROUND_XP_COMPLETION_BONUS, ROUND_XP_IMPROVEMENT_FACTOR, ROUND_XP_IMPROVEMENT_CAP
    rid    = rnd["id"]
    lvl    = rnd["level"]
    rtype  = rnd["round_type"]
    seq    = rnd.get("retest_sequence")
    is_open = rnd["status"] == "open"
    rlabel = f"Level {lvl} {rtype.title()}" + (f" #{seq}" if seq else "")

    LEVEL_COLOURS = {1:"#1EBE8B", 2:"#3B82F6", 3:"#F3AA33", 4:"#F97316", 5:"#8B5CF6"}
    clr = LEVEL_COLOURS.get(lvl, "#6E737B")

    if rtype == "baseline":
        axp_note = f"You earn <strong>{ROUND_XP_BASELINE_PER_GAME} AXP</strong> per game you complete, plus a <strong>{ROUND_XP_COMPLETION_BONUS} AXP</strong> bonus for finishing all games."
    else:
        axp_note = f"AXP is based on how much you improved since your baseline. The more you improve, the more AXP you earn — up to <strong>{ROUND_XP_IMPROVEMENT_CAP} AXP</strong> per game plus a <strong>{ROUND_XP_COMPLETION_BONUS} AXP</strong> completion bonus."

    callout = f"""
    <div style="background:linear-gradient(135deg,{clr}22 0%,{clr}11 100%);
                border:2px solid {clr};border-radius:16px;padding:18px 20px;margin-bottom:20px;">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                  color:{clr};margin-bottom:6px;">Testing Round Open</div>
      <div style="font-size:22px;font-weight:900;color:#2D323B;margin-bottom:6px;">{esc(rlabel)}</div>
      <p style="margin:0;font-size:13px;color:#555;">
        Enter your scores below using the <strong>Level {lvl} game cards</strong>.
        Make sure you're playing at Level {lvl} for all games — check your game card before starting each one.
      </p>
      <p style="margin:10px 0 0;font-size:13px;color:#555;">{axp_note}</p>
    </div>"""

    if not is_open:
        callout = f"""
    <div style="background:#F4F5F7;border-radius:14px;padding:14px 18px;margin-bottom:20px;
                font-size:13px;color:#6E737B;">
      This round (<strong>{esc(rlabel)}</strong>) is now <strong>closed</strong>.
      Your scores are saved — AXP has been awarded.
    </div>"""

    # Score entry fields
    score_cards = ""
    for section in games:
        for g in section.get("games", []):
            gkey  = g["key"]
            gdisp = esc(GAME_DISPLAY_NAMES.get(gkey, gkey.replace("_", " ").title()))
            visible = [f for f in g.get("fields", []) if not f.get("hidden") and not f.get("computed")]
            if not visible:
                continue
            inputs = ""
            for f in visible:
                fkey   = f["key"]
                flabel = esc(f.get("label", fkey))
                funit  = esc(f.get("unit", ""))
                val    = existing_scores.get(gkey, {}).get(fkey, "")
                val_s  = str(val) if val != "" else ""
                ro     = 'readonly style="background:#F4F5F7;color:#9CA3AF;"' if not is_open else ""
                inputs += f"""
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <label style="flex:1;font-size:13px;color:#555555;">{flabel}
                  {f'<span style="color:#BDC4CA;font-size:11px;"> ({funit})</span>' if funit else ''}
                </label>
                <input type="number" step="any" placeholder="—"
                       class="score-input" data-game="{gkey}" data-field="{fkey}"
                       value="{val_s}" {ro}
                       style="width:90px;border:1.5px solid #DDE0E3;border-radius:8px;
                              padding:7px 10px;font-size:15px;text-align:center;
                              font-weight:700;color:#2D323B;">
              </div>"""
            save_btn = ""
            if is_open:
                save_btn = f"""
            <button onclick="saveGame('{gkey}', this)"
                    data-gkey="{gkey}"
                    style="margin-top:8px;background:{clr};color:#fff;font-weight:700;
                           font-size:13px;border:none;border-radius:8px;padding:9px 18px;
                           cursor:pointer;width:100%;">
              Save {gdisp} Scores
            </button>
            <div class="save-msg" data-gkey="{gkey}"
                 style="font-size:12px;color:#6E737B;margin-top:6px;text-align:center;"></div>"""
            score_cards += f"""
        <div style="background:#FFFFFF;border:1.5px solid #E5E7EB;border-radius:14px;
                    padding:16px 18px;margin-bottom:14px;">
          <div style="font-weight:800;font-size:15px;color:#2D323B;margin-bottom:12px;
                      display:flex;align-items:center;gap:8px;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                         background:{clr};flex-shrink:0;"></span>
            {gdisp}
          </div>
          {inputs}
          {save_btn}
        </div>"""

    body = f"""
    <div style="max-width:560px;margin:0 auto;">
      {callout}
      {score_cards}
      <div style="margin-top:8px;padding:14px;background:#EEF3F5;border-radius:12px;
                  font-size:13px;color:#6E737B;text-align:center;">
        AXP is awarded automatically when your practitioner closes the round.<br>
        You can update your scores any time while the round is open.
      </div>
    </div>

    <script>
    async function saveGame(gkey, btn) {{
      const inputs = document.querySelectorAll(`.score-input[data-game="${{gkey}}"]`);
      const scores = {{}};
      inputs.forEach(inp => {{
        if (inp.value !== '') scores[gkey + '.' + inp.dataset.field] = parseFloat(inp.value);
      }});
      const msgEl = document.querySelector(`.save-msg[data-gkey="${{gkey}}"]`);
      btn.disabled = true;
      btn.textContent = 'Saving…';
      try {{
        const r = await fetch('/athlete/round/{rid}/score', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{ scores }}),
        }});
        const j = await r.json();
        if (j.ok) {{
          msgEl.textContent = '✓ Saved';
          msgEl.style.color = '#1EBE8B';
        }} else {{
          msgEl.textContent = j.error || 'Error — try again';
          msgEl.style.color = '#EF4444';
        }}
      }} catch(e) {{
        msgEl.textContent = 'Network error';
        msgEl.style.color = '#EF4444';
      }}
      btn.disabled = false;
      btn.textContent = 'Save ' + btn.dataset.gkey.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()) + ' Scores';
      setTimeout(() => {{ if (msgEl) msgEl.textContent = ''; }}, 4000);
    }}
    </script>"""

    return layout(f"{rlabel} — My Scores", body, user=athlete, active_nav="home")


def measurement_window_status_page(coach, window, group, athletes, submissions, submitted_ids):
    # DEPRECATED — kept for any lingering references. Redirects to testing hub.
    gid = window.get("group_id", "")
    return layout("Redirecting…",
        f'<script>window.location="/coach/groups/{gid}/testing";</script>',
        user=coach)
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


# ── Individual Athlete Report ──────────────────────────────────────────────────

def individual_athlete_report_page(coach, athlete, sessions, levels_by_area,
                                   thresholds_raw, sc_programme=True):
    """
    Printable individual athlete report.
    Shows latest scores, gap identification against thresholds (if set),
    S&C gap language, and S&C programme recommendations.

    athlete:         user row
    sessions:        list of session dicts (most-recent first), each with 'results' dict keyed (game_key, field_key)
    levels_by_area:  {(game_key, field_key): level}
    thresholds_raw:  list of threshold rows from get_all_thresholds()
    sc_programme:    bool — whether to show the S&C programme section
    """
    from constants import SCORING_AREAS, threshold_field_key, SC_GAP_LANGUAGE, XP_GAME_CONFIG

    today = _dt.date.today().strftime("%d %B %Y")
    name  = esc(athlete.get("name", "Athlete"))
    num   = esc(athlete.get("athlete_number") or "")
    sport = esc(athlete.get("sport") or "")

    # Build threshold lookup: {(game_key, field_key, level): threshold_value}
    thresh_lookup = {}
    for t in thresholds_raw:
        thresh_lookup[(t["game_key"], t["field_key"] or "", t["level"])] = t
    has_thresholds = bool(thresh_lookup)

    # Latest session results
    latest_results = {}  # (game_key, field_key) → value
    latest_date = ""
    if sessions:
        latest = sessions[0]  # most recent first
        latest_results = latest.get("results", {})
        latest_date = latest.get("date", "")

    # First (oldest) session results — used for improvement calculation
    first_results = {}
    first_date = ""
    has_history = len(sessions) >= 2
    if has_history:
        first = sessions[-1]
        first_results = first.get("results", {})
        first_date = first.get("date", "")

    # ── Per-area analysis ────────────────────────────────────────────────────
    FAMILY_ORDER = [
        "Balance & Postural Control",
        "Explosive & Landing",
        "Dynamic Locomotor",
        "Perceptual-Motor Speed",
    ]
    # Canonical brand colours — must match FAMILY_META in athlete_movement_report_page
    FAMILY_META = {
        "Balance & Postural Control": {"col": "#3B6BC4", "icon": "&#9651;"},  # △ blue
        "Explosive & Landing":        {"col": "#F0A82E", "icon": "&#9650;"},  # ▲ gold
        "Dynamic Locomotor":          {"col": "#1EBE8B", "icon": "&#9654;"},  # ▶ green
        "Perceptual-Motor Speed":     {"col": "#D4622F", "icon": "&#9673;"},  # ⊙ terracotta
    }
    FAMILY_COL = {k: v["col"] for k, v in FAMILY_META.items()}

    gap_areas     = []  # areas below threshold (or all if no thresholds)
    tracking_well = []  # areas above threshold that have a recorded score
    score_rows    = []  # for the summary table

    for area in SCORING_AREAS:
        gk       = area["game_key"]
        fk       = area["field_key"]          # None = pooled
        lower    = area["lower_is_better"]
        disp     = area["display_name"]
        stored   = threshold_field_key(area)

        # Resolve score from latest session
        cfg = XP_GAME_CONFIG.get(gk, {})
        if fk is None:
            # Pooled: take max across all score_fields
            vals = [latest_results.get((gk, f)) for f in cfg.get("score_fields", [])]
            vals = [v for v in vals if v is not None]
            score = max(vals) if vals else None
        else:
            score = latest_results.get((gk, fk))

        # Current level for this area
        ach_fk = fk or ""
        cur_level = levels_by_area.get((gk, ach_fk), 0)

        # Find threshold at current_level+1 (what they need to hit next)
        next_level = cur_level + 1
        next_thresh = thresh_lookup.get((gk, stored, next_level))

        # Gap check
        is_gap = False
        gap_label = ""
        if score is not None and next_thresh:
            tv = next_thresh["threshold_value"]
            if lower:
                is_gap = float(score) > tv          # higher time = slower = gap
                gap_label = f"Target: ≤ {tv:g}  (current: {score:g})"
            else:
                is_gap = float(score) < tv
                gap_label = f"Target: {tv:g}  (current: {score:g})"
        elif score is None:
            is_gap = False  # not enough data yet
        elif not has_thresholds:
            is_gap = True   # flag all areas when no thresholds set

        # First-session score for improvement calculation
        if fk is None:
            fvals = [first_results.get((gk, f)) for f in cfg.get("score_fields", [])]
            fvals = [v for v in fvals if v is not None]
            first_score = max(fvals) if fvals else None
        else:
            first_score = first_results.get((gk, fk))

        # Direction-corrected % improvement (first → latest)
        improvement = None
        if score is not None and first_score is not None and first_score != 0:
            raw_pct = (float(score) - float(first_score)) / abs(float(first_score)) * 100
            improvement = -raw_pct if lower else raw_pct  # negative time change = improvement

        # Score row data
        score_s = f"{score:g}" if score is not None else "—"
        score_rows.append({
            "display":     disp,
            "score":       score_s,
            "first_score": f"{first_score:g}" if first_score is not None else None,
            "improvement": improvement,
            "level":       cur_level,
            "next_thr":    f"{next_thresh['threshold_value']:g}" if next_thresh else ("—" if has_thresholds else "not set"),
            "is_gap":      is_gap,
            "gap_label":   gap_label,
            "lower":       lower,
        })

        if is_gap:
            sc_info = SC_GAP_LANGUAGE.get((gk, stored)) or SC_GAP_LANGUAGE.get((gk, ach_fk))
            # Is this athlete close to levelling up? (within 15% of threshold)
            close_to_next = False
            if score is not None and next_thresh:
                tv = next_thresh["threshold_value"]
                if lower:
                    close_to_next = float(score) <= tv * 1.15
                else:
                    close_to_next = float(score) >= tv * 0.85
            gap_areas.append({
                "display":        disp,
                "family":         sc_info["family"] if sc_info else "—",
                "cla_constraint": sc_info.get("cla_constraint", "") if sc_info else "",
                "resource_tag":   sc_info.get("resource_tag", "") if sc_info else "",
                "athlete_games":  sc_info.get("athlete_games", []) if sc_info else [],
                "sc_gap":         sc_info["sc_gap"] if sc_info else "",
                "sc_programme":   sc_info["sc_programme"] if sc_info else "",
                "d2_focus":       sc_info["d2_focus"] if sc_info else [],
                "gap_label":      gap_label,
                "close_to_next":  close_to_next,
            })
        elif score is not None:
            tracking_well.append({
                "display": disp,
                "score":   f"{score:g}",
                "level":   cur_level,
                "lower":   lower,
            })

    # ── Summary table ────────────────────────────────────────────────────────
    LEVEL_C = {0: ("#E5E7EB","#6B7280"), 1: ("#1EBE8B","#fff"), 2: ("#F0A82E","#2D323B"),
               3: ("#2D323B","#fff"), 4: ("#F97316","#fff"), 5: ("#8B5CF6","#fff")}

    def _level_chip(lvl):
        bg, fg = LEVEL_C.get(lvl, ("#E5E7EB","#6B7280"))
        lbl = f"L{lvl}" if lvl else "—"
        return f'<span style="font-size:11px;font-weight:700;background:{bg};color:{fg};border-radius:999px;padding:2px 8px;">{lbl}</span>'

    # Overall improvement summary (direction-corrected average across all areas with history)
    all_imps = [r["improvement"] for r in score_rows if r["improvement"] is not None]
    overall_imp = sum(all_imps) / len(all_imps) if all_imps else None

    def _imp_cell(imp):
        if imp is None:
            return '<span style="font-size:12px;color:#9CA3AF;">—</span>'
        sign = "+" if imp >= 0 else ""
        col  = "#065F46" if imp >= 0 else "#9B1C1C"
        bg   = "rgba(30,190,139,0.10)" if imp >= 0 else "rgba(220,38,38,0.08)"
        return (f'<span style="font-size:11px;font-weight:700;color:{col};background:{bg};'
                f'border-radius:999px;padding:2px 9px;">{sign}{imp:.1f}%</span>')

    trs = ""
    for r in score_rows:
        row_bg  = "rgba(240,168,46,0.06)" if r["is_gap"] else "#fff"
        gap_ind = ('<span style="font-size:11px;font-weight:700;color:#7A5800;'
                   'background:rgba(240,168,46,0.15);border:1px solid rgba(240,168,46,0.30);'
                   'border-radius:999px;padding:2px 10px;">&#9650; Gap</span>'
                   ) if r["is_gap"] else '<span style="font-size:13px;color:#1EBE8B;font-weight:700;">&#10003;</span>'
        lower_note = " ↓" if r["lower"] else ""
        first_cell = (f'<div style="font-size:10px;color:#9CA3AF;margin-top:1px;">was {esc(r["first_score"])}</div>'
                      if r.get("first_score") else "")
        trs += f"""
        <tr style="background:{row_bg};border-bottom:1px solid #F3F4F5;">
          <td style="padding:8px 12px;font-size:13px;font-weight:600;color:#2D323B;">{esc(r['display'])}</td>
          <td style="padding:8px 12px;font-size:13px;text-align:center;">
            {esc(r['score'])}{lower_note}{first_cell}
          </td>
          <td style="padding:8px 12px;text-align:center;">{_imp_cell(r['improvement'])}</td>
          <td style="padding:8px 12px;text-align:center;">{_level_chip(r['level'])}</td>
          <td style="padding:8px 12px;font-size:12px;color:#6E737B;text-align:center;">{esc(r['next_thr'])}</td>
          <td style="padding:8px 12px;text-align:center;">{gap_ind}</td>
        </tr>"""

    imp_col_header = (f'<th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;'
                      f'letter-spacing:0.05em;color:rgba(255,255,255,0.75);text-align:center;">Change</th>'
                      if has_history else
                      f'<th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;'
                      f'letter-spacing:0.05em;color:rgba(255,255,255,0.40);text-align:center;">Change</th>')

    history_note = ""
    if has_history:
        history_note = (f'<div style="font-size:11px;color:#6E737B;margin-bottom:12px;">'
                        f'Showing improvement from first session ({esc(first_date[:10])}) to latest ({esc(latest_date[:10])}) '
                        f'across {len(sessions)} sessions.</div>')

    no_thresh_note = ""
    if not has_thresholds:
        no_thresh_note = '<div style="background:#FFF3D6;border-left:4px solid #F0A82E;border-radius:6px;padding:10px 14px;font-size:12px;color:#92400E;margin-bottom:12px;">No thresholds have been set yet — all scoring areas are shown. Once thresholds are configured, this report will highlight only the areas where this athlete is below their next level target.</div>'

    score_table = f"""
    {no_thresh_note}
    {history_note}
    <div style="border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;margin-bottom:28px;">
      <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
      <table style="width:100%;border-collapse:collapse;min-width:540px;">
        <thead>
          <tr style="background:#2D323B;border-bottom:2px solid #F0A82E;">
            <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.05em;color:rgba(255,255,255,0.75);">Test Area</th>
            <th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.05em;color:rgba(255,255,255,0.75);text-align:center;">Latest Score</th>
            {imp_col_header}
            <th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.05em;color:rgba(255,255,255,0.75);text-align:center;">Level</th>
            <th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.05em;color:rgba(255,255,255,0.75);text-align:center;">Next Threshold</th>
            <th style="padding:10px 12px;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.05em;color:rgba(255,255,255,0.75);text-align:center;">Status</th>
          </tr>
        </thead>
        <tbody>{trs}</tbody>
      </table>
      </div>
    </div>"""

    # ── Gap analysis section (CLA-framed) ────────────────────────────────────
    if not gap_areas:
        gap_html = ('<div style="background:rgba(30,190,139,0.08);border-left:4px solid #1EBE8B;'
                    'border-radius:8px;padding:14px 18px;font-size:13px;color:#065F46;margin-bottom:28px;">'
                    '<strong>No gaps identified.</strong> This athlete is meeting all current thresholds.</div>')
    else:
        by_family = {}
        for g in gap_areas:
            by_family.setdefault(g["family"], []).append(g)

        gap_cards = ""
        for family in FAMILY_ORDER:
            if family not in by_family:
                continue
            fm   = FAMILY_META.get(family, {"col": "#2D323B", "icon": "&#9632;"})
            col  = fm["col"]
            icon = fm["icon"]
            items = by_family[family]
            area_cards = ""
            for g in items:
                d2_chips = "".join(
                    f'<span style="font-size:11px;background:{col}14;border:1px solid {col}30;'
                    f'border-radius:999px;padding:2px 10px;color:{col};font-weight:600;">{esc(q)}</span>'
                    for q in g["d2_focus"]
                )
                gap_lbl_html = (
                    f'<span style="font-size:11px;font-weight:700;color:#7A5800;'
                    f'background:rgba(240,168,46,0.12);border:1px solid rgba(240,168,46,0.28);'
                    f'border-radius:999px;padding:2px 10px;">'
                    f'{esc(g["gap_label"])}</span>'
                ) if g["gap_label"] else ""

                # Close-to-levelling nudge
                close_nudge = ""
                if g.get("close_to_next"):
                    close_nudge = (
                        '<div style="background:rgba(30,190,139,0.08);border-left:3px solid #1EBE8B;'
                        'border-radius:0 8px 8px 0;padding:10px 12px;margin:10px 0;font-size:12px;color:#065F46;line-height:1.5;">'
                        '<strong>&#9650; Close to levelling up</strong> — this athlete is within striking distance of the next threshold. '
                        'Consider offering a self-test attempt at the next level as motivation.'
                        '</div>'
                    )

                # Game suggestions
                games_list = g.get("athlete_games", [])
                if games_list:
                    game_tags = "".join(
                        f'<span style="font-size:11px;font-weight:600;background:#2D323B;color:#F0A82E;'
                        f'border-radius:6px;padding:3px 10px;white-space:nowrap;">{esc(gm)}</span>'
                        for gm in games_list
                    )
                    games_html = (
                        f'<div style="margin-top:10px;">'
                        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                        f'letter-spacing:0.06em;color:#6E737B;margin-bottom:6px;">Self-test opportunities</div>'
                        f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{game_tags}</div>'
                        f'</div>'
                    )
                else:
                    games_html = ""

                # Resource filter suggestion
                tag = g.get("resource_tag", "")
                resource_html = (
                    f'<div style="font-size:12px;color:#6E737B;margin-top:8px;">'
                    f'&#128269; Filter the game library by <strong>&ldquo;{esc(tag)}&rdquo;</strong> '
                    f'to find game options that target this area.'
                    f'</div>'
                ) if tag else ""

                area_cards += f"""
                <div style="border:1px solid #E5E7EB;border-left:3px solid {col};border-radius:8px;
                            padding:14px 16px;margin-bottom:12px;background:#fff;">
                  <div style="display:flex;align-items:flex-start;justify-content:space-between;
                              gap:8px;flex-wrap:wrap;margin-bottom:8px;">
                    <div style="font-size:13px;font-weight:700;color:#2D323B;">{esc(g['display'])}</div>
                    {gap_lbl_html}
                  </div>
                  {f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px;">{d2_chips}</div>' if d2_chips else ''}
                  <div style="font-size:12px;color:#374151;line-height:1.65;margin-bottom:4px;">
                    {esc(g['cla_constraint'])}
                  </div>
                  {close_nudge}
                  {games_html}
                  {resource_html}
                </div>"""

            gap_cards += f"""
            <div style="margin-bottom:24px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;
                          padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,0.06);">
                <div style="width:28px;height:28px;border-radius:7px;flex-shrink:0;display:flex;
                            align-items:center;justify-content:center;font-size:13px;font-weight:700;
                            color:{col};background:{col}1A;border:1px solid {col}44;">{icon}</div>
                <span style="font-size:14px;font-weight:800;color:#2D323B;">{esc(family)}</span>
              </div>
              {area_cards}
            </div>"""

        gap_html = gap_cards

    # ── Tracking well section ─────────────────────────────────────────────────
    if tracking_well:
        tw_items = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;padding:7px 0;'
            f'border-bottom:1px solid rgba(0,0,0,0.04);">'
            f'<span style="font-size:15px;color:#1EBE8B;">&#10003;</span>'
            f'<span style="font-size:13px;font-weight:600;color:#2D323B;flex:1;">{esc(t["display"])}</span>'
            f'<span style="font-size:12px;color:#6E737B;">{t["score"]}{"↓" if t["lower"] else ""}</span>'
            f'</div>'
            for t in tracking_well
        )
        tracking_well_html = f"""
        <div style="display:flex;align-items:center;gap:0;margin-bottom:10px;">
          <div style="width:3px;height:18px;background:#1EBE8B;border-radius:2px;margin-right:10px;"></div>
          <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Tracking Well</span>
        </div>
        <div style="background:rgba(30,190,139,0.06);border:1px solid rgba(30,190,139,0.20);
                    border-radius:10px;padding:12px 16px;margin-bottom:28px;">
          {tw_items}
        </div>"""
    else:
        tracking_well_html = ""

    # ── S&C footnote (consolidated, at bottom) ────────────────────────────────
    sc_footnote_html = ""
    if sc_programme and gap_areas and any(g["sc_gap"] for g in gap_areas):
        sc_items = ""
        for g in gap_areas:
            if not g["sc_gap"]:
                continue
            sc_items += f"""
            <div style="margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid rgba(0,0,0,0.06);">
              <div style="font-size:12px;font-weight:700;color:#2D323B;margin-bottom:4px;">{esc(g['display'])}</div>
              <div style="font-size:11px;color:#4B5563;line-height:1.6;margin-bottom:4px;">{esc(g['sc_gap'])}</div>
              {('<div style="font-size:11px;color:#6E737B;line-height:1.6;font-style:italic;">' + esc(g['sc_programme']) + '</div>') if g['sc_programme'] else ''}
            </div>"""
        sc_footnote_html = f"""
        <div style="margin-top:32px;">
          <div style="display:flex;align-items:center;gap:0;margin-bottom:10px;">
            <div style="width:3px;height:18px;background:#6E737B;border-radius:2px;margin-right:10px;"></div>
            <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#6E737B;">S&amp;C Reference — if running a supplementary programme</span>
          </div>
          <div style="background:rgba(110,115,123,0.05);border:1px solid rgba(110,115,123,0.15);
                      border-radius:10px;padding:14px 16px;">
            <p style="font-size:12px;color:#6E737B;margin:0 0 12px;line-height:1.6;">
              The areas below represent movement qualities where physical conditioning can support
              game-based development. These are a supplementary reference — the primary recommendation
              is to create the right game environment first.
            </p>
            {sc_items}
          </div>
        </div>"""

    # ── Page layout ───────────────────────────────────────────────────────────
    athlete_meta = f"#{num} · " if num else ""
    athlete_meta += f"{sport} · " if sport else ""
    athlete_meta += f"Latest session: {esc(latest_date)}" if latest_date else "No sessions recorded"

    if overall_imp is not None:
        _oi_sign  = "+" if overall_imp >= 0 else ""
        _oi_col   = "#1EBE8B" if overall_imp >= 0 else "#F87171"
        _oi_arrow = "&#9650;" if overall_imp >= 0 else "&#9660;"
        overall_imp_badge = (
            f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;'
            f'font-weight:700;color:{_oi_col};background:rgba(255,255,255,0.08);'
            f'border:1px solid {_oi_col}44;border-radius:999px;padding:3px 10px;margin-top:6px;">'
            f'{_oi_arrow} {_oi_sign}{overall_imp:.1f}% overall since first session</span>'
        )
    else:
        overall_imp_badge = ""

    body = f"""
    <div class="container" style="max-width:860px;">

      <!-- Hero banner -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:28px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                        border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                        justify-content:center;font-size:20px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9650;</div>
            <div>
              <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
                          color:rgba(240,168,46,0.80);margin-bottom:3px;">Adaptability Progress Report</div>
              <div style="font-size:22px;font-weight:800;color:#FFFFFF;line-height:1.2;">{name}</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:4px;">{athlete_meta}</div>
              {overall_imp_badge}
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            <a href="/coach/participants/{athlete['id']}"
               style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.70);text-decoration:none;
                      padding:6px 14px;border:1px solid rgba(255,255,255,0.20);border-radius:20px;"
               onmouseover="this.style.background='rgba(255,255,255,0.1)'"
               onmouseout="this.style.background=''">&larr; Back to Profile</a>
            <button onclick="window.print()"
                    style="font-size:12px;font-weight:700;color:#2D323B;background:#F0A82E;
                           border:none;border-radius:20px;padding:6px 16px;cursor:pointer;">
              &#9113; Print Report</button>
          </div>
        </div>
      </div>

      <!-- Latest Scores -->
      <div style="display:flex;align-items:center;gap:0;margin-bottom:14px;">
        <div style="width:3px;height:18px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Latest Scores</span>
      </div>
      {score_table}

      <!-- Development Focus -->
      <div style="display:flex;align-items:center;gap:0;margin-bottom:6px;">
        <div style="width:3px;height:18px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">
          Development Focus{"" if has_thresholds else " — no thresholds set"}
        </span>
      </div>
      <p style="font-size:13px;color:#6E737B;margin:0 0 16px;line-height:1.5;">
        {"Areas below the next level threshold — game environment and self-test suggestions to guide development." if has_thresholds else "Once thresholds are set, only areas below threshold will appear here."}
      </p>
      {gap_html}

      {tracking_well_html}

      {sc_footnote_html}

      <div style="border-top:1px solid #E5E7EB;margin-top:32px;padding-top:12px;
                  font-size:11px;color:#9CA3AF;text-align:center;">
        JAG Athlete Adaptability Programme &nbsp;&middot;&nbsp; {esc(name)} &nbsp;&middot;&nbsp; Generated {today}
      </div>
    </div>

    <style>
    @media print {{
      .btn, nav, header {{ display: none !important; }}
      body {{ background: #fff; }}
      .container {{ padding-top: 0 !important; }}
    }}
    </style>"""

    return layout(f"Adaptability Progress Report — {athlete.get('name','Athlete')}", body, user=coach, active_nav="progress")


# ─────────────────────────────────────────────────────────────────────────────
# Athlete-facing movement report — plain English, motivational
# ─────────────────────────────────────────────────────────────────────────────

def athlete_movement_report_page(athlete, sessions, levels_by_area, thresholds_raw):
    """
    Rebuilt athlete-facing movement report.
    CLA-informed language, Perception-Action callout, family-grouped strengths/work-ons,
    next-level self-test targets, plain-English S&C ideas.
    """
    from constants import SCORING_AREAS, SC_GAP_LANGUAGE, threshold_field_key

    name = esc(athlete.get("name", "Athlete"))
    first_name = esc(athlete.get("name", "Athlete").split()[0])
    sport = athlete.get("sport") or ""

    FAMILY_META = {
        "Balance & Postural Control": {
            "icon": "&#9651;", "colour": "#3B6BC4",
            "plain": "Balance and Postural Control",
            "tag":   "staying steady under pressure",
            "desc": "How steady you are — especially when something else is happening at the same time.",
        },
        "Explosive & Landing": {
            "icon": "&#9650;", "colour": "#F0A82E",
            "plain": "Explosive & Landing",
            "tag":   "power, force and safe landing",
            "desc": "Your ability to project force — jumping, leaping — and land safely.",
        },
        "Dynamic Locomotor": {
            "icon": "&#9654;", "colour": "#1EBE8B",
            "plain": "Dynamic Locomotor",
            "tag":   "speed and efficient movement",
            "desc": "How fast and efficiently you move — straight lines, changing direction, with or without a ball.",
        },
        "Perceptual-Motor Speed": {
            "icon": "&#9673;", "colour": "#D4622F",
            "plain": "Perceptual-Motor Speed",
            "tag":   "reading the game and reacting",
            "desc": "Your ability to pick up movement cues and respond — before your brain has time to think.",
        },
    }

    # ── Build thresholds lookup (game_key, field_key, level) → value ──────────
    thresh_by_level = {}
    for row in (thresholds_raw or []):
        thresh_by_level[(row["game_key"], row["field_key"], row["level"])] = row["threshold_value"]

    # Also flat lookup for gap detection
    thresholds_flat = {}
    for row in (thresholds_raw or []):
        thresholds_flat[(row["game_key"], row["field_key"])] = row["threshold_value"]

    # ── Classify each area ────────────────────────────────────────────────────
    well = []    # strengths
    focus = []   # work-ons
    no_data = []

    for area in SCORING_AREAS:
        gk = area["game_key"]
        fk = area.get("field_key")
        stored = threshold_field_key(area)
        lang = SC_GAP_LANGUAGE.get((gk, stored)) or SC_GAP_LANGUAGE.get((gk, fk))
        if not lang:
            continue

        ach = (levels_by_area or {}).get((gk, stored or "")) or (levels_by_area or {}).get((gk, fk or ""))
        current_level = ach if isinstance(ach, int) else 0

        threshold = thresholds_flat.get((gk, stored)) or thresholds_flat.get((gk, fk))
        next_level = current_level + 1
        next_threshold = (thresh_by_level.get((gk, stored, next_level))
                          or thresh_by_level.get((gk, fk, next_level)))
        lower_is_better = area.get("lower_is_better", False)

        entry = {
            "display": lang["display"],
            "family": lang["family"],
            "current_level": current_level,
            "next_level": next_level,
            "next_threshold": next_threshold,
            "lower_is_better": lower_is_better,
            "athlete_what": lang.get("athlete_what", ""),
            "athlete_why": lang.get("athlete_why", ""),
            "athlete_games": lang.get("athlete_games", []),
            "athlete_sc": lang.get("athlete_sc", ""),
            "self_test": (lang.get("athlete_games") or [""])[0],
        }

        if threshold is None:
            no_data.append(entry)
        elif current_level == 0:
            focus.append(entry)
        else:
            well.append(entry)

    # ── Synopsis ──────────────────────────────────────────────────────────────
    n_well = len(well)
    n_focus = len(focus)
    if n_well == 0 and n_focus == 0:
        synopsis = "No measurement data yet — once you've been tested your report will appear here."
    elif n_focus == 0:
        synopsis = f"You're tracking well across all your tested areas, {first_name}. Keep playing, keep challenging yourself."
    elif n_well == 0:
        synopsis = f"You've got some clear areas to grow into, {first_name}. That's a good thing — it means there's a lot of progress ahead of you."
    else:
        synopsis = (f"You're tracking well in {n_well} area{'s' if n_well != 1 else ''} "
                    f"and have {n_focus} area{'s' if n_focus != 1 else ''} to develop. "
                    f"Use this as a guide for what to work on between sessions.")

    # ── Perception-Action callout ─────────────────────────────────────────────
    pa_callout = """
    <div style="background:linear-gradient(135deg,#2D323B 0%,#3D434F 100%);border-radius:14px;
                padding:20px 24px;margin-bottom:28px;">
      <div style="font-size:12px;font-weight:700;color:#F0A82E;text-transform:uppercase;
                  letter-spacing:.06em;margin-bottom:8px;">Remember this 💡</div>
      <p style="font-size:14px;color:#fff;line-height:1.7;margin:0;">
        Whatever you're doing, movement and skill happen at the same time.
        This is called <strong style="color:#F0A82E;">Perception-Action</strong> —
        your body and senses work together, not separately.
        When you train or move at home, <strong style="color:#F0A82E;">get a ball involved</strong>.
        Even just bouncing, catching, or throwing against a wall while you move is making you better.
      </p>
    </div>"""

    # ── Family summary ────────────────────────────────────────────────────────
    family_status = {}
    for entry in well:
        fam = entry["family"]
        family_status.setdefault(fam, {"well": 0, "focus": 0})
        family_status[fam]["well"] += 1
    for entry in focus:
        fam = entry["family"]
        family_status.setdefault(fam, {"well": 0, "focus": 0})
        family_status[fam]["focus"] += 1

    family_cards = ""
    for fam, meta in FAMILY_META.items():
        counts = family_status.get(fam, {})
        fw = counts.get("well", 0)
        ff = counts.get("focus", 0)
        if fw == 0 and ff == 0:
            continue
        if ff == 0:
            tag = f'<span style="font-size:11px;font-weight:700;color:#065F46;background:rgba(30,190,139,0.12);border:1px solid rgba(30,190,139,0.28);border-radius:999px;padding:2px 10px;">Strength</span>'
        elif fw == 0:
            tag = f'<span style="font-size:11px;font-weight:700;color:#fff;background:#2D323B;border-radius:999px;padding:2px 10px;">Focus area</span>'
        else:
            tag = f'<span style="font-size:11px;font-weight:700;color:#7A5800;background:rgba(240,168,46,0.14);border:1px solid rgba(240,168,46,0.32);border-radius:999px;padding:2px 10px;">Mixed</span>'

        family_cards += f"""
        <div style="border:1px solid #E5E7EB;border-left:4px solid {meta['colour']};border-radius:0 10px 10px 0;
                    padding:14px 16px;background:#fff;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;flex-wrap:wrap;">
            <div style="width:30px;height:30px;border-radius:8px;flex-shrink:0;display:flex;
                        align-items:center;justify-content:center;font-size:14px;font-weight:700;
                        color:{meta['colour']};background:{meta['colour']}1A;border:1px solid {meta['colour']}44;">{meta['icon']}</div>
            <div>
              <div style="font-size:13px;font-weight:700;color:#2D323B;">{esc(meta['plain'])}</div>
              <div style="font-size:11px;color:{meta['colour']};font-style:italic;">{esc(meta['tag'])}</div>
            </div>
            <div style="margin-left:auto;">{tag}</div>
          </div>
          <div style="font-size:12px;color:#6B7280;margin-top:6px;">{esc(meta['desc'])}</div>
        </div>"""

    families_html = f"""
    <div style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:0;margin-bottom:12px;">
        <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
        <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Movement Families</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;">
        {family_cards}
      </div>
    </div>""" if family_cards else ""

    # ── Strengths ─────────────────────────────────────────────────────────────
    if well:
        # Group well items by family, preserving FAMILY_META order
        well_by_family = {}
        for item in well:
            well_by_family.setdefault(item["family"], []).append(item)
        well_groups_html = ""
        for fam_key, meta in FAMILY_META.items():
            items = well_by_family.get(fam_key, [])
            if not items:
                continue
            well_cards_inner = ""
            for item in items:
                well_cards_inner += f"""
                <div style="display:flex;align-items:center;gap:12px;padding:12px 14px;
                            background:#fff;border:1px solid #D1FAE5;border-radius:10px;margin-bottom:8px;">
                  <span style="font-size:18px;">&#9989;</span>
                  <div>
                    <div style="font-size:13px;font-weight:700;color:#065F46;">{esc(item['display'])}</div>
                    <div style="font-size:12px;color:#6B7280;">Level {item['current_level']} — you're tracking well here. Keep playing and pushing the level.</div>
                  </div>
                </div>"""
            well_groups_html += f"""
            <div style="margin-bottom:16px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="font-size:15px;">{meta['icon']}</span>
                <div>
                  <span style="font-size:12px;font-weight:700;color:#2D323B;">{esc(meta['plain'])}</span>
                  <span style="font-size:11px;color:{meta['colour']};font-style:italic;margin-left:6px;">({esc(meta['tag'])})</span>
                </div>
                <div style="flex:1;height:1px;background:{meta['colour']};opacity:0.25;margin-left:4px;"></div>
              </div>
              {well_cards_inner}
            </div>"""
        strengths_html = f"""
        <div style="margin-bottom:28px;">
          <div style="display:flex;align-items:center;gap:0;margin-bottom:12px;">
            <div style="width:3px;height:16px;background:#1EBE8B;border-radius:2px;margin-right:10px;"></div>
            <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Tracking Well</span>
          </div>
          {well_groups_html}
        </div>"""
    else:
        strengths_html = ""

    # ── Focus areas ───────────────────────────────────────────────────────────
    def _focus_card(item):
        # Next level self-test tip
        nt = item["next_threshold"]
        direction = "or lower" if item["lower_is_better"] else "or more"
        if nt is not None:
            test_tip = (f'<div style="background:rgba(240,168,46,0.10);border:1px solid rgba(240,168,46,0.32);'
                        f'border-radius:8px;padding:10px 14px;margin-top:10px;">'
                        f'<div style="font-size:11px;font-weight:700;color:#C07C00;margin-bottom:4px;">&#127919; Self-Test Challenge</div>'
                        f'<div style="font-size:12px;color:#2D323B;line-height:1.6;">'
                        f'Try the <strong>{esc(item["self_test"])}</strong> self-test. '
                        f'Level {item["next_level"]} target is <strong>{nt} {direction}</strong>. '
                        f'Do it once normally, then try to hit that number — see how close you are.'
                        f'</div></div>')
        else:
            games_list = " · ".join(item["athlete_games"])
            test_tip = (f'<div style="font-size:12px;color:#6B7280;margin-top:8px;">'
                        f'<strong>Games to try:</strong> {esc(games_list)}</div>') if games_list else ""

        sc_html = ""
        if item["athlete_sc"]:
            sc_html = (f'<div style="margin-top:10px;background:#FFFBEB;border-left:3px solid #F0A82E;'
                       f'border-radius:0 6px 6px 0;padding:10px 12px;font-size:12px;color:#78350F;line-height:1.6;">'
                       f'<strong>💪 If you\'re doing gym work:</strong> {esc(item["athlete_sc"])}</div>')

        return f"""
        <div style="border:1px solid #E5E7EB;border-radius:12px;padding:16px 18px;margin-bottom:14px;background:#fff;">
          <div style="font-size:14px;font-weight:800;color:#2D323B;margin-bottom:4px;">{esc(item['display'])}</div>
          <div style="font-size:12px;color:#374151;line-height:1.6;margin-bottom:6px;">{esc(item['athlete_what'])}</div>
          <div style="font-size:12px;color:#6B7280;line-height:1.5;font-style:italic;margin-bottom:4px;">{esc(item['athlete_why'])}</div>
          {test_tip}
          {sc_html}
        </div>"""

    if focus:
        # Group focus items by family, preserving FAMILY_META order
        focus_by_family = {}
        for item in focus:
            focus_by_family.setdefault(item["family"], []).append(item)
        focus_groups_html = ""
        for fam_key, meta in FAMILY_META.items():
            items = focus_by_family.get(fam_key, [])
            if not items:
                continue
            focus_groups_html += f"""
            <div style="margin-bottom:20px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span style="font-size:15px;">{meta['icon']}</span>
                <div>
                  <span style="font-size:12px;font-weight:700;color:#2D323B;">{esc(meta['plain'])}</span>
                  <span style="font-size:11px;color:{meta['colour']};font-style:italic;margin-left:6px;">({esc(meta['tag'])})</span>
                </div>
                <div style="flex:1;height:1px;background:{meta['colour']};opacity:0.25;margin-left:4px;"></div>
              </div>
              {"".join(_focus_card(item) for item in items)}
            </div>"""
        focus_html = f"""
        <div style="margin-bottom:28px;">
          <div style="display:flex;align-items:center;gap:0;margin-bottom:14px;">
            <div style="width:3px;height:16px;background:#F0A82E;border-radius:2px;margin-right:10px;"></div>
            <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:#2D323B;">Development Areas</span>
          </div>
          {focus_groups_html}
        </div>"""
    elif well:
        focus_html = """
        <div style="background:#D1FAE5;border-radius:12px;padding:20px 24px;margin-bottom:28px;text-align:center;">
          <div style="font-size:22px;margin-bottom:6px;">🏆</div>
          <div style="font-size:14px;font-weight:700;color:#065F46;">Above threshold in all tested areas — keep pushing the next level!</div>
        </div>"""
    else:
        focus_html = """
        <div class="card" style="text-align:center;padding:32px;">
          <p style="color:#6B7280;margin:0;">No measurement results yet — once you've been tested your report will show here.</p>
        </div>"""

    sport_line = f" &middot; {esc(sport)}" if sport else ""
    body = f"""
    <div class="container" style="max-width:700px;padding-bottom:48px;">

      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:24px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                        border:1.5px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                        justify-content:center;font-size:20px;color:#F0A82E;flex-shrink:0;font-weight:700;">&#9654;</div>
            <div>
              <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;
                          color:rgba(240,168,46,0.80);margin-bottom:2px;">Movement Report</div>
              <div style="font-size:20px;font-weight:800;color:#FFFFFF;line-height:1.2;">{name}</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.50);margin-top:2px;">Athlete Adaptability Programme{sport_line}</div>
            </div>
          </div>
          <a href="/athlete"
             style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.65);text-decoration:none;
                    padding:5px 12px;border-radius:20px;border:1px solid rgba(255,255,255,0.20);
                    background:rgba(255,255,255,0.08);white-space:nowrap;align-self:flex-start;"
             onmouseover="this.style.background='rgba(255,255,255,0.15)'"
             onmouseout="this.style.background='rgba(255,255,255,0.08)'">&larr; Dashboard</a>
        </div>
        <!-- Synopsis -->
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.10);
                    font-size:13px;color:rgba(255,255,255,0.80);line-height:1.7;">{esc(synopsis)}</div>
      </div>

      {pa_callout}
      {families_html}
      {strengths_html}
      {focus_html}

    </div>

    <style>
    @media print {{
      .btn, nav, header {{ display: none !important; }}
      body {{ background: #fff; }}
      .container {{ padding-top: 0 !important; }}
    }}
    </style>"""

    return layout("My Movement Report", body, user=athlete, active_nav="dashboard")



# ─────────────────────────────────────────────────────────────────────────────
# Group Next Steps Report — practitioner session planning guide
# ─────────────────────────────────────────────────────────────────────────────

def group_next_steps_page(coach, group, athletes_with_levels, thresholds_raw, game_resources=None):
    """
    5-week session planning guide for a group post-testing.
    Analyses group-level gaps and strengths across SCORING_AREAS, calls out
    outliers, and generates a suggested rotation of programme games + test spaces.
    """
    from constants import SCORING_AREAS, SC_GAP_LANGUAGE, threshold_field_key
    import statistics

    group_name = esc(group["name"] if isinstance(group, dict) else group["name"])
    group_id = group["id"] if isinstance(group, dict) else group["id"]
    today = __import__("datetime").date.today().strftime("%-d %B %Y")
    n_athletes = len(athletes_with_levels)

    if n_athletes == 0:
        body = f"""
        <div class="page-head">
          <div><h1>{group_name} — Next Steps</h1></div>
          <a class="btn btn-ghost" href="/coach/progress">&larr; Reports</a>
        </div>
        <div class="card"><p class="muted">No athletes in this group yet.</p></div>"""
        return layout(f"{group_name} — Next Steps", body, user=coach, active_nav="dashboard")

    # ── Build thresholds lookup ───────────────────────────────────────────────
    thresholds = {}
    for row in (thresholds_raw or []):
        thresholds[(row["game_key"], row["field_key"])] = row["threshold_value"]

    game_resources = game_resources or {}

    # ── Analyse each area across the group ───────────────────────────────────
    area_analysis = []
    for area in SCORING_AREAS:
        gk = area["game_key"]
        fk = area.get("field_key")
        stored = threshold_field_key(area)
        area_key = (gk, stored)
        lang = SC_GAP_LANGUAGE.get(area_key) or SC_GAP_LANGUAGE.get((gk, fk))
        if not lang:
            continue

        threshold = thresholds.get(area_key) or thresholds.get((gk, fk))
        lower_is_better = area.get("lower_is_better", False)

        athlete_levels = []
        below_threshold = []
        above_threshold = []

        for ath in athletes_with_levels:
            lvl = ath["levels"].get((gk, stored or fk or ""), 0)
            athlete_levels.append((ath["name"], ath.get("athlete_number") or "", lvl))
            if threshold is not None:
                # We don't have raw scores here — use level as proxy
                # Level 0 = gap, Level 1+ = above baseline
                if lvl == 0:
                    below_threshold.append(ath["name"])
                else:
                    above_threshold.append(ath["name"])

        if not athlete_levels:
            continue

        levels_only = [x[2] for x in athlete_levels]
        try:
            modal_level = max(set(levels_only), key=levels_only.count)
        except Exception:
            modal_level = 0

        n_below = len(below_threshold)
        n_above = len(above_threshold)
        pct_gap = (n_below / n_athletes * 100) if n_athletes else 0

        # Outliers: athletes 2+ levels above modal
        advanced_outliers = [n for n, _, l in athlete_levels if l >= modal_level + 2]
        # Athletes significantly behind
        behind_outliers = [n for n, _, l in athlete_levels if modal_level >= 2 and l == 0]

        gk_resources = game_resources.get(gk, {})
        area_analysis.append({
            "key": area_key,
            "display": lang["display"],
            "family": lang["family"],
            "modal_level": modal_level,
            "pct_gap": pct_gap,
            "n_below": n_below,
            "n_above": n_above,
            "athlete_levels": athlete_levels,
            "advanced_outliers": advanced_outliers,
            "behind_outliers": behind_outliers,
            "programme_games": gk_resources.get("programme", [])[:3],
            "test_games": gk_resources.get("test", [])[:3],
        })

    # Sort: gaps first (highest pct_gap), then strengths
    gap_areas = [a for a in area_analysis if a["pct_gap"] >= 50]
    strength_areas = [a for a in area_analysis if a["pct_gap"] < 30]
    mixed_areas = [a for a in area_analysis if 30 <= a["pct_gap"] < 50]

    gap_areas.sort(key=lambda x: -x["pct_gap"])
    strength_areas.sort(key=lambda x: x["pct_gap"])

    # ── Group snapshot section ────────────────────────────────────────────────
    def area_bar(pct):
        col = "#EF4444" if pct >= 60 else "#F59E0B" if pct >= 30 else "#10B981"
        return (f'<div style="height:6px;border-radius:3px;background:#F3F4F6;margin-top:4px;">'
                f'<div style="width:{pct:.0f}%;height:100%;background:{col};border-radius:3px;"></div></div>')

    snapshot_rows = ""
    for a in area_analysis:
        pct = a["pct_gap"]
        if a["modal_level"] == 0 and not thresholds:
            tag = '<span style="font-size:10px;color:#9CA3AF;">No thresholds set</span>'
        elif pct >= 50:
            tag = '<span style="font-size:10px;font-weight:700;color:#fff;background:#2D323B;border-radius:999px;padding:1px 8px;">Focus area</span>'
        elif pct < 30:
            tag = '<span style="font-size:10px;font-weight:700;color:#065F46;background:rgba(30,190,139,0.12);border:1px solid rgba(30,190,139,0.28);border-radius:999px;padding:1px 8px;">Strength</span>'
        else:
            tag = '<span style="font-size:10px;font-weight:700;color:#7A5800;background:rgba(240,168,46,0.14);border:1px solid rgba(240,168,46,0.32);border-radius:999px;padding:1px 8px;">Mixed</span>'

        lvl_chips = "".join(
            f'<span title="{esc(nm)}" style="font-size:10px;background:#F3F4F6;border-radius:999px;padding:1px 7px;color:#374151;">L{lvl}</span>'
            for nm, num, lvl in a["athlete_levels"]
        )

        snapshot_rows += f"""
        <tr style="border-bottom:1px solid #F3F4F6;">
          <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#2D323B;">{esc(a['display'])}</td>
          <td style="padding:10px 12px;">{tag}</td>
          <td style="padding:10px 12px;">
            <div style="display:flex;flex-wrap:wrap;gap:4px;">{lvl_chips}</div>
            {area_bar(pct)}
          </td>
        </tr>"""

    snapshot_html = f"""
    <div style="margin-bottom:32px;">
      <h2 style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                 color:#2D323B;margin-bottom:12px;border-left:3px solid #F0A82E;padding-left:10px;">Group Snapshot</h2>
      <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#F9FAFB;border-bottom:1px solid #E5E7EB;">
              <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;">Area</th>
              <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;">Status</th>
              <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;">Athlete levels (hover for name)</th>
            </tr>
          </thead>
          <tbody>{snapshot_rows}</tbody>
        </table>
      </div>
    </div>"""

    # ── Outlier callouts ──────────────────────────────────────────────────────
    outlier_items = ""
    for a in area_analysis:
        for nm in a["advanced_outliers"]:
            outlier_items += f"""
            <div style="display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #F3F4F6;">
              <span style="font-size:16px;">⭐</span>
              <div>
                <strong style="font-size:13px;color:#2D323B;">{esc(nm)}</strong>
                <span style="font-size:12px;color:#6B7280;"> — {esc(a['display'])}</span>
                <div style="font-size:12px;color:#374151;margin-top:2px;">
                  2+ levels ahead of the group. Consider extending constraints — make the game harder for them or use them to demonstrate to peers.
                </div>
              </div>
            </div>"""
        for nm in a["behind_outliers"]:
            outlier_items += f"""
            <div style="display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #F3F4F6;">
              <span style="font-size:16px;">🔍</span>
              <div>
                <strong style="font-size:13px;color:#2D323B;">{esc(nm)}</strong>
                <span style="font-size:12px;color:#6B7280;"> — {esc(a['display'])}</span>
                <div style="font-size:12px;color:#374151;margin-top:2px;">
                  Still at baseline while the rest of the group has progressed. Give this athlete extra reps or a simplified constraint to build confidence.
                </div>
              </div>
            </div>"""

    outliers_html = ""
    if outlier_items:
        outliers_html = f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                     color:#2D323B;margin-bottom:12px;border-left:3px solid #F0A82E;padding-left:10px;">Athletes to Watch</h2>
          <div style="background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:4px 16px;">
            {outlier_items}
          </div>
        </div>"""

    # ── 5-week session plan ───────────────────────────────────────────────────
    # Build a pool: cycle through gap areas (2x), then fill with strength/mixed
    focus_pool = (gap_areas * 2) + mixed_areas + strength_areas
    # Each session: primary focus area + one complementary (strength or mixed)
    FAMILY_COLOURS = {
        "Balance & Postural Control": "#6366F1",
        "Explosive & Landing":        "#F59E0B",
        "Dynamic Locomotor":          "#10B981",
        "Perceptual-Motor Speed":     "#EF4444",
    }

    sessions_html = ""
    used_primaries = []
    comp_pool = strength_areas + mixed_areas

    for week in range(1, 6):
        # Pick primary: rotate through gap areas, avoid repeating last session's primary
        primary = None
        for a in focus_pool:
            if a not in used_primaries[-1:]:
                primary = a
                focus_pool = [x for x in focus_pool if x is not a or focus_pool.index(x) > 0]
                break
        if not primary and area_analysis:
            primary = area_analysis[(week - 1) % len(area_analysis)]
        if not primary:
            continue
        used_primaries.append(primary)

        # Complementary: pick from strength/mixed, different family if possible
        comp = None
        for c in comp_pool:
            if c is not primary and c.get("family") != primary.get("family"):
                comp = c
                break
        if not comp:
            for c in comp_pool:
                if c is not primary:
                    comp = c
                    break
        # Rotate comp pool
        if comp_pool:
            comp_pool = comp_pool[1:] + comp_pool[:1]

        # Build game cards for this session
        def game_card(area, is_primary=True):
            col = FAMILY_COLOURS.get(area["family"], "#6366F1")
            badge = "Primary Focus" if is_primary else "Complementary"
            if is_primary:
                badge_style = "font-size:11px;font-weight:700;color:#2D323B;background:#F0A82E;border-radius:999px;padding:1px 9px;"
            else:
                badge_style = "font-size:11px;font-weight:700;color:rgba(255,255,255,0.80);background:#2D323B;border-radius:999px;padding:1px 9px;"
            fam_plain = FAMILY_META.get(area["family"], {}).get("plain", area["family"])
            lvl_note = f"Group modal level: L{area['modal_level']}"
            adv = ", ".join(area["advanced_outliers"])
            adv_note = (f'<div style="font-size:11px;color:#6366F1;margin-top:4px;">&#11088; {esc(adv)} — extend constraints</div>'
                        if adv else "")
            behind = ", ".join(area["behind_outliers"])
            behind_note = (f'<div style="font-size:11px;color:#7A5800;margin-top:4px;">&#128269; {esc(behind)} — simplify or extra reps</div>'
                           if behind else "")
            pg = area.get("programme_games", [])
            if pg:
                pg_chips = "".join(
                    f'<span style="font-size:11px;font-weight:600;background:rgba(240,168,46,0.12);color:#7A5800;'
                    f'border-radius:999px;padding:2px 10px;border:1px solid rgba(240,168,46,0.25);">{esc(g)}</span>'
                    for g in pg
                )
                pg_html = (f'<div style="margin-bottom:6px;">'
                           f'<span style="font-size:10px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:.05em;">Programme games</span>'
                           f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px;">{pg_chips}</div>'
                           f'</div>')
            else:
                pg_html = '<div style="font-size:12px;color:#9CA3AF;margin-bottom:6px;">No programme games tagged for this area yet.</div>'
            return f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:3px solid {col};
                        border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:10px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
                <span style="{badge_style}">{badge}</span>
                <span style="font-size:13px;font-weight:700;color:#2D323B;">{esc(area['display'])}</span>
                <span style="font-size:11px;color:{col};font-style:italic;">{esc(fam_plain)}</span>
              </div>
              {pg_html}
              <div style="font-size:11px;color:#9CA3AF;">{lvl_note}</div>
              {adv_note}{behind_note}
            </div>"""

        primary_card = game_card(primary, True)
        comp_card = game_card(comp, False) if comp else ""

        # Optional test games — from primary area's tagged test resources
        test_games = primary.get("test_games", [])
        if test_games:
            tg_chips = "".join(
                f'<span style="font-size:11px;font-weight:600;background:rgba(45,50,59,0.07);color:#2D323B;'
                f'border-radius:999px;padding:2px 10px;border:1px solid rgba(45,50,59,0.15);">{esc(g)}</span>'
                for g in test_games
            )
            test_html = (f'<div style="background:rgba(45,50,59,0.04);border:1px solid rgba(45,50,59,0.12);'
                         f'border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
                         f'<div style="font-size:11px;font-weight:700;color:#2D323B;margin-bottom:6px;">&#128203; Optional Test Games</div>'
                         f'<div style="display:flex;flex-wrap:wrap;gap:5px;">{tg_chips}</div>'
                         f'<div style="font-size:11px;color:#6B7280;margin-top:6px;">Run alongside sessions for informal self-testing.</div>'
                         f'</div>')
        else:
            test_html = ""

        sessions_html += f"""
        <div style="margin-bottom:24px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#2D323B;
                        display:flex;align-items:center;justify-content:center;
                        font-size:13px;font-weight:800;color:#F0A82E;flex-shrink:0;">{week}</div>
            <h3 style="margin:0;font-size:15px;font-weight:700;color:#2D323B;">Week {week}</h3>
          </div>
          {primary_card}
          {comp_card}
          {test_html}
        </div>"""

    plan_html = f"""
    <div style="margin-bottom:32px;">
      <h2 style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                 color:#2D323B;margin-bottom:4px;border-left:3px solid #F0A82E;padding-left:10px;">5-Week Session Guide</h2>
      <p style="font-size:12px;color:#6B7280;margin-bottom:16px;padding-left:13px;">
        This is a suggestion — use your judgement and adjust based on what you see in the session.
      </p>
      {sessions_html}
    </div>"""

    if not area_analysis:
        plan_html = '<div class="card"><p class="muted">No measurement data or thresholds set yet — complete a testing round to generate a session plan.</p></div>'

    # ── Family summary cards ──────────────────────────────────────────────────
    FAMILY_META = {
        "Balance & Postural Control": {"icon": "&#9651;", "colour": "#3B6BC4",
                                       "plain": "Balance and Postural Control",
                                       "tag": "staying steady under pressure"},
        "Explosive & Landing":        {"icon": "&#9650;", "colour": "#F0A82E",
                                       "plain": "Explosive & Landing",
                                       "tag": "power, force and safe landing"},
        "Dynamic Locomotor":          {"icon": "&#9654;", "colour": "#1EBE8B",
                                       "plain": "Dynamic Locomotor",
                                       "tag": "speed and efficient movement"},
        "Perceptual-Motor Speed":     {"icon": "&#9673;", "colour": "#D4622F",
                                       "plain": "Perceptual-Motor Speed",
                                       "tag": "reading the game and reacting"},
    }
    family_buckets = {}
    for a in area_analysis:
        fam = a["family"]
        family_buckets.setdefault(fam, {"gap": [], "strength": [], "mixed": []})
        if a["pct_gap"] >= 50:
            family_buckets[fam]["gap"].append(a["display"])
        elif a["pct_gap"] < 30:
            family_buckets[fam]["strength"].append(a["display"])
        else:
            family_buckets[fam]["mixed"].append(a["display"])

    family_cards_html = ""
    for fam, meta in FAMILY_META.items():
        b = family_buckets.get(fam, {})
        gaps = b.get("gap", [])
        strengths = b.get("strength", [])
        mixed = b.get("mixed", [])
        if not gaps and not strengths and not mixed:
            continue
        if gaps and not strengths:
            status_tag = ('<span style="font-size:11px;font-weight:700;color:#fff;'
                          'background:#2D323B;border-radius:999px;padding:2px 10px;">Focus area</span>')
        elif strengths and not gaps:
            status_tag = ('<span style="font-size:11px;font-weight:700;color:#065F46;'
                          'background:rgba(30,190,139,0.12);border:1px solid rgba(30,190,139,0.28);border-radius:999px;padding:2px 10px;">Strength</span>')
        else:
            status_tag = ('<span style="font-size:11px;font-weight:700;color:#7A5800;'
                          'background:rgba(240,168,46,0.14);border:1px solid rgba(240,168,46,0.32);border-radius:999px;padding:2px 10px;">Mixed</span>')

        detail_parts = []
        if gaps:
            detail_parts.append(
                f'<span style="font-size:11px;color:#6B7280;">'
                f'<span style="color:#B91C1C;font-weight:700;">&#9660;</span> '
                f'{", ".join(gaps)}</span>')
        if strengths:
            detail_parts.append(
                f'<span style="font-size:11px;color:#6B7280;">'
                f'<span style="color:#1EBE8B;font-weight:700;">&#10003;</span> '
                f'{", ".join(strengths)}</span>')
        if mixed:
            detail_parts.append(
                f'<span style="font-size:11px;color:#6B7280;">'
                f'<span style="color:#F0A82E;font-weight:700;">~</span> '
                f'{", ".join(mixed)}</span>')

        family_cards_html += f"""
        <div style="border:1px solid #E5E7EB;border-left:4px solid {meta['colour']};
                    border-radius:0 10px 10px 0;padding:14px 16px;background:#fff;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
            <span style="font-size:18px;">{meta['icon']}</span>
            <div style="flex:1;min-width:0;">
              <div style="font-size:13px;font-weight:700;color:#2D323B;">{esc(meta['plain'])}</div>
              <div style="font-size:11px;color:{meta['colour']};font-style:italic;">{esc(meta['tag'])}</div>
            </div>
            {status_tag}
          </div>
          <div style="margin-top:8px;display:flex;flex-direction:column;gap:3px;">
            {"".join(f"<div>{p}</div>" for p in detail_parts)}
          </div>
        </div>"""

    families_section = f"""
    <div style="margin-bottom:28px;">
      <h2 style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                 color:#2D323B;margin-bottom:12px;border-left:3px solid #F0A82E;padding-left:10px;">
        Movement Families Overview</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">
        {family_cards_html}
      </div>
    </div>""" if family_cards_html else ""

    body = f"""
    <div style="max-width:900px;margin:0 auto;padding:32px 16px 48px;">

      <!-- Hero banner -->
      <div style="background:linear-gradient(135deg,#2D323B 0%,#3d4350 100%);border-radius:16px;
                  padding:24px 28px;margin-bottom:24px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;
                    gap:16px;flex-wrap:wrap;">
          <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:48px;height:48px;border-radius:13px;background:rgba(240,168,46,0.18);
                        border:1px solid rgba(240,168,46,0.35);display:flex;align-items:center;
                        justify-content:center;font-size:20px;font-weight:700;color:#F0A82E;
                        flex-shrink:0;">&#9654;</div>
            <div>
              <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;
                          color:rgba(255,255,255,0.45);margin-bottom:3px;">Next Steps Report</div>
              <h1 style="font-size:22px;font-weight:800;color:#FFFFFF;margin:0 0 3px;">{group_name}</h1>
              <p style="font-size:12px;color:rgba(255,255,255,0.45);margin:0;">{n_athletes} athletes &middot; Generated {today}</p>
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            <a href="/coach/progress" class="btn btn-ghost btn-sm"
               style="color:rgba(255,255,255,0.70);border-color:rgba(255,255,255,0.25);">&larr; Reports</a>
            <button onclick="window.print()" class="btn btn-primary btn-sm">&#128438; Print</button>
          </div>
        </div>
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.10);
                    font-size:13px;color:rgba(255,255,255,0.65);line-height:1.6;">
          Based on your group's latest measurement results, this report suggests a 5-week session focus —
          mixing development areas with strengths so sessions stay engaging.
          Each week shows recommended programme games and optional test games to run alongside.
          <strong style="color:#F0A82E;">Adjust freely</strong> — this is a guide, not a prescription.
        </div>
      </div>

      {families_section}
      {snapshot_html}
      {outliers_html}
      {plan_html}
    </div>

    <style>
    @media print {{
      .btn, nav, header {{ display: none !important; }}
      body {{ background: #fff; }}
    }}
    </style>"""

    return layout(f"Next Steps — {group_name}", body, user=coach, active_nav="dashboard")
