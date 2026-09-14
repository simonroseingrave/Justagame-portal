"""Email helper for Just A Game portal.

Reads config from environment variables (preferred for production) or falls
back to email_config.py if that file exists alongside this one.

Required config keys
--------------------
JAG_SMTP_HOST   - e.g. smtp.gmail.com
JAG_SMTP_PORT   - e.g. 587
JAG_SMTP_USER   - full sending address, e.g. portal@justagame.co.nz
JAG_SMTP_PASS   - Google App Password (16 chars, no spaces)
JAG_APP_URL     - public root URL, e.g. https://portal.justagame.co.nz
                  (used to build the login link in emails)

Optional
--------
JAG_SMTP_FROM   - "From" display name + address, defaults to
                  "Just A Game <JAG_SMTP_USER>"

If NONE of the required keys are set the module loads fine but all send
functions become no-ops, so the portal works without email configured.
"""

import os
import smtplib
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Config resolution ──────────────────────────────────────────────────────────

def _load_config():
    """Return config dict from env vars, falling back to email_config.py."""
    cfg = {
        "host":     os.environ.get("JAG_SMTP_HOST", ""),
        "port":     os.environ.get("JAG_SMTP_PORT", "587"),
        "user":     os.environ.get("JAG_SMTP_USER", ""),
        "password": os.environ.get("JAG_SMTP_PASS", ""),
        "from":     os.environ.get("JAG_SMTP_FROM", ""),
        "app_url":  os.environ.get("JAG_APP_URL", "").rstrip("/"),
    }

    # Try email_config.py as fallback (values there only fill in missing slots)
    if not cfg["host"] or not cfg["user"]:
        try:
            import importlib, importlib.util
            spec = importlib.util.spec_from_file_location(
                "email_config",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.py"),
            )
            if spec:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for key in ("host", "port", "user", "password", "from_", "app_url"):
                    attr = "from_" if key == "from" else key
                    val = getattr(mod, key.upper(), None) or getattr(mod, attr.upper(), None)
                    if val and not cfg.get(key if key != "from_" else "from"):
                        cfg["from" if key == "from_" else key] = str(val)
        except Exception:
            pass

    if not cfg["from"]:
        cfg["from"] = f"Just A Game <{cfg['user']}>" if cfg["user"] else ""

    return cfg


_CFG = _load_config()


def is_configured():
    """True if the minimum SMTP config is present."""
    return bool(_CFG["host"] and _CFG["user"] and _CFG["password"])


# ── Low-level send ─────────────────────────────────────────────────────────────

def _send(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send one email. Returns True on success, False on failure (logs to stderr)."""
    if not is_configured():
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = _CFG["from"]
    msg["To"]      = to_email

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        port = int(_CFG["port"])
        with smtplib.SMTP(_CFG["host"], port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(_CFG["user"], _CFG["password"])
            smtp.sendmail(_CFG["user"], to_email, msg.as_string())
        return True
    except Exception:
        print(f"[mailer] Failed to send to {to_email}:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False


# ── HTML email template ────────────────────────────────────────────────────────

_NAVY  = "#2D323B"
_GOLD  = "#F0A82E"
_BG    = "#F3F4F5"
_WHITE = "#FFFFFF"


def _html_wrap(headline: str, body_rows: str, cta_label: str = "Log in now",
               cta_url: str = "") -> str:
    cta_url = cta_url or (_CFG["app_url"] + "/login")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{headline}</title>
</head>
<body style="margin:0;padding:0;background:{_BG};font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{_BG};padding:32px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="max-width:560px;width:100%;background:{_WHITE};
                    border-radius:12px;overflow:hidden;
                    box-shadow:0 2px 12px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:{_NAVY};padding:28px 36px;text-align:center;">
            <span style="font-size:22px;font-weight:800;color:{_GOLD};
                         letter-spacing:0.03em;font-family:Arial,sans-serif;">
              Just A Game
            </span>
            <div style="font-size:12px;color:rgba(255,255,255,.55);
                        margin-top:4px;letter-spacing:0.08em;text-transform:uppercase;">
              Athlete Adaptability Tracking
            </div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 36px 8px;">
            <h2 style="margin:0 0 18px;font-size:20px;color:{_NAVY};font-weight:700;">
              {headline}
            </h2>
            {body_rows}
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:8px 36px 32px;text-align:center;">
            <a href="{cta_url}"
               style="display:inline-block;background:{_GOLD};color:{_NAVY};
                      font-weight:800;font-size:15px;padding:13px 32px;
                      border-radius:8px;text-decoration:none;margin-top:8px;">
              {cta_label}
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:{_BG};padding:18px 36px;text-align:center;
                     font-size:12px;color:#6E737B;border-top:1px solid #E5E7EB;">
            This email was sent automatically by the Just A Game portal.<br>
            If you did not expect it, please ignore it.
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _row(label: str, value: str) -> str:
    return (
        f'<p style="margin:6px 0;font-size:15px;color:#374151;">'
        f'<span style="font-weight:700;color:{_NAVY};">{label}:</span> '
        f'<span style="font-family:monospace;background:#F3F4F5;padding:2px 8px;'
        f'border-radius:4px;">{value}</span></p>'
    )


def _para(text: str) -> str:
    return (
        f'<p style="margin:0 0 14px;font-size:15px;color:#374151;line-height:1.6;">'
        f'{text}</p>'
    )


# ── Public send functions ──────────────────────────────────────────────────────

def send_welcome_coach(name: str, email: str, password: str) -> bool:
    """Welcome email for a newly created coach account."""
    login_url = _CFG["app_url"] + "/login"
    subject = "Welcome to the Just A Game portal"
    html = _html_wrap(
        headline=f"Welcome, {name}!",
        body_rows=(
            _para("Your coach account on the Just A Game Athlete Adaptability Tracking portal "
                  "has been created. Use the details below to log in.")
            + _row("Email",    email)
            + _row("Password", password)
            + _para(
                '<span style="color:#92400e;font-size:13px;">'
                '&#9888;&nbsp; Please change your password after your first login '
                '(Account &rarr; Change Password).</span>'
            )
        ),
        cta_label="Log in to the portal",
        cta_url=login_url,
    )
    text = (
        f"Welcome to Just A Game, {name}!\n\n"
        f"Your coach account has been created.\n\n"
        f"Login URL: {login_url}\n"
        f"Email:     {email}\n"
        f"Password:  {password}\n\n"
        f"Please change your password after your first login."
    )
    return _send(email, subject, html, text)


def send_welcome_athlete(name: str, email: str, password: str) -> bool:
    """Welcome email for a newly created athlete/participant account."""
    login_url = _CFG["app_url"] + "/login"
    subject = "Your Just A Game athlete portal login"
    html = _html_wrap(
        headline=f"Welcome, {name}!",
        body_rows=(
            _para("Your coach has set up an account for you on the Just A Game "
                  "Athlete Adaptability Tracking portal. Log in to see your progress "
                  "and results.")
            + _row("Email",    email)
            + _row("Password", password)
            + _para(
                '<span style="color:#92400e;font-size:13px;">'
                '&#9888;&nbsp; We recommend changing your password after your first login '
                '(Account &rarr; Change Password).</span>'
            )
        ),
        cta_label="View my progress",
        cta_url=login_url,
    )
    text = (
        f"Welcome to Just A Game, {name}!\n\n"
        f"Your athlete portal account has been created.\n\n"
        f"Login URL: {login_url}\n"
        f"Email:     {email}\n"
        f"Password:  {password}\n\n"
        f"You can change your password after logging in."
    )
    return _send(email, subject, html, text)


def send_password_reset(name: str, email: str, new_password: str) -> bool:
    """Password reset notification — replaces the flash-message approach."""
    login_url = _CFG["app_url"] + "/login"
    subject = "Your Just A Game portal password has been reset"
    html = _html_wrap(
        headline="Password reset",
        body_rows=(
            _para(f"Hi {name}, your password on the Just A Game portal has been reset "
                  "by an administrator. Use the temporary password below to log in, "
                  "then change it straight away.")
            + _row("Email",             email)
            + _row("Temporary password", new_password)
            + _para(
                '<span style="color:#92400e;font-size:13px;">'
                '&#9888;&nbsp; Change your password immediately after logging in.</span>'
            )
        ),
        cta_label="Log in now",
        cta_url=login_url,
    )
    text = (
        f"Hi {name},\n\n"
        f"Your password on the Just A Game portal has been reset.\n\n"
        f"Login URL:          {login_url}\n"
        f"Email:              {email}\n"
        f"Temporary password: {new_password}\n\n"
        f"Please change your password as soon as you log in."
    )
    return _send(email, subject, html, text)
