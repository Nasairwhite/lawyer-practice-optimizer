"""
Cloud Storage Scanner

Scans Google Drive, Dropbox, and OneDrive for file organization patterns
and inefficiencies.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Google Drive API
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class CloudScanner:
    """Scans cloud storage and analyzes file organization patterns."""

    def __init__(self, auth_data: Optional[Dict[str, Any]] = None):
        self.auth_data = auth_data
        self.analysis_results = {}

    # ==================== GOOGLE DRIVE SCANNING ====================

    def scan_google_drive(self, max_files: int = 10000) -> Dict[str, Any]:
        """
        Scan Google Drive and analyze organization patterns.

        Args:
            max_files: Maximum number of files to analyze

        Returns:
            Analysis results with statistics and recommendations
        """
        logger.info("Starting Google Drive scan...")

        results = {
            'provider': 'google_drive',
            'scan_timestamp': datetime.now().isoformat(),
            'total_files': 0,
            'total_folders': 0,
            'total_size_bytes': 0,
            'files_by_type': defaultdict(int),
            'files_by_category': defaultdict(int),
            'folders': {},
            'orphaned_files': [],
            'shared_files': [],
            'duplicates': [],
            'organization_issues': [],
            'file_paths': [],
            'recommendations': [],
            'quota_info': {}
        }

        try:
            service = self.auth_data['service']

            # Get user info and quota
            about = service.about().get(fields="user, storageQuota").execute()
            results['user_email'] = about.get('user', {}).get('emailAddress')
            results['user_name'] = about.get('user', {}).get('displayName', '')

            quota = about.get('storageQuota', {})
            results['quota_info'] = {
                'limit_bytes': int(quota.get('limit', 0)),
                'usage_bytes': int(quota.get('usage', 0)),
                'usage_in_drive_bytes': int(quota.get('usageInDrive', 0)),
                'usage_percent': (int(quota.get('usage', 0)) / int(quota.get('limit', 1))) * 100
            }

            logger.info(f"Scanning Google Drive for {results['user_email']}")

            # Scan all files and folders
            page_token = None
            file_count = 0
            all_files = []

            while file_count < max_files:
                try:
                    response = service.files().list(
                        pageSize=min(1000, max_files - file_count),
                        pageToken=page_token,
                        fields="nextPageToken, files(id, name, mimeType, size, parents, modifiedTime, createdTime, shared, owners, webViewLink)"
                    ).execute()

                    files = response.get('files', [])
                    all_files.extend(files)
                    file_count += len(files)

                    page_token = response.get('nextPageToken')
                    if not page_token:
                        break

                except HttpError as e:
                    logger.error(f"Google Drive API error: {e}")
                    break

            logger.info(f"Found {len(all_files)} files in Google Drive")

            # Analyze files
            for file_info in all_files:
                mime_type = file_info.get('mimeType', '')

                # Count folders
                if mime_type == 'application/vnd.google-apps.folder':
                    results['total_folders'] += 1
                    results['folders'][file_info['id']] = {
                        'name': file_info['name'],
                        'id': file_info['id']
                    }
                    continue

                # Analyze files
                results['total_files'] += 1

                size = int(file_info.get('size', 0))
                results['total_size_bytes'] += size

                # Categorize file
                category = self._categorize_drive_file(file_info)
                results['files_by_category'][category] += 1

                # Track by type
                results['files_by_type'][mime_type] += 1

                # Check if shared
                if file_info.get('shared', False):
                    results['shared_files'].append({
                        'name': file_info['name'],
                        'id': file_info['id'],
                        'type': mime_type
                    })

                # Store file info
                results['file_paths'].append({
                    'path': file_info['name'],
                    'size': size,
                    'modified': file_info.get('modifiedTime'),
                    'created': file_info.get('createdTime'),
                    'category': category,
                    'mime_type': mime_type,
                    'shared': file_info.get('shared', False)
                })

            # Detect organization issues
            results['organization_issues'] = self._detect_drive_issues(results)

            # Generate recommendations
            results['recommendations'] = self._generate_drive_recommendations(results)

            results['scan_complete'] = True
            logger.info(f"Google Drive scan completed: {results['total_files']:,} files")

        except Exception as e:
            logger.error(f"Google Drive scan failed: {e}")
            results['error'] = str(e)
            results['scan_complete'] = False

        self.analysis_results = results
        return results

    def _categorize_drive_file(self, file_info: Dict) -> str:
        """Categorize Google Drive file based on mimeType and name."""
        name = file_info.get('name', '').lower()
        mime_type = file_info.get('mimeType', '')

        # Special Google Drive types
        if mime_type.startswith('application/vnd.google-apps'):
            if 'document' in mime_type:
                return 'google_docs'
            elif 'spreadsheet' in mime_type:
                return 'google_sheets'
            elif 'presentation' in mime_type:
                return 'google_slides'
            elif 'form' in mime_type:
                return 'google_forms'
            else:
                return 'google_files'

        # PDFs
        elif mime_type == 'application/pdf':
            if 'contract' in name or 'agreement' in name:
                return 'legal_contracts'
            elif 'pleading' in name or 'motion' in name:
                return 'legal_pleadings'
            elif 'discovery' in name:
                return 'legal_discovery'
            else:
                return 'documents'

        # Microsoft Office
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'documents'
        elif mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            if 'billing' in name or 'invoice' in name:
                return 'billing'
            return 'spreadsheets'
        elif mime_type in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
            return 'presentations'

        # Images
        elif mime_type.startswith('image/'):
            return 'images'

        # Archives
        elif mime_type in ['application/zip', 'application/x-zip-compressed', 'application/x-rar-compressed', 'application/x-7z-compressed']:
            return 'archives'

        else:
            return 'other'

    def _detect_drive_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect organization issues in Google Drive."""
        issues = []

        # Check storage usage
        quota = results.get('quota_info', {})
        usage_percent = quota.get('usage_percent', 0)
        if usage_percent > 80:
            issues.append({
                'severity': 'high',
                'issue': 'high_storage_usage',
                'description': f'Google Drive is {usage_percent:.1f}% full ({quota.get("usage_bytes", 0) / (1024**3):.1f}GB of {quota.get("limit_bytes", 0) / (1024**3):.1f}GB)',
                'impact': 'Risk of running out of space, possible need to upgrade plan'
            })

        # Check for many uncategorized files
        uncategorized = results['files_by_category'].get('other', 0)
        if uncategorized / max(results['total_files'], 1) > 0.2:
            issues.append({
                'severity': 'medium',
                'issue': 'many_uncategorized_files',
                'description': f'{uncategorized} files uncategorized ({uncategorized / results["total_files"] * 100:.1f}%)',
                'impact': 'Difficult to find files, poor organization'
            })

        # Check for shared files (security concern)
        shared_files = results.get('shared_files', [])
        if len(shared_files) > 50:
            issues.append({
                'severity': 'medium',
                'issue': 'excessive_shared_files',
                'description': f'{len(shared_files)} files are shared externally',
                'impact': 'Potential security/privacy concerns'
            })

        return issues

    def _generate_drive_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for Google Drive organization."""
        recommendations = []

        # Storage optimization
        quota = results.get('quota_info', {})
        if quota.get('usage_percent', 0) > 70:
            recommendations.append({
                'priority': 'high',
                'area': 'storage_optimization',
                'title': 'Optimize Google Drive storage',
                'description': f"Drive is {quota['usage_percent']:.1f}% full. Remove duplicates and unnecessary files.",
                'estimated_time_savings_hours_per_week': 0.5,
                'implementation_time': '2-4 hours',
                'difficulty': 'easy'
            })

        # Folder organization
        if results['total_folders'] > 50:
            recommendations.append({
                'priority': 'medium',
                'area': 'folder_organization',
                'title': 'Organize Drive folders',
                'description': f"{results['total_folders']} folders is excessive. Consolidate to 5-10 main folders with subfolders.",
                'estimated_time_savings_hours_per_week': 0.5,
                'implementation_time': '2-4 hours',
                'difficulty': 'medium'
            })

        # Shared files review
        shared_files = results.get('shared_files', [])
        if len(shared_files) > 20:
            recommendations.append({
                'priority': 'low',
                'area': 'security',
                'title': 'Review external sharing permissions',
                'description': f"{len(shared_files)} files are shared externally. Review and revoke unnecessary shares.",
                'estimated_time_savings_hours_per_week': 0,
                'implementation_time": "1-2 hours',
                'difficulty': 'easy'
            })

        # File naming conventions
        if results['files_by_category'].get('other', 0) > 0:
            recommendations.append({
                'priority': 'low',
                'area': 'naming_convention',
                'title': 'Implement file naming conventions',
                'description': "Use consistent naming with dates, case numbers, or client names for easier searching.",
                'estimated_time_savings_hours_per_week': 1.0,
                'implementation_time': '1-2 hours',
                'difficulty': 'easy'
            })

        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)

    def get_summary(self) -> str:
        """Get a summary of the cloud storage analysis."""
        if not self.analysis_results:
            return "No analysis completed yet."

        results = self.analysis_results

        quota = results.get('quota_info', {})
        usage_gb = quota.get('usage_bytes', 0) / (1024**3)
        limit_gb = quota.get('limit_bytes', 0) / (1024**3)
        usage_percent = quota.get('usage_percent', 0)

        summary = f"""Cloud Storage Analysis Summary ({results.get('provider', 'Unknown')})
{'='*60}
User: {results.get('user_email', 'Unknown')}
Date: {results.get('scan_timestamp', 'Unknown')}

Storage Usage:
- Total files: {results.get('total_files', 0):,}
- Total folders: {results.get('total_folders', 0)}
- Total size: {usage_gb:.2f} GB / {limit_gb:.2f} GB
- Usage: {usage_percent:.1f}%

File Categories (Top 5):
"""

        for category, count in sorted(results.get('files_by_category', {}).items(),
                                      key=lambda x: x[1], reverse=True)[:5]:
            summary += f"  - {category.replace('_', ' ').title()}: {count:,} files\n"

        summary += f"\nTop Recommendations:\n"
        for i, rec in enumerate(results.get('recommendations', [])[:3], 1):
            summary += f"{i}. {rec['title']} (Priority: {rec['priority']})\n"

        return summary


def scan_cloud_storage(provider: str, auth_data: Dict[str, Any]) -> CloudScanner:
    """
    Convenience function to scan cloud storage.

    Args:
        provider: 'google_drive', 'dropbox', or 'onedrive'
        auth_data: Authentication data from AuthManager

    Returns:
        CloudScanner instance with analysis results
    """
    scanner = CloudScanner(auth_data)

    if provider == 'google_drive':
        scanner.scan_google_drive()
    # Add more providers here as they're implemented

    return scanner


if __name__ == "__main__":
    import sys

    # Test mode
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("Cloud Storage Scanner Test")
        print("="*50)

        print("\nTest requires authentication.")
        print("Run: python auth_manager.py")
        print("Then: python cloud_scanner.py scan")

    elif len(sys.argv) > 1 and sys.argv[1] == 'scan':
        # Requires authentication
        from auth_manager import auth_manager

        print("Cloud Storage Scanner")
        print("="*50)

        # Authenticate with Google
        auth = auth_manager.authenticate_gmail()  # Use same auth for Drive
        if auth:
            auth['provider'] = 'google_drive'
            # Note: Need Drive scopes in auth_manager for this to work
            scanner = CloudScanner(auth)
            results = scanner.scan_google_drive()
            print(scanner.get_summary())
    else:
        print("Usage:")
        print("  python cloud_scanner.py test  # Show test info")
        print("  python cloud_scanner.py scan  # Run scan (requires auth)")
