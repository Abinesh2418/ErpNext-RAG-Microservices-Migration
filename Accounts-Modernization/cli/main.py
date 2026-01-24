#!/usr/bin/env python3
"""
Accounts-Modernization CLI
Main entry point for the accounts-modernizor command
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.analyzer.scanner import AccountsScanner
from backend.analyzer.dependency_analyzer import DependencyAnalyzer
from backend.converter.ai_converter import AIConverter
from backend.utils.logger import setup_logger
from backend.utils.config import Config


class AccountsModernizorCLI:
    """CLI interface for Accounts-Modernization system"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('cli', self.config.get('LOG_DIR', 'logs'))
        
    def convert(self, path: str):
        """
        Convert ERPNext Accounts module code from Python to Go
        
        Args:
            path: Path to file or folder to convert
        """
        self.logger.info(f"Starting conversion process for: {path}")
        print(f"\n{'='*60}")
        print(f"  ACCOUNTS-MODERNIZATION - Python to Go Converter")
        print(f"{'='*60}\n")
        
        # Validate input path
        if not os.path.exists(path):
            self.logger.error(f"Path not found: {path}")
            print(f"❌ Error: Path '{path}' does not exist")
            return 1
        
        try:
            # STEP 1: Scan the accounts module
            print("📋 STEP 1: Scanning Accounts Module...")
            scanner = AccountsScanner(self.config, self.logger)
            scan_results = scanner.scan(path)
            
            if scan_results['file_count'] == 0:
                print(f"   ❌ No Python files found in: {path}")
                print(f"\n⚠️  CONVERSION ABORTED")
                print(f"\nPlease check:")
                print(f"   • The path exists and contains Python files (.py)")
                print(f"   • You have read permissions for the directory")
                print(f"   • The path is not empty\n")
                self.logger.warning(f"No Python files found in {path}")
                return 1
            
            print(f"   ✓ Found {scan_results['file_count']} Python files")
            print(f"   ✓ Scan log: {scan_results['log_file']}\n")
            
            # STEP 2: Analyze dependencies
            print("🔍 STEP 2: Analyzing Dependencies...")
            dependency_analyzer = DependencyAnalyzer(self.config, self.logger)
            dependency_results = dependency_analyzer.analyze(scan_results['files'])
            print(f"   ✓ Analyzed {dependency_results['total_dependencies']} dependencies")
            print(f"   ✓ Dependency log: {dependency_results['log_file']}\n")
            
            # STEP 3: Prepare context for AI
            print("📝 STEP 3: Preparing Context for AI Conversion...")
            context = dependency_analyzer.prepare_context(dependency_results)
            print(f"   ✓ Context prepared with {context['file_count']} files\n")
            
            # STEP 4: AI Conversion
            print("🤖 STEP 4: Converting Python to Go...")
            converter = AIConverter(self.config, self.logger)
            conversion_results = converter.convert(context, scan_results['files'])
            print(f"   ✓ Generated Go code in: modern/")
            print(f"   ✓ Conversion report: {conversion_results['report_file']}\n")
            
            # STEP 5: Summary
            print("✅ CONVERSION COMPLETED!")
            print(f"\n📊 Summary:")
            print(f"   • Files processed: {scan_results['file_count']}")
            print(f"   • Go modules created: {conversion_results['modules_created']}")
            print(f"   • Warnings: {conversion_results['warnings']}")
            print(f"\n📂 Generated Files:")
            print(f"   • Go code: modern/")
            print(f"   • Logs: logs/")
            print(f"   • Results: results/")
            print(f"\n🧪 Next Steps:")
            print(f"   1. Review conversion report: {conversion_results['report_file']}")
            print(f"   2. Run tests: pytest tests/")
            print(f"   3. Review flagged issues in the report\n")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            print(f"\n❌ Error: Conversion failed - {str(e)}")
            print(f"   Check logs/cli.log for details\n")
            return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='accounts-modernizor',
        description='Convert ERPNext Accounts module from Python to Go',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  accounts-modernizor convert accounts/party.py
  
  # Convert entire accounts folder
  accounts-modernizor convert accounts/
  
  # Convert with absolute path
  accounts-modernizor convert /path/to/erpnext/accounts/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert Python Accounts code to Go'
    )
    convert_parser.add_argument(
        'path',
        type=str,
        help='Path to file or folder to convert'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    cli = AccountsModernizorCLI()
    
    if args.command == 'convert':
        return cli.convert(args.path)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
