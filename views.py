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
            links = [("/coach", "Dashboard", "dashboard")]
            if user.get("is_admin"):
                links += [
                    ("/coach/participants/new", "Add Participant", "new_participant"),
                    ("/coach/coaches", "Coaches", "coaches"),
                ]
            links.append(("/coach/session", "Record Session", "session"))
            links.append(("/coach/progress", "Achievement Statistics", "progress"))
            links.append(("/coach/resources", "Resources", "resources"))
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


def _measurement_field_input(game_key, field):
    """One labelled number input with an inline quick-save button."""
    ftype = field["type"]
    step = "0.01" if ftype == "time" else "1"
    suffix = " (seconds)" if ftype == "time" else (f" ({field['unit']})" if field.get("unit") else "")
    input_id = f"mg__{game_key}__{field['key']}"
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
    section. Each field has its own quick-save button; the session is
    created lazily on the first save. A bulk-submit fallback is also
    available via the full form."""
    sections_html = "".join(f"""
    <div class="mg-section">
      <h4>{esc(section['section'])}</h4>
      {''.join(_measurement_game_fieldset(g) for g in section['games'])}
    </div>
    """ for section in MEASUREMENT_GAMES)

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
          btn.style.background = '#0f6e62';
          btn.style.color = '#fff';
          btn.style.borderColor = '#0f6e62';
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
    }})();
    </script>"""

    return f"""
    <div class="card form-card">
      <h3>Measurement Games</h3>
      <p class="muted">Enter a value and click <strong>&#10003; Save</strong> next to each field.
      The Skipping Rope Sprint average is calculated automatically from Time 1/2/3.</p>
      <label for="mg-date">Session date</label>
      <input type="date" id="mg-date" name="date" style="max-width:200px; margin-bottom:16px;" />
      {sections_html}
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


def _participant_row(p, is_admin=False):
    drag = '<span class="drag-handle" title="Drag to move group">&#9776;</span>' if is_admin else ""
    sport_prog = esc(p['sport'] or '')
    if p.get('programme'):
        sport_prog += f' &middot; {esc(p["programme"])}'
    return f"""<tr class="res-item" data-id="{p['id']}">
      <td style="width:20px; padding-right:0;">{drag}</td>
      <td><a href="/coach/participants/{p['id']}" style="font-weight:600;">{esc(p['name'])}</a></td>
      <td class="muted" style="font-size:13px;">{sport_prog}</td>
      <td style="white-space:nowrap;">{p['test_count']} test{"s" if p['test_count'] != 1 else ""}</td>
      <td style="text-align:right;"><a href="/coach/participants/{p['id']}" class="btn btn-ghost btn-sm">Manage</a></td>
    </tr>"""


def _participant_table(rows_html, is_admin=False):
    """Wrap participant rows in a table with column headers."""
    if not rows_html:
        return ""
    return f"""<table class="table" style="width:100%;">
      <thead><tr>
        {"<th style='width:20px;'></th>" if is_admin else ""}
        <th>Name</th><th>Sport / Programme</th><th>Tests</th><th></th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>"""


def edit_group_page(user, group, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    try:
        icon_url = group["icon_url"] or ""
    except Exception:
        icon_url = ""
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
        {f'<img src="{esc(icon_url)}" style="margin-top:8px;width:32px;height:32px;object-fit:contain;border-radius:4px;border:1px solid var(--jag-border);" onerror="this.style.display=\'none\'">' if icon_url else ""}
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
        count_badge = f'<span class="res-count">{count} athlete{"s" if count != 1 else ""}</span>'
        items_html = "".join(_participant_row(p, is_admin=is_admin) for p in participants)
        empty = '<div class="res-drop-hint">Drop participants here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No participants in this group.</p>'
        list_html = _participant_table(items_html, is_admin=is_admin) if items_html else empty
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder groups">&#9776;</span>' if is_admin else ""
        try:
            icon_url = group["icon_url"]
        except Exception:
            icon_url = None
        icon_html = (f'<img src="{esc(icon_url)}" style="width:22px;height:22px;object-fit:contain;border-radius:3px;flex-shrink:0;" '
                     f'onerror="this.style.display=\'none\'">')  if icon_url else "&#128193;"
        summary_link = f'<a href="/coach/groups/{group["id"]}/achievement-summary" class="btn btn-sm" style="font-size:12px; background:var(--jag-green); color:var(--jag-navy); font-weight:600; border:none;">&#128200; Group Stats</a>'
        admin_btns = f"""
            <a href="/coach/groups/{group['id']}/edit" class="btn btn-ghost btn-sm" style="font-size:12px;">Edit</a>
            <form method="post" action="/coach/groups/{group['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete group \\'{esc(group['name'])}\\'? Participants move to ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm" style="font-size:12px;">Delete</button>
            </form>""" if is_admin else ""
        group_sections += f"""
        <div class="res-folder" data-group-id="{group['id']}">
          <div class="res-folder-tab">
            {folder_handle}
            <button type="button" class="res-folder-toggle" onclick="var f=this.closest('.res-folder'),l=f.querySelector('.res-list'),o=f.classList.toggle('res-folder--open');if(l)l.style.display=o?'block':'none';" title="Expand / collapse">
              <span class="res-folder-icon">{icon_html}</span>
              <strong class="res-folder-name">{esc(group['name'])}</strong>
              {count_badge}
              <span class="res-folder-chevron">&#9654;</span>
            </button>
            {summary_link}
            {admin_btns}
          </div>
          <div class="res-list" data-group-list-id="{group['id']}" style="display:none">{list_html}</div>
        </div>"""

    ungrouped_count = len(ungrouped_summaries)
    ug_badge = f'<span class="res-count">{ungrouped_count} athlete{"s" if ungrouped_count != 1 else ""}</span>'
    ug_items = "".join(_participant_row(p, is_admin=is_admin) for p in ungrouped_summaries)
    ug_empty = '<div class="res-drop-hint">Drop participants here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No ungrouped participants.</p>'
    ug_list_html = _participant_table(ug_items, is_admin=is_admin) if ug_items else ug_empty

    ungrouped_section = f"""
    <div class="res-folder res-folder--open res-ungrouped">
      <div class="res-folder-tab res-folder-tab--ungrouped">
        <button type="button" class="res-folder-toggle" onclick="var f=this.closest('.res-folder'),l=f.querySelector('.res-list'),o=f.classList.toggle('res-folder--open');if(l)l.style.display=o?'block':'none';" title="Expand / collapse">
          <span class="res-folder-icon">&#128193;</span>
          <strong class="res-folder-name">{"Participants" if not group_summaries else "Ungrouped"}</strong>
          {ug_badge}
          <span class="res-folder-chevron" style="transform:rotate(90deg);">&#9654;</span>
        </button>
      </div>
      <div class="res-list" data-group-list-id="ungrouped">{ug_list_html}</div>
    </div>"""

    if not group_summaries and not ungrouped_summaries:
        if is_admin:
            content = '<div class="card"><p class="muted">No participants yet. Add one to get started.</p></div>' + ungrouped_section
        else:
            content = '<div class="card"><p class="muted">You haven\'t been assigned to a group yet. Contact an admin to be assigned.</p></div>'
    else:
        content = f'<div id="groups-container">{group_sections}</div>{ungrouped_section}'

    add_btn = '<a class="btn btn-primary" href="/coach/participants/new">+ Add Participant</a>' if is_admin else ""

    create_group_form = f"""
    <div class="card form-card" style="max-width:360px; margin-top:8px;">
      <h3 style="margin-top:0; font-size:15px;">Create Group</h3>
      <form method="post" action="/coach/groups/new" style="display:flex; gap:8px;">
        <input type="text" name="group_name" placeholder="e.g. Class 5A" required style="flex:1;" />
        <button type="submit" class="btn btn-primary btn-sm" style="white-space:nowrap;">+ Group</button>
      </form>
    </div>""" if is_admin else ""

    sortable_js = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.2/Sortable.min.js"></script>
    <script>
    function post(url, body) {
      fetch(url, { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: body });
    }
    // Reorder groups
    var gc = document.getElementById('groups-container');
    if (gc) {
      Sortable.create(gc, {
        handle: '.folder-handle', animation: 150,
        onEnd: function() {
          var ids = Array.from(gc.querySelectorAll('.res-folder[data-group-id]'))
                        .map(function(el){ return el.dataset.groupId; });
          post('/coach/groups/reorder', 'ids=' + ids.join(','));
        }
      });
    }
    // Cross-group participant drag
    document.querySelectorAll('[data-group-list-id]').forEach(function(list) {
      Sortable.create(list, {
        group: { name:'participants', pull:true, put:true },
        handle: '.drag-handle:not(.folder-handle)',
        animation: 150,
        ghostClass: 'res-item--ghost',
        onEnd: function(evt) {
          var fromList = evt.from, toList = evt.to, itemId = evt.item.dataset.id;
          if (fromList !== toList) {
            var newGroupId = toList.dataset.groupListId;
            post('/coach/participants/' + itemId + '/move-group',
                 'group_id=' + (newGroupId === 'ungrouped' ? '' : newGroupId));
            updateGroupCount(fromList);
            updateGroupCount(toList);
          }
        }
      });
    });
    function updateGroupCount(list) {
      var folder = list.closest('.res-folder');
      if (!folder) return;
      var badge = folder.querySelector('.res-count');
      if (!badge) return;
      var n = list.querySelectorAll('.res-item').length;
      badge.textContent = n + (n === 1 ? ' athlete' : ' athletes');
      var hint = list.querySelector('.res-drop-hint');
      if (hint) hint.style.display = n > 0 ? 'none' : '';
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
    <div class="page-head">
      <div>
        <h1>Coach Dashboard</h1>
        <p class="muted">{subtitle}</p>
      </div>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">{add_btn}</div>
    </div>
    {message_html}
    {content}
    {create_group_form}
    {sortable_js}
    <script>
    document.querySelectorAll('.res-folder-tab').forEach(function(tab) {{
      tab.addEventListener('click', function(e) {{
        if (e.target.closest('button, a, input, select, form')) return;
        var folder = tab.closest('.res-folder');
        var list = folder.querySelector('.res-list');
        var isOpen = folder.classList.contains('res-folder--open');
        folder.classList.toggle('res-folder--open');
        if (list) list.style.display = isOpen ? 'none' : 'block';
      }});
    }});
    </script>
    """
    return layout("Coach Dashboard", body, user=user, active_nav="dashboard")


def new_participant_form(user, error=None, groups=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    sport_options = "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in
                             ["Cricket", "Football", "Hockey", "Multi-sport"])
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
        <label for="email">Email (used to log in)</label>
        <input type="email" id="email" name="email" required />
        <label for="password">Temporary password</label>
        <input type="text" id="password" name="password" required value="Athlete123!" />
        <label for="sport">Sport</label>
        <select id="sport" name="sport">{sport_options}</select>
        <label for="programme">Programme / notes</label>
        <input type="text" id="programme" name="programme" placeholder="e.g. Athlete Adaptability Programme - Masterton 2026" />
        <label for="group_id">Group (optional)</label>
        <select id="group_id" name="group_id">{group_opts}</select>
        <button type="submit" class="btn btn-primary">Create Participant</button>
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
    group_badge = f' &middot; <span class="tag">{esc(current_group_name)}</span>' if current_group_name else ""

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
      <button type="submit" class="btn btn-ghost">Reset Password</button>
    </form>""" if is_admin else ""

    body = f"""
    <div class="page-head">
      <div>
        <h1>{esc(participant['name'])}</h1>
        <p class="muted">{esc(participant['sport'] or '')} &middot; {esc(participant['programme'] or '')} &middot; {esc(participant['email'])}{group_badge}</p>
      </div>
      <div style="display:flex; gap:8px;">
        {reset_btn}
        <a class="btn btn-primary" href="/coach/participants/{participant['id']}/progress">&#128200; Achievement Statistics</a>
        <a class="btn btn-ghost" href="/coach">&larr; Back</a>
      </div>
    </div>
    {message_html}
    {group_form}

    <section class="stat-row">
      <div class="card stat-card"><div class="stat-number">{len(measurement_sessions)}</div><div class="stat-label">Test Sessions</div></div>
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

    body = f"""
    <div class="page-head">
      <div>
        <h1>{esc(participant['name'])} &mdash; Achievement Statistics</h1>
        <p class="muted">{esc(participant.get('sport') or '')} &middot; {n} test session{"s" if n != 1 else ""}</p>
      </div>
      <a class="btn btn-ghost" href="/coach/participants/{pid}">&larr; Back</a>
    </div>
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
    gname = esc(group["name"]) if group else "Group"

    if not active:
        body = f"""
        <div class="page-head">
          <div><h1>{gname} &mdash; Achievement Summary</h1></div>
          <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
        </div>
        <div class="card"><p class="muted">No athletes in this group have two or more test sessions yet — come back after the second round of measurements.</p></div>"""
        return layout(f"{group['name']} Achievement Summary", body, user=coach, active_nav="progress")

    athlete_count = len(active)
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
                for _p, sessions in active:
                    first_s  = sessions[-1]   # oldest (list is newest-first)
                    latest_s = sessions[0]
                    fv = first_s["results"].get((game["key"], fkey))
                    lv = latest_s["results"].get((game["key"], fkey))
                    if fv is not None and lv is not None and fv != 0:
                        pcts.append((lv - fv) / fv * 100)

                if not pcts:
                    continue

                n      = len(pcts)
                avg    = sum(pcts) / n
                # For time fields lower is better; for everything else higher is better
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
        sections_html = '<div class="card"><p class="muted">No measurements recorded yet.</p></div>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>{gname} &mdash; Achievement Summary</h1>
        <p class="muted">Average improvement from first to most recent session &mdash; {athlete_count} athlete{"s" if athlete_count != 1 else ""} with 2+ sessions</p>
      </div>
      <a class="btn btn-ghost" href="/coach">&larr; Dashboard</a>
    </div>
    {sections_html}"""
    return layout(f"{group['name']} Achievement Summary", body, user=coach, active_nav="progress")


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


def all_progress_page(coach, groups_data):
    """Admin-only page: progress across all participants, organised by group.
    groups_data: list of (group_or_None, [(participant, sessions), ...])
    """
    body_sections = ""
    any_data = False

    for group, participants_sessions in groups_data:
        active = [(p, s) for p, s in participants_sessions if s]
        if not active:
            continue
        any_data = True
        gname = esc(group["name"]) if group else "Ungrouped"
        gid   = group["id"] if group else None
        prog_link = f'<a class="btn btn-ghost btn-sm" href="/coach/groups/{gid}/progress">Full group achievement statistics</a>' if gid else ""

        # Summary table: participant | sessions | games tested | first session | latest session
        rows = ""
        for p, sessions in active:
            n = len(sessions)
            first_date  = sessions[-1]["date"] if sessions else "—"
            latest_date = sessions[0]["date"]  if sessions else "—"
            # Count distinct games with data in latest session
            games_in_latest = len({gk for (gk, _) in sessions[0]["results"].keys()}) if sessions else 0
            rows += f"""<tr>
              <td><a href="/coach/participants/{p['id']}/progress">{esc(p['name'])}</a></td>
              <td>{n}</td>
              <td>{first_date}</td>
              <td>{latest_date}</td>
              <td>{games_in_latest} game{"s" if games_in_latest!=1 else ""}</td>
            </tr>"""

        body_sections += f"""
        <h2 class="section-title">{gname} {prog_link}</h2>
        <div class="card">
          <table class="table">
            <thead><tr><th>Participant</th><th>Sessions</th><th>First Test</th><th>Latest Test</th><th>Latest Coverage</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    if not any_data:
        body_sections = '<div class="card"><p class="muted">No test sessions recorded yet.</p></div>'

    # Count totals
    total_participants = sum(len(ps) for _, ps in groups_data)
    total_with_data = sum(len([p for p, s in ps if s]) for _, ps in groups_data)
    total_sessions = sum(len(s) for _, ps in groups_data for _, s in ps)

    overall_report = _overall_achievement_html(groups_data)

    body = f"""
    <div class="page-head">
      <div><h1>Achievement Statistics Overview</h1>
        <p class="muted">{total_with_data} of {total_participants} participants tested &middot; {total_sessions} total sessions</p>
      </div>
    </div>
    {body_sections}
    {overall_report}"""
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

    # Game options grouped by section + JS data map
    game_opts = '<option value="">— Select game —</option>'
    games_data = {}
    for section in MEASUREMENT_GAMES:
        game_opts += f'<optgroup label="{esc(section["section"])}">'
        for game in section["games"]:
            game_opts += f'<option value="{esc(game["key"])}">{esc(game["name"])}</option>'
            games_data[game["key"]] = {
                "name": game["name"],
                "fields": [
                    {"key": f["key"], "label": f["label"], "type": f["type"]}
                    for f in game["fields"]
                ],
            }
        game_opts += '</optgroup>'

    games_js = _json.dumps(games_data)
    today = __import__("datetime").date.today().isoformat()
    show_group_filter = "block" if groups else "none"

    body = f"""
    <div class="page-head"><h1>Record Session</h1></div>

    <div class="card form-card" style="max-width:560px;">
      <label for="qs-date">Date</label>
      <input type="date" id="qs-date" value="{today}" style="max-width:200px; margin-bottom:16px;" />

      <div id="qs-group-wrap" style="display:{show_group_filter}; margin-bottom:16px;">
        <label for="qs-group">Group</label>
        <select id="qs-group">{group_opts}</select>
      </div>

      <label for="qs-athlete">Athlete</label>
      <select id="qs-athlete" style="margin-bottom:16px;">{athlete_opts}</select>

      <label for="qs-game">Measurement Game</label>
      <select id="qs-game" style="margin-bottom:16px;">{game_opts}</select>

      <div id="qs-fields" style="margin-top:4px;"></div>
    </div>

    <div class="card" style="max-width:560px; margin-top:16px;">
      <h3 style="margin:0 0 10px; font-size:15px;">Session log</h3>
      <div id="qs-log" style="font-size:13px; color:var(--jag-muted);">Nothing saved yet.</div>
    </div>

    <script>
    (function() {{
      var GAMES = {games_js};
      var saveUrl = '/coach/session/save';
      var sessionIds = {{}}; // athlete_id -> session_id (cached per page load)

      var dateEl    = document.getElementById('qs-date');
      var groupEl   = document.getElementById('qs-group');
      var athleteEl = document.getElementById('qs-athlete');
      var gameEl    = document.getElementById('qs-game');
      var fieldsEl  = document.getElementById('qs-fields');
      var logEl     = document.getElementById('qs-log');
      var logEmpty  = true;

      // All original athlete <option> elements (cached before any filtering)
      var allAthleteOpts = Array.from(athleteEl.querySelectorAll('option'));

      function filterAthletes() {{
        if (!groupEl) return;
        var gid = groupEl.value;
        var prev = athleteEl.value;
        // Rebuild options
        athleteEl.innerHTML = '';
        allAthleteOpts.forEach(function(opt) {{
          if (!opt.value || !gid || opt.dataset.group === String(gid)) {{
            athleteEl.appendChild(opt.cloneNode(true));
          }}
        }});
        // Restore previous selection if still valid, else reset
        if (Array.from(athleteEl.options).some(function(o) {{ return o.value === prev; }})) {{
          athleteEl.value = prev;
        }} else {{
          athleteEl.value = '';
          fieldsEl.innerHTML = '';
        }}
      }}

      if (groupEl) groupEl.addEventListener('change', filterAthletes);

      function renderFields(gameKey) {{
        fieldsEl.innerHTML = '';
        if (!gameKey || !GAMES[gameKey]) return;
        var game = GAMES[gameKey];
        game.fields.forEach(function(f) {{
          var step = (f.type === 'time') ? '0.01' : '1';
          var suffix = (f.type === 'time') ? ' (seconds)' : '';
          var div = document.createElement('div');
          div.className = 'mg-field';
          div.style.marginBottom = '12px';
          div.innerHTML =
            '<label style="font-size:13px; font-weight:600; display:block; margin-bottom:4px;">' +
              f.label + suffix +
            '</label>' +
            '<div class="mg-field-row">' +
              '<input type="number" step="' + step + '" min="0" id="qs-input-' + f.key + '" ' +
                     'data-field="' + f.key + '" style="max-width:140px;" />' +
              '<button type="button" class="mg-save-btn" data-field="' + f.key + '">&#10003; Save</button>' +
            '</div>';
          fieldsEl.appendChild(div);
        }});

        // Wire save buttons
        fieldsEl.querySelectorAll('.mg-save-btn').forEach(function(btn) {{
          btn.addEventListener('click', function() {{
            var fieldKey  = btn.dataset.field;
            var input     = document.getElementById('qs-input-' + fieldKey);
            var value     = input ? input.value.trim() : '';
            var athleteId = athleteEl.value;
            var gameKey2  = gameEl.value;
            if (!athleteId) {{ alert('Please select an athlete first.'); return; }}
            if (!value)     {{ alert('Please enter a value first.'); return; }}
            doSave(athleteId, gameKey2, fieldKey, value, btn, input);
          }});
          // Enter key
          var inp = document.getElementById('qs-input-' + btn.dataset.field);
          if (inp) inp.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{ e.preventDefault(); btn.click(); }}
          }});
        }});
      }}

      function markBtn(btn, state) {{
        if (state === 'saving') {{
          btn.textContent = '...'; btn.disabled = true; btn.style.background = '';
        }} else if (state === 'ok') {{
          btn.textContent = '\\u2713 Saved'; btn.disabled = false;
          btn.style.background = '#0f6e62'; btn.style.color = '#fff'; btn.style.borderColor = '#0f6e62';
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

      async function doSave(athleteId, gameKey, fieldKey, value, btn, input) {{
        markBtn(btn, 'saving');
        try {{
          var game   = GAMES[gameKey] || {{}};
          var field  = (game.fields || []).find(function(f) {{ return f.key === fieldKey; }}) || {{}};
          var athleteName = athleteEl.options[athleteEl.selectedIndex].text;
          var body = 'athlete_id=' + encodeURIComponent(athleteId) +
                     '&date='       + encodeURIComponent(dateEl.value) +
                     '&game_key='   + encodeURIComponent(gameKey) +
                     '&field_key='  + encodeURIComponent(fieldKey) +
                     '&value='      + encodeURIComponent(value);
          var resp = await fetch(saveUrl, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
            body: body,
          }});
          var data = await resp.json();
          if (!resp.ok || !data.ok) throw new Error(data.error || 'Save failed');
          markBtn(btn, 'ok');
          input.value = '';
          // Log entry
          if (logEmpty) {{ logEl.innerHTML = ''; logEmpty = false; }}
          var entry = document.createElement('div');
          entry.style.cssText = 'padding:6px 0; border-bottom:1px solid var(--jag-border); display:flex; gap:8px; align-items:baseline;';
          entry.innerHTML =
            '<span style="font-weight:700; color:var(--jag-text);">' + athleteName + '</span>' +
            '<span style="color:var(--jag-muted);">' + (game.name || gameKey) + ' &rarr; ' + (field.label || fieldKey) + '</span>' +
            '<span style="margin-left:auto; font-weight:700; color:var(--jag-navy);">' + value + (field.type === 'time' ? 's' : '') + '</span>';
          logEl.insertBefore(entry, logEl.firstChild);
        }} catch(e) {{
          markBtn(btn, 'error');
        }}
      }}

      gameEl.addEventListener('change', function() {{ renderFields(gameEl.value); }});
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

    rows = []
    for c in coaches:
        is_self = c["id"] == user["id"]
        status = "Active" if c["active"] else "Inactive"
        status_class = "tag-active" if c["active"] else "tag-inactive"
        admin_badge = ' <span class="tag tag-active" style="font-size:11px;">Admin</span>' if c["is_admin"] else ""
        assigned_ids = coach_group_map.get(c["id"], [])
        assigned_names = [esc(group_map[gid]) for gid in assigned_ids if gid in group_map]
        group_badge = (" &middot; " + ", ".join(f'<span class="tag">{n}</span>' for n in assigned_names)) if assigned_names else ""

        if is_self:
            action_html = '<span class="muted">(you)</span>'
        else:
            toggle_label = "Deactivate" if c["active"] else "Reactivate"
            admin_toggle_label = "Remove Admin" if c["is_admin"] else "Make Admin"
            # Multi-select checkboxes for group assignment
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
        rows.append(f"""<tr>
          <td>{esc(c['name'])}{admin_badge}</td>
          <td>{esc(c['email'])}{group_badge}</td>
          <td><span class="tag {status_class}">{status}</span></td>
          <td>{action_html}</td>
        </tr>""")
    rows_html = "".join(rows)
    body = f"""
    <div class="page-head">
      <h1>Coaches</h1>
      <a class="btn btn-primary" href="/coach/coaches/new">Add Coach</a>
    </div>
    {message_html}
    <div class="card">
      <table class="table">
        <thead><tr><th>Name</th><th>Email / Groups</th><th>Status</th><th></th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
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
        <label for="password">Temporary password</label>
        <input type="text" id="password" name="password" required value="CoachTemp123!" />
        <button type="submit" class="btn btn-primary">Create Coach</button>
      </form>
    </div>
    """
    return layout("Add Coach", body, user=user, active_nav="coaches")


def _resource_row(r, is_admin=False):
    name_q = esc(r['name']).replace("'", "\\'")
    admin_actions = f"""
      <a href="/coach/resources/{r['id']}/edit" class="btn btn-ghost btn-sm">Edit</a>
      <form method="post" action="/coach/resources/{r['id']}/delete" style="display:inline"
            onsubmit="return confirm('Delete \\'{name_q}\\'?');">
        <button type="submit" class="btn btn-ghost btn-sm">Delete</button>
      </form>""" if is_admin else ""
    drag_handle = '<span class="drag-handle" title="Drag to reorder">&#9776;</span>' if is_admin else ""
    desc = f'<span class="muted" style="font-size:13px;">{esc(r["description"])}</span>' if r['description'] else ''
    return f"""<tr class="res-item" data-id="{r['id']}">
      <td style="width:20px; padding-right:0;">{drag_handle}</td>
      <td><a href="{esc(r['url'])}" target="_blank" rel="noopener" style="font-weight:600;">{esc(r['name'])}</a></td>
      <td>{desc}</td>
      <td style="text-align:right; white-space:nowrap;">{admin_actions}</td>
    </tr>"""


def _resource_table(rows_html, is_admin=False, list_id=None):
    """Wrap resource rows in a table with column headers."""
    if not rows_html:
        return ""
    tbody_attr = f' data-list-id="{list_id}"' if list_id is not None else ""
    return f"""<table class="table" style="width:100%;">
      <thead><tr>
        {"<th style='width:20px;'></th>" if is_admin else ""}
        <th>Name</th><th>Description</th><th></th>
      </tr></thead>
      <tbody{tbody_attr}>{rows_html}</tbody>
    </table>"""


def resources_page(user, folder_groups, ungrouped, folders, message=None, error=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    is_admin = user.get("is_admin")

    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}">{esc(f["name"])}</option>' for f in folders
    )

    # Build folder sections
    folder_sections = ""
    for folder, resources in folder_groups:
        items_html = "".join(_resource_row(r, is_admin=is_admin) for r in resources)
        count = len(resources)
        count_badge = f'<span class="res-count">{count} link{"s" if count != 1 else ""}</span>'
        empty_drop = '<div class="res-drop-hint">Drop resources here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No resources yet.</p>'
        list_content = _resource_table(items_html, is_admin=is_admin, list_id=folder['id']) if items_html else empty_drop
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder folders">&#9776;</span>' if is_admin else ""
        is_protected_folder = folder['name'].strip().lower() == "measurement games"
        delete_folder_btn = f"""<form method="post" action="/coach/resources/folders/{folder['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete folder \\'{esc(folder['name'])}\\'? Resources will move to Ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm">Delete Folder</button>
            </form>""" if is_admin and not is_protected_folder else ""
        folder_sections += f"""
        <div class="res-folder res-folder--open" data-folder-id="{folder['id']}">
          <div class="res-folder-tab">
            {folder_handle}
            <div class="res-folder-toggle">
              <span class="res-folder-icon">&#128193;</span>
              <strong class="res-folder-name">{esc(folder['name'])}</strong>
              {count_badge}
            </div>
            {delete_folder_btn}
          </div>
          <div class="res-list" data-list-id="{folder['id']}">{list_content}</div>
        </div>"""

    # Ungrouped section — open by default
    ungrouped_html = "".join(_resource_row(r, is_admin=is_admin) for r in ungrouped)
    ug_count = len(ungrouped)
    ug_count_badge = f'<span class="res-count">{ug_count} link{"s" if ug_count != 1 else ""}</span>'
    ug_empty = '<div class="res-drop-hint">Drop resources here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No ungrouped resources.</p>'
    ungrouped_list_html = _resource_table(ungrouped_html, is_admin=is_admin) if ungrouped_html else ug_empty

    manage_forms = f"""
    <div class="two-col" style="gap:16px; align-items:flex-start; margin-bottom:24px;">
      <div class="card form-card">
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
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Add Resource</button>
        </form>
      </div>
      <div class="card form-card">
        <h2 style="margin-top:0; font-size:16px;">Add a folder</h2>
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
          var ids = Array.from(foldersContainer.querySelectorAll('.res-folder[data-folder-id]'))
                        .map(function(el) { return el.dataset.folderId; });
          postOrder('/coach/resources/folders/reorder', ids);
        }
      });
    }

    // Drag resources within and between lists (cross-folder)
    // Target <tbody data-list-id> because resource rows are <tr> elements
    document.querySelectorAll('tbody[data-list-id]').forEach(function(list) {
      Sortable.create(list, {
        group: { name: 'resources', pull: true, put: true },
        handle: '.drag-handle:not(.folder-handle)',
        animation: 150,
        ghostClass: 'res-item--ghost',
        onEnd: function(evt) {
          var fromList = evt.from;
          var toList   = evt.to;
          var itemId   = evt.item.dataset.id;

          if (fromList !== toList) {
            // Moved to a different folder — update folder_id on the server
            var newListId = toList.dataset.listId;
            var folderId  = (newListId === 'ungrouped') ? '' : newListId;
            post('/coach/resources/' + itemId + '/move', 'folder_id=' + folderId);

            // Update the count badges on both affected folders
            updateCount(fromList);
            updateCount(toList);
          }
          // Always persist the new order of the destination list
          var destIds = Array.from(toList.querySelectorAll('.res-item'))
                            .map(function(el) { return el.dataset.id; });
          postOrder('/coach/resources/reorder', destIds);
        }
      });
    });

    function updateCount(list) {
      var folder = list.closest('.res-folder');
      if (!folder) return;
      var badge = folder.querySelector('.res-count');
      if (!badge) return;
      var n = list.querySelectorAll('.res-item').length;
      badge.textContent = n + (n === 1 ? ' link' : ' links');
      // Show/hide the drop hint
      var hint = list.querySelector('.res-drop-hint');
      if (hint) hint.style.display = n > 0 ? 'none' : '';
    }
    </script>""" if is_admin else ""

    body = f"""
    <div class="page-head"><h1>Resources</h1></div>
    {message_html}{error_html}
    {manage_forms}
    <div id="folders-container">{folder_sections}</div>
    {sortable_js}
    """
    return layout("Resources", body, user=user, active_nav="resources")


def edit_resource_page(user, resource, folders, error=None):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    folder_opts = '<option value="">— Ungrouped —</option>' + "".join(
        f'<option value="{f["id"]}" {"selected" if resource["folder_id"] == f["id"] else ""}>{esc(f["name"])}</option>'
        for f in folders
    )
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
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:14px;">Save Changes</button>
      </form>
    </div>
    """
    return layout("Edit Resource", body, user=user, active_nav="resources")


