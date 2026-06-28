"""HTML rendering. Pages are built with small Python functions rather than
a templating engine, so there is no extra dependency to install. All
user-supplied text is passed through `esc()` (html.escape) before being
placed in markup to avoid HTML/script injection.
"""
from html import escape as esc

from constants import CATEGORIES, CATEGORY_ICONS, CATEGORY_BLURBS, get_level_info


def layout(title, body, user=None, flash=None, active_nav=None):
    nav = ""
    if user:
        if user["role"] == "coach":
            links = [
                ("/coach", "Dashboard", "dashboard"),
                ("/coach/participants/new", "Add Participant", "new_participant"),
            ]
        else:
            links = [("/dashboard", "My Portal", "dashboard")]
        nav_items = "".join(
            f'<a class="nav-link{" active" if active_nav == key else ""}" href="{href}">{label}</a>'
            for href, label, key in links
        )
        nav = f"""
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span>Just A Game <small>Portal</small></span>
            </a>
            <nav class="nav">{nav_items}</nav>
            <div class="user-pill">
              <span>{esc(user['name'])}</span>
              <a href="/logout" class="btn btn-ghost btn-sm">Log out</a>
            </div>
          </div>
        </header>
        """
    else:
        nav = """
        <header class="topbar">
          <div class="topbar-inner">
            <a class="brand" href="/">
              <img src="/static/img/logo.png" alt="Just A Game" class="brand-logo" />
              <span>Just A Game <small>Portal</small></span>
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
  <title>{esc(title)} - Just A Game Portal</title>
  <link rel="stylesheet" href="/static/css/style.css" />
</head>
<body>
  {nav}
  <main class="container">
    {flash_html}
    {body}
  </main>
  <footer class="footer">
    <p>Just A Game &middot; Activity &amp; Achievement Portal &middot; <a href="https://www.justagame.co.nz" target="_blank" rel="noopener">justagame.co.nz</a></p>
  </footer>
</body>
</html>"""


def login_page(error=None, prefill_email=""):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    body = f"""
    <div class="login-wrap">
      <div class="card login-card">
        <img src="/static/img/logo.png" alt="Just A Game" class="login-logo" />
        <h1>Activity &amp; Achievement Portal</h1>
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


def progress_bar(fraction, label=""):
    pct = max(0, min(100, round(fraction * 100)))
    return f"""
    <div class="progress">
      <div class="progress-bar" style="width:{pct}%"></div>
    </div>
    <div class="progress-label">{label}</div>
    """


TROPHY_ICON = "\U0001F3C6"
LOCK_ICON = "\U0001F512"


def badge_card(name, description, points, earned, date_awarded=None):
    cls = "badge-card earned" if earned else "badge-card locked"
    icon = TROPHY_ICON if earned else LOCK_ICON
    sub = f'<span class="badge-date">Earned {esc(date_awarded)}</span>' if earned and date_awarded else (
        '<span class="badge-locked-tag">Not yet earned</span>' if not earned else ""
    )
    return f"""
    <div class="{cls}">
      <div class="badge-icon">{icon}</div>
      <div class="badge-body">
        <div class="badge-name">{esc(name)}</div>
        <div class="badge-desc">{esc(description)}</div>
        <div class="badge-meta"><span class="pts">+{points} pts</span>{sub}</div>
      </div>
    </div>
    """


def participant_dashboard(user, activities, awards, all_achievements, total_points):
    level_info = get_level_info(total_points)
    if level_info["next_name"]:
        level_label = f"{level_info['current_name']} &rarr; {level_info['points_to_next']} pts to {level_info['next_name']}"
    else:
        level_label = f"{level_info['current_name']} (top level reached!)"

    # group achievements by category, mark earned ones
    earned_ids = {a["achievement_id"]: a["date_awarded"] for a in awards}
    by_category = {}
    for ach in all_achievements:
        by_category.setdefault(ach["category"], []).append(ach)

    category_sections = []
    for cat in CATEGORIES + ["Milestone"]:
        items = by_category.get(cat, [])
        if not items:
            continue
        earned_count = sum(1 for a in items if a["id"] in earned_ids)
        icon = CATEGORY_ICONS.get(cat, "⭐")
        blurb = CATEGORY_BLURBS.get(cat, "Milestones earned along the way.")
        cards = "".join(
            badge_card(a["name"], a["description"], a["points_value"], a["id"] in earned_ids, earned_ids.get(a["id"]))
            for a in items
        )
        cat_title = "Milestones" if cat == "Milestone" else cat
        category_sections.append(f"""
        <section class="category-block">
          <div class="category-head">
            <span class="cat-icon">{icon}</span>
            <div>
              <h3>{esc(cat_title)}</h3>
              <p class="muted">{esc(blurb)}</p>
            </div>
            <div class="cat-count">{earned_count}/{len(items)}</div>
          </div>
          <div class="badge-grid">{cards}</div>
        </section>
        """)

    activity_rows = "".join(
        f"""<tr>
              <td>{esc(a['date'])}</td>
              <td>{esc(a['title'])}</td>
              <td><span class="tag">{esc(a['category'] or '-')}</span></td>
              <td>{esc(a['notes'] or '')}</td>
              <td class="pts-cell">+{a['points']}</td>
            </tr>"""
        for a in activities
    ) or '<tr><td colspan="5" class="muted">No activity logged yet.</td></tr>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>Welcome back, {esc(user['name'].split(' ')[0])}</h1>
        <p class="muted">{esc(user.get('sport') or '')} &middot; {esc(user.get('programme') or '')}</p>
      </div>
    </div>

    <section class="stat-row">
      <div class="card stat-card">
        <div class="stat-number">{total_points}</div>
        <div class="stat-label">Total Points</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{len(earned_ids)}</div>
        <div class="stat-label">Badges Earned</div>
      </div>
      <div class="card stat-card">
        <div class="stat-number">{len(activities)}</div>
        <div class="stat-label">Sessions Logged</div>
      </div>
    </section>

    <section class="card level-card">
      <h3>Level: {esc(level_info['current_name'])}</h3>
      {progress_bar(level_info['progress'], level_label)}
    </section>

    <h2 class="section-title">Achievements</h2>
    {''.join(category_sections)}

    <h2 class="section-title">Activity Log</h2>
    <div class="card">
      <table class="table">
        <thead><tr><th>Date</th><th>Session</th><th>Focus</th><th>Coach notes</th><th>Points</th></tr></thead>
        <tbody>{activity_rows}</tbody>
      </table>
    </div>
    """
    return layout("My Portal", body, user=user, active_nav="dashboard")


def coach_dashboard(participants):
    rows = []
    for p in participants:
        level_info = get_level_info(p["total_points"])
        rows.append(f"""
        <tr>
          <td><a href="/coach/participants/{p['id']}">{esc(p['name'])}</a></td>
          <td>{esc(p['sport'] or '-')}</td>
          <td>{esc(p['programme'] or '-')}</td>
          <td>{p['total_points']}</td>
          <td>{esc(level_info['current_name'])}</td>
          <td>{p['badge_count']}</td>
          <td>{p['activity_count']}</td>
          <td><a class="btn btn-sm btn-secondary" href="/coach/participants/{p['id']}">Manage</a></td>
        </tr>
        """)
    rows_html = "".join(rows) or '<tr><td colspan="8" class="muted">No participants yet. Add one to get started.</td></tr>'

    body = f"""
    <div class="page-head">
      <div>
        <h1>Coach Dashboard</h1>
        <p class="muted">Log activity, award achievements and track every athlete's progress.</p>
      </div>
      <a class="btn btn-primary" href="/coach/participants/new">+ Add Participant</a>
    </div>
    <div class="card">
      <table class="table">
        <thead><tr><th>Name</th><th>Sport</th><th>Programme</th><th>Points</th><th>Level</th><th>Badges</th><th>Sessions</th><th></th></tr></thead>
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


def coach_participant_detail(coach, participant, activities, awards, all_achievements, total_points, message=None):
    level_info = get_level_info(total_points)
    earned_ids = {a["achievement_id"]: a["date_awarded"] for a in awards}

    achievement_options = "".join(
        f'<option value="{a["id"]}">{esc(a["name"])} ({esc(a["category"])}, +{a["points_value"]} pts)</option>'
        for a in all_achievements if a["id"] not in earned_ids
    )
    category_options = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in CATEGORIES)

    activity_rows = "".join(
        f"""<tr>
              <td>{esc(a['date'])}</td>
              <td>{esc(a['title'])}</td>
              <td><span class="tag">{esc(a['category'] or '-')}</span></td>
              <td>{esc(a['notes'] or '')}</td>
              <td class="pts-cell">+{a['points']}</td>
            </tr>"""
        for a in activities
    ) or '<tr><td colspan="5" class="muted">No activity logged yet.</td></tr>'

    earned_badges = "".join(
        badge_card(a["name"], a["description"], a["points_value"], True, earned_ids.get(a["id"]))
        for a in all_achievements if a["id"] in earned_ids
    ) or '<p class="muted">No badges awarded yet.</p>'

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
      <div class="card stat-card"><div class="stat-number">{total_points}</div><div class="stat-label">Total Points</div></div>
      <div class="card stat-card"><div class="stat-number">{len(earned_ids)}</div><div class="stat-label">Badges Earned</div></div>
      <div class="card stat-card"><div class="stat-number">{esc(level_info['current_name'])}</div><div class="stat-label">Current Level</div></div>
    </section>

    <div class="two-col">
      <div class="card form-card">
        <h3>Log an Activity</h3>
        <form method="post" action="/coach/participants/{participant['id']}/activity">
          <label>Date</label>
          <input type="date" name="date" required />
          <label>Session title</label>
          <input type="text" name="title" placeholder="e.g. Week 6 - Adaptability Programme Session" required />
          <label>Focus area</label>
          <select name="category">{category_options}</select>
          <label>Coach notes</label>
          <textarea name="notes" rows="3" placeholder="What did they work on / show?"></textarea>
          <label>Points</label>
          <input type="number" name="points" value="10" min="0" max="100" />
          <button type="submit" class="btn btn-primary">Log Activity</button>
        </form>
      </div>

      <div class="card form-card">
        <h3>Award a Badge</h3>
        <form method="post" action="/coach/participants/{participant['id']}/award">
          <label>Achievement</label>
          <select name="achievement_id" required>{achievement_options or '<option value="">All badges already earned</option>'}</select>
          <label>Date awarded</label>
          <input type="date" name="date_awarded" required />
          <button type="submit" class="btn btn-secondary">Award Badge</button>
        </form>
      </div>
    </div>

    <h2 class="section-title">Earned Badges</h2>
    <div class="badge-grid">{earned_badges}</div>

    <h2 class="section-title">Activity Log</h2>
    <div class="card">
      <table class="table">
        <thead><tr><th>Date</th><th>Session</th><th>Focus</th><th>Coach notes</th><th>Points</th></tr></thead>
        <tbody>{activity_rows}</tbody>
      </table>
    </div>
    """
    return layout(participant["name"], body, user=coach, active_nav="dashboard")


def simple_message_page(title, message, user=None):
    body = f'<div class="card"><p>{esc(message)}</p></div>'
    return layout(title, body, user=user)
