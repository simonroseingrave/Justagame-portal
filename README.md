# Just A Game — Athlete Adaptability Tracking

A web app for Just A Game athletes: coaches record Measurement Games test
results, and each athlete logs in to see their own results history.

It has **zero external dependencies** — it only uses the Python standard
library (no Flask, Django, or `pip install` needed to run it). That makes
it easy to run almost anywhere Python 3 is available.

## What's included

- Coach login → dashboard listing every participant, with a test session count.
- "Add Participant" form to create new athlete logins.
- **Measurement Games** — a structured physical-test battery, entered per athlete, per dated session: Timed Events (Skipping Rope Sprint and Slalom Running/Dribbling, each with the average of three times calculated automatically) and Points Events (Balance Ball Catching, Leap Catching & Throwing, Reaction Catching, Gate Dive, Target Shooting/Passing, Diamond Games, Leap & Land). A coach can fill in just the games tested that day and leave the rest blank — every previous session is kept on record (and can be deleted if entered by mistake), so progress over time is visible on both the coach's participant page and the athlete's own dashboard.
- "Change password" page (top bar, any logged-in user) to set a new password in-app — no email/reset-link flow needed.
- Participant login → personal dashboard with their Measurement Games results history.
- Sample/demo data (1 coach + 3 demo athletes, including a sample Measurement Games session) pre-loaded so you can see it working immediately.

**Paused for now:** the Activity Log (logging session activity with notes/points) and the points/level system have been removed from the UI, since they aren't needed at this stage. The underlying code hasn't been deleted — the `activities` table (`db.py`) and the level thresholds (`LEVELS`/`get_level_info` in `constants.py`) are still there, unused, ready to be wired back in later if you want them.

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
  constants.py  Measurement Games structure (plus unused levels/points thresholds, paused for now)
  static/       CSS + logo
  data/         SQLite database (created on first run, not in git)
```

## Branding

Your official logo (`static/img/logo.png`) and brand colours are already
applied — `static/css/style.css` uses your real hex codes (`#2D323B`,
`#AEB4BB`, `#F0A82E`, `#FFFFFF`) as CSS variables at the top of the file,
so any future colour tweaks only need changing in one place.

## Customising it further

1. **Measurement Games** — the list of sections, games and fields lives in
   `constants.py` (`MEASUREMENT_GAMES`). Add, remove, rename or re-type any
   game or field there and the entry form *and* the results history on
   every athlete's page both pick it up automatically — no other code
   changes needed. (The result values themselves are fully editable in the
   UI: a coach can log a new dated session any time, and delete a session
   if it was entered by mistake.)
2. **Levels & points (paused)** — the threshold logic still lives in `constants.py` (`LEVELS`/`get_level_info`) and the `activities` table is still in `db.py`, just not wired into any page right now. Say the word if you want the Activity Log and points/level system back.
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
