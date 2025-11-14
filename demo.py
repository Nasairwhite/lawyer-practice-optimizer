#!/usr/bin/env python3
"""
Demo script for Lawyer Practice Optimization Diagnostic
Shows how to send a diagnostic invitation to your lawyer.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_sender import send_diagnostic_to_lawyer

def main():
    """Demo: Send diagnostic invitation to a lawyer."""

    print("=" * 70)
    print("Lawyer Practice Optimization Diagnostic - Demo")
    print("=" * 70)
    print()

    # Check for required environment variables
    required_vars = [
        "MOONSHOT_API_KEY",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "FROM_EMAIL"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("Please set these in your .env file before running the demo.")
        print()
        print("To get started:")
        print("1. Copy .env.template to .env")
        print("2. Add your Moonshot API key from https://platform.moonshot.cn")
        print("3. Add your SMTP credentials for sending emails")
        print()
        return

    print("✅ Environment variables configured!")
    print()

    # Get lawyer details
    print("Enter your lawyer's information:")
    print("-" * 70)

    lawyer_name = input("Lawyer's full name: ").strip()
    lawyer_email = input("Lawyer's email address: ").strip()
    sender_name = input("Your name (sender): ").strip()

    if not all([lawyer_name, lawyer_email, sender_name]):
        print()
        print("❌ All fields are required!")
        return

    print()
    print("Sending diagnostic invitation...")
    print()

    # Send the email
    success = send_diagnostic_to_lawyer(
        lawyer_name=lawyer_name,
        lawyer_email=lawyer_email,
        sender_name=sender_name
    )

    if success:
        print("✅ Success! Email sent successfully!")
        print()
        print(f"📧 {lawyer_name} will receive an email at {lawyer_email}")
        print(f"   with a secure link to complete the diagnostic.")
        print()
        print("What happens next:")
        print("1. Lawyer clicks the link in the email")
        print("2. Completes the 20-question diagnostic (10-15 minutes)")
        print("3. Receives personalized AI-generated report")
        print("4. You can review the report together to plan next steps")
        print()
        print("Link expires in 7 days for security.")
    else:
        print("❌ Failed to send email")
        print()
        print("Troubleshooting:")
        print("- Check your SMTP credentials in .env")
        print("- For Gmail, ensure you're using an App Password")
        print("- Check console for detailed error messages")

    print()
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
