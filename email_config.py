# Just A Game — email configuration
# ─────────────────────────────────
# Fill in the values below, then restart the portal.
# Keep this file out of version control (add it to .gitignore).
#
# Alternatively, set these as environment variables instead
# (environment variables take precedence over this file):
#
#   export JAG_SMTP_HOST=smtp.gmail.com
#   export JAG_SMTP_PORT=587
#   export JAG_SMTP_USER=portal@justagame.co.nz
#   export JAG_SMTP_PASS=xxxx xxxx xxxx xxxx
#   export JAG_APP_URL=https://portal.justagame.co.nz

# Google Workspace / Gmail SMTP settings
HOST     = "smtp.gmail.com"
PORT     = 587

# The Google Workspace address emails are sent FROM
# (must match the account whose App Password you generate)
USER     = "portal@justagame.co.nz"   # ← change to your actual address

# Google App Password — 16 characters, generated at:
# myaccount.google.com → Security → 2-Step Verification → App passwords
# Enter them with the spaces as shown (or without — both work)
PASSWORD = ""                          # ← paste your App Password here

# Public URL of the portal (used to build the login link in emails)
# No trailing slash
APP_URL  = "https://portal.justagame.co.nz"  # ← change to your actual URL

# Optional: customise the From display name
# Defaults to "Just A Game <USER>" if left blank
FROM_    = "Just A Game <portal@justagame.co.nz>"
