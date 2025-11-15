"""
System Coordinator

Coordinates all scanning modules, aggregates data, and generates
comprehensive analysis of lawyer's practice systems.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import all scanners
from auth_manager import AuthManager
from email_scanner import EmailScanner
from fs_analyzer import FileAnalyzer
from cloud_scanner import CloudScanner
from moonshot_client import get_moonshot_client

logger = logging.getLogger(__name__)


class SystemCoordinator:
    """Coordinates scanning, analysis, and reporting of lawyer's systems."""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.scan_results = {}
        self.analysis_timestamp = None
        self.lawyer_name = None
        self.lawyer_email = None

    def run_full_analysis(self,
                         lawyer_name: str,
                         lawyer_email: str,
                         scan_local_files: bool = True,
                         scan_gmail: bool = True,
                         scan_drive: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive analysis of lawyer's systems.

        Args:
            lawyer_name: Lawyer"'"s full name
            lawyer_email: Lawyer"'"s email address
            scan_local_files: Whether to scan local file system
            scan_gmail: Whether to scan Gmail (requires auth)
            scan_drive: Whether to scan Google Drive (requires auth)

        Returns:
            Comprehensive analysis results
        """
        logger.info(f"Starting full system analysis for {lawyer_name}")

        self.analysis_timestamp = datetime.now().isoformat()
        self.lawyer_name = lawyer_name
        self.lawyer_email = lawyer_email

        self.scan_results = {
            'lawyer_info': {
                'name': lawyer_name,
                'email': lawyer_email,
                'analysis_date': self.analysis_timestamp
            },
            'scan_summary': {
                'modules_scanned': [],
                'total_findings': 0,
                'total_recommendations': 0,
                'total_time_savings_estimate': 0
            },
            'email_analysis': None,
            'filesystem_analysis': None,
            'cloud_analysis': None,
            'consolidated_findings': None,
            'ai_insights': None,
            'prioritized_recommendations': None
        }

        # 1. Scan email system
        if scan_gmail:
            logger.info("Scanning email system...")
            gmail_auth = self.auth_manager.authenticate_gmail()
            if gmail_auth:
                email_scanner = EmailScanner(gmail_auth)
                email_results = email_scanner.scan_gmail()
                self.scan_results['email_analysis'] = email_results
                self.scan_results['scan_summary']['modules_scanned'].append('email')
                logger.info(f"Email scan complete: {email_results.get('total_emails_in_account', 0):,} emails")
            else:
                logger.warning("Gmail authentication failed, skipping email scan")

        # 2. Scan local file system
        if scan_local_files:
            logger.info("Scanning local file system...")
            # Default to Documents folder
            docs_path = Path.home() / "Documents"
            if docs_path.exists():
                fs_analyzer = FileAnalyzer(str(docs_path))
                fs_results = fs_analyzer.scan_filesystem()
                self.scan_results['filesystem_analysis'] = fs_results
                self.scan_results['scan_summary']['modules_scanned'].append('filesystem')
                logger.info(f"File system scan complete: {fs_results.get('total_files', 0):,} files")
            else:
                logger.warning(f"Documents directory not found: {docs_path}")

        # 3. Scan Google Drive
        if scan_drive:
            logger.info("Scanning Google Drive...")
            drive_auth = self.auth_manager.authenticate_gmail()  # Reuse Gmail auth for Drive
            if drive_auth:
                drive_scanner = CloudScanner(drive_auth)
                drive_results = drive_scanner.scan_google_drive()
                self.scan_results['cloud_analysis'] = drive_results
                self.scan_results['scan_summary']['modules_scanned'].append('google_drive')
                logger.info(f"Google Drive scan complete: {drive_results.get('total_files', 0):,} files")
            else:
                logger.warning("Drive authentication failed, skipping drive scan")

        # 4. Consolidate findings
        logger.info("Consolidating findings across all modules...")
        consolidated = self._consolidate_findings()
        self.scan_results['consolidated_findings'] = consolidated
        self.scan_results['scan_summary']['total_findings'] = len(consolidated.get('issues', []))

        # 5. Generate AI insights
        logger.info("Generating AI insights...")
        ai_insights = self._generate_ai_insights()
        self.scan_results['ai_insights'] = ai_insights

        # 6. Create prioritized recommendations
        logger.info("Creating prioritized recommendations...")
        recommendations = self._create_prioritized_recommendations()
        self.scan_results['prioritized_recommendations'] = recommendations
        self.scan_results['scan_summary']['total_recommendations'] = len(recommendations)
        self.scan_results['scan_summary']['total_time_savings_estimate'] = sum(
            r.get('estimated_time_savings_hours_per_week', 0) for r in recommendations
        )

        logger.info("Full system analysis completed")
        return self.scan_results

    def _consolidate_findings(self) -> Dict[str, Any]:
        """Combine findings from all scanning modules."""
        consolidated = {
            'critical_issues': [],
            'high_priority_issues': [],
            'medium_priority_issues': [],
            'low_priority_issues': [],
            'opportunities': [],
            'security_concerns': []
        }

        # Extract issues from each module
        modules = [
            self.scan_results.get('email_analysis'),
            self.scan_results.get('filesystem_analysis'),
            self.scan_results.get('cloud_analysis')
        ]

        for module in modules:
            if module and module.get('scan_complete'):
                issues = module.get('organization_issues', [])

                for issue in issues:
                    severity = issue.get('severity', 'low')
                    combined_issue = {
                        'module': module.get('provider', 'unknown'),
                        'severity': severity,
                        'issue': issue.get('issue'),
                        'description': issue.get('description'),
                        'impact': issue.get('impact')
                    }

                    if severity == 'critical':
                        consolidated['critical_issues'].append(combined_issue)
                    elif severity == 'high':
                        consolidated['high_priority_issues'].append(combined_issue)
                    elif severity == 'medium':
                        consolidated['medium_priority_issues'].append(combined_issue)
                    else:
                        consolidated['low_priority_issues'].append(combined_issue)

        return consolidated

    def _generate_ai_insights(self) -> Dict[str, Any]:
        """Generate AI-powered insights from scan results."""
        try:
            moonshot_client = get_moonshot_client()

            # Prepare data for AI analysis
            analysis_prompt = self._prepare_ai_analysis_prompt()

            response = moonshot_client.client.chat.completions.create(
                model=moonshot_client.model,
                messages=[
                    {"role": "system", "content": self._get_ai_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )

            insights = response.choices[0].message.content.strip()

            # Parse insights into structured format
            return self._parse_ai_insights(insights)

        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {
                'error': 'AI analysis failed',
                'summary': 'Unable to generate AI insights due to technical issue.',
                'key_patterns': [],
                'unusual_workflows': [],
                'efficiency_opportunities': []
            }

    def _prepare_ai_analysis_prompt(self) -> str:
        """Prepare scan data as prompt for AI analysis."""
        prompt = f"""Analyze the following system scan data for {self.lawyer_name} (litigation attorney):

SCAN SUMMARY:
- Analysis Date: {self.analysis_timestamp}
- Modules Scanned: {', '.join(self.scan_results['scan_summary']['modules_scanned'])}

"""

        # Add email analysis data
        email_analysis = self.scan_results.get('email_analysis')
        if email_analysis and email_analysis.get('scan_complete'):
            prompt += f"""
EMAIL SYSTEM ANALYSIS:
- Provider: {email_analysis.get('provider', 'Unknown')}
- Total Emails: {email_analysis.get('total_emails_in_account', 0):,}
- Folders/Labels: {email_analysis.get('folder_count', 0)}
- Avg Response Time: {email_analysis.get('response_analysis', {}).get('avg_response_time_hours', 0):.1f} hours
- Template Candidates: {len(email_analysis.get('email_patterns', {}).get('template_candidates', []))}
- Workflows Identified: {len(email_analysis.get('email_patterns', {}).get('workflows', []))}
"""

        # Add file system data
        fs_analysis = self.scan_results.get('filesystem_analysis')
        if fs_analysis and fs_analysis.get('scan_complete'):
            prompt += f"""
FILE SYSTEM ANALYSIS:
- Files Scanned: {fs_analysis.get('total_files', 0):,}
- Total Size: {fs_analysis.get('total_size_bytes', 0) / (1024**3):.2f} GB
- Directories: {len(fs_analysis.get('directories', {}))}
- Duplicate Groups: {len(fs_analysis.get('duplicates', []))}
- Top Categories: {', '.join(f"{cat}: {count}" for cat, count in sorted(fs_analysis.get('files_by_category', {}).items(), key=lambda x: x[1], reverse=True)[:3])}
"""

        # Add cloud storage data
        drive_analysis = self.scan_results.get('cloud_analysis')
        if drive_analysis and drive_analysis.get('scan_complete'):
            prompt += f"""
GOOGLE DRIVE ANALYSIS:
- Total Files: {drive_analysis.get('total_files', 0):,}
- Storage Used: {drive_analysis.get('quota_info', {}).get('usage_percent', 0):.1f}%
- Shared Files: {len(drive_analysis.get('shared_files', []))}
- Top Categories: {', '.join(f"{cat}: {count}" for cat, count in sorted(drive_analysis.get('files_by_category', {}).items(), key=lambda x: x[1], reverse=True)[:3])}
"""

        prompt += """

Based on this data, provide:
1. Key patterns and insights about this lawyer's workflow
2. Unusual workflows or inefficiencies detected
3. Specific opportunities for automation and improvement
4. Estimated time savings for each recommendation
5. Implementation priorities

Be specific, data-driven, and actionable. Focus on patterns that indicate repetitive work, disorganization, or manual processes that could be automated.
"""

        return prompt

    def _get_ai_system_prompt(self) -> str:
        """Get system prompt for AI analysis."""
        return """You are an expert legal practice management consultant with 20+ years of experience optimizing law firm operations.

Your role is to analyze system data (emails, files, organization patterns) and identify opportunities for automation and efficiency improvements.

For each analysis, provide:
1. Key Pattern Identification - What the data reveals about their workflow
2. Efficiency Gaps - Where time is being wasted
3. Automation Opportunities - Specific repetitive tasks that could be automated
4. Organization Issues - Structural problems causing inefficiency
5. Prioritized Action Plan - What to fix first, with ROI estimates

Be specific, use concrete numbers from the data, and provide actionable recommendations.
Focus on quick wins (immediate impact, low effort) and high-ROI improvements.

Output format:
- Start with an executive summary
- List 3-5 key patterns with specific data points
- Provide 5-7 prioritized recommendations
- Include estimated time savings for each
- Note implementation difficulty
"""

    def _parse_ai_insights(self, insights: str) -> Dict[str, Any]:
        """Parse AI insights into structured format."""
        # This is a simplified parser - in production would use more sophisticated parsing
        return {
            'raw_insights': insights,
            'structured': {
                'executive_summary': insights.split('\n')[0] if insights else "",
                'key_patterns': [],
                'efficiency_gaps': [],
                'automation_opportunities': [],
                'organization_issues': []
            }
        }

    def _create_prioritized_recommendations(self) -> List[Dict[str, Any]]:
        """Create consolidated, prioritized recommendations from all modules."""
        all_recs = []

        # Get recommendations from each module
        modules = [
            self.scan_results.get('email_analysis'),
            self.scan_results.get('filesystem_analysis'),
            self.scan_results.get('cloud_analysis')
        ]

        for module in modules:
            if module and module.get('scan_complete'):
                module_recs = module.get('recommendations', [])
                for rec in module_recs:
                    rec['source'] = module.get('provider', 'unknown')
                    all_recs.append(rec)

        # Sort by priority and time savings
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        all_recs.sort(
            key=lambda x: (priority_order.get(x.get('priority', 'low'), 0),
                          x.get('estimated_time_savings_hours_per_week', 0)),
            reverse=True
        )

        return all_recs

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive markdown report."""
        if not self.scan_results.get('scan_summary'):
            return "No analysis completed yet. Run run_full_analysis() first."

        summary = self.scan_results['scan_summary']
        consolidated = self.scan_results.get('consolidated_findings', {})
        ai_insights = self.scan_results.get('ai_insights', {})
        recommendations = self.scan_results.get('prioritized_recommendations', [])

        report = f"""# Practice Systems Analysis Report
**For:** {self.lawyer_name}
**Email:** {self.lawyer_email}
**Analysis Date:** {self.analysis_timestamp}
**Scan Modules:** {', '.join(summary.get('modules_scanned', []))}

---

## Executive Summary

This automated analysis scanned your practice systems and identified **{summary.get('total_findings', 0)}** findings with **{summary.get('total_recommendations', 0)}** actionable recommendations.

**Estimated Time Savings:** {summary.get('total_time_savings_estimate', 0):.1f} hours per week (approximately ${summary.get('total_time_savings_estimate', 0) * 100:.0f}/week at $100/hr billing rate)

### Key Statistics

"""

        # Add module-specific stats
        email_analysis = self.scan_results.get('email_analysis')
        if email_analysis and email_analysis.get('scan_complete'):
            report += f"* **Email System:** {email_analysis.get('total_emails_in_account', 0):,} emails, "
            report += f"{email_analysis.get('folder_count', 0)} folders, "
            report += f"{email_analysis.get('response_analysis', {}).get('avg_response_time_hours', 0):.1f}hr avg response time\n"

        fs_analysis = self.scan_results.get('filesystem_analysis')
        if fs_analysis and fs_analysis.get('scan_complete'):
            report += f"* **File System:** {fs_analysis.get('total_files', 0):,} files, "
            report += f"{fs_analysis.get('total_size_bytes', 0) / (1024**3):.2f}GB total, "
            report += f"{len(fs_analysis.get('duplicates', []))} duplicate groups\n"

        drive_analysis = self.scan_results.get('cloud_analysis')
        if drive_analysis and drive_analysis.get('scan_complete'):
            quota = drive_analysis.get('quota_info', {})
            report += f"* **Google Drive:** {drive_analysis.get('total_files', 0):,} files, "
            report += f"{quota.get('usage_percent', 0):.1f}% storage used\n"

        # Add critical issues
        if consolidated.get('critical_issues'):
            report += f"\n### 🚨 Critical Issues Requiring Immediate Attention\n\n"
            for issue in consolidated['critical_issues']:
                report += f"- **{issue['issue']}** ({issue['module']}): {issue['description']}\n"
                report += f"  Impact: {issue['impact']}\n\n"

        # Add high priority issues
        if consolidated.get('high_priority_issues'):
            report += f"\n### ⚠️ High Priority Issues\n\n"
            for issue in consolidated['high_priority_issues'][:5]:
                report += f"- **{issue['issue']}** ({issue['module']}): {issue['description']}\n"
                report += f"  Impact: {issue['impact']}\n\n"

        # Add AI insights
        if ai_insights:
            report += f"\n## 🤖 AI-Generated Insights\n\n"
            report += f"{ai_insights.get('raw_insights', 'AI insights not available')}\n\n"

        # Add recommendations
        if recommendations:
            report += f"\n## 🎯 Prioritized Recommendations\n\n"
            report += f"| Priority | Action | Time Savings/Week | Implementation Time | Difficulty |\n"
            report += f"|----------|--------|-------------------|---------------------|------------|\n"

            for rec in recommendations[:10]:  # Top 10
                report += f"| {rec.get('priority', 'unknown').title()} | {rec.get('title', 'N/A')} | "
                report += f"{rec.get('estimated_time_savings_hours_per_week', 0)} hrs | "
                report += f"{rec.get('implementation_time', 'N/A')} | "
                report += f"{rec.get('difficulty', 'unknown').title()} |\n"
            report += "\n"

        report += "---\n\n"
        report += "*This report was generated by an automated system analysis. "
        report += "Recommendations are based on actual data from your practice systems.*"

        return report

    def get_summary(self) -> str:
        """Get quick summary of analysis."""
        if not self.scan_results.get('scan_summary'):
            return "No analysis completed yet."

        summary = self.scan_results['scan_summary']

        return f"""System Analysis Summary
{'='*50}
Lawyer: {self.lawyer_name}
Email: {self.lawyer_email}
Date: {self.analysis_timestamp[:19]}

Modules Scanned: {len(summary.get('modules_scanned', []))}
Total Findings: {summary.get('total_findings', 0)}
Total Recommendations: {summary.get('total_recommendations', 0)}
Est. Time Savings: {summary.get('total_time_savings_estimate', 0):.1f} hrs/week

Status: {'✅ Complete' if all(m and m.get('scan_complete') for m in [
    self.scan_results.get('email_analysis'),
    self.scan_results.get('filesystem_analysis'),
    self.scan_results.get('cloud_analysis')
] if m) else '⚠️ Partial'}

Next Steps: Review full report and prioritize top 3 recommendations.
"""


# Convenience function
def run_full_system_analysis(lawyer_name: str,
                           lawyer_email: str,
                           **scan_options) -> SystemCoordinator:
    """
    Run complete system analysis.

    Args:
        lawyer_name: Lawyer"'"s name
        lawyer_email: Lawyer"'"s email
        **scan_options: Options for what to scan

    Returns:
        SystemCoordinator instance with complete analysis
    """
    coordinator = SystemCoordinator()
    coordinator.run_full_analysis(lawyer_name, lawyer_email, **scan_options)
    return coordinator


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python system_coordinator.py 'Lawyer Name' 'lawyer@email.com'")
        print("\nOptions:")
        print("  --no-files     Skip file system scan")
        print("  --no-email     Skip email scan")
        print("  --no-drive     Skip Google Drive scan")
        print("\nExample:")
        print("  python system_coordinator.py 'John Smith' 'john@lawfirm.com'")
        sys.exit(1)

    name = sys.argv[1]
    email = sys.argv[2]

    # Parse options
    scan_options = {
        'scan_local_files': '--no-files' not in sys.argv,
        'scan_gmail': '--no-email' not in sys.argv,
        'scan_drive': '--no-drive' not in sys.argv
    }

    print(f"Running full system analysis for {name}")
    print("="*60)
    print("This will take several minutes depending on system size...")
    print()

    coordinator = run_full_system_analysis(name, email, **scan_options)

    print(coordinator.get_summary())
    print()

    # Save report to file
    report = coordinator.generate_comprehensive_report()
    report_filename = f"system_analysis_{email.replace('@', '_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_filename, 'w') as f:
        f.write(report)

    print(f"✅ Full report saved to: {report_filename}")
    print()
    print("Next steps:")
    print("1. Review the report")
    print("2. Prioritize top 3 recommendations")
    print("3. Generate automation scripts")
