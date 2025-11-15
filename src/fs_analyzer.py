"""
File System Analyzer

Scans local directories, analyzes organization patterns,
identifies inefficiencies, and suggests improvements.
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """Analyzes file system organization, patterns, and inefficiencies."""

    def __init__(self, scan_path: Optional[str] = None):
        self.scan_path = Path(scan_path) if scan_path else Path.home() / "Documents"
        self.analysis_results = {}
        self.excluded_dirs = {
            '.git', '.svn', 'node_modules', '__pycache__', 'venv', 'env',
            'Library', 'AppData', 'Cookies', 'Recent', 'Temp', 'Temporary'
        }
        self.excluded_extensions = {'.tmp', '.temp', '.cache', '.lock'}

    def scan_filesystem(self, max_files: int = 10000) -> Dict[str, Any]:
        """
        Scan file system and analyze organization patterns.

        Args:
            max_files: Maximum number of files to analyze (to prevent timeouts)

        Returns:
            Analysis results with statistics and recommendations
        """
        logger.info(f"Starting file system scan from: {self.scan_path}")

        results = {
            'scan_timestamp': datetime.now().isoformat(),
            'scan_path': str(self.scan_path),
            'total_files': 0,
            'total_dirs': 0,
            'total_size_bytes': 0,
            'files_by_type': defaultdict(int),
            'files_by_category': defaultdict(int),
            'size_by_category': defaultdict(int),
            'directories': {},
            'duplicates': [],
            'organization_issues': [],
            'file_paths': [],
            'depth_analysis': {},
            'naming_patterns': {},
            'recommendations': []
        }

        try:
            # Walk directory tree
            file_count = 0
            file_hashes = defaultdict(list)
            dir_structure = defaultdict(list)

            for root, dirs, files in os.walk(self.scan_path):
                # Exclude hidden/system directories
                dirs[:] = [d for d in dirs if d not in self.excluded_dirs and not d.startswith('.')]

                rel_path = Path(root).relative_to(self.scan_path)
                current_dir = str(rel_path) if str(rel_path) != '.' else 'root'

                # Analyze directory
                if files:
                    results['directories'][current_dir] = {
                        'file_count': len(files),
                        'total_size': 0,
                        'depth': len(rel_path.parts) if str(rel_path) != '.' else 0
                    }

                # Analyze files
                for filename in files:
                    if file_count >= max_files:
                        logger.warning(f"Reached max file limit: {max_files}")
                        break

                    if any(filename.endswith(ext) for ext in self.excluded_extensions):
                        continue

                    filepath = Path(root) / filename

                    try:
                        # File stats
                        stat = filepath.stat()
                        file_size = stat.st_size
                        file_ext = filepath.suffix.lower()

                        # Collect data
                        results['total_files'] += 1
                        results['total_size_bytes'] += file_size
                        results['directories'][current_dir]['total_size'] += file_size

                        # Categorize file
                        category = self._categorize_file(filepath)
                        results['files_by_category'][category] += 1
                        results['size_by_category'][category] += file_size

                        # Track by extension
                        results['files_by_type'][file_ext] += 1

                        # Store path for later analysis
                        results['file_paths'].append({
                            'path': str(filepath),
                            'size': file_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'category': category,
                            'extension': file_ext,
                            'dir': current_dir
                        })

                        # Check for duplicates
                        if file_size > 1024:  # Skip tiny files
                            file_hash = self._get_file_hash(filepath)
                            if file_hash:
                                file_hashes[file_hash].append(str(filepath))

                        # Track directory structure
                        dir_structure[current_dir].append({
                            'filename': filename,
                            'size': file_size,
                            'category': category
                        })

                        file_count += 1

                        if file_count % 1000 == 0:
                            logger.debug(f"Scanned {file_count} files...")

                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access {filepath}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error analyzing {filepath}: {e}")
                        continue

            # Analyze duplicates
            for file_hash, paths in file_hashes.items():
                if len(paths) > 1:
                    # Calculate total size of duplicates (excluding first)
                    total_duplicate_size = sum(Path(p).stat().st_size for p in paths[1:])
                    results['duplicates'].append({
                        'hash': file_hash[:16],
                        'file_count': len(paths),
                        'total_size_bytes': total_duplicate_size,
                        'paths': paths[:5]  # Store first 5 paths
                    })

            # Analyze directory depth
            results['depth_analysis'] = self._analyze_depth(dir_structure)

            # Analyze naming patterns
            results['naming_patterns'] = self._analyze_naming_patterns(results['file_paths'])

            # Detect organization issues
            results['organization_issues'] = self._detect_organization_issues(results)

            # Generate recommendations
            results['recommendations'] = self._generate_file_recommendations(results)

            results['scan_complete'] = True
            logger.info(f"File system scan completed: {results['total_files']:,} files analyzed")

        except Exception as e:
            logger.error(f"File system scan failed: {e}")
            results['error'] = str(e)
            results['scan_complete'] = False

        self.analysis_results = results
        return results

    def _categorize_file(self, filepath: Path) -> str:
        """Categorize file based on extension and path."""
        ext = filepath.suffix.lower()
        path_str = str(filepath).lower()

        # Legal documents
        if ext in ['.pdf', '.doc', '.docx', '.rtf']:
            if 'contract' in path_str or 'agreement' in path_str:
                return 'legal_contracts'
            elif 'pleading' in path_str or 'motion' in path_str:
                return 'legal_pleadings'
            elif 'discovery' in path_str:
                return 'legal_discovery'
            elif 'letter' in path_str:
                return 'legal_correspondence'
            else:
                return 'documents'

        # Images
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            return 'images'

        # Spreadsheets
        elif ext in ['.xls', '.xlsx', '.csv']:
            if 'billing' in path_str or 'invoice' in path_str:
                return 'billing'
            return 'spreadsheets'

        # Presentations
        elif ext in ['.ppt', '.pptx']:
            return 'presentations'

        # Archives
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return 'archives'

        # Executables
        elif ext in ['.exe', '.msi', '.app', '.bat', '.sh']:
            return 'executables'

        # Code
        elif ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c']:
            return 'code'

        else:
            return 'other'

    def _get_file_hash(self, filepath: Path) -> Optional[str]:
        """Calculate MD5 hash of file for duplicate detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None

    def _analyze_depth(self, dir_structure: Dict[str, List]) -> Dict[str, Any]:
        """Analyze directory depth and structure."""
        analysis = {
            'avg_depth': 0,
            'max_depth': 0,
            'deep_folders': [],
            'shallow_folders': [],
            'optimal_depth': 3,  # Best practice: 3-4 levels
            'depth_distribution': defaultdict(int)
        }

        for dir_path, files in dir_structure.items():
            depth = dir_path.count('/')
            analysis['depth_distribution'][depth] += 1

            if depth > analysis['max_depth']:
                analysis['max_depth'] = depth

        # Calculate avg depth
        if dir_structure:
            depths = [path.count('/') for path in dir_structure.keys()]
            analysis['avg_depth'] = sum(depths) / len(depths)

        # Identify problematic deep folders (hard to navigate)
        for dir_path in dir_structure.keys():
            depth = dir_path.count('/')
            if depth >= 6:  # Too deep
                analysis['deep_folders'].append({
                    'path': dir_path,
                    'depth': depth,
                    'file_count': len(dir_structure[dir_path])
                })
            elif depth <= 1 and len(dir_structure[dir_path]) > 20:  # Too shallow and crowded
                analysis['shallow_folders'].append({
                    'path': dir_path,
                    'depth': depth,
                    'file_count': len(dir_structure[dir_path])
                })

        return dict(analysis)

    def _analyze_naming_patterns(self, file_paths: List[Dict]) -> Dict[str, Any]:
        """Analyze file naming conventions and patterns."""
        patterns = {
            'date_in_name': 0,
            'client_name_in_name': 0,
            'case_number_in_name': 0,
            'spaces_in_name': 0,
            'special_chars_in_name': 0,
            'descriptive_names': 0,
            'generic_names': 0
        }

        sample_files = file_paths[:200]  # Analyze first 200 files

        for file_info in sample_files:
            filename = Path(file_info['path']).name
            filename_lower = filename.lower()

            # Check for date patterns (YYYY-MM-DD, MM-DD-YYYY, etc.)
            if any(pattern in filename_lower for pattern in ['202', '2024', '2025']):
                patterns['date_in_name'] += 1

            # Check for client identifiers
            if any(word in filename_lower for word in ['client', 'matter', 'case']):
                patterns['client_name_in_name'] += 1

            # Check for case numbers (e.g., CA-2024-1234)
            if any(char.isdigit() for char in filename) and '-' in filename:
                patterns['case_number_in_name'] += 1

            # Check naming quality
            name_without_ext = Path(filename).stem
            if ' ' in name_without_ext:
                patterns['spaces_in_name'] += 1

            if any(char in name_without_ext for char in ['!', '@', '#', '$', '%']):
                patterns['special_chars_in_name'] += 1

            # Check if descriptive (>15 chars, multiple words) or generic (<10 chars)
            if len(name_without_ext) > 15:
                patterns['descriptive_names'] += 1
            elif len(name_without_ext) < 10:
                patterns['generic_names'] += 1

        # Convert to percentages
        total_sample = len(sample_files) if sample_files else 1
        for key in patterns:
            patterns[key] = (patterns[key] / total_sample) * 100

        return patterns

    def _detect_organization_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect organization issues and inefficiencies."""
        issues = []

        # Check for too many files at root
        root_files = results['directories'].get('root', {}).get('file_count', 0)
        if root_files > 50:
            issues.append({
                'severity': 'high',
                'issue': 'too_many_root_files',
                'description': f'{root_files} files in root directory (should be < 20)',
                'impact': 'Hard to find files, poor organization'
            })

        # Check for deep folder structures
        if results['depth_analysis'].get('max_depth', 0) >= 8:
            issues.append({
                'severity': 'medium',
                'issue': 'folder_depth_too_deep',
                'description': f"Max folder depth: {results['depth_analysis']['max_depth']} levels",
                'impact': 'Difficult navigation, hard to locate files'
            })

        # Check for many folders with few files
        shallow_folders = results['depth_analysis'].get('shallow_folders', [])
        if len(shallow_folders) > 5:
            issues.append({
                'severity': 'medium',
                'issue': 'overcrowded_top_level',
                'description': f'{len(shallow_folders)} folders with >20 files at shallow depth',
                'impact': 'Cluttered organization, hard to find files'
            })

        # Check for inconsistent naming
        naming_patterns = results['naming_patterns']
        if naming_patterns.get('spaces_in_name', 0) > 30:
            issues.append({
                'severity': 'low',
                'issue': 'spaces_in_filenames',
                'description': f"{naming_patterns['spaces_in_name']:.1f}% of files have spaces",
                'impact': 'Cross-platform compatibility issues'
            })

        # Check for duplicates
        duplicates = results.get('duplicates', [])
        if duplicates:
            total_duplicate_size = sum(d['total_size_bytes'] for d in duplicates)
            issues.append({
                'severity': 'medium',
                'issue': 'duplicate_files',
                'description': f'{len(duplicates)} duplicate groups, {total_duplicate_size / (1024**3):.1f}GB wasted',
                'impact': 'Wasted storage, confusion about which file is current'
            })

        # Check for missing date/client info
        if naming_patterns.get('date_in_name', 0) < 10:
            issues.append({
                'severity': 'low',
                'issue': 'missing_dates_in_filenames',
                'description': f"Only {naming_patterns['date_in_name']:.1f}% of files have dates",
                'impact': 'Hard to track file versions and dates'
            })

        return issues

    def _generate_file_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on file analysis."""
        recommendations = []

        # Duplicate cleanup
        duplicates = results.get('duplicates', [])
        if duplicates:
            total_duplicate_size = sum(d['total_size_bytes'] for d in duplicates)
            recommendations.append({
                'priority': 'high',
                'area': 'duplicate_cleanup',
                'title': f'Remove {len(duplicates)} duplicate file groups',
                'description': f'Found {len(duplicates)} groups of duplicate files wasting {total_duplicate_size / (1024**3):.1f}GB of storage.',
                'estimated_time_savings_hours_per_week': 0.5,  # Time saved searching
                'implementation_time': '2-4 hours',
                'difficulty': 'easy'
            })

        # Folder structure simplification
        depth_analysis = results.get('depth_analysis', {})
        if depth_analysis.get('max_depth', 0) >= 6:
            recommendations.append({
                'priority': 'medium',
                'area': 'folder_structure',
                'title': 'Simplify folder structure (max depth too high)',
                'description': f"Folder structure is {depth_analysis['max_depth']} levels deep. Simplifying to 3-4 levels would improve navigation.",
                'estimated_time_savings_hours_per_week': 1.0,
                'implementation_time': '4-8 hours',
                'difficulty': 'medium'
            })

        # Naming convention standardization
        naming_patterns = results.get('naming_patterns', {})
        if naming_patterns.get('spaces_in_name', 0) > 30:
            recommendations.append({
                'priority': 'low',
                'area': 'naming_convention',
                'title': 'Standardize file naming conventions',
                'description': f"{naming_patterns['spaces_in_name']:.1f}% of files use spaces. Consider using dashes/underscores for better cross-platform compatibility.",
                'estimated_time_savings_hours_per_week': 0.2,
                'implementation_time': '1-2 hours',
                'difficulty': 'easy'
            })

        # File categorization
        total_files = results.get('total_files', 0)
        uncategorized = results['files_by_category'].get('other', 0)
        if uncategorized / total_files > 0.3 if total_files > 0 else False:
            recommendations.append({
                'priority': 'medium',
                'area': 'file_categorization',
                'title': 'Implement better file categorization',
                'description': f"{uncategorized / total_files * 100:.1f}% of files are uncategorized. Organizing by case/client/type would help.",
                'estimated_time_savings_hours_per_week': 2.0,
                'implementation_time': '4-6 hours',
                'difficulty': 'medium'
            })

        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)

    def get_summary(self) -> str:
        """Get a summary of the file analysis."""
        if not self.analysis_results:
            return "No analysis completed yet."

        results = self.analysis_results

        summary = f"""File System Analysis Summary
{'='*50}
Scan Path: {results.get('scan_path', 'Unknown')}
Date: {results.get('scan_timestamp', 'Unknown')}

Statistics:
- Total files: {results.get('total_files', 0):,}
- Total directories: {len(results.get('directories', {}))}
- Total size: {results.get('total_size_bytes', 0) / (1024**3):.2f} GB
- Duplicate groups: {len(results.get('duplicates', []))}

File Categories:
"""

        for category, count in sorted(results.get('files_by_category', {}).items(),
                                    key=lambda x: x[1], reverse=True)[:5]:
            summary += f"  - {category.replace('_', ' ').title()}: {count:,} files\n"

        summary += f"\nTop Recommendations:\n"
        for i, rec in enumerate(results.get('recommendations', [])[:3], 1):
            summary += f"{i}. {rec['title']} (Priority: {rec['priority']})\n"
            summary += f"   Time savings: {rec.get('estimated_time_savings_hours_per_week', 0)} hrs/week\n"

        return summary


def scan_filesystem(path: Optional[str] = None) -> FileAnalyzer:
    """
    Convenience function to scan a file system path.

    Args:
        path: Path to scan (default: ~/Documents)

    Returns:
        FileAnalyzer instance with analysis results
    """
    analyzer = FileAnalyzer(path)
    results = analyzer.scan_filesystem()
    return analyzer


if __name__ == "__main__":
    import sys

    # Test mode
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("File System Analyzer Test")
        print("="*50)

        # Test on current directory or specified path
        test_path = sys.argv[2] if len(sys.argv) > 2 else "./"

        print(f"Testing on path: {test_path}")
        print("(Limited to 1000 files for quick test)")
        print()

        analyzer = FileAnalyzer(test_path)
        results = analyzer.scan_filesystem(max_files=1000)

        print(analyzer.get_summary())

        if results.get('scan_complete'):
            print(f"\n✅ Scan completed successfully")
            print(f"   Found {results.get('total_files', 0)} files")

            if results.get('duplicates'):
                print(f"   Found {len(results['duplicates'])} duplicate groups")

            if results.get('organization_issues'):
                print(f"   Identified {len(results['organization_issues'])} organization issues")
        else:
            print(f"\n❌ Scan failed: {results.get('error', 'Unknown error')}")

    else:
        print("Usage:")
        print("  python fs_analyzer.py test              # Test on current directory")
        print("  python fs_analyzer.py test /path/to/dir # Test on specific path")
