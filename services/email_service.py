# services/email_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Handles sending emails via Gmail SMTP.
#
# Key features:
#   - Modern HTML card-style templates with Jobandu logo
#   - Support for multiple recipients (TO list)
#   - Support for CC list
#   - Support for file attachments (CV/resume)
#   - Admin notifications go to ADMIN_NOTIFICATION_EMAILS (not the Gmail sender)
#
# IMPORTANT: Use a Gmail App Password, not your real Gmail password.
# ─────────────────────────────────────────────────────────────────────────────

import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional

from config import settings
from utils.logger import AppLogger

logger = AppLogger.get_logger()

# Jobandu brand logo (used in all email templates)
LOGO_URL = "https://jobandu.de/wp-content/uploads/2025/05/1.png"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_email_list(raw: str) -> List[str]:
    """
    Converts a comma-separated email string from config into a clean list.
    Example: "hr@jobandu.dk, ops@jobandu.dk" → ["hr@jobandu.dk", "ops@jobandu.dk"]
    Empty strings are filtered out.
    """
    return [e.strip() for e in raw.split(",") if e.strip()]


def _card_wrapper(inner_html: str) -> str:
    """
    Wraps any inner HTML content inside the shared modern email card layout.
    Every template uses this so they all look consistent.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#f0f2f5;padding:40px 0;">
    <tr>
      <td align="center">

        <!-- Card -->
        <table width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;background:#ffffff;
                      border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.10);">

          <!-- Header with gradient + logo -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
                       padding:36px 40px;text-align:center;">
              <img src="{LOGO_URL}"
                   alt="Jobandu"
                   width="160"
                   style="display:block;margin:0 auto;max-width:160px;height:auto;" />
            </td>
          </tr>

          <!-- Body content injected here -->
          <tr>
            <td style="padding:40px 40px 32px 40px;color:#1a1a2e;">
              {inner_html}
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <hr style="border:none;border-top:1px solid #e8ecf0;margin:0;" />
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;text-align:center;background:#fafbfc;
                       border-radius:0 0 16px 16px;">
              <p style="margin:0 0 6px;font-size:13px;color:#6b7280;">
                © 2025 Jobandu · Connecting workers with employers
              </p>
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                <a href="https://jobandu.de" style="color:#0f3460;text-decoration:none;">jobandu.de</a>
              </p>
            </td>
          </tr>

        </table>
        <!-- /Card -->

      </td>
    </tr>
  </table>

</body>
</html>"""


# ── Core send function ─────────────────────────────────────────────────────────

async def send_email(
    to_emails: List[str],
    subject: str,
    body_html: str,
    cc_emails: Optional[List[str]] = None,
    attachment_path: Optional[str] = None,   # local file path to attach
) -> bool:
    """
    Sends an HTML email via Gmail SMTP.

    Args:
        to_emails:       List of recipient email addresses
        subject:         Email subject line
        body_html:       Full HTML content (use _card_wrapper() for branded look)
        cc_emails:       Optional list of CC email addresses
        attachment_path: Optional path to a local file to attach (e.g. CV PDF)

    Returns:
        bool: True if sent successfully, False otherwise
    """

    # Use "mixed" when we have attachments, "alternative" when HTML-only
    if attachment_path:
        message = MIMEMultipart("mixed")
    else:
        message = MIMEMultipart("alternative")

    message["From"] = settings.GMAIL_USER
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject

    if cc_emails:
        message["Cc"] = ", ".join(cc_emails)

    # Attach the HTML body
    html_part = MIMEText(body_html, "html")
    message.attach(html_part)

    # Attach file if provided (e.g. CV/resume)
    if attachment_path and os.path.exists(attachment_path):
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as f:
            file_data = f.read()

        file_part = MIMEApplication(file_data, Name=filename)
        file_part["Content-Disposition"] = f'attachment; filename="{filename}"'
        message.attach(file_part)

    # Build the full recipients list (TO + CC) for SMTP delivery
    all_recipients = list(to_emails)
    if cc_emails:
        all_recipients.extend(cc_emails)

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.GMAIL_USER,
            password=settings.GMAIL_APP_PASSWORD,
            recipients=all_recipients,   # explicit list ensures CC is actually delivered
        )
        return True
    except Exception as e:
        logger.error(f"Email failed → {to_emails} | {e}")
        return False


# ── Email templates ────────────────────────────────────────────────────────────

async def send_applicant_confirmation(
    applicant_name: str,
    applicant_email: str,
    cv_path: Optional[str] = None,   # local path to CV file for attachment
):
    """
    Sends a branded confirmation email to the applicant.
    Attaches their uploaded CV so they have a copy in their inbox.
    """
    subject = "We received your application – Jobandu"

    inner = f"""
      <h2 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a2e;">
        Hello, {applicant_name}! 👋
      </h2>
      <p style="margin:0 0 20px;font-size:15px;color:#4b5563;line-height:1.6;">
        Thank you for submitting your application on <strong>Jobandu</strong>.
        We have received your profile and our team will be in touch with you
        shortly via phone or email.
      </p>

      <!-- Info box -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#f0f6ff;border-radius:10px;margin:0 0 24px;">
        <tr>
          <td style="padding:20px 24px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;
                      color:#0f3460;text-transform:uppercase;letter-spacing:0.5px;">
              What happens next?
            </p>
            <ul style="margin:8px 0 0;padding-left:18px;color:#374151;
                       font-size:14px;line-height:1.8;">
              <li>Our admin team reviews your profile</li>
              <li>We match you with suitable employers</li>
              <li>We contact you directly via phone or email</li>
            </ul>
          </td>
        </tr>
      </table>

      <p style="margin:0;font-size:14px;color:#6b7280;">
        If you have any questions, feel free to reply to this email.<br>
        <strong style="color:#1a1a2e;">The Jobandu Team</strong>
      </p>
    """

    body = _card_wrapper(inner)

    # Attach CV if provided so the applicant has a copy
    return await send_email(
        to_emails=[applicant_email],
        subject=subject,
        body_html=body,
        # attachment_path=cv_path,
    )


async def send_employer_confirmation(
    contact_person: str,
    employer_email: str,
    company_name: str,
):
    """Sends a branded confirmation email to the employer after their request."""
    subject = "We received your staff request – Jobandu"

    inner = f"""
      <h2 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a2e;">
        Hello, {contact_person}! 👋
      </h2>
      <p style="margin:0 0 20px;font-size:15px;color:#4b5563;line-height:1.6;">
        Thank you for reaching out to <strong>Jobandu</strong>. We have received
        your staffing request for <strong>{company_name}</strong> and our team
        is already working on finding the right candidates for you.
      </p>

      <!-- Info box -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#f0f6ff;border-radius:10px;margin:0 0 24px;">
        <tr>
          <td style="padding:20px 24px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;
                      color:#0f3460;text-transform:uppercase;letter-spacing:0.5px;">
              What happens next?
            </p>
            <ul style="margin:8px 0 0;padding-left:18px;color:#374151;
                       font-size:14px;line-height:1.8;">
              <li>We review your requirements</li>
              <li>We shortlist suitable candidates from our pool</li>
              <li>Our team contacts you with candidate profiles</li>
            </ul>
          </td>
        </tr>
      </table>

      <p style="margin:0;font-size:14px;color:#6b7280;">
        If you have any questions, feel free to reply to this email.<br>
        <strong style="color:#1a1a2e;">The Jobandu Team</strong>
      </p>
    """

    body = _card_wrapper(inner)

    return await send_email(
        to_emails=[employer_email],
        subject=subject,
        body_html=body,
    )


async def send_admin_notification_new_applicant(
    applicant_name: str,
    applicant_email: str,
    applicant_phone: str = "",
    applicant_skills: list = None,
    applicant_location: str = "",
    applicant_experience_years: int = 0,
    cv_path: Optional[str] = None,   # attach CV so admin sees it immediately
):
    """
    Notifies ALL admin recipients when a new applicant submits a form.
    Sends to ADMIN_NOTIFICATION_EMAILS (not the Gmail sender account).
    CC goes to ADMIN_CC_EMAILS.
    CV is attached as a file so admin can open it directly from the email.
    """
    subject = f"🆕 New Applicant: {applicant_name}"

    skills_html = ""
    if applicant_skills:
        badges = "".join(
            f'<span style="display:inline-block;background:#e0e7ff;color:#3730a3;'
            f'border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600;'
            f'margin:2px;">{s}</span>'
            for s in applicant_skills
        )
        skills_html = f'<p style="margin:4px 0 0;">{badges}</p>'

    inner = f"""
      <h2 style="margin:0 0 4px;font-size:22px;font-weight:700;color:#1a1a2e;">
        New Applicant Submitted
      </h2>
      <p style="margin:0 0 24px;font-size:14px;color:#6b7280;">
        A new job application has been received. Details below.
      </p>

      <!-- Details card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#f8fafc;border-radius:10px;
                    border:1px solid #e2e8f0;margin:0 0 24px;">
        <tr>
          <td style="padding:24px;">

            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Name</span><br>
                  <span style="font-size:15px;color:#1a1a2e;font-weight:600;">
                    {applicant_name}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Email</span><br>
                  <a href="mailto:{applicant_email}"
                     style="font-size:15px;color:#0f3460;text-decoration:none;">
                    {applicant_email}
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Phone</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{applicant_phone or "—"}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Location</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{applicant_location or "—"}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Experience</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{applicant_experience_years} years</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Skills</span><br>
                  {skills_html if skills_html else '<span style="font-size:15px;color:#1a1a2e;">—</span>'}
                </td>
              </tr>
            </table>

          </td>
        </tr>
      </table>

      {'<p style="margin:0 0 16px;font-size:13px;color:#059669;font-weight:600;">📎 CV attached to this email</p>' if cv_path else ''}

      <p style="margin:0;font-size:13px;color:#6b7280;">
        Log in to the admin panel to review the full profile and update the status.
      </p>
    """

    body = _card_wrapper(inner)

    # Recipients: parse from config (not GMAIL_USER)
    to_list = _parse_email_list(settings.ADMIN_NOTIFICATION_EMAILS)
    cc_list = _parse_email_list(settings.ADMIN_CC_EMAILS) or None

    return await send_email(
        to_emails=to_list,
        subject=subject,
        body_html=body,
        cc_emails=cc_list,
        attachment_path=cv_path,   # CV attached for admin too
    )


async def send_admin_notification_new_employer(
    company_name: str,
    contact_person: str,
    contact_email: str = "",
    contact_phone: str = "",
    requirements: list = None,
    location: str = "",
    notes: str = "",
):
    """
    Notifies ALL admin recipients when a new employer submits a staffing request.
    Sends to ADMIN_NOTIFICATION_EMAILS with optional CC.
    """
    subject = f"🏢 New Employer Request: {company_name}"

    requirements_html = ""
    if requirements:
        badges = "".join(
            f'<span style="display:inline-block;background:#dcfce7;color:#166534;'
            f'border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600;'
            f'margin:2px;">{r}</span>'
            for r in requirements
        )
        requirements_html = f'<p style="margin:4px 0 0;">{badges}</p>'

    inner = f"""
      <h2 style="margin:0 0 4px;font-size:22px;font-weight:700;color:#1a1a2e;">
        New Employer Request
      </h2>
      <p style="margin:0 0 24px;font-size:14px;color:#6b7280;">
        A company is looking for staff. Details below.
      </p>

      <!-- Details card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#f8fafc;border-radius:10px;
                    border:1px solid #e2e8f0;margin:0 0 24px;">
        <tr>
          <td style="padding:24px;">

            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Company</span><br>
                  <span style="font-size:15px;color:#1a1a2e;font-weight:600;">
                    {company_name}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Contact Person</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{contact_person}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Email</span><br>
                  <a href="mailto:{contact_email}"
                     style="font-size:15px;color:#0f3460;text-decoration:none;">
                    {contact_email or "—"}
                  </a>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Phone</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{contact_phone or "—"}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Location</span><br>
                  <span style="font-size:15px;color:#1a1a2e;">{location or "—"}</span>
                </td>
              </tr>
              <tr>
                <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:12px;font-weight:600;color:#6b7280;
                               text-transform:uppercase;letter-spacing:0.5px;">Requirements</span><br>
                  {requirements_html if requirements_html else '<span style="font-size:15px;color:#1a1a2e;">—</span>'}
                </td>
              </tr>
              {'<tr><td style="padding:8px 0;"><span style="font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;">Notes</span><br><span style="font-size:14px;color:#374151;line-height:1.6;">' + notes + '</span></td></tr>' if notes else ''}
            </table>

          </td>
        </tr>
      </table>

      <p style="margin:0;font-size:13px;color:#6b7280;">
        Log in to the admin panel to review the full request and update the status.
      </p>
    """

    body = _card_wrapper(inner)

    to_list = _parse_email_list(settings.ADMIN_NOTIFICATION_EMAILS)
    cc_list = _parse_email_list(settings.ADMIN_CC_EMAILS) or None

    return await send_email(
        to_emails=to_list,
        subject=subject,
        body_html=body,
        cc_emails=cc_list,
    )
