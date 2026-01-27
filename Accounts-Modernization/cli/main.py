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
from backend.utils.pre_indexer import PreIndexer, DependencyScheduler
from backend.qdrant import QdrantIndex


class AccountsModernizorCLI:
    """CLI interface for Accounts-Modernization system"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('cli', self.config.get('LOG_DIR', 'logs'))
        
    def convert(self, path: str, parallel: bool = True, workers: int = 4):
        """
        Convert ERPNext Accounts module code from Python to Go
        
        Args:
            path: Path to file or folder to convert
            parallel: Enable parallel execution (default: True)
            workers: Number of parallel workers (default: 4)
        """
        self.logger.info(f"Starting conversion process for: {path}")
        mode_str = f"PARALLEL MODE ({workers} workers)" if parallel else "SEQUENTIAL MODE"
        print(f"\n{'='*60}")
        print(f"  ACCOUNTS-MODERNIZATION - Python to Go Converter")
        print(f"  {mode_str}")
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
            
            # STEP 3: Pre-index files in Qdrant (if parallel mode)
            if parallel:
                print("🔍 STEP 3: Pre-Indexing Files into Qdrant...")
                qdrant_index = QdrantIndex(self.config, self.logger)
                pre_indexer = PreIndexer(self.config, self.logger, qdrant_index)
                indexing_stats = pre_indexer.index_all_files(scan_results['files'])
                print(f"   ✓ Indexed {indexing_stats['indexed_files']} files")
                print(f"   ✓ Indexed {indexing_stats['indexed_functions']} functions")
                print(f"   ✓ Indexed {indexing_stats['indexed_classes']} classes")
                print(f"   ✓ Indexing time: {indexing_stats['elapsed_time']:.2f}s\n")
                
                # STEP 4: Build dependency levels
                print("📊 STEP 4: Building Dependency Levels...")
                scheduler = DependencyScheduler(self.logger)
                dependency_levels = scheduler.build_dependency_levels(dependency_results, scan_results['files'])
                print(f"   ✓ Created {len(dependency_levels)} dependency levels\n")
            else:
                print("ℹ️  STEP 3-4: Skipped (sequential mode)\n")
            
            # STEP 5: Prepare context for AI
            step_num = 5 if parallel else 3
            print(f"📝 STEP {step_num}: Preparing Context for AI Conversion...")
            context = dependency_analyzer.prepare_context(dependency_results)
            print(f"   ✓ Context prepared with {context['file_count']} files\n")
            
            # STEP 6: AI Conversion
            step_num += 1
            print(f"🤖 STEP {step_num}: Converting Python to Go...")
            converter = AIConverter(self.config, self.logger)
            
            if parallel:
                conversion_results = converter.convert_parallel(
                    context,
                    scan_results['files'],
                    dependency_levels,
                    num_workers=workers
                )
            else:
                conversion_results = converter.convert(context, scan_results['files'])
            
            print(f"   ✓ Generated Go code in: modern/")
            print(f"   ✓ Conversion report: {conversion_results['report_file']}\n")
            
            # STEP 7: Summary
            print("✅ CONVERSION COMPLETED!")
            print(f"\n📊 Summary:")
            print(f"   • Files processed: {scan_results['file_count']}")
            print(f"   • Go modules created: {conversion_results['modules_created']}")
            print(f"   • Warnings: {conversion_results['warnings']}")
            if parallel:
                print(f"   • Dependency levels: {conversion_results.get('dependency_levels', 0)}")
                print(f"   • Workers used: {conversion_results.get('num_workers', 0)}")
            
            # Timing information
            total_time = conversion_results.get('total_conversion_time', 0)
            avg_time = conversion_results.get('average_conversion_time', 0)
            throughput = conversion_results['modules_created'] / total_time if total_time > 0 else 0
            print(f"\n⏱️  Performance:")
            print(f"   • Total conversion time: {total_time:.2f}s")
            print(f"   • Average per file: {avg_time:.2f}s")
            print(f"   • Throughput: {throughput:.2f} files/second")
            if conversion_results.get('cache_hits', 0) > 0:
                cache_efficiency = (conversion_results['cache_hits'] / (conversion_results['cache_hits'] + conversion_results['cache_misses']) * 100)
                print(f"   • Cache efficiency: {cache_efficiency:.1f}%")
                print(f"   • Cache hits/misses: {conversion_results['cache_hits']}/{conversion_results['cache_misses']}")
            
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
    convert_parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Enable parallel conversion with worker pool (default: True)'
    )
    convert_parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers to use (default: 4)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    cli = AccountsModernizorCLI()
    
    if args.command == 'convert':
        parallel = getattr(args, 'parallel', True)
        workers = getattr(args, 'workers', 4)
        return cli.convert(args.path, parallel=parallel, workers=workers)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
