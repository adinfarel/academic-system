"""
services/email.py — Email service for PolsriEduAI

Responsible for all email delivery systems:
- Email approval (verification code)
- Email rejection (rejection notification)

Libraries used: smtplib (built-in to Python, no installation required)
+ email.mime for beautiful HTML email formatting

Why not use an external library like sendgrid?
→ smtplib is sufficient for this scope
→ No additional dependencies needed
→ Easier to understand how it works
"""

import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.utils.logger import get_logger
# LOGGER
logger = get_logger(__name__)

from backend.config import get_settings

settings = get_settings()

def generate_verification_code(length: int = 8) -> str:
    """
    Generate secure random verification codes.

    Characters used: uppercase letters + numbers.
    → Avoid similar letters: O (the letter O) vs. 0 (the number zero).
    → Avoid l (lowercase l) vs. 1 (the number one) vs. I (uppercase I).
    → So students don't get confused when reading emails.

    Args:
        length: code length (default 8 characters).

    Returns:
        str: random code like "AX7K2P9M"
    """
    alphabet = (
        string.ascii_uppercase.replace("0", '').replace("I", "").replace("L", "") +
        string.digits.replace("0", "").replace("1", "")
    )
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def _create_smtp_connection():
    """
    Establish a connection to the Gmail SMTP server.

    Protocol used: STARTTLS (port 587)
    → Start an unencrypted connection
    → Upgrade to TLS (encryption) before sending credentials
    → More secure than straight SSL (port 465) for Gmail

    Connection flow:
    1. Connect to smtp.gmail.com:587
    2. ehlo() → Introduce yourself to the server ("Hello, I'm PolsriEduAI")
    3. starttls() → Enable encryption
    4. ehlo() again → Introduce yourself again after enabling encryption
    5. login() → Authenticate with App Password

    Returns:
    smtplib.SMTP: Authenticated SMTP connection

    Raises:
    Exception: if connection or login fails
    """
    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    return server

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Core functionality for sending a single email.

    The email format we send is multipart/alternate
    → Contains both plain text (fallback) and HTML (primary) versions
    → If the email client doesn't support HTML, display plain text
    → Best practice for maximum compatibility

    Arguments:
        to_email: email recipient address
        subject: email subject
        html_body: email body in HTML format

    Returns:
        bool: True on success, False on failure
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['Form'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        
        plain_text = "Email ini membutuhkan HTML viewer untuk ditampilkan dengan benar."
        
        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        server = _create_smtp_connection()
        server.sendmail(
            settings.SMTP_FROM_EMAIL,
            to_email,
            msg.as_string(),
        )
        server.quit()
        
        logger.info(f"[EMAIL] Sent to {to_email} - {subject}")
        return True
    
    except Exception as e:
        logger.error(f"[EMAIL] Fail send to {to_email}: {e}")
        return False
    
def send_approval_email(
    to_email: str,
    nama: str,
    nim: str,
    verification_code: str,
) -> bool:
    """
    Send an approval email with a verification code to the student.

    This email is sent when the admin approves the student's registration.
    Contains the code used as the first password to log in.

    Args:
        to_email: Student email
        name: Student's full name
        nim: Student's student ID number
        verification_code: 8-character generated code

    Returns:
        bool: True if sent successfully
    """
    subject = "Pendaftaran PolsriEduAI Disetujui - Kode Akses Anda"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #fff;
                     border-radius: 12px; overflow: hidden; }}
        .header {{ background: #111; padding: 32px; text-align: center; }}
        .header h1 {{ color: #fff; font-size: 20px; font-weight: 500;
                     margin: 0; letter-spacing: -0.5px; }}
        .body {{ padding: 32px; }}
        .greeting {{ font-size: 15px; color: #333; margin-bottom: 16px; }}
        .info {{ font-size: 14px; color: #666; line-height: 1.6;
                margin-bottom: 24px; }}
        .code-box {{ background: #f8f8f8; border: 1px dashed #ddd;
                    border-radius: 8px; padding: 20px; text-align: center;
                    margin: 24px 0; }}
        .code-label {{ font-size: 11px; color: #999; letter-spacing: 1px;
                      margin-bottom: 8px; }}
        .code {{ font-size: 32px; font-weight: 700; color: #111;
                letter-spacing: 6px; font-family: monospace; }}
        .nim-box {{ font-size: 13px; color: #888; margin-top: 8px; }}
        .warning {{ font-size: 12px; color: #999; background: #fffbf0;
                   border-left: 3px solid #f0c040; padding: 12px 16px;
                   border-radius: 4px; margin-top: 24px; }}
        .footer {{ padding: 20px 32px; border-top: 1px solid #f0f0f0;
                  font-size: 12px; color: #bbb; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>PolsriEduAI</h1>
        </div>
        <div class="body">
          <p class="greeting">Halo, <strong>{nama}</strong>!</p>
          <p class="info">
            Pendaftaran akun Anda di sistem PolsriEduAI telah <strong>disetujui</strong>
            oleh admin. Gunakan kode di bawah ini sebagai password pertama Anda untuk login.
          </p>
          <div class="code-box">
            <div class="code-label">KODE AKSES ANDA</div>
            <div class="code">{verification_code}</div>
            <div class="nim-box">Login dengan username: <strong>{nim}</strong></div>
          </div>
          <p class="info">
            Setelah login pertama, Anda akan diminta untuk mengganti password
            dengan password baru yang lebih personal.
          </p>
          <div class="warning">
            Jangan bagikan kode ini ke siapapun. Kode bersifat rahasia dan
            hanya untuk digunakan sekali saat login pertama.
          </div>
        </div>
        <div class="footer">
          PolsriEduAI — Sistem Akademik Terintegrasi Politeknik Sriwijaya
        </div>
      </div>
    </body>
    </html>
    """
    
    return _send_email(to_email=to_email, subject=subject, html_body=html_body)

def send_rejection_email(
    to_email: str,
    nama: str,
    reason: str = None,
) -> bool:
    """
    Send a registration rejection email to the student.

    Sent when the admin rejects the registration.
    Contains the reason for the rejection if the admin provides it, or a general message if not.

    Args:
        to_email: student email
        name: student's full name
        reason: reason for rejection (optional, entered by the admin)

    Returns:
        bool: True if sent successfully
    """
    subject = "Informasi Pendaftaran PolsriEduAI"

    alasan_text = (
        f"<p class='info'><strong>Alasan:</strong> {reason}</p>"
        if reason else ""
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #fff;
                     border-radius: 12px; overflow: hidden; }}
        .header {{ background: #111; padding: 32px; text-align: center; }}
        .header h1 {{ color: #fff; font-size: 20px; font-weight: 500; margin: 0; }}
        .body {{ padding: 32px; }}
        .greeting {{ font-size: 15px; color: #333; margin-bottom: 16px; }}
        .info {{ font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 16px; }}
        .notice {{ background: #fff5f5; border-left: 3px solid #e55;
                  padding: 12px 16px; border-radius: 4px;
                  font-size: 13px; color: #c33; margin: 20px 0; }}
        .footer {{ padding: 20px 32px; border-top: 1px solid #f0f0f0;
                  font-size: 12px; color: #bbb; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header"><h1>PolsriEduAI</h1></div>
        <div class="body">
          <p class="greeting">Halo, <strong>{nama}</strong>.</p>
          <div class="notice">
            Pendaftaran akun Anda di PolsriEduAI tidak dapat disetujui
            saat ini berdasarkan verifikasi data yang dilakukan admin.
          </div>
          {alasan_text}
          <p class="info">
            Jika Anda merasa ini adalah kesalahan, silakan hubungi bagian
            akademik kampus secara langsung dengan membawa kartu identitas mahasiswa.
          </p>
        </div>
        <div class="footer">
          PolsriEduAI — Sistem Akademik Terintegrasi Politeknik Sriwijaya
        </div>
      </div>
    </body>
    </html>
    """

    return _send_email(to_email, subject, html_body)