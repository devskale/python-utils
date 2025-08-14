#!/usr/bin/env python3
"""
Comprehensive test script for OFS (Opinionated Filesystem) CLI commands.

This script tests all available OFS commands with various parameters and scenarios
to ensure functionality and catch potential issues.

Usage:
    python test_ofs_commands.py

Requirements:
    - OFS package installed
    - Test data directory (.dir) with sample projects
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time


class OFSTestRunner:
    """Test runner for OFS CLI commands."""
    
    def __init__(self, test_dir: str = ".dir"):
        """Initialize test runner with test directory.
        
        Args:
            test_dir: Directory containing test OFS projects
        """
        self.test_dir = Path(test_dir)
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        
    def _get_result_description(self, cmd: List[str], result: Dict[str, Any]) -> str:
        """Get a descriptive result message for a command.
        
        Args:
            cmd: Command list that was executed
            result: Command execution result
            
        Returns:
            Description of what the command checked
        """
        cmd_str = ' '.join(cmd)
        
        # Basic commands
        if cmd_str == 'ofs --help':
            return "Help documentation displayed successfully"
        elif cmd_str == 'ofs --version':
            return "Version information retrieved"
        elif cmd_str == 'ofs root':
            return "OFS root directory path verified"
        
        # List commands
        elif cmd_str == 'ofs list':
            return "Directory listing generated successfully"
        elif cmd_str == 'ofs list-projects':
            return "Project list retrieved and parsed"
        elif cmd_str.startswith('ofs list-bidders '):
            project = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Bidder list for project '{project}' retrieved"
        elif cmd_str.startswith('ofs find-bidder '):
            project = cmd[2] if len(cmd) > 2 else 'unknown'
            bidder = cmd[3] if len(cmd) > 3 else 'unknown'
            return f"Bidder '{bidder}' found in project '{project}'"
        
        # Document commands
        elif cmd_str.startswith('ofs list-docs '):
            target = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Document list for '{target}' retrieved"
        elif cmd_str.startswith('ofs read-doc '):
            doc = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Document '{doc}' content accessed"
        
        # Tree commands
        elif cmd_str == 'ofs tree':
            return "Directory tree structure generated"
        elif cmd_str == 'ofs tree --directories':
            return "Directory-only tree structure generated"
        
        # Kriterien commands
        elif cmd_str.startswith('ofs kriterien ') and 'pop' in cmd_str:
            project = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Criteria population data for project '{project}' extracted"
        elif cmd_str.startswith('ofs kriterien ') and 'tree' in cmd_str:
            project = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Criteria tree structure for project '{project}' generated"
        elif cmd_str.startswith('ofs kriterien ') and 'tag' in cmd_str:
            project = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"Criteria tags for project '{project}' processed"
        
        # Index commands
        elif cmd_str.startswith('ofs index create '):
            directory = cmd[3] if len(cmd) > 3 else 'unknown'
            return f"Search index created for directory '{directory}'"
        elif cmd_str.startswith('ofs index update '):
            directory = cmd[3] if len(cmd) > 3 else 'unknown'
            return f"Search index updated for directory '{directory}'"
        elif cmd_str.startswith('ofs index stats '):
            directory = cmd[3] if len(cmd) > 3 else 'unknown'
            return f"Index statistics retrieved for directory '{directory}'"
        elif cmd_str.startswith('ofs index un '):
            directory = cmd[3] if len(cmd) > 3 else 'unknown'
            json_flag = '--json' in cmd_str
            format_type = 'JSON' if json_flag else 'text'
            return f"Index content listed for directory '{directory}' in {format_type} format"
        elif cmd_str.startswith('ofs index clear '):
            directory = cmd[3] if len(cmd) > 3 else 'unknown'
            return f"Search index cleared for directory '{directory}'"
        
        # Get-path commands
        elif cmd_str.startswith('ofs get-path '):
            target = cmd[2] if len(cmd) > 2 else 'unknown'
            return f"File system path for '{target}' resolved"
        
        # Error cases (expected failures)
        elif not result.get('expected_success', True):
            return "Expected error condition handled correctly"
        
        # Default fallback
        return "Command executed successfully"
    
    def run_command(self, cmd: List[str], expect_success: bool = True) -> Dict[str, Any]:
        """Run an OFS command and capture results.
        
        Args:
            cmd: Command list to execute
            expect_success: Whether command should succeed
            
        Returns:
            Dictionary with command results
        """
        try:
            # Set environment to handle encoding issues on Windows
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
                encoding='utf-8',
                errors='replace'  # Replace problematic characters instead of failing
            )
            
            success = (result.returncode == 0) == expect_success
            
            test_result = {
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'expected_success': expect_success,
                'actual_success': result.returncode == 0,
                'test_passed': success
            }
            
            if success:
                self.passed += 1
                result_description = self._get_result_description(cmd, test_result)
                print(f"✅ PASS: {' '.join(cmd)} Result: {result_description}")
            else:
                self.failed += 1
                print(f"❌ FAIL: {' '.join(cmd)}")
                print(f"   Expected success: {expect_success}, Got: {result.returncode == 0}")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
            
            self.results.append(test_result)
            return test_result
            
        except subprocess.TimeoutExpired:
            self.failed += 1
            print(f"❌ TIMEOUT: {' '.join(cmd)}")
            test_result = {
                'command': ' '.join(cmd),
                'error': 'timeout',
                'test_passed': False,
                'expected_success': expect_success,
                'actual_success': False
            }
            self.results.append(test_result)
            return test_result
        except Exception as e:
            self.failed += 1
            print(f"❌ ERROR: {' '.join(cmd)} - {str(e)}")
            test_result = {
                'command': ' '.join(cmd),
                'error': str(e),
                'test_passed': False,
                'expected_success': expect_success,
                'actual_success': False
            }
            self.results.append(test_result)
            return test_result
    
    def test_basic_commands(self):
        """Test basic OFS commands without parameters."""
        print("\n=== Testing Basic Commands ===")
        
        # Test help and version
        self.run_command(['ofs', '--help'])
        self.run_command(['ofs', '--version'])
        
        # Test root command
        self.run_command(['ofs', 'root'])
        
    def test_list_commands(self):
        """Test various list commands."""
        print("\n=== Testing List Commands ===")
        
        # Basic list commands (no directory arguments - they use OFS root)
        self.run_command(['ofs', 'list'])
        self.run_command(['ofs', 'list-projects'])
        
        # Get first project for further testing
        result = self.run_command(['ofs', 'list-projects'])
        if result.get('actual_success') and result.get('stdout'):
            try:
                # Try to parse as JSON first
                data = json.loads(result['stdout'])
                if 'projects' in data and data['projects']:
                    first_project = data['projects'][0]
                    print(f"Using project '{first_project}' for bidder tests")
                    
                    # Test bidder commands with first project
                    self.run_command(['ofs', 'list-bidders', first_project])
                    
                    # Test find-bidder (this might fail if no bidders exist)
                    bidder_result = self.run_command(['ofs', 'list-bidders', first_project])
                    if bidder_result.get('actual_success') and bidder_result.get('stdout'):
                        try:
                            bidder_data = json.loads(bidder_result['stdout'])
                            if 'bidders' in bidder_data and bidder_data['bidders']:
                                first_bidder = bidder_data['bidders'][0]
                                self.run_command(['ofs', 'find-bidder', first_project, first_bidder])
                        except json.JSONDecodeError:
                            # Fallback to text parsing
                            bidders = [line.strip() for line in bidder_result['stdout'].strip().split('\n') if line.strip()]
                            if bidders:
                                first_bidder = bidders[0]
                                self.run_command(['ofs', 'find-bidder', first_project, first_bidder])
            except json.JSONDecodeError:
                # Fallback to text parsing
                projects = [line.strip() for line in result['stdout'].strip().split('\n') if line.strip()]
                if projects:
                    first_project = projects[0]
                    print(f"Using project '{first_project}' for bidder tests")
                    
                    # Test bidder commands with first project
                    self.run_command(['ofs', 'list-bidders', first_project])
                    
                    # Test find-bidder (this might fail if no bidders exist)
                    bidder_result = self.run_command(['ofs', 'list-bidders', first_project])
                    if bidder_result.get('actual_success') and bidder_result.get('stdout'):
                        bidders = [line.strip() for line in bidder_result['stdout'].strip().split('\n') if line.strip()]
                        if bidders:
                            first_bidder = bidders[0]
                            self.run_command(['ofs', 'find-bidder', first_project, first_bidder])
    
    def test_docs_commands(self):
        """Test document-related commands."""
        print("\n=== Testing Document Commands ===")
        
        # Test list-docs with a project name (requires project@bidder format)
        result = self.run_command(['ofs', 'list-projects'])
        if result.get('actual_success') and result.get('stdout'):
            try:
                # Try to parse as JSON first
                data = json.loads(result['stdout'])
                if 'projects' in data and data['projects']:
                    first_project = data['projects'][0]
                    # Test list-docs with project name
                    self.run_command(['ofs', 'list-docs', first_project])
                    
                    # Test with project@bidder format if bidders exist
                    bidder_result = self.run_command(['ofs', 'list-bidders', first_project])
                    if bidder_result.get('actual_success') and bidder_result.get('stdout'):
                        try:
                            bidder_data = json.loads(bidder_result['stdout'])
                            if 'bidders' in bidder_data and bidder_data['bidders']:
                                first_bidder = bidder_data['bidders'][0]
                                self.run_command(['ofs', 'list-docs', f'{first_project}@{first_bidder}'])
                        except json.JSONDecodeError:
                            pass
            except json.JSONDecodeError:
                # Fallback to text parsing
                projects = [line.strip() for line in result['stdout'].strip().split('\n') if line.strip()]
                if projects:
                    first_project = projects[0]
                    self.run_command(['ofs', 'list-docs', first_project])
        
        # Test read-doc (this will likely fail without specific document identifier)
        self.run_command(['ofs', 'read-doc', 'NonExistent@Project@Document.pdf'], expect_success=False)
    
    def test_tree_command(self):
        """Test tree structure commands."""
        print("\n=== Testing Tree Commands ===")
        
        # Basic tree command
        self.run_command(['ofs', 'tree'])
        
        # Test with directories only flag
        self.run_command(['ofs', 'tree', '--directories'])
    
    def test_kriterien_command(self):
        """Test criteria analysis commands."""
        print("\n=== Testing Kriterien Commands ===")
        
        # Get projects for kriterien testing
        result = self.run_command(['ofs', 'list-projects'])
        if result.get('actual_success') and result.get('stdout'):
            try:
                # Try to parse as JSON first
                data = json.loads(result['stdout'])
                if 'projects' in data and data['projects']:
                    first_project = data['projects'][0]
                    # Test kriterien subcommands
                    self.run_command(['ofs', 'kriterien', first_project, 'pop'])
                    self.run_command(['ofs', 'kriterien', first_project, 'tree'])
                    self.run_command(['ofs', 'kriterien', first_project, 'tag'])
            except json.JSONDecodeError:
                # Fallback to text parsing
                projects = [line.strip() for line in result['stdout'].strip().split('\n') if line.strip()]
                if projects:
                    first_project = projects[0]
                    # Test kriterien subcommands
                    self.run_command(['ofs', 'kriterien', first_project, 'pop'])
                    self.run_command(['ofs', 'kriterien', first_project, 'tree'])
                    self.run_command(['ofs', 'kriterien', first_project, 'tag'])
    
    def test_index_commands(self):
        """Test index management commands."""
        print("\n=== Testing Index Commands ===")
        
        if not self.test_dir.exists():
            print("Skipping index tests - test directory not found")
            return
            
        # Test various index commands
        self.run_command(['ofs', 'index', 'create', str(self.test_dir)])
        self.run_command(['ofs', 'index', 'update', str(self.test_dir)])
        self.run_command(['ofs', 'index', 'stats', str(self.test_dir)])  # 'stats' instead of 'list'
        self.run_command(['ofs', 'index', 'un', str(self.test_dir)])
        self.run_command(['ofs', 'index', 'un', str(self.test_dir), '--json'])
        self.run_command(['ofs', 'index', 'clear', str(self.test_dir)])
    
    def test_get_path_command(self):
        """Test get-path commands."""
        print("\n=== Testing Get-Path Commands ===")
        
        # Get projects for path testing
        result = self.run_command(['ofs', 'list-projects'])
        if result.get('actual_success') and result.get('stdout'):
            try:
                # Try to parse as JSON first
                data = json.loads(result['stdout'])
                if 'projects' in data and data['projects']:
                    first_project = data['projects'][0]
                    self.run_command(['ofs', 'get-path', first_project])
                    
                    # Test with bidder if available
                    bidder_result = self.run_command(['ofs', 'list-bidders', first_project])
                    if bidder_result.get('actual_success') and bidder_result.get('stdout'):
                        try:
                            bidder_data = json.loads(bidder_result['stdout'])
                            if 'bidders' in bidder_data and bidder_data['bidders']:
                                first_bidder = bidder_data['bidders'][0]
                                self.run_command(['ofs', 'get-path', first_bidder])
                        except json.JSONDecodeError:
                            # Fallback to text parsing
                            bidders = [line.strip() for line in bidder_result['stdout'].strip().split('\n') if line.strip()]
                            if bidders:
                                first_bidder = bidders[0]
                                self.run_command(['ofs', 'get-path', first_bidder])
            except json.JSONDecodeError:
                # Fallback to text parsing
                projects = [line.strip() for line in result['stdout'].strip().split('\n') if line.strip()]
                if projects:
                    first_project = projects[0]
                    self.run_command(['ofs', 'get-path', first_project])
                    
                    # Test with bidder if available
                    bidder_result = self.run_command(['ofs', 'list-bidders', first_project])
                    if bidder_result.get('actual_success') and bidder_result.get('stdout'):
                        bidders = [line.strip() for line in bidder_result['stdout'].strip().split('\n') if line.strip()]
                        if bidders:
                            first_bidder = bidders[0]
                            self.run_command(['ofs', 'get-path', first_bidder])
    
    def test_error_cases(self):
        """Test various error conditions."""
        print("\n=== Testing Error Cases ===")
        
        # Test with invalid project names (may return empty list instead of error)
        self.run_command(['ofs', 'list-bidders', 'NonExistentProject'])
        
        # Test invalid commands (should fail)
        self.run_command(['ofs', 'invalid-command'], expect_success=False)
        
        # Test missing required arguments
        self.run_command(['ofs', 'list-bidders'], expect_success=False)
        self.run_command(['ofs', 'get-path'], expect_success=False)
        
        # Test invalid kriterien subcommands
        self.run_command(['ofs', 'kriterien'], expect_success=False)
        self.run_command(['ofs', 'kriterien', 'TestProject', 'invalid_action'], expect_success=False)
        
        # Test invalid index subcommands
        self.run_command(['ofs', 'index'], expect_success=False)
        self.run_command(['ofs', 'index', 'invalid'], expect_success=False)
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting OFS CLI Test Suite")
        print(f"Test directory: {self.test_dir.absolute()}")
        print(f"Test directory exists: {self.test_dir.exists()}")
        
        start_time = time.time()
        
        # Run test suites
        self.test_basic_commands()
        self.test_list_commands()
        self.test_docs_commands()
        self.test_tree_command()
        self.test_kriterien_command()
        self.test_index_commands()
        self.test_get_path_command()
        self.test_error_cases()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.get('test_passed', False):
                    print(f"  - {result['command']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
                    elif result.get('stderr'):
                        print(f"    Stderr: {result['stderr'].strip()}")
        
        return self.failed == 0
    
    def save_results(self, filename: str = "ofs_test_results.json"):
        """Save test results to JSON file.
        
        Args:
            filename: Output filename for results
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': self.passed + self.failed,
                    'passed': self.passed,
                    'failed': self.failed
                },
                'results': self.results
            }, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


def main():
    """Main test execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test OFS CLI commands')
    parser.add_argument('--test-dir', default='.dir', help='Test directory path')
    parser.add_argument('--save-results', action='store_true', help='Save results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create and run tests
    runner = OFSTestRunner(args.test_dir)
    success = runner.run_all_tests()
    
    if args.save_results:
        runner.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()