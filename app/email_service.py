import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from flask import current_app


def _plain_text_from_html(html_body: str) -> str:
    """Very small fallback when only HTML text is provided."""
    return (
        html_body.replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
        .replace("</p>", "\n")
        .replace("</h1>", "\n")
        .replace("</h2>", "\n")
        .replace("</h3>", "\n")
    )


def send_email(to_email, subject, text_body=None, html_body=None, attachments=None):
    """Send an email through configured SMTP settings.

    The function is intentionally safe for development: if SMTP is not
    configured, suppressed, or unavailable, it logs the problem and returns
    False without crashing the request.
    """
    if not to_email:
        current_app.logger.info("Email skipped because recipient was empty: %s", subject)
        return False

    if current_app.config.get("MAIL_SUPPRESS_SEND", True):
        current_app.logger.info("Email suppressed: to=%s subject=%s", to_email, subject)
        return False

    server = current_app.config.get("MAIL_SERVER")
    port = int(current_app.config.get("MAIL_PORT", 587))
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username

    if not server or not sender:
        current_app.logger.warning("Email not sent because SMTP server/sender is not configured.")
        return False

    original_recipient = to_email
    redirect_recipient = (current_app.config.get("MAIL_REDIRECT_ALL_TO") or "").strip()
    if redirect_recipient:
        to_email = redirect_recipient
        subject = f"[Originally to {original_recipient}] {subject}"
        if text_body:
            text_body = f"Original recipient: {original_recipient}\n\n{text_body}"
        if html_body:
            html_body = f"<p><strong>Original recipient:</strong> {escape(original_recipient)}</p>" + html_body

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to_email

    if text_body is None and html_body:
        text_body = _plain_text_from_html(html_body)
    message.set_content(text_body or "")

    if html_body:
        message.add_alternative(html_body, subtype="html")

    for attachment in attachments or []:
        filename = attachment.get("filename") or "attachment.txt"
        content = attachment.get("content") or ""
        mime_type = attachment.get("mime_type") or "application/octet-stream"
        maintype, _, subtype = mime_type.partition("/")
        subtype = subtype or "octet-stream"

        if isinstance(content, bytes):
            message.add_attachment(
                content,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )
        elif maintype == "text":
            message.add_attachment(
                str(content),
                subtype=subtype,
                filename=filename,
            )
        else:
            message.add_attachment(
                str(content).encode("utf-8"),
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

    try:
        if current_app.config.get("MAIL_USE_SSL", False):
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(server, port, context=context, timeout=15) as smtp:
                if username:
                    smtp.login(username, password or "")
                smtp.send_message(message)
        else:
            with smtplib.SMTP(server, port, timeout=15) as smtp:
                if current_app.config.get("MAIL_USE_TLS", True):
                    smtp.starttls(context=ssl.create_default_context())
                if username:
                    smtp.login(username, password or "")
                smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - depends on external SMTP
        current_app.logger.warning("Email could not be sent to %s: %s", to_email, exc)
        return False

    current_app.logger.info("Email sent: to=%s subject=%s", to_email, subject)
    return True


def send_registration_otp_email(user, otp_code, expires_in_minutes=10):
    """Email a registration OTP to a patient."""
    safe_name = escape(user.first_name or "Patient")
    text_body = (
        f"Hello {user.first_name},\n\n"
        f"Your MediQueue email verification code is: {otp_code}\n\n"
        f"This code expires in {expires_in_minutes} minutes.\n\n"
        "If you did not create a MediQueue account, please ignore this email."
    )
    html_body = f"""
    <div style=\"font-family: Arial, sans-serif; color: #0f172a; line-height: 1.6;\">
      <h2 style=\"color: #2563eb;\">MediQueue email verification</h2>
      <p>Hello {safe_name},</p>
      <p>Your email verification code is:</p>
      <p style=\"font-size: 28px; font-weight: 700; letter-spacing: 6px; color: #0f172a;\">{otp_code}</p>
      <p>This code expires in <strong>{expires_in_minutes} minutes</strong>.</p>
      <p>If you did not create a MediQueue account, please ignore this email.</p>
    </div>
    """
    return send_email(
        user.email,
        "Your MediQueue email verification code",
        text_body=text_body,
        html_body=html_body,
    )


def send_notification_email(user, title, message, attachments=None):
    """Send an email copy of an in-app notification to one user."""
    if user is None or not getattr(user, "email", None):
        return False

    display_name = escape(getattr(user, "first_name", None) or "MediQueue user")
    safe_title = escape(title or "MediQueue notification")
    safe_message = escape(message or "")

    text_body = (
        f"Hello {getattr(user, 'first_name', None) or 'MediQueue user'},\n\n"
        f"{title}\n\n"
        f"{message}\n\n"
        "This email was sent because you received an in-app notification in MediQueue."
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #0f172a; line-height: 1.6;">
      <h2 style="color: #2563eb;">MediQueue notification</h2>
      <p>Hello {display_name},</p>
      <h3>{safe_title}</h3>
      <p>{safe_message}</p>
      <p style="color: #475569; font-size: 13px;">
        This email was sent because you received an in-app notification in MediQueue.
      </p>
    </div>
    """
    return send_email(
        user.email,
        f"MediQueue notification: {title}",
        text_body=text_body,
        html_body=html_body,
        attachments=attachments,
    )
