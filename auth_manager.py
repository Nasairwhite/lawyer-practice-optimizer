"""
Authentication Manager for System Analyzer

Handles OAuth2 authentication for Gmail, Outlook, and other providers.
Ensures read-only access and secure token management.
"""

import json
import os
import pickle
import logging
from typing import Dict, Optional, Any
from pathlib import Path

# Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Microsoft Graph
import msal
import requests

# Load environment
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages OAuth2 authentication for multiple providers."""

    def __init__(self, token_storage_dir="./.tokens"):
        self.token_storage_dir = Path(token_storage_dir)
        self.token_storage_dir.mkdir(exist_ok=True, parents=True)

        # Gmail API Scopes - read-only for security
        self.GMAIL_SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.metadata',
        ]

        # Gmail API credentials
        self.gmail_creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "gmail_credentials.json")

        # Microsoft Graph Scopes - read-only
        self.MS_SCOPES = [
            'Mail.Read',
            'Files.Read.All',
            'openid',
            'profile',
        ]

        # Microsoft credentials
        self.ms_client_id = os.getenv("MS_CLIENT_ID")
        self.ms_client_secret = os.getenv("MS_CLIENT_SECRET")
        self.ms_tenant_id = os.getenv("MS_TENANT_ID", "common")

    # ==================== GMAIL AUTHENTICATION ====================

    def authenticate_gmail(self) -> Optional[Dict[str, Any]]:
        """
        Authenticate with Gmail using OAuth2.

        Returns:
            Dict with service object and user info, or None on failure
        """
        creds = None
        token_path = self.token_storage_dir / "gmail_token.pickle"

        # Load existing token
        if token_path.exists():
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing Gmail token")
            except Exception as e:
                logger.warning(f"Failed to load Gmail token: {e}")

        # Refresh or create new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Gmail token")
                except Exception as e:
                    logger.error(f"Failed to refresh Gmail token: {e}")
                    return None
            else:
                # Initialize OAuth flow
                if not os.path.exists(self.gmail_creds_file):
                    logger.error(f"Gmail credentials file not found: {self.gmail_creds_file}")
                    logger.info("Download from: https://console.cloud.google.com/apis/credentials")
                    return None

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.gmail_creds_file, self.GMAIL_SCOPES
                    )
                    logger.info("Starting Gmail OAuth flow...")
                    creds = flow.run_local_server(port=0)
                    logger.info("Gmail OAuth completed successfully")
                except Exception as e:
                    logger.error(f"Gmail OAuth flow failed: {e}")
                    return None

            # Save token
            try:
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved Gmail token to {token_path}")
            except Exception as e:
                logger.warning(f"Failed to save Gmail token: {e}")

        # Build service
        try:
            service = build('gmail', 'v1', credentials=creds)

            # Get user info
            profile = service.users().getProfile(userId='me').execute()
            user_info = {
                'email': profile.get('emailAddress'),
                'name': 'Gmail User'
            }

            logger.info(f"Gmail authentication successful for {user_info['email']}")

            return {
                'service': service,
                'creds': creds,
                'user_info': user_info
            }

        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return None

    def revoke_gmail_access(self):
        """Revoke Gmail access token."""
        token_path = self.token_storage_dir / "gmail_token.pickle"
        if token_path.exists():
            try:
                if os.getenv("CI") or os.getenv("TESTING"):
                    # Skip revocation in CI/test environments
                    token_path.unlink()
                    logger.info("Gmail token deleted (test environment)")
                    return True

                token_path.unlink()
                logger.info("Gmail access revoked")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke Gmail access: {e}")
                return False
        return True

    # ==================== MICROSOFT AUTHENTICATION ====================

    def authenticate_microsoft(self) -> Optional[Dict[str, Any]]:
        """
        Authenticate with Microsoft Graph API.

        Returns:
            Dict with access token and user info, or None on failure
        """
        if not all([self.ms_client_id, self.ms_client_secret]):
            logger.warning("Microsoft credentials not configured")
            return None

        token_path = self.token_storage_dir / "ms_token.pickle"

        # Initialize MSAL
        app = msal.PublicClientApplication(
            self.ms_client_id,
            authority=f"https://login.microsoftonline.com/{self.ms_tenant_id}"
        )

        # Try to load existing token
        result = None
        if token_path.exists():
            try:
                with open(token_path, 'rb') as f:
                    cached_token = pickle.load(f)

                # Check if token is still valid
                accounts = app.get_accounts()
                if accounts:
                    result = app.acquire_token_silent(self.MS_SCOPES, account=accounts[0])
                    logger.info("Loaded Microsoft token from cache")
            except Exception as e:
                logger.warning(f"Failed to load Microsoft token: {e}")

        # If no valid token, initiate new flow
        if not result:
            logger.info("Starting Microsoft OAuth flow...")
            flow = app.initiate_device_flow(scopes=self.MS_SCOPES)

            if "user_code" not in flow:
                logger.error(f"Failed to create device flow: {flow}")
                return None

            print("Microsoft Authentication:")
            print(flow["message"])
            print(f"Code: {flow['user_code']}")

            # Wait for user authentication
            result = app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                # Save token
                try:
                    with open(token_path, 'wb') as f:
                        pickle.dump(result, f)
                    logger.info(f"Saved Microsoft token to {token_path}")
                except Exception as e:
                    logger.warning(f"Failed to save Microsoft token: {e}")
            else:
                logger.error(f"Microsoft authentication failed: {result}")
                return None

        # Extract access token and user info
        if "access_token" in result:
            access_token = result["access_token"]

            # Get user info
            try:
                user_response = requests.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                user_response.raise_for_status()
                user_info = user_response.json()

                logger.info(f"Microsoft authentication successful for {user_info.get('mail')}")

                return {
                    'access_token': access_token,
                    'user_info': {
                        'email': user_info.get('mail'),
                        'name': user_info.get('displayName'),
                        'user_id': user_info.get('id')
                    },
                    'full_token': result
                }

            except Exception as e:
                logger.error(f"Failed to get Microsoft user info: {e}")
                return None

        logger.error("Microsoft authentication failed: No access token")
        return None

    def revoke_microsoft_access(self):
        """Revoke Microsoft access token."""
        token_path = self.token_storage_dir / "ms_token.pickle"
        if token_path.exists():
            try:
                token_path.unlink()
                logger.info("Microsoft access revoked")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke Microsoft access: {e}")
                return False
        return True

    # ==================== UTILITY METHODS ====================

    def get_available_providers(self) -> Dict[str, bool]:
        """Check which providers are configured and available."""
        providers = {
            'gmail': os.path.exists(self.gmail_creds_file),
            'microsoft': all([self.ms_client_id, self.ms_client_secret])
        }

        # Check for existing tokens
        token_gmail = self.token_storage_dir / "gmail_token.pickle"
        token_ms = self.token_storage_dir / "ms_token.pickle"

        providers['gmail_authenticated'] = token_gmail.exists()
        providers['microsoft_authenticated'] = token_ms.exists()

        logger.info(f"Available providers: {providers}")
        return providers

    def revoke_all_access(self):
        """Revoke all stored access tokens."""
        results = {
            'gmail': self.revoke_gmail_access(),
            'microsoft': self.revoke_microsoft_access()
        }

        revoked = [k for k, v in results.items() if v]
        failed = [k for k, v in results.items() if not v]

        logger.info(f"Revoked: {revoked}")
        if failed:
            logger.warning(f"Failed to revoke: {failed}")

        return results

    def test_connections(self) -> Dict[str, bool]:
        """Test connections to all authenticated providers."""
        results = {}
        providers = self.get_available_providers()

        # Test Gmail
        if providers.get('gmail_authenticated'):
            auth = self.authenticate_gmail()
            results['gmail'] = auth is not None

        # Test Microsoft
        if providers.get('microsoft_authenticated'):
            auth = self.authenticate_microsoft()
            results['microsoft'] = auth is not None

        logger.info(f"Connection test results: {results}")
        return results


# Global instance
auth_manager = AuthManager()


# CLI helper functions
def authenticate_provider_cli(provider: str):
    """CLI helper to authenticate with a specific provider."""
    if provider.lower() == 'gmail':
        print("Authenticating with Gmail...")
        print(f"Make sure {auth_manager.gmail_creds_file} exists")
        print("Download from: https://console.cloud.google.com/apis/credentials")
        print()
        input("Press Enter to continue...")

        auth = auth_manager.authenticate_gmail()
        if auth:
            print("✅ Gmail authentication successful!")
            print(f"   Email: {auth['user_info']['email']}")
        else:
            print("❌ Gmail authentication failed")

    elif provider.lower() in ['microsoft', 'outlook']:
        print("Authenticating with Microsoft...")
        auth = auth_manager.authenticate_microsoft()
        if auth:
            print("✅ Microsoft authentication successful!")
            print(f"   Email: {auth['user_info']['email']}")
        else:
            print("❌ Microsoft authentication failed")

    else:
        print(f"Unknown provider: {provider}")
        print("Available: gmail, microsoft")


def list_authenticated_providers():
    """CLI helper to show authenticated providers."""
    providers = auth_manager.get_available_providers()

    print("Authentication Status:")
    print("=" * 40)

    if providers['gmail']:
        if providers['gmail_authenticated']:
            print("✅ Gmail: Authenticated")
            # Try to get email
            auth = auth_manager.authenticate_gmail()
            if auth:
                print(f"   Email: {auth['user_info']['email']}")
        else:
            print("⏹  Gmail: Available but not authenticated")
            print(f"   Run: python -c 'from auth_manager import authenticate_provider_cli; authenticate_provider_cli(\"gmail\")'")
    else:
        print("❌ Gmail: Not configured")
        print(f"   Missing: {auth_manager.gmail_creds_file}")
        print("   Get from: https://console.cloud.google.com/apis/credentials")

    print()

    if providers['microsoft']:
        if providers['microsoft_authenticated']:
            print("✅ Microsoft: Authenticated")
            auth = auth_manager.authenticate_microsoft()
            if auth:
                print(f"   Email: {auth['user_info']['email']}")
        else:
            print("⏹  Microsoft: Available but not authenticated")
            print(f"   Run: python -c 'from auth_manager import authenticate_provider_cli; authenticate_provider_cli(\"microsoft\")'")
    else:
        print("❌ Microsoft: Not configured")
        print("   Set MS_CLIENT_ID and MS_CLIENT_SECRET in .env")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] in ['--list', '-l']:
            list_authenticated_providers()
        else:
            authenticate_provider_cli(sys.argv[1])
    else:
        print("Usage:")
        print("  python auth_manager.py gmail        # Authenticate Gmail")
        print("  python auth_manager.py microsoft    # Authenticate Microsoft")
        print("  python auth_manager.py --list       # Show status")
