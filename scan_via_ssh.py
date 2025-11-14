#!/usr/bin/env python3
"""
SSH-Based Practice Analyzer

Connects to lawyer's system via SSH tunnel and performs comprehensive analysis.
This is the simplified approach - instead of OAuth/APIs, just SSH in and scan.
"""

import paramiko
import imaplib
import ssl
import time
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from tqdm import tqdm


class SSHPracticeAnalyzer:
    """Analyzes lawyer's practice through SSH tunnel"""

    def __init__(self, hostname='localhost', port=9999, username='lawyer'):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.ssh = None
        self.sftp = None
        self.results = {}

    def connect(self, password):
        """Connect to lawyer's machine via SSH tunnel"""
        print(f"🔌 Connecting to {self.username}@{self.hostname}:{self.port}")

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.hostname, port=self.port,
                        username=self.username, password=password)

        self.sftp = self.ssh.open_sftp()
        print("✅ Connected successfully!")
        return True

    def scan_email_quick(self, email_user, email_password):
        """
        Quick IMAP email analysis through tunnel
        Only analyzes metadata, not full content
        """
        print("\n📧 Scanning email system...")

        # Connect to IMAP through tunnel
        mail = imaplib.IMAP4(self.hostname, 1993)  # IMAP port through tunnel
        mail.starttls()
        mail.login(email_user, email_password)

        email_results = {
            'total_emails': 0,
            'folders': [],
            'top_senders': Counter(),
            'template_candidates': [],
            'response_patterns': {}
        }

        # Get folder list
        status, folders = mail.list()
        print(f"   Found {len(folders)} folders")

        for folder_data in tqdm(folders[:20], desc="Scanning email folders"):  # Limit to first 20 folders
            try:
                # Parse folder name
                folder_name = self._parse_folder_name(folder_data)

                # Select folder
                status, _ = mail.select(f'"{folder_name}"')
                if status != 'OK':
                    continue

                # Get email count
                status, messages = mail.search(None, 'ALL')
                if status != 'OK' or not messages[0]:
                    continue

                msg_count = len(messages[0].split())
                email_results['total_emails'] += msg_count

                email_results['folders'].append({
                    'name': folder_name,
                    'count': msg_count
                })

                # Sample emails for patterns (first 100 in each folder)
                message_ids = messages[0].split()[:100]

                for msg_id in message_ids:
                    try:
                        status, msg_data = mail.fetch(msg_id, '(FLAGS ENVELOPE)')
                        if status == 'OK':
                            self._analyze_email_envelope(msg_data[0], email_results)
                    except:
                        pass

                # Close folder
                mail.close()

            except Exception as e:
                print(f"   Error with folder: {e}")
                continue

        mail.logout()

        # Identify template candidates
        email_results['template_candidates'] = self._identify_templates(
            email_results['subject_patterns']
        )

        return email_results

    def scan_filesystem_quick(self, scan_path='~/Documents'):
        """
        Quick file system scan
        Only scans structure and key patterns, not every file
        """
        print(f"\n📁 Scanning file system (starting at {scan_path})...")

        fs_results = {
            'total_files': 0,
            'total_size': 0,
            'files_by_type': Counter(),
            'files_by_category': Counter(),
            'directory_depth': {},
            'naming_issues': [],
            'organization_score': 0,
            'duplicates_found': 0
        }

        # Expand path
        if scan_path.startswith('~'):
            scan_path = f"/Users/{self.username}/{scan_path[2:]}"

        try:
            # Walk directory tree
            for entry in self.sftp.listdir_attr(scan_path):
                if stat.S_ISDIR(entry.st_mode):
                    # Scan subdirectories
                    self._scan_remote_dir(
                        os.path.join(scan_path, entry.filename),
                        fs_results,
                        depth=1,
                        max_depth=3  # Limit depth
                    )
        except Exception as e:
            print(f"   Error accessing {scan_path}: {e}")

        # Calculate organization score
        fs_results['organization_score'] = self._calculate_org_score(fs_results)

        return fs_results

    def generate_quick_report(self, email_results, fs_results, lawyer_name):
        """Generate quick analysis report"""
        print(f"\n{'='*70}")
        print(f"PRACTICE ANALYSIS REPORT - {lawyer_name}")
        print(f"{'='*70}")

        print(f"\n📊 OVERVIEW")
        print(f"   Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"   Email folders: {len(email_results['folders'])}")
        print(f"   Files scanned: {fs_results['total_files']:,}")
        print(f"   Organization score: {fs_results['organization_score']}/10")

        # Email findings
        print(f"\n📧 EMAIL FINDINGS")
        print(f"   Total emails: {email_results['total_emails']:,}")

        if email_results['top_senders']:
            print(f"\n   Top senders:")
            for sender, count in email_results['top_senders'].most_common(5):
                print(f"     {count:4d} - {sender[:40]}")

        if email_results['template_candidates']:
            print(f"\n   📝 Template opportunities ({len(email_results['template_candidates'])}):")
            for template in email_results['template_candidates'][:5]:
                print(f"     {template['count']:3d}x - {template['subject'][:50]}")

        # File system findings
        print(f"\n📁 FILE SYSTEM FINDINGS")
        print(f"   Total size: {fs_results['total_size'] / (1024**3):.2f} GB")

        if fs_results['files_by_category']:
            print(f"\n   Top categories:")
            for category, count in fs_results['files_by_category'].most_common(5):
                print(f"     {count:5d} - {category.replace('_', ' ').title()}")

        # Recommendations
        print(f"\n💡 KEY RECOMMENDATIONS")
        recommendations = self._generate_recommendations(
            email_results, fs_results
        )

        for i, rec in enumerate(recommendations, 1):
            print(f"\n   {i}. {rec['title']}")
            print(f"      Priority: {rec['priority'].title()}")
            print(f"      Time savings: {rec['time_savings']:.1f} hrs/week")
            print(f"      Effort: {rec['effort']}")

        print(f"\n{'='*70}")
        print(f"Total potential time savings: {sum(r['time_savings'] for r in recommendations):.1f} hours/week")
        print(f"{'='*70}")

        return recommendations

    def _generate_recommendations(self, email_results, fs_results):
        """Generate specific recommendations based on findings"""
        recommendations = []

        # Email template recommendations
        if email_results['template_candidates']:
            high_frequency = [t for t in email_results['template_candidates'] if t['count'] > 5]
            if high_frequency:
                recommendations.append({
                    'priority': 'high',
                    'title': f'Create {len(high_frequency)} email templates',
                    'description': f'You repeatedly send {len(high_frequency)} similar emails.',
                    'time_savings': len(high_frequency) * 0.5,  # 0.5 hrs per template per week
                    'effort': '1-2 hours'
                })

        # File organization
        if fs_results['organization_score'] < 5:
            recommendations.append({
                'priority': 'high',
                'title': 'Implement file organization system',
                'description': 'Files are disorganized, making them hard to find.',
                'time_savings': 2.0,
                'effort': '4-6 hours'
            })

        # Folder simplification
        if len(email_results['folders']) > 20:
            recommendations.append({
                'priority': 'medium',
                'title': 'Simplify email folder structure',
                'description': f'You have {len(email_results["folders"])} folders (recommended: 5-10).',
                'time_savings': 1.0,
                'effort': '1-2 hours'
            })

        return sorted(recommendations, key=lambda x: x['priority'])

    def disconnect(self):
        """Close connections"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print("\n🔌 Disconnected")


# Helper methods
import imaplib
from email import message_from_bytes
def parse_folder_name(folder_data):
    """Parse IMAP folder name"""
    # Folder format: b'(\\HasNoChildren) "/" "INBOX"'
    parts = str(folder_data).split('"')
    return parts[-2] if len(parts) >= 2 else 'Unknown'

def _analyze_email_envelope(self, msg_data, email_results):
    """Extract info from email envelope"""
    # This is a simplified version - real implementation would parse IMAP envelope
    # For now, just demonstrate structure
    if b'ENVELOPE' in msg_data:
        # Extract sender, subject, date
        # In real implementation, parse the IMAP envelope response
        pass

def _identify_templates(self, subject_patterns):
    """Identify frequently used email subjects as template candidates"""
    from collections import Counter
    import re

    templates = []

    # Count exact matches
    for subject, count in subject_patterns.items():
        if count > 2:  # Sent more than twice
            templates.append({
                'subject': subject,
                'count': count,
                'frequency': count
            })

    return sorted(templates, key=lambda x: x['count'], reverse=True)

def _calculate_org_score(self, fs_results):
    """Calculate organization score 0-10"""
    score = 5.0  # Base score

    # Deduct for deep directories
    if fs_results.get('max_depth', 0) > 5:
        score -= 1.0

    # Deduct for many files in root
    if fs_results['total_files'] > 0:
        root_ratio = fs_results.get('root_files', 0) / fs_results['total_files']
        if root_ratio > 0.3:
            score -= 1.5

    # Deduct for duplicates
    if fs_results['duplicates_found'] > 10:
        score -= 1.0

    # Add for good categorization
    if len(fs_results.get('files_by_category', {}).most_common(5)) > 3:
        score += 0.5

    return max(0, min(10, score))


import stat
if __name__ == "__main__":
    import sys
    import getpass

    if len(sys.argv) < 2:
        print("Usage: python scan_via_ssh.py --demo")
        print("\nThis requires:")
        print("  1. SSH tunnel to be established")
        print("  2. IMAP port forwarded (usually 1993)")
        print("  3. Lawyer's email credentials")
        sys.exit(1)

    if sys.argv[1] == '--demo':
        print("🚀 SSH-Based Practice Analyzer - Demo Mode")
        print("="*60)
        print()
        print("This demonstrates how to scan a lawyer's systems via SSH tunnel.")
        print()
        print("Setup required:")
        print("  1. Lawyer runs: ssh -R 9999:localhost:22 -N your-user@your-server")
        print("  2. Forward IMAP: ssh -L 1993:localhost:993 -N your-server")
        print("  3. Run this script with lawyer's credentials")
        print()
        print("Benefits:")
        print("  ✓ No complex OAuth setup")
        print("  ✓ Full access to systems (with permission)")
        print("  ✓ Use all your existing tools")
        print("  ✓ Lawyer controls access (can close tunnel)")
        print()
        print("See SSH_TUNNEL_SETUP.md for detailed instructions")
        sys.exit(0)

    # Real usage would require actual SSH tunnel and credentials
    hostname = input("SSH tunnel host [localhost]: ") or 'localhost'
    ssh_port = int(input("SSH tunnel port [9999]: ") or 9999)
    ssh_user = input("SSH username: ")
    ssh_pass = getpass.getpass("SSH password: ")

    email_user = input("Lawyer's email: ")
    email_pass = getpass.getpass("Lawyer's email password: ")

    print("\n" + "="*60)
    print("STARTING ANALYSIS")
    print("="*60)

    analyzer = SSHPracticeAnalyzer(hostname, ssh_port, ssh_user)
    analyzer.connect(ssh_pass)

    # Quick email scan
    email_results = analyzer.scan_email_quick(email_user, email_pass)

    # Quick file system scan
    fs_results = analyzer.scan_filesystem_quick()

    # Generate report
    recommendations = analyzer.generate_quick_report(
        email_results,
        fs_results,
        ssh_user
    )

    analyzer.disconnect()

    print("\n✅ Analysis complete!")
