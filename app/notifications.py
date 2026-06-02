"""
Email notifications for DirtDesk.
Uses stdlib smtplib — no extra dependencies.
Silently logs errors rather than crashing the request if mail fails.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


def _send_email(to_address, subject, body_text, body_html=None):
    """Send an email. Returns True on success, False on failure."""
    app = current_app._get_current_object()
    server   = app.config.get('MAIL_SERVER', '')
    port     = app.config.get('MAIL_PORT', 465)
    username = app.config.get('MAIL_USERNAME', '')
    password = app.config.get('MAIL_PASSWORD', '')
    from_addr = app.config.get('MAIL_FROM', '') or username
    use_ssl  = app.config.get('MAIL_USE_SSL', True)

    if not server or not username or not password:
        logger.warning('Email not configured — skipping notification to %s', to_address)
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'DirtDesk <{from_addr}>'
    msg['To']      = to_address
    msg.attach(MIMEText(body_text, 'plain'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html'))

    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(from_addr, to_address, msg.as_string())
        smtp.quit()
        logger.info('Email sent to %s: %s', to_address, subject)
        return True
    except Exception as exc:
        logger.error('Failed to send email to %s: %s', to_address, exc)
        return False


def notify_authorization_requested(auth):
    """Email the customer when a new authorization request is added to their RO."""
    ro       = auth.repair_order
    customer = ro.customer
    if not customer.email:
        return

    shop_name  = current_app.config.get('SHOP_NAME', 'Red Dirt UTV Performance')
    shop_phone = current_app.config.get('SHOP_PHONE', '')
    machine    = ro.machine.display_name if ro.machine else 'your machine'

    subject = f'Authorization Needed — {ro.ro_number} — {shop_name}'

    text = f"""Hi {customer.name},

We've found something on {machine} that needs your approval before we can continue.

What we found:
{auth.description}

Please call or text us to approve or decline:
  {shop_phone or shop_name}

Work Order: {ro.ro_number}

Thanks,
{shop_name}
"""

    html = f"""
<p>Hi {customer.name},</p>
<p>We've found something on <strong>{machine}</strong> that needs your approval before we can continue.</p>
<table style="border-left:4px solid #c0392b;padding:8px 16px;background:#fdf3f3;margin:16px 0;">
  <tr><td><strong>What we found:</strong><br>{auth.description}</td></tr>
</table>
<p>Please <strong>call or text us</strong> to approve or decline:<br>
<strong>{shop_phone or shop_name}</strong></p>
<p style="color:#888;font-size:.9em;">Work Order: {ro.ro_number}</p>
<p>Thanks,<br>{shop_name}</p>
"""
    _send_email(customer.email, subject, text, html)


def notify_ro_status_changed(ro, new_status):
    """Email the customer when their RO status changes to Complete or Delivered."""
    customer = ro.customer
    if not customer.email:
        return

    shop_name  = current_app.config.get('SHOP_NAME', 'Red Dirt UTV Performance')
    shop_phone = current_app.config.get('SHOP_PHONE', '')
    machine    = ro.machine.display_name if ro.machine else 'your machine'

    if new_status == 'Complete':
        subject = f'Your machine is ready — {ro.ro_number}'
        action  = 'is ready for pickup'
    elif new_status == 'Delivered':
        subject = f'Work order closed — {ro.ro_number}'
        action  = 'has been delivered/closed'
    else:
        return

    text = f"""Hi {customer.name},

Good news! {machine} {action}.

Work Order: {ro.ro_number}
Total: ${float(ro.grand_total or 0):.2f}

Give us a call if you have any questions:
  {shop_phone or shop_name}

Thanks,
{shop_name}
"""

    html = f"""
<p>Hi {customer.name},</p>
<p>Good news! <strong>{machine}</strong> {action}.</p>
<table style="border-left:4px solid #27ae60;padding:8px 16px;background:#f3fdf5;margin:16px 0;">
  <tr><td><strong>Work Order:</strong> {ro.ro_number}</td></tr>
  <tr><td><strong>Total:</strong> ${float(ro.grand_total or 0):.2f}</td></tr>
</table>
<p>Give us a call if you have any questions:<br>
<strong>{shop_phone or shop_name}</strong></p>
<p>Thanks,<br>{shop_name}</p>
"""
    _send_email(customer.email, subject, text, html)
