# Deploying to Render (free tier)

Render deploys from a Git repository, not a zip upload — so step 1 is
getting this code onto GitHub. Account creation and logins are things
I can't do on your behalf, but here's exactly what to click.

## Important: read this before you put real athlete data in

Render's **free** web services have an *ephemeral* filesystem — every
time the service spins down (it sleeps after 15 minutes with no
visitors) or you redeploy, the local file is wiped. This app stores
everything in a local SQLite file (`data/justagame.db`), so **on the
free tier, logged activity/badges can be lost** whenever the service
sleeps and restarts.

Free tier is fine for: trying it out, showing coaches/athletes a demo,
deciding if this is the right tool.

For real season data, you'd want Render's **Starter plan ($7/month)**
with a small **persistent disk** added (a few cents/month extra) — that
removes both the sleep behaviour and the data wipe. You can start free
today and upgrade later with no code changes; just say the word and
I'll give you the persistent-disk config for `render.yaml`.

## Step 1 — Push the code to GitHub

1. If you don't have a GitHub account, create one free at github.com.
2. Create a new repository (e.g. `justagame-portal`) — Public is fine,
   Private also works if you connect Render to GitHub via OAuth in step 2.
3. From a terminal, inside the `justagame-portal` folder I gave you:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/justagame-portal.git
   git push -u origin main
   ```

   (GitHub will show you this exact set of commands when you create the
   repo, with your username already filled in.)

## Step 2 — Create the Render service

1. Go to render.com and sign up free (no card required).
2. Click **New +** → **Web Service**.
3. Either connect your GitHub account and pick the `justagame-portal`
   repo, or choose **Public Git Repository** and paste the repo URL —
   either works.
4. Fill in:
   - **Name:** `justagame-portal` (or whatever you like — this becomes part of your `.onrender.com` URL)
   - **Language/Runtime:** Python 3
   - **Build Command:** *(leave blank — there's nothing to install)*
   - **Start Command:** `python3 app.py`
   - **Instance Type:** Free
5. Click **Create Web Service**. First deploy takes a couple of minutes.
6. Once it's live, Render gives you a URL like
   `https://justagame-portal.onrender.com` — that's the link to put on
   justagame.co.nz.

## Step 3 — Change the demo coach password

The seeded demo coach login (`coach@justagame.co.nz` / `CoachDemo123!`)
will work on the live site too. Log in and, for now, just use "Add
Participant" to set up real athletes — there's no in-app password
change yet, so treat the live URL as not-quite-public until you're
ready (or tell me and I'll add a "change my password" page).

## Later: adding a persistent disk (removes the data-wipe risk)

When you're ready to move off the free tier, upgrade the service to
**Starter** in the Render dashboard, then add a disk:

- Mount path: `/app/data`
- Size: 1 GB is far more than enough

Tell me when you've done this and I'll double check the app's `db.py`
path lines up with the mount path you chose.
