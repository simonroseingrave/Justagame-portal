"""HTML rendering. Pages are built with small Python functions rather than
a templating engine, so there is no extra dependency to install. All
user-supplied text is passed through `esc()` (html.escape) before being
placed in markup to avoid HTML/script injection.
"""
import re as _re
from html import escape as esc

from constants import (
    APP_NAME,
    MEASUREMENT_GAMES,
    SPORT_SPECIFIC_GAMES,
    all_measurement_games,
)


def layout(title, body, user=None, flash=None, active_nav=None):
    nav = ""
    if user:
        if user["role"] == "coach":
            links = [("/coach", "Dashboard", "dashboard")]
            if user.get("is_admin"):
                links.append(("/coach/participants/new", "Add Participant", "new_participant"))
            links.append(("/coach/session", "Record Session", "session"))
            links.append(("/coach/resources", "Resources", "resources"))
            if user.get("is_admin"):
                links.append(("/coach/coaches", "Coaches", "coaches"))
            links.append(("/coach/progress", "Achievement Statistics", "progress"))
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
              <a href="/account/password" class="btn btn-ghost btn-sm">My Account</a>
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
  <link rel="stylesheet" href="/static/css/style.css?v=18" />
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
        <p class="muted">Log in to view your progress, or manage athletes as a coach.</p>
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
          <p><strong>Coach:</strong> coach@justagame.co.nz / CoachDemo123!</p>
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
          This app doesn't send reset emails — instead, your coach can issue
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
        <span style="font-size:14px;font-weight:700;color:#2D323B;">{esc(game['name'])}</span>
        <span id="mg-toggle-{game_key}"
              style="font-size:11px;color:#F0A82E;font-weight:700;letter-spacing:0.05em;">&#9650; COLLAPSE</span>
      </div>
      <div id="{body_id}" style="padding:12px 14px 14px;background:#fafafa;border-top:1px solid #DDE0E3;">
        <div class="mg-field-grid">{fields_html}{computed_html}</div>
      </div>
    </div>
    """


def measurement_games_form(participant_id):
    """The coach-facing entry form for recording a Measurement Games test
    session -- one date, with a fieldset per game grouped under each
    section. Each field has its own quick-save button; the session is
    created lazily on the first save. A bulk-submit fallback is also
    available via the full form."""
    # Build game chip list and sections HTML together
    all_games_for_chips = []
    for section in MEASUREMENT_GAMES:
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

    sections_html = chip_panel_html + "".join(f"""
    <div class="mg-section" style="margin-bottom:24px;">
      <div style="border-left:4px solid #F0A82E;padding-left:10px;margin-bottom:12px;">
        <h4 style="margin:0;font-size:15px;font-weight:700;color:var(--jag-navy);">{esc(section['section'])}</h4>
      </div>
      {''.join(_measurement_game_fieldset(g) for g in section['games'])}
    </div>
    """ for section in MEASUREMENT_GAMES)

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

      function getDate() {{
        var d = document.getElementById('mg-date').value;
        return d || new Date().toISOString().slice(0, 10);
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
        var resp = await fetch(baseUrl + '/start', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
          body: 'date=' + encodeURIComponent(getDate()),
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
      <p class="muted">Enter a value and click <strong>&#10003; Save</strong> next to each field.
      The Skipping Rope Sprint average is calculated automatically from Time 1/2/3.</p>
      <label for="mg-date">Session date</label>
      <input type="date" id="mg-date" name="date" style="max-width:200px; margin-bottom:16px;" />
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


def _calc_improvement_pct(measurement_sessions):
    """Average % improvement across all fields, first vs latest session.
    Returns None if fewer than 2 sessions."""
    if len(measurement_sessions) < 2:
        return None
    latest = measurement_sessions[0]
    first  = measurement_sessions[-1]
    improvements = []
    for game in all_measurement_games():
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


def participant_dashboard(user, measurement_sessions):
    from constants import get_improvement_level
    first_name = esc(user['name'].split(' ')[0])
    # Avatar
    name = user['name']
    parts = name.strip().split()
    inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
    sport = esc(user.get('sport') or '')
    programme = esc(user.get('programme') or '')
    session_count = len(measurement_sessions)
    # Improvement-based level
    imp_pct = _calc_improvement_pct(measurement_sessions)
    lvl = get_improvement_level(imp_pct)
    bar_pct = int(lvl['progress'] * 100)
    if lvl['baseline_only']:
        next_txt = ('<span style="font-size:12px;color:var(--jag-muted);">'
                    'Baseline recorded &mdash; your progress unlocks after your next session</span>')
        bar_marker = ('<div style="width:10px;height:10px;border-radius:50%;background:var(--jag-green);'
                      'margin-top:-1px;"></div>')
        bar_inner = bar_marker
    elif lvl['next_name']:
        to_next = lvl['next_threshold'] - (imp_pct or 0)
        next_txt = (f'<span style="font-size:12px;color:var(--jag-muted);">'
                    f'{to_next:.1f}% avg improvement to {esc(lvl["next_name"])}</span>')
        bar_inner = (f'<div style="background:var(--jag-green);width:{bar_pct}%;height:100%;'
                     f'border-radius:999px;transition:width 0.6s ease;"></div>')
    else:
        next_txt = '<span style="font-size:12px;color:var(--jag-green);font-weight:700;">Top level reached!</span>'
        bar_inner = '<div style="background:var(--jag-green);width:100%;height:100%;border-radius:999px;"></div>'
    level_bar = f"""
    <div style="margin-top:10px;">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
        <span style="font-weight:700;font-size:14px;color:var(--jag-navy);">&#127942; {esc(lvl['name'])}</span>
        {next_txt}
      </div>
      <div style="background:var(--jag-border);border-radius:999px;height:8px;overflow:hidden;
                  display:flex;align-items:center;">
        {bar_inner}
      </div>
    </div>"""
    sport_pill = (f'<span style="font-size:12px;font-weight:600;background:{av_color}22;color:{av_color};'
                  f'border-radius:999px;padding:2px 10px;">{sport}</span>') if sport else ''
    imp_stat = (f'{imp_pct:+.1f}%' if imp_pct is not None else '—')
    body = f"""
    <div style="background:var(--jag-card);border-radius:16px;padding:24px 28px;margin-bottom:28px;
                display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;
                border:2px solid rgba(240,168,46,0.35);">
      <div style="width:68px;height:68px;border-radius:50%;background:#2D323B;display:flex;
                  align-items:center;justify-content:center;font-weight:800;font-size:24px;color:#F0A82E;
                  flex-shrink:0;box-shadow:0 4px 16px rgba(45,50,59,0.35);">{inits}</div>
      <div style="flex:1;min-width:200px;">
        <h1 style="margin:0 0 4px;font-size:24px;">Welcome back, {first_name}!</h1>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:4px;">{sport_pill}</div>
        {f'<p style="margin:0 0 4px;font-size:13px;color:var(--jag-muted);">{programme}</p>' if programme else ''}
        {level_bar}
      </div>
    </div>

    <section class="stat-row">
      <div class="card stat-card">
        <div class="stat-number">{session_count}</div>
        <div class="stat-label">Test Sessions</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{imp_stat}</div>
        <div class="stat-label">Avg Improvement</div>
      </div>
    </section>

    <h2 class="section-title">Measurement Games Results</h2>
    {measurement_games_history(measurement_sessions)}
    """
    return layout("My Dashboard", body, user=user, active_nav="dashboard")


def _athlete_tile(p, is_admin=False):
    """Render a single athlete as a clickable tile with initials avatar."""
    name = p['name']
    parts = name.strip().split()
    inits = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[0].upper()
    sport = esc(p.get('sport') or '')
    drag = '<span class="drag-handle" title="Drag to move group" style="position:absolute;top:6px;right:8px;font-size:11px;color:#bbb;line-height:1;">&#9776;</span>' if is_admin else ""
    sport_badge = (f'<span style="font-size:10px;font-weight:600;background:rgba(240,168,46,0.15);color:#CF8F1F;'
                   f'border-radius:999px;padding:2px 8px;white-space:nowrap;">{sport}</span>') if sport else ''
    return f"""<a href="/coach/participants/{p['id']}" class="athlete-tile" data-id="{p['id']}" data-sport="{esc(p.get('sport') or '')}"
      style="position:relative;display:flex;flex-direction:column;align-items:center;gap:8px;
             padding:20px 12px 16px;background:var(--jag-card);border:2px solid var(--jag-border);
             border-radius:14px;text-decoration:none;color:inherit;cursor:pointer;
             transition:box-shadow 0.18s ease,border-color 0.18s ease,transform 0.18s ease;"
      onmouseover="this.style.boxShadow='0 6px 20px rgba(0,0,0,0.13)';this.style.borderColor='#F0A82E';this.style.transform='translateY(-2px)';"
      onmouseout="this.style.boxShadow='';this.style.borderColor='var(--jag-border)';this.style.transform='';">
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
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:16px;">Save Changes</button>
      </form>
    </div>
    """
    return layout(f"Edit Group — {group['name']}", body, user=user, active_nav="dashboard")


def coach_dashboard_for(user, group_summaries, ungrouped_summaries, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    is_admin = user.get("is_admin")

    group_sections = ""
    for group, participants in group_summaries:
        count = len(participants)
        tiles_html = "".join(_athlete_tile(p, is_admin=is_admin) for p in participants)
        empty_msg = '<p class="muted" style="font-size:13px;padding:8px 0;">No athletes in this group yet.</p>'
        tiles_wrap = f'<div class="athlete-tiles-wrap" data-group-list-id="{group["id"]}" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;padding:8px 0 4px;">{tiles_html or empty_msg}</div>'
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder groups" style="color:var(--jag-muted);cursor:grab;font-size:16px;">&#9776;</span>' if is_admin else ""
        summary_link = (f'<a href="/coach/groups/{group["id"]}/achievement-summary" class="btn btn-sm" style="font-size:12px;background:var(--jag-green);color:var(--jag-navy);font-weight:600;border:none;">&#128200; Group Stats</a>'
                        f'<a href="/coach/groups/{group["id"]}/scores" class="btn btn-sm btn-ghost" style="font-size:12px;">&#128203; Scores Table</a>')
        admin_btns = f"""<a href="/coach/groups/{group['id']}/edit" class="btn btn-ghost btn-sm" style="font-size:12px;">Edit</a>
            <form method="post" action="/coach/groups/{group['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete group \\'{esc(group['name'])}\\'? Participants move to ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm" style="font-size:12px;">Delete</button>
            </form>""" if is_admin else ""
        group_sections += f"""
        <div class="group-section" data-group-id="{group['id']}" style="margin-bottom:44px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
            {folder_handle}
            <div style="border-left:4px solid var(--jag-green);padding-left:12px;flex:1;min-width:0;">
              <h2 style="margin:0;font-size:20px;font-weight:700;color:var(--jag-navy);line-height:1.2;">{esc(group['name'])}</h2>
              <span class="muted group-count" style="font-size:13px;">{count} athlete{"s" if count != 1 else ""}</span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
              {summary_link}
              {admin_btns}
            </div>
          </div>
          {tiles_wrap}
        </div>"""

    # Ungrouped section
    ug_count = len(ungrouped_summaries)
    ug_tiles = "".join(_athlete_tile(p, is_admin=is_admin) for p in ungrouped_summaries)
    ug_empty = '<p class="muted" style="font-size:13px;padding:8px 0;">No ungrouped athletes.</p>'
    ug_wrap = f'<div class="athlete-tiles-wrap" data-group-list-id="ungrouped" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;padding:8px 0 4px;">{ug_tiles or ug_empty}</div>'
    ug_label = "Athletes" if not group_summaries else "Ungrouped"
    ungrouped_section = f"""
    <div class="group-section" style="margin-bottom:44px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="border-left:4px solid var(--jag-border);padding-left:12px;">
          <h2 style="margin:0;font-size:20px;font-weight:700;color:var(--jag-muted);line-height:1.2;">{ug_label}</h2>
          <span class="muted group-count" style="font-size:13px;">{ug_count} athlete{"s" if ug_count != 1 else ""}</span>
        </div>
      </div>
      {ug_wrap}
    </div>"""

    # Collect unique sports across all participants for filter bar
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
                   background:var(--jag-green);color:var(--jag-navy);font-size:13px;cursor:pointer;font-weight:600;">
            All
          </button>
          {sport_btns}
        </div>"""
        filter_js = """
        <script>
        var activeSport = '';
        function filterSport(btn, sport) {
          activeSport = sport;
          document.querySelectorAll('#sport-filter button').forEach(function(b) {
            var isSel = (b === btn);
            b.style.background = isSel ? 'var(--jag-green)' : 'var(--jag-card)';
            b.style.color = isSel ? 'var(--jag-navy)' : 'inherit';
            b.style.borderColor = isSel ? 'var(--jag-green)' : 'var(--jag-border)';
            b.style.fontWeight = isSel ? '600' : '400';
          });
          document.querySelectorAll('.athlete-tile').forEach(function(tile) {
            var ts = tile.dataset.sport || '';
            tile.style.display = (!sport || ts === sport) ? '' : 'none';
          });
          document.querySelectorAll('.group-section').forEach(function(sec) {
            var wrap = sec.querySelector('.athlete-tiles-wrap');
            if (!wrap) return;
            var visible = Array.from(wrap.querySelectorAll('.athlete-tile')).filter(function(t){ return t.style.display !== 'none'; }).length;
            var badge = sec.querySelector('.group-count');
            if (badge) badge.textContent = visible + (visible === 1 ? ' athlete' : ' athletes');
            sec.style.display = visible === 0 ? 'none' : '';
          });
        }
        </script>"""
    else:
        filter_bar = ""
        filter_js = ""

    if not group_summaries and not ungrouped_summaries:
        content = '<p class="muted">No participants yet. Add one to get started.</p>' if is_admin else '<p class="muted">You haven\'t been assigned to a group yet. Contact an admin.</p>'
    else:
        content = f'<div id="groups-container">{group_sections}</div>{ungrouped_section}'

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
    </div>
    {create_group_form}""" if is_admin else ""

    sortable_js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.2/Sortable.min.js"></script>
    <script>
    function post(url, body) {
      fetch(url, { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: body });
    }
    var gc = document.getElementById('groups-container');
    if (gc) {
      Sortable.create(gc, {
        handle: '.folder-handle', animation: 150,
        onEnd: function() {
          var ids = Array.from(gc.querySelectorAll('.group-section[data-group-id]'))
                        .map(function(el){ return el.dataset.groupId; });
          post('/coach/groups/reorder', 'ids=' + ids.join(','));
        }
      });
    }
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
      badge.textContent = '(' + n + (n === 1 ? ' athlete' : ' athletes') + ')';
    }
    </script>""" if is_admin else ""

    if is_admin:
        subtitle = 'Viewing all participant groups &mdash; administrator access.'
    elif group_summaries:
        names = ", ".join(f'<strong>{esc(g["name"])}</strong>' for g, _ in group_summaries)
        subtitle = f'Your assigned group{"s" if len(group_summaries) > 1 else ""}: {names}'
    else:
        subtitle = 'No group assigned yet &mdash; contact an admin.'

    body = f"""
    <style>.athlete-tile {{transition:box-shadow 0.18s ease,border-color 0.18s ease,transform 0.18s ease;}}</style>
    <div style="max-width:1320px;">
    <div class="page-head">
      <div>
        <h1>Coach Dashboard</h1>
        <p class="muted">{subtitle}</p>
      </div>
    </div>
    {action_btns}
    {message_html}
    <div style="margin-top:28px;">
      {filter_bar}
      {content}
    </div>
    </div>
    {sortable_js}
    {filter_js}
    """
    return layout("Coach Dashboard", body, user=user, active_nav="dashboard")


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


def coach_participant_detail(coach, participant, measurement_sessions, groups=None, message=None):
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
    session_count = len(measurement_sessions)

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
          {sport_pill}{group_pill}
          <span style="font-size:12px;color:var(--jag-muted);">{esc(participant['email'])}</span>
        </div>
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

    <section class="stat-row">
      <div class="card stat-card">
        <div class="stat-number">{session_count}</div>
        <div class="stat-label">Test Sessions (all groups)</div>
      </div>
    </section>

    {measurement_games_form(participant['id'])}

    <h2 class="section-title">Measurement Games History</h2>
    {measurement_games_history(measurement_sessions, show_delete=True, participant_id=participant['id'])}
    """
    return layout(participant["name"], body, user=coach, active_nav="dashboard")


def participant_progress_page(coach, participant, measurement_sessions):
    """Progress page: first vs latest comparison + full trend across all sessions."""
    from constants import all_measurement_games, MEASUREMENT_GAMES

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
    for section in MEASUREMENT_GAMES:
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
            for game in all_measurement_games():
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
        for section in MEASUREMENT_GAMES:
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
    for game in all_measurement_games():
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


def group_progress_page(coach, group, participants_sessions):
    """Progress summary for a group: each measurement, each participant, first→latest.
    participants_sessions: list of (participant_dict, sessions_list)
    """
    active = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Ungrouped"

    if not active:
        body = f"""
        <div class="page-head"><div><h1>{gname} &mdash; Group Achievement Statistics</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Back</a></div>
        <div class="card"><p class="muted">No test sessions recorded for this group yet.</p></div>"""
        return layout(f"{group['name']} Progress", body, user=coach, active_nav="progress")

    # Build one table per game
    sections_html = ""
    for section in MEASUREMENT_GAMES:
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
    {sections_html}"""
    return layout(f"{group['name'] if group else 'Group'} Progress", body, user=coach, active_nav="progress")


def group_achievement_summary_page(coach, group, participants_sessions):
    """One-page collective summary: average % improvement per field across all group members."""
    # Only athletes with at least 2 sessions contribute to the averages
    active = [(p, s) for p, s in participants_sessions if len(s) >= 2]
    all_with_sessions = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Group"
    group_id = group["id"] if group else None

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
    sections_html = ""
    for section in MEASUREMENT_GAMES:
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
    {hero_card}
    {athlete_grid}
    <div style="border-left:4px solid var(--jag-green);padding-left:12px;margin-bottom:20px;">
      <h2 style="margin:0 0 2px;font-size:17px;font-weight:700;">Measurement Breakdown</h2>
      <p class="muted" style="margin:0;">Group average per field with individual athlete results</p>
    </div>
    {sections_html}"""
    return layout(f"{group['name']} Achievement Summary", body, user=coach, active_nav="progress")


def group_scores_table_page(coach, group, participants_sessions):
    """Flat table: rows = athletes, columns = every measurement field (latest session values)."""
    active = [(p, s) for p, s in participants_sessions if s]
    gname = esc(group["name"]) if group else "Group"
    group_id = group["id"] if group else None
    summary_url = f'/coach/groups/{group_id}/achievement-summary' if group_id else '/coach'

    if not active:
        body = f"""
        <div class="page-head">
          <div><h1>{gname} &mdash; Scores Table</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
        </div>
        <div class="card"><p class="muted">No test sessions recorded for this group yet.</p></div>"""
        return layout(f"{group['name']} Scores Table", body, user=coach, active_nav="progress")

    # Build the full column list from all games (base + sport-specific for athletes' sports)
    # Use base MEASUREMENT_GAMES only (sport-specific vary per athlete — keep it simple)
    # Column spec: list of (section_name, game_name, game_key, field_label, field_key, field_type)
    cols = []
    for section in MEASUREMENT_GAMES:
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

    for section in MEASUREMENT_GAMES:
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


def all_progress_page(coach, groups_data, sport_filter=None):
    """Overview page: programme stats, group cards, round-based measurement tables.
    Accessible to all coaches (admins see all groups; non-admins see their groups only).
    sport_filter: optional sport string to filter athlete averages.
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
        for section in MEASUREMENT_GAMES:
            sec_tables = "".join(_round_table(filtered, game) for game in section["games"])
            if sec_tables:
                tables_html += f'<h3 style="font-size:14px;color:var(--jag-muted);text-transform:uppercase;letter-spacing:0.05em;margin:20px 0 10px;">{esc(section["section"])}</h3>{sec_tables}'

        if not tables_html:
            tables_html = '<div class="card"><p class="muted">No measurement data yet.</p></div>'

        links = ""
        if gid:
            links = (f'<a href="/coach/groups/{gid}/achievement-summary" class="btn btn-sm" '
                     f'style="font-size:12px;background:var(--jag-green);color:var(--jag-navy);font-weight:700;border:none;">Group Stats</a>'
                     f'<a href="/coach/groups/{gid}/scores" class="btn btn-ghost btn-sm" style="font-size:12px;">Scores Table</a>')

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
            for section in MEASUREMENT_GAMES:
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

    body = f"""
    <div class="page-head">
      <div>
        <h1>Achievement Statistics Overview</h1>
        <p class="muted">Group averages across all measurement rounds{(" &mdash; " + esc(sport_filter) + " athletes") if sport_filter else ""}</p>
      </div>
    </div>
    {hero_card}
    {group_cards}
    {filter_bar}
    {group_sections_html}
    {overall_html}"""
    return layout("Achievement Statistics", body, user=coach, active_nav="progress")


def group_session_page(coach, participants, groups=None):
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

    for section in MEASUREMENT_GAMES:
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
      <label for="qs-date">Date</label>
      <input type="date" id="qs-date" value="{today}" style="max-width:200px; margin-bottom:16px;" />

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

      var dateEl       = document.getElementById('qs-date');
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
          var body = 'athlete_id=' + encodeURIComponent(athleteId) +
                     '&date='      + encodeURIComponent(dateEl.value) +
                     '&game_key='  + encodeURIComponent(gameKey) +
                     '&field_key=' + encodeURIComponent(fieldKey) +
                     '&value='     + encodeURIComponent(value);
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


def simple_message_page(title, message, user=None):
    body = f'<div class="card"><p>{esc(message)}</p></div>'
    return layout(title, body, user=user)


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


def coach_list_page(user, coaches, groups=None, coach_group_map=None, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    groups = groups or []
    coach_group_map = coach_group_map or {}
    group_map = {g["id"]: g["name"] for g in groups}

    # Collect unique organisations for filter bar
    all_orgs = sorted(set(
        c["organisation"] for c in coaches
        if c["organisation"]
    ))

    rows = []
    for c in coaches:
        is_self = c["id"] == user["id"]
        status = "Active" if c["active"] else "Inactive"
        status_class = "tag-active" if c["active"] else "tag-inactive"
        admin_badge = ' <span class="tag tag-active" style="font-size:11px;">Admin</span>' if c["is_admin"] else ""
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
            admin_toggle_label = "Remove Admin" if c["is_admin"] else "Make Admin"
            checkboxes = "".join(
                f'<label style="display:flex;align-items:center;gap:6px;font-size:12px;font-weight:normal;margin:2px 0;">'
                f'<input type="checkbox" name="group_id" value="{g["id"]}"'
                f'{" checked" if g["id"] in assigned_ids else ""}> {esc(g["name"])}</label>'
                for g in groups
            ) if groups else '<span class="muted" style="font-size:12px;">No groups yet</span>'
            action_html = f"""
            <form method="post" action="/coach/coaches/{c['id']}/reset-password" style="display:inline"
                  onsubmit="return confirm('Reset {esc(c['name'])}&#39;s password?');">
              <button type="submit" class="btn btn-ghost btn-sm">Reset Password</button>
            </form>
            <form method="post" action="/coach/coaches/{c['id']}/toggle-admin" style="display:inline"
                  onsubmit="return confirm('{admin_toggle_label} for {esc(c['name'])}?');">
              <button type="submit" class="btn btn-ghost btn-sm">{admin_toggle_label}</button>
            </form>
            <form method="post" action="/coach/coaches/{c['id']}/toggle" style="display:inline">
              <button type="submit" class="btn btn-ghost btn-sm">{toggle_label}</button>
            </form>
            <form method="post" action="/coach/coaches/{c['id']}/assign-group" style="display:inline-block; vertical-align:middle; margin-left:4px;">
              <div style="border:1px solid var(--jag-border); border-radius:6px; padding:6px 10px; background:#fff; margin-bottom:4px;">{checkboxes}</div>
              <button type="submit" class="btn btn-ghost btn-sm">Set Groups</button>
            </form>"""
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
      <button class="coach-filter-btn btn btn-ghost btn-sm" data-filter="admin" style="border-radius:999px;">Admins only</button>
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
          if(active === 'admin') show = r.dataset.admin === '1';
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
      <h1>Coaches</h1>
      <a class="btn btn-primary" href="/coach/coaches/new">Add Coach</a>
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
    return layout("Coaches", body, user=user, active_nav="coaches")


def new_coach_form(user, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    body = f"""
    <div class="page-head"><h1>Add Coach</h1></div>
    {error_html}
    <div class="card form-card">
      <form method="post" action="/coach/coaches/new">
        <label for="name">Full name</label>
        <input type="text" id="name" name="name" required />
        <label for="email">Email (used to log in)</label>
        <input type="email" id="email" name="email" required />
        <label for="organisation">Organisation <span style="font-weight:400;color:var(--jag-muted);">(school, club, etc. — optional)</span></label>
        <input type="text" id="organisation" name="organisation" placeholder="e.g. Masterton High School" />
        <label for="password">Temporary password</label>
        <input type="text" id="password" name="password" required value="CoachTemp123!" />
        <button type="submit" class="btn btn-primary">Create Coach</button>
      </form>
    </div>
    """
    return layout("Add Coach", body, user=user, active_nav="coaches")


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
    <div class="page-head"><h1>Resources</h1></div>
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
        <label for="folder_id">Folder</label>
        <select id="folder_id" name="folder_id">{folder_opts}</select>
        {tags_section}
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Save Changes</button>
      </form>
    </div>
    """
    return layout("Edit Resource", body, user=user, active_nav="resources")


