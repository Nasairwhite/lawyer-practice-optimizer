"""
Email Delivery System for Lawyer Practice Optimization Diagnostic

This module handles sending emails to lawyers with personalized links
to take the diagnostic assessment.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmailConfig:
    """Configuration for email delivery."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "Practice Optimization Diagnostic")
        self.base_url = os.getenv("BASE_URL", "http://localhost:5000")
        self.link_expiration_days = int(os.getenv("LINK_EXPIRATION_DAYS", "7"))

        # Validate required config
        if not self.smtp_username or not self.smtp_password:
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be set in environment variables")


class EmailTokenManager:
    """Manages secure tokens for diagnostic access."""

    def __init__(self):
        # In production, use a proper database
        self.tokens: Dict[str, Dict] = {}

    def generate_token(self, lawyer_name: str, lawyer_email: str) -> str:
        """
        Generate a secure token for accessing the diagnostic.

        Args:
            lawyer_name: Name of the lawyer
            lawyer_email: Email address of the lawyer

        Returns:
            Secure token string
        """
        import secrets
        import hashlib

        # Create token from random bytes and lawyer info
        random_part = secrets.token_urlsafe(32)
        data_to_hash = f"{lawyer_email}:{lawyer_name}:{random_part}"
        token = hashlib.sha256(data_to_hash.encode()).hexdigest()[:32]

        # Store token info with expiration
        expiration = datetime.now() + timedelta(days=7)
        self.tokens[token] = {
            "lawyer_name": lawyer_name,
            "lawyer_email": lawyer_email,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiration.isoformat(),
            "used": False
        }

        logger.info(f"Generated token for {lawyer_name} ({lawyer_email})")
        return token

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate a token and return the associated data.

        Args:
            token: Token to validate

        Returns:
            Token data if valid, None if invalid or expired
        """
        if token not in self.tokens:
            logger.warning(f"Invalid token attempted: {token[:8]}...")
            return None

        token_data = self.tokens[token]
        expires_at = datetime.fromisoformat(token_data["expires_at"])

        if datetime.now() > expires_at:
            logger.warning(f"Expired token attempted: {token[:8]}...")
            return None

        if token_data.get("used", False):
            logger.warning(f"Already-used token attempted: {token[:8]}...")
            return None

        return token_data

    def mark_token_used(self, token: str):
        """Mark a token as used after successful completion."""
        if token in self.tokens:
            self.tokens[token]["used"] = True
            self.tokens[token]["used_at"] = datetime.now().isoformat()
            logger.info(f"Token marked as used: {token[:8]}...")

    def cleanup_expired_tokens(self):
        """Remove expired tokens from storage."""
        now = datetime.now()
        expired = [
            token for token, data in self.tokens.items()
            if now > datetime.fromisoformat(data["expires_at"])
        ]
        for token in expired:
            del self.tokens[token]
        logger.info(f"Cleaned up {len(expired)} expired tokens")


class EmailSender:
    """Handles sending emails for the diagnostic system."""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self.token_manager = EmailTokenManager()

    def send_diagnostic_invitation(self, lawyer_name: str, lawyer_email: str, sender_name: str = "Your Consultant") -> bool:
        """
        Send an email invitation to take the diagnostic.

        Args:
            lawyer_name: Name of the lawyer
            lawyer_email: Email address of the lawyer
            sender_name: Name of the person sending the invitation

        Returns:
            True if email sent successfully, False otherwise
        """
        # Generate secure token
        token = self.token_manager.generate_token(lawyer_name, lawyer_email)

        # Build diagnostic URL
        diagnostic_url = f"{self.config.base_url}/diagnostic/{token}"

        # Create email message
        subject = f"Practice Optimization Diagnostic - Personalized Analysis for {lawyer_name}"

        # HTML body
        html_body = self._build_html_email(
            lawyer_name=lawyer_name,
            diagnostic_url=diagnostic_url,
            sender_name=sender_name
        )

        # Plain text body
        text_body = self._build_text_email(
            lawyer_name=lawyer_name,
            diagnostic_url=diagnostic_url,
            sender_name=sender_name
        )

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        msg["To"] = f"{lawyer_name} <{lawyer_email}>"

        # Attach parts
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {lawyer_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {lawyer_email}: {e}")
            return False

    def send_reminder(self, lawyer_name: str, lawyer_email: str, token: str) -> bool:
        """
        Send a reminder email to complete the diagnostic.

        Args:
            lawyer_name: Name of the lawyer
            lawyer_email: Email address of the lawyer
            token: Existing token for the diagnostic

        Returns:
            True if email sent successfully, False otherwise
        """
        diagnostic_url = f"{self.config.base_url}/diagnostic/{token}"

        subject = f"Reminder: Complete Your Practice Optimization Diagnostic"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Complete Your Practice Assessment</h2>
                <p>Hi {lawyer_name},</p>
                <p>This is a friendly reminder to complete your Practice Optimization Diagnostic.</p>
                <p>The assessment takes about 10-15 minutes and will provide you with:</p>
                <ul>
                    <li>Personalized recommendations for your practice</li>
                    <li>Estimated time savings</li>
                    <li>Specific action steps</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{diagnostic_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Complete Assessment Now
                    </a>
                </div>
                <p><small>This link expires in {self.config.link_expiration_days} days.</small></p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Hi {lawyer_name},

        This is a friendly reminder to complete your Practice Optimization Diagnostic.

        The assessment takes about 10-15 minutes and will provide personalized recommendations for your practice.

        Complete it here: {diagnostic_url}

        This link expires in {self.config.link_expiration_days} days.
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        msg["To"] = f"{lawyer_name} <{lawyer_email}>"

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Reminder sent successfully to {lawyer_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send reminder to {lawyer_email}: {e}")
            return False

    def _build_html_email(self, lawyer_name: str, diagnostic_url: str, sender_name: str) -> str:
        """Build the HTML version of the invitation email."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Optimize Your Legal Practice</h2>
                <p>Hi {lawyer_name},</p>
                <p>{sender_name} has invited you to complete a <strong>Practice Optimization Diagnostic</strong> designed specifically for litigation attorneys.</p>

                <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <h3 style="margin-top: 0;">What You'll Get:</h3>
                    <ul>
                        <li><strong>Personalized Analysis:</strong> Customized recommendations based on your specific practice and workflow</li>
                        <li><strong>Time Savings:</strong> Identify opportunities to save 5-10+ hours per week</li>
                        <li><strong>AI Guidance:</strong> Intelligent assistance while completing the assessment</li>
                        <li><strong>Action Roadmap:</strong> Clear next steps prioritized by impact</li>
                    </ul>
                </div>

                <p>The diagnostic takes approximately <strong>10-15 minutes</strong> to complete.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{diagnostic_url}" style="background-color: #3498db; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; display: inline-block; font-size: 16px;">
                        Start Your Assessment
                    </a>
                </div>

                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Your assessment link:</strong><br>
                    <code style="background-color: white; padding: 5px; border-radius: 3px;">{diagnostic_url}</code></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px;"><small>This secure link expires in 7 days and can only be used once.</small></p>
                </div>

                <p>Questions? Reply to this email or contact {sender_name} directly.</p>

                <p style="margin-top: 30px; font-size: 14px; color: #7f8c8d;">
                    Best regards,<br>
                    Practice Optimization System
                </p>
            </div>
        </body>
        </html>
        """

    def _build_text_email(self, lawyer_name: str, diagnostic_url: str, sender_name: str) -> str:
        """Build the plain text version of the invitation email."""
        return f"""
Hi {lawyer_name},

{sender_name} has invited you to complete a Practice Optimization Diagnostic designed specifically for litigation attorneys.

WHAT YOU'LL GET:
" Personalized Analysis - Customized recommendations based on your specific practice
" Time Savings - Identify opportunities to save 5-10+ hours per week
" AI Guidance - Intelligent assistance while completing the assessment
" Action Roadmap - Clear next steps prioritized by impact

The diagnostic takes approximately 10-15 minutes to complete.

START YOUR ASSESSMENT:
{diagnostic_url}

This secure link expires in 7 days and can only be used once.

Questions? Reply to this email or contact {sender_name} directly.

Best regards,
Practice Optimization System
"""

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a diagnostic access token."""
        return self.token_manager.validate_token(token)

    def mark_token_used(self, token: str):
        """Mark a token as used."""
        self.token_manager.mark_token_used(token)


# Global instance
email_sender = EmailSender()


def send_diagnostic_to_lawyer(lawyer_name: str, lawyer_email: str, sender_name: str = "Your Consultant") -> bool:
    """
    Convenience function to send diagnostic invitation.

    Args:
        lawyer_name: Name of the lawyer
        lawyer_email: Email address
        sender_name: Your name

    Returns:
        True if successful
    """
    return email_sender.send_diagnostic_invitation(lawyer_name, lawyer_email, sender_name)
