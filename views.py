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


def _participant_row(p, is_admin=False):
    drag = '<span class="drag-handle" title="Drag to move group">&#9776;</span>' if is_admin else ""
    return f"""<div class="res-item" data-id="{p['id']}">
      {drag}
      <div class="res-item-body">
        <a href="/coach/participants/{p['id']}">{esc(p['name'])}</a>
        <span class="res-desc">{esc(p['sport'] or '')}{'  ·  ' + esc(p['programme']) if p.get('programme') else ''}</span>
      </div>
      <div class="res-item-actions">
        <span class="muted" style="font-size:12px; padding:0 6px;">{p['test_count']} test{"s" if p['test_count'] != 1 else ""}</span>
        <a href="/coach/participants/{p['id']}" class="btn btn-ghost btn-sm">Manage</a>
      </div>
    </div>"""


def coach_dashboard_for(user, group_summaries, ungrouped_summaries, message=None):
    message_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    is_admin = user.get("is_admin")

    group_sections = ""
    for group, participants in group_summaries:
        count = len(participants)
        count_badge = f'<span class="res-count">{count} athlete{"s" if count != 1 else ""}</span>'
        items_html = "".join(_participant_row(p, is_admin=is_admin) for p in participants)
        empty = '<div class="res-drop-hint">Drop participants here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No participants in this group.</p>'
        list_html = items_html if items_html else empty
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder groups">&#9776;</span>' if is_admin else ""
        delete_btn = f"""<form method="post" action="/coach/groups/{group['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete group \\'{esc(group['name'])}\\'? Participants move to ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm">Delete Group</button>
            </form>""" if is_admin else ""
        group_sections += f"""
        <div class="res-folder" data-group-id="{group['id']}">
          <div class="res-folder-tab">
            {folder_handle}
            <button type="button" class="res-folder-toggle" onclick="var f=this.closest('.res-folder'),l=f.querySelector('.res-list'),o=f.classList.toggle('res-folder--open');if(l)l.style.display=o?'block':'none';" title="Expand / collapse">
              <span class="res-folder-icon">&#128193;</span>
              <strong class="res-folder-name">{esc(group['name'])}</strong>
              {count_badge}
              <span class="res-folder-chevron">&#9654;</span>
            </button>
            {delete_btn}
          </div>
          <div class="res-list" data-group-list-id="{group['id']}" style="display:none">{list_html}</div>
        </div>"""

    ungrouped_count = len(ungrouped_summaries)
    ug_badge = f'<span class="res-count">{ungrouped_count} athlete{"s" if ungrouped_count != 1 else ""}</span>'
    ug_items = "".join(_participant_row(p, is_admin=is_admin) for p in ungrouped_summaries)
    ug_empty = '<div class="res-drop-hint">Drop participants here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No ungrouped participants.</p>'
    ug_list_html = ug_items if ug_items else ug_empty

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
        <a class="btn btn-ghost" href="/coach">&larr; Back to all participants</a>
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
    return f"""<div class="res-item" data-id="{r['id']}">
      {drag_handle}
      <div class="res-item-body">
        <a href="{esc(r['url'])}" target="_blank" rel="noopener">{esc(r['name'])}</a>
        {f'<span class="muted res-desc">{esc(r["description"])}</span>' if r['description'] else ''}
      </div>
      <div class="res-item-actions">{admin_actions}</div>
    </div>"""


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
        list_content = items_html if items_html else empty_drop
        folder_handle = '<span class="drag-handle folder-handle" title="Drag to reorder folders">&#9776;</span>' if is_admin else ""
        delete_folder_btn = f"""<form method="post" action="/coach/resources/folders/{folder['id']}/delete" style="display:inline"
              onsubmit="return confirm('Delete folder \\'{esc(folder['name'])}\\'? Resources will move to Ungrouped.');">
              <button type="submit" class="btn btn-ghost btn-sm">Delete Folder</button>
            </form>""" if is_admin else ""
        folder_sections += f"""
        <div class="res-folder" data-folder-id="{folder['id']}">
          <div class="res-folder-tab">
            {folder_handle}
            <button type="button" class="res-folder-toggle" onclick="var f=this.closest('.res-folder'),l=f.querySelector('.res-list'),o=f.classList.toggle('res-folder--open');if(l)l.style.display=o?'block':'none';" title="Expand / collapse">
              <span class="res-folder-icon">&#128193;</span>
              <strong class="res-folder-name">{esc(folder['name'])}</strong>
              {count_badge}
              <span class="res-folder-chevron">&#9654;</span>
            </button>
            {delete_folder_btn}
          </div>
          <div class="res-list" data-list-id="{folder['id']}" style="display:none">{list_content}</div>
        </div>"""

    # Ungrouped section — open by default
    ungrouped_html = "".join(_resource_row(r, is_admin=is_admin) for r in ungrouped)
    ug_count = len(ungrouped)
    ug_count_badge = f'<span class="res-count">{ug_count} link{"s" if ug_count != 1 else ""}</span>'
    ug_empty = '<div class="res-drop-hint">Drop resources here</div>' if is_admin else '<p class="muted" style="padding:8px 4px; font-size:13px;">No ungrouped resources.</p>'
    ungrouped_list_html = ungrouped_html if ungrouped_html else ug_empty

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
    document.querySelectorAll('.res-list').forEach(function(list) {
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

    <div class="res-folder res-folder--open res-ungrouped">
      <div class="res-folder-tab res-folder-tab--ungrouped">
        <button type="button" class="res-folder-toggle" onclick="var f=this.closest('.res-folder'),l=f.querySelector('.res-list'),o=f.classList.toggle('res-folder--open');if(l)l.style.display=o?'block':'none';" title="Expand / collapse">
          <span class="res-folder-icon">&#128194;</span>
          <strong class="res-folder-name">Ungrouped</strong>
          {ug_count_badge}
          <span class="res-folder-chevron" style="transform:rotate(90deg);">&#9654;</span>
        </button>
      </div>
      <div class="res-list" data-list-id="ungrouped">{ungrouped_list_html}</div>
    </div>
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


