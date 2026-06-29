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
- "My Account" page (top bar, any logged-in user) to edit your own name/email and change your password in-app — no email/reset-link flow needed.
- "Coaches" page (coach nav) to add other coaches and deactivate/reactivate their accounts — each coach gets their own named login.
- "Forgot your password?" link on login — no email setup needed; a coach resets the person's password for them with one click (works for participants and other coaches).
- Participant login → personal dashboard with their Measurement Games results history.
- Sample/demo data (1 coach + 3 demo athletes, including a sample Measurement Games session) pre-loaded so you can see it working immediately.
- Installable as a home-screen app on phones (Add to Home Screen / PWA) — athletes and coaches get an app icon and a full-screen view, no app store needed. See "Using it as an app on your phone" below.

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

Before giving real people access: log in as the demo coach, open **My
Account** in the top bar, and update the name/email to your own (e.g.
Simon / `simon@justagame.co.nz`), then set a real password in the same
page. If other people will coach too, use the **Coaches** link to give
each of them their own named login rather than sharing one account.

## Coach accounts

- **My Account** (top bar) — edit your own name/email, and change your
  password. Works for the seeded demo coach account too, so you can turn
  it into a real one without anyone touching the database directly.
- **Coaches** (top bar, coach nav) — lists every coach account. **Add
  Coach** creates a new one (you set a temporary password, same as
  adding a participant); **Deactivate** disables a coach's login without
  deleting their account or anything they've logged (consistent with
  this app's "never delete, just deactivate" approach elsewhere). You
  can't deactivate your own account from here — have another coach do it,
  or just stop sharing the login.
- **Forgot password** — there's no email/reset-link flow (no email
  sending is set up). Instead, the **Forgot your password?** link on the
  login page tells the person to contact their coach, and any coach can
  issue a fresh password with one click: a **Reset Password** button on
  a participant's page, or on another coach's row in **Coaches**. The new
  password is shown once in a flash message right after — copy it and
  send it to them straight away (by text, email, in person, whatever's
  easiest), since it won't be shown again. This also signs them out of
  any device they were already logged in on, so the old password stops
  working immediately.

## Project structure

```
justagame-portal/
  app.py        routes + request handlers (start here)
  core.py       tiny zero-dependency web framework (routing, request/response)
  db.py         SQLite schema + seed data
  auth.py       password hashing, sessions
  views.py      page templates (plain Python functions, not Jinja)
  constants.py  Measurement Games structure (plus unused levels/points thresholds, paused for now)
  static/       CSS, logo, PWA icons + manifest.json (sw.js is served from app.py, not static/)
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
4. **Passwords & details** — every user (coach or athlete) can update their
   own name, email and password from **My Account** in the top bar.
5. **Other coaches** — use **Coaches** in the top bar to add a login for
   each coach, or deactivate one that shouldn't have access any more.

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

## Using it as an app on your phone

The portal can be added to a phone's home screen like a regular app — a
real icon, a full-screen window (no browser address bar), and the static
parts (CSS, icons) cached so it opens instantly. This needs the site to
be served over **HTTPS** (already the case once it's live on Render or
on `athletes.justagame.co.nz`) — it won't show the install option over
plain `http://localhost`.

**On iPhone (Safari):**
1. Open the portal URL in Safari.
2. Tap the **Share** icon (square with an arrow) → **Add to Home Screen**.
3. Tap **Add**. The "Just A Game" icon now opens full-screen, like an app.

**On Android (Chrome):**
1. Open the portal URL in Chrome.
2. Tap the **⋮** menu → **Add to Home screen** (or **Install app**, if
   Chrome offers it directly).
3. Tap **Add** / **Install**.

Worth passing this on to athletes and coaches once the portal is live —
it's the easiest way for them to get to it day-to-day.

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
