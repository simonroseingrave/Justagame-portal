# Just A Game — Activity & Achievement Portal

A web app for Just A Game athletes: coaches log session activity and award
achievement badges, and each athlete logs in to see their own activity
history, badges, and points/level progress.

It has **zero external dependencies** — it only uses the Python standard
library (no Flask, Django, or `pip install` needed to run it). That makes
it easy to run almost anywhere Python 3 is available.

## What's included

- Coach login → dashboard listing every participant, with points, level, badge and session counts.
- "Add Participant" form to create new athlete logins.
- Per-participant page to log activity sessions (date, focus area, coach notes, points) and award badges. Focus area is free text with autocomplete suggestions, so a coach can type a brand-new category any time — no code changes needed.
- "Achievements" admin page (coach nav bar) to add, edit, or delete badges/categories at any time — points values, descriptions and categories are all editable in the UI. A badge can't be deleted once it's been awarded to someone, to protect already-earned points.
- "Change password" page (top bar, any logged-in user) to set a new password in-app — no email/reset-link flow needed.
- Participant login → personal dashboard: total points, level progress bar, badges earned by category, and a full activity log.
- 15 pre-built achievement badges across the four pillars from Just A Game's coaching philosophy (Physical Capability, Game Understanding, Skill Adaptability, Confidence & Resilience), plus 3 milestone badges — all editable/extendable via the Achievements admin page.
- A 5-level points system (Rookie → Elite Adaptor) — thresholds are configurable in `constants.py`.
- Sample/demo data (1 coach + 3 demo athletes) pre-loaded so you can see it working immediately.

## Running it locally

Requires Python 3.8+, already installed on macOS.

```bash
cd justagame-portal
python3 app.py
```

Open **http://localhost:8000**. The database (`data/justagame.db`) and
demo data are created automatically on first run.

**Demo logins:**
| Role | Email | Password |
|---|---|---|
| Coach | `coach@justagame.co.nz` | `CoachDemo123!` |
| Participant | `alex.demo@example.com` | `Athlete123!` |

Change the coach password (use the **Change password** link in the top bar
once logged in) and remove/replace the demo participants before giving real
people access — see "Going live" below.

## Project structure

```
justagame-portal/
  app.py        routes + request handlers (start here)
  core.py       tiny zero-dependency web framework (routing, request/response)
  db.py         SQLite schema + seed data
  auth.py       password hashing, sessions
  views.py      page templates (plain Python functions, not Jinja)
  constants.py  achievement categories, levels/points thresholds
  static/       CSS + logo
  data/         SQLite database (created on first run, not in git)
```

## Branding

Your official logo (`static/img/logo.png`) and brand colours are already
applied — `static/css/style.css` uses your real hex codes (`#2D323B`,
`#AEB4BB`, `#F0A82E`, `#FFFFFF`) as CSS variables at the top of the file,
so any future colour tweaks only need changing in one place.

## Customising it further

1. **Achievement badges & categories** — manage these entirely in the UI
   now: log in as a coach, open **Achievements** in the top bar, and
   add/edit/delete badges, point values, descriptions and categories any
   time. New categories you type there immediately show up as "Focus area"
   options when logging activity, and as new sections on athletes'
   dashboards — no code changes needed. (The hardcoded list in `db.py`'s
   `seed_demo_data()` only matters for the very first run, to seed demo data.)
2. **Levels & points** — thresholds live in `constants.py` (`LEVELS`).
3. **Real participants** — once live, log in as the coach and use
   "Add Participant" to create accounts one at a time. There's no bulk
   import yet; if you have a long roster, tell me and I can add a CSV
   import.
4. **Passwords** — every user (coach or athlete) can change their own
   password from the **Change password** link in the top bar.

## Going live on Render

See **`DEPLOY_RENDER.md`** for exact step-by-step instructions — pushing
the code to GitHub, creating the Render service, and an important note
on the free tier's data-persistence limits (and how to remove that
limit later for ~$7/month).

Once it's hosted, add a button/link on justagame.co.nz (e.g. on the
Athlete Adaptability Programmes or Coaching pages) pointing to the
portal's URL — that part just needs a normal link block in Squarespace,
no code.

Outstanding: let me know how many coaches need real logins (there's
currently one demo coach account) and I'll set those up.

### Deploying with gunicorn (optional, for real traffic)

The built-in server (`python3 app.py`) is fine for local use or a handful
of concurrent users. For a public-facing deployment, install gunicorn on
the host and run:

```bash
pip install gunicorn
gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 2
```

`wsgi.py` is already set up as the entry point.

## Notes on security

- Passwords are hashed with PBKDF2-HMAC-SHA256 (260,000 iterations) — never stored in plain text.
- Sessions are random server-side tokens stored in SQLite, not signed cookies, so they can't be forged or replayed across deployments.
- All user-entered text (names, notes) is HTML-escaped before rendering, to prevent script injection.
- This demo runs over plain HTTP for local testing. Any real hosting (Render/Railway/PythonAnywhere) will give you HTTPS automatically — make sure it's enabled before sharing real participant logins.
