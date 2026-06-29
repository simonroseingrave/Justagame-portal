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
   - **Build Command:** `pip install -r requirements.txt` (Render requires
     something here even though this app has no real dependencies — this
     is safe, pip just finds nothing to install and exits immediately)
   - **Start Command:** `python3 app.py`
   - **Instance Type:** Free
5. Click **Create Web Service**. First deploy takes a couple of minutes.
6. Once it's live, Render gives you a URL like
   `https://justagame-portal.onrender.com` — that's the link to put on
   justagame.co.nz.

## Step 3 — Change the demo coach password

The seeded demo coach login (`coach@justagame.co.nz` / `CoachDemo123!`)
will work on the live site too. Log in, click **Change password** in the
top bar, and set a real password before sharing the link with anyone.
Do this first — treat the live URL as not-quite-public until you have.

## Later: adding a persistent disk (removes the data-wipe risk)

When you're ready to move off the free tier:

1. Open your service in the Render dashboard → **Settings** → change
   **Instance Type** from Free to **Starter** ($7/month). Render will
   ask for a payment method at this point — that's a billing step only
   you can complete.
2. Go to the service's **Disks** tab → **Add Disk**:
   - Mount path: `/opt/render/project/src/data`
   - Size: 1 GB is far more than enough (~$0.25/month extra)
3. Click **Add Disk**. Render redeploys automatically; the disk is live
   once that finishes.

The mount path above already matches exactly where this app stores its
database (`data/justagame.db`, relative to the code), so no code changes
are needed — the disk just needs to be mounted at that exact path.

## Connecting it to athletes.justagame.co.nz

This makes the portal live at `athletes.justagame.co.nz` instead of the
`onrender.com` address, and adds a link to it from the main site.

**1. Add the domain in Render**
- Service → **Settings** → **Custom Domains** → **+ Add Custom Domain**
- Enter `athletes.justagame.co.nz` → **Save**

**2. Add a DNS record in Squarespace**
- Squarespace account → **Settings** → **Domains** → click `justagame.co.nz`
- **DNS Settings** → **Custom Records** → **Add Record**
- Type: `CNAME` · Host: `athletes` · Data: `justagame-portal.onrender.com`
- Save

**3. Verify**
- Back in Render, click **Verify** next to the domain (DNS can take a
  few minutes to a few hours to propagate — if it fails at first, wait
  and retry). Render issues the HTTPS certificate automatically once
  verified.

**4. Link it from the main site**
- Edit the Coaching / Programmes page in Squarespace → add a **Button**
  block → URL `https://athletes.justagame.co.nz` → label it (e.g.
  "Athlete Portal Login") → save and publish.
