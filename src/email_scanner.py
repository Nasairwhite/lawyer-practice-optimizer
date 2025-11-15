"""
Email Scanner for System Analyzer

Analyzes email patterns, workflows, and inefficiencies in Gmail/Outlook.
Focuses on metadata and patterns, not reading private content.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

# Gmail API
from googleapiclient.discovery import build

# Microsoft Graph
import requests

logger = logging.getLogger(__name__)


class EmailScanner:
    """Scans email systems and analyzes workflows, patterns, and inefficiencies."""

    def __init__(self, auth_data: Dict[str, Any]):
        self.auth = auth_data
        self.provider = auth_data.get('provider', 'unknown')
        self.sample_size = 5000  # Number of emails to analyze
        self.analysis_results = {}

    # ==================== GMAIL SCANNING ====================

    def scan_gmail(self) -> Dict[str, Any]:
        """
        Scan Gmail account and analyze patterns.

        Returns:
            Analysis results with patterns, workflows, and recommendations
        """
        logger.info("Starting Gmail scan...")
        results = {
            'provider': 'gmail',
            'scan_timestamp': datetime.now().isoformat(),
            'total_emails_analyzed': 0,
            'folders': {},
            'patterns': {},
            'workflows': {},
            'inefficiencies': {},
            'recommendations': []
        }

        try:
            service = self.auth['service']

            # Get user info
            profile = service.users().getProfile(userId='me').execute()
            results['email_address'] = profile.get('emailAddress')
            results['total_emails_in_account'] = profile.get('messagesTotal', 0)

            logger.info(f"Scanning Gmail for {results['email_address']}")

            # Scan folders/labels
            logger.info("Scanning Gmail labels...")
            labels = service.users().labels().list(userId='me').execute()
            results['folder_count'] = len(labels.get('labels', []))

            # Analyze each label
            for label in labels.get('labels', [])[:20]:  # Limit to top 20 labels
                label_id = label['id']
                label_name = label['name']

                try:
                    # Get message count for this label
                    label_info = service.users().labels().get(userId='me', id=label_id).execute()
                    message_count = label_info.get('messagesTotal', 0)

                    if message_count > 10:  # Only analyze labels with significant messages
                        results['folders'][label_name] = {
                            'id': label_id,
                            'message_count': message_count,
                            'threads_count': label_info.get('threadsTotal', 0)
                        }

                        logger.debug(f"Label '{label_name}': {message_count} messages")

                except Exception as e:
                    logger.warning(f"Failed to analyze label {label_name}: {e}")

            # Analyze recent emails for patterns
            logger.info(f"Analyzing up to {self.sample_size} recent emails...")
            results['email_patterns'] = self._analyze_gmail_emails(service)

            # Analyze response times
            logger.info("Analyzing response time patterns...")
            results['response_analysis'] = self._analyze_response_times(service)

            # Generate recommendations
            logger.info("Generating recommendations...")
            results['recommendations'] = self._generate_email_recommendations(results)

            results['scan_complete'] = True
            logger.info("Gmail scan completed successfully")

        except Exception as e:
            logger.error(f"Gmail scan failed: {e}")
            results['error'] = str(e)
            results['scan_complete'] = False

        self.analysis_results = results
        return results

    def _analyze_gmail_emails(self, service) -> Dict[str, Any]:
        """Analyze email patterns and workflows."""
        patterns = {
            'total_analyzed': 0,
            'common_senders': Counter(),
            'common_subjects': Counter(),
            'email_categories': defaultdict(int),
            'template_candidates': [],
            'follow_up_patterns': [],
            'workflows': []
        }

        try:
            # Get recent messages
            results = service.users().messages().list(
                userId='me',
                maxResults=min(self.sample_size, 500)
            ).execute()

            messages = results.get('messages', [])
            patterns['total_analyzed'] = len(messages)

            logger.info(f"Analyzing {len(messages)} messages for patterns...")

            for i, message in enumerate(messages[:100]):  # Analyze first 100 in detail
                if i % 50 == 0:
                    logger.debug(f"Processed {i} messages...")

                try:
                    # Get message details (metadata only for efficiency)
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date', 'To', 'Cc']
                    ).execute()

                    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

                    # Extract sender
                    sender = headers.get('From', '')
                    if '<' in sender:
                        sender_name = sender.split('<')[0].strip()
                        sender_email = sender.split('<')[1].strip('>')
                    else:
                        sender_name = sender
                        sender_email = sender

                    patterns['common_senders'][sender_email] += 1

                    # Extract subject
                    subject = headers.get('Subject', '')
                    patterns['common_subjects'][subject[:60]] += 1

                    # Categorize email
                    category = self._categorize_email(subject, sender_email)
                    patterns['email_categories'][category] += 1

                except Exception as e:
                    logger.warning(f"Failed to analyze message {message['id']}: {e}")

            # Identify template opportunities
            patterns['template_candidates'] = self._identify_template_candidates(
                patterns['common_subjects']
            )

            # Identify workflows
            patterns['workflows'] = self._identify_workflows(patterns['email_categories'])

        except Exception as e:
            logger.error(f"Failed to analyze Gmail emails: {e}")

        return dict(patterns)

    def _analyze_response_times(self, service) -> Dict[str, Any]:
        """Analyze response time patterns."""
        response_analysis = {
            'avg_response_time_hours': 0,
            'response_time_distribution': defaultdict(int),
            'slow_responses': [],
            'unanswered_count': 0
        }

        try:
            # Get threads (conversations)
            threads = service.users().threads().list(
                userId='me',
                maxResults=200
            ).execute().get('threads', [])

            response_times = []

            for thread in threads[:100]:  # Sample size
                try:
                    thread_detail = service.users().threads().get(
                        userId='me',
                        id=thread['id']
                    ).execute()

                    messages = thread_detail.get('messages', [])

                    # Analyze timestamps in thread
                    timestamps = []
                    for msg in messages:
                        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                        date_str = headers.get('Date')
                        if date_str:
                            try:
                                date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                                timestamps.append(date)
                            except:
                                pass

                    # Calculate response times between messages
                    if len(timestamps) >= 2:
                        for i in range(1, len(timestamps)):
                            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # hours
                            if 0.1 < time_diff < 720:  # Between 6 minutes and 30 days
                                response_times.append(time_diff)

                except Exception as e:
                    logger.warning(f"Failed to analyze thread: {e}")

            # Calculate statistics
            if response_times:
                response_analysis['avg_response_time_hours'] = sum(response_times) / len(response_times)

                # Distribution
                for rt in response_times:
                    if rt < 1:
                        response_analysis['response_time_distribution']['< 1 hour'] += 1
                    elif rt < 4:
                        response_analysis['response_time_distribution']['1-4 hours'] += 1
                    elif rt < 24:
                        response_analysis['response_time_distribution']['4-24 hours'] += 1
                    elif rt < 72:
                        response_analysis['response_time_distribution']['1-3 days'] += 1
                    else:
                        response_analysis['response_time_distribution']['> 3 days'] += 1

        except Exception as e:
            logger.error(f"Failed to analyze response times: {e}")

        return dict(response_analysis)

    # ==================== MICROSOFT OUTLOOK SCANNING ====================

    def scan_outlook(self) -> Dict[str, Any]:
        """
        Scan Microsoft Outlook/Exchange via Graph API.

        Returns:
            Analysis results similar to Gmail scan
        """
        logger.info("Starting Outlook scan...")
        results = {
            'provider': 'outlook',
            'scan_timestamp': datetime.now().isoformat(),
            'total_emails_analyzed': 0,
            'folders': {},
            'patterns': {},
            'workflows': {},
            'inefficiencies': {},
            'recommendations': []
        }

        try:
            access_token = self.auth['access_token']
            user_email = self.auth['user_info']['email']

            logger.info(f"Scanning Outlook for {user_email}")

            # Get folder structure
            logger.info("Scanning Outlook folders...")
            folders = self._get_outlook_folders(access_token)
            results['folders'] = folders
            results['folder_count'] = len(folders)

            # Analyze emails
            logger.info("Analyzing Outlook emails...")
            results['email_patterns'] = self._analyze_outlook_emails(access_token)

            # Analysis complete
            results['scan_complete'] = True
            logger.info("Outlook scan completed successfully")

        except Exception as e:
            logger.error(f"Outlook scan failed: {e}")
            results['error'] = str(e)
            results['scan_complete'] = False

        self.analysis_results = results
        return results

    def _get_outlook_folders(self, access_token) -> Dict[str, Any]:
        """Get Outlook folder structure."""
        folders = {}

        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/mailFolders",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()

            data = response.json()
            for folder in data.get('value', []):
                folder_name = folder.get('displayName')
                folders[folder_name] = {
                    'id': folder.get('id'),
                    'message_count': folder.get('totalItemCount', 0),
                    'unread_count': folder.get('unreadItemCount', 0)
                }

        except Exception as e:
            logger.error(f"Failed to get Outlook folders: {e}")

        return folders

    def _analyze_outlook_emails(self, access_token) -> Dict[str, Any]:
        """Analyze Outlook emails for patterns."""
        patterns = {
            'total_analyzed': 0,
            'common_senders': Counter(),
            'email_categories': defaultdict(int),
            'template_candidates': []
        }

        try:
            # Get recent messages
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/me/messages?$top={min(self.sample_size, 50)}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()

            data = response.json()
            messages = data.get('value', [])
            patterns['total_analyzed'] = len(messages)

            for msg in messages:
                sender = msg.get('from', {}).get('emailAddress', {}).get('address', '')
                if sender:
                    patterns['common_senders'][sender] += 1

                subject = msg.get('subject', '')
                category = self._categorize_email(subject, sender)
                patterns['email_categories'][category] += 1

        except Exception as e:
            logger.error(f"Failed to analyze Outlook emails: {e}")

        return dict(patterns)

    # ==================== ANALYSIS UTILITIES ====================

    def _categorize_email(self, subject: str, sender: str) -> str:
        """Categorize email based on subject and sender."""
        subject_lower = subject.lower()

        # Client communications
        if any(word in subject_lower for word in ['re:', 'fw:', 'fw:', 'update', 'status']):
            return 'client_communication'

        # Court/Deadlines
        if any(word in subject_lower for word in ['hearing', 'motion', 'deadline', 'filing', 'court']):
            return 'court_deadline'

        # Billing
        if any(word in subject_lower for word in ['invoice', 'payment', 'billing', 'hours']):
            return 'billing'

        # Marketing/Referral
        if any(word in subject_lower for word in ['referral', 'lead', 'inquiry', 'consultation']):
            return 'marketing'

        # Internal/Admin
        if any(word in subject_lower for word in ['staff', 'meeting', 'calendar', 'internal']):
            return 'admin'

        return 'other'

    def _identify_template_candidates(self, subjects: Counter) -> List[Dict[str, Any]]:
        """Identify emails that could be templated."""
        candidates = []

        # Look for similar subjects (potential templates)
        for subject, count in subjects.most_common(50):
            if count > 3:  # Sent more than 3 times
                candidates.append({
                    'subject': subject,
                    'count': count,
                    'confidence': 'high'
                })
            elif count > 1:
                candidates.append({
                    'subject': subject,
                    'count': count,
                    'confidence': 'medium'
                })

        return candidates

    def _identify_workflows(self, categories: Dict[str, int]) -> List[Dict[str, Any]]:
        """Identify common workflows from email categories."""
        workflows = []
        total = sum(categories.values())

        for category, count in categories.items():
            if count > total * 0.1:  # More than 10% of emails
                workflows.append({
                    'type': category,
                    'volume': count,
                    'percentage': (count / total) * 100
                })

        return sorted(workflows, key=lambda x: x['volume'], reverse=True)

    def _generate_email_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on analysis."""
        recommendations = []

        # Template recommendations
        templates = results.get('email_patterns', {}).get('template_candidates', [])
        if templates:
            high_confidence = [t for t in templates if t['confidence'] == 'high']
            if high_confidence:
                recommendations.append({
                    'priority': 'high',
                    'area': 'email_templates',
                    'title': f'Create {len(high_confidence)} email templates',
                    'description': f"You repeatedly send {len(high_confidence)} similar emails. Creating templates could save 2-3 hours/week.",
                    'estimated_time_savings_hours_per_week': len(high_confidence) * 0.5,
                    'implementation_time': '2-3 hours',
                    'difficulty': 'easy'
                })

        # Response time recommendations
        response_time = results.get('response_analysis', {}).get('avg_response_time_hours', 0)
        if response_time > 24:
            recommendations.append({
                'priority': 'medium',
                'area': 'response_time',
                'title': 'Improve email response workflow',
                'description': f"Your average response time is {response_time:.1f} hours. Creating canned responses and setting up notifications could improve this.",
                'estimated_time_savings_hours_per_week': 1.0,
                'implementation_time': '1-2 hours',
                'difficulty': 'easy'
            })

        # Folder organization
        if len(results.get('folders', {})) > 20:
            recommendations.append({
                'priority': 'medium',
                'area': 'organization',
                'title': 'Simplify email folder structure',
                'description': f"You have {len(results['folders'])} folders. Simplifying to 5-10 key folders with better labels could save time.",
                'estimated_time_savings_hours_per_week': 0.5,
                'implementation_time': '1 hour',
                'difficulty': 'easy'
            })

        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)

    def get_summary(self) -> str:
        """Get a summary of the analysis."""
        if not self.analysis_results:
            return "No analysis completed yet."

        results = self.analysis_results
        summary = f"""Email System Analysis Summary
{'='*50}
Provider: {results.get('provider', 'Unknown')}
Email: {results.get('email_address', 'Unknown')}
Date: {results.get('scan_timestamp', 'Unknown')}

Statistics:
- Total emails in account: {results.get('total_emails_in_account', 0):,}
- Emails analyzed: {results.get('email_patterns', {}).get('total_analyzed', 0)}
- Folders/Labels: {results.get('folder_count', 0)}
- Avg response time: {results.get('response_analysis', {}).get('avg_response_time_hours', 0):.1f} hours

Key Findings:
- Template candidates: {len(results.get('email_patterns', {}).get('template_candidates', []))}
- Email workflows: {len(results.get('email_patterns', {}).get('workflows', []))}
- Recommendations: {len(results.get('recommendations', []))}

Top Recommendations:
"""

        for i, rec in enumerate(results.get('recommendations', [])[:3], 1):
            summary += f"{i}. {rec['title']} (Priority: {rec['priority']})\n"
            summary += f"   Time savings: {rec.get('estimated_time_savings_hours_per_week', 0)} hrs/week\n"

        return summary


# Example usage function
def scan_email_system(auth_data: Dict[str, Any]) -> EmailScanner:
    """
    Convenience function to scan an email system.

    Args:
        auth_data: Authentication data from AuthManager

    Returns:
        EmailScanner instance with analysis results
    """
    scanner = EmailScanner(auth_data)

    if 'service' in auth_data:  # Gmail
        scanner.scan_gmail()
    elif 'access_token' in auth_data:  # Outlook
        scanner.scan_outlook()

    return scanner


if __name__ == "__main__":
    import sys

    # Test with existing authentication
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        from auth_manager import auth_manager

        print("Email Scanner Test")
        print("="*50)

        providers = auth_manager.get_available_providers()
        print("Available providers:", providers)

        if providers.get('gmail_authenticated'):
            print("\nTesting Gmail scan...")
            auth = auth_manager.authenticate_gmail()
            if auth:
                auth['provider'] = 'gmail'
                scanner = EmailScanner(auth)
                results = scanner.scan_gmail()
                print(scanner.get_summary())

        elif providers.get('microsoft_authenticated'):
            print("\nTesting Outlook scan...")
            auth = auth_manager.authenticate_microsoft()
            if auth:
                auth['provider'] = 'outlook'
                scanner = EmailScanner(auth)
                results = scanner.scan_outlook()
                print(scanner.get_summary())

        else:
            print("No authenticated providers found.")
            print("Run: python auth_manager.py gmail")
