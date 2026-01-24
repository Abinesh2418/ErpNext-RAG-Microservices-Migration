#!/usr/bin/env python3
"""
Cleanup Script for Accounts-Modernization
Removes logs, results, and generated Go code
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


class CleanupManager:
    """Manages cleanup operations"""
    
    def __init__(self):
        """Initialize cleanup manager"""
        self.project_root = Path(__file__).parent
        self.directories = {
            'logs': self.project_root / 'logs',
            'results': self.project_root / 'results',
            'modern': self.project_root / 'modern',
        }
        
    def analyze(self):
        """Analyze what would be deleted"""
        print("\n" + "="*70)
        print("  ACCOUNTS-MODERNIZATION - CLEANUP ANALYSIS")
        print("="*70 + "\n")
        
        total_size = 0
        total_files = 0
        
        for name, dir_path in self.directories.items():
            if not dir_path.exists():
                print(f"📁 {name.upper()}/")
                print(f"   Status: Directory does not exist")
                print()
                continue
            
            files = list(dir_path.rglob('*'))
            file_count = sum(1 for f in files if f.is_file())
            dir_size = sum(f.stat().st_size for f in files if f.is_file())
            
            total_files += file_count
            total_size += dir_size
            
            print(f"📁 {name.upper()}/")
            print(f"   Location: {dir_path}")
            print(f"   Files: {file_count}")
            print(f"   Size: {self._format_size(dir_size)}")
            
            # Show recent files
            if file_count > 0:
                recent_files = sorted(
                    [f for f in files if f.is_file()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )[:5]
                
                print(f"   Recent files:")
                for f in recent_files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    size = self._format_size(f.stat().st_size)
                    print(f"      - {f.name} ({size}, {mtime.strftime('%Y-%m-%d %H:%M')})")
            
            print()
        
        print("="*70)
        print(f"  TOTAL: {total_files} files, {self._format_size(total_size)}")
        print("="*70 + "\n")
        
        return total_files, total_size
    
    def cleanup_all(self, confirm=True):
        """
        Clean all directories
        
        Args:
            confirm: Ask for confirmation before deleting
        """
        print("\n" + "="*70)
        print("  CLEANUP ALL - DELETE EVERYTHING")
        print("="*70 + "\n")
        
        if confirm:
            response = input("⚠️  This will DELETE all logs, results, and modern code. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cleanup cancelled")
                return False
        
        deleted_count = 0
        
        for name, dir_path in self.directories.items():
            if dir_path.exists():
                print(f"\n🗑️  Deleting {name.upper()}/...")
                try:
                    # Delete all contents but keep directory
                    for item in dir_path.iterdir():
                        if item.is_file():
                            item.unlink()
                            deleted_count += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            deleted_count += 1
                    
                    print(f"   ✅ Cleaned {name}/ directory")
                except Exception as e:
                    print(f"   ❌ Error cleaning {name}/: {e}")
        
        print("\n" + "="*70)
        print(f"  ✅ CLEANUP COMPLETE - {deleted_count} items deleted")
        print("="*70 + "\n")
        
        return True
    
    def cleanup_logs(self):
        """Clean only logs directory"""
        return self._cleanup_directory('logs')
    
    def cleanup_results(self):
        """Clean only results directory"""
        return self._cleanup_directory('results')
    
    def cleanup_modern(self):
        """Clean only modern directory"""
        return self._cleanup_directory('modern')
    
    def _cleanup_directory(self, dir_name):
        """Clean specific directory"""
        dir_path = self.directories.get(dir_name)
        
        if not dir_path or not dir_path.exists():
            print(f"❌ Directory {dir_name}/ does not exist")
            return False
        
        print(f"\n🗑️  Cleaning {dir_name.upper()}/...")
        
        try:
            deleted = 0
            for item in dir_path.iterdir():
                if item.is_file():
                    item.unlink()
                    deleted += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted += 1
            
            print(f"   ✅ Deleted {deleted} items from {dir_name}/")
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def cleanup_old_files(self, days=7):
        """
        Clean files older than specified days
        
        Args:
            days: Delete files older than this many days
        """
        from datetime import timedelta
        
        print(f"\n🗑️  Cleaning files older than {days} days...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for name, dir_path in self.directories.items():
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"   🗑️  Deleted: {file_path.name}")
                    except Exception as e:
                        print(f"   ❌ Failed to delete {file_path.name}: {e}")
        
        print(f"\n   ✅ Deleted {deleted_count} old files")
        return deleted_count
    
    def _format_size(self, size_bytes):
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def show_menu():
    """Show cleanup menu"""
    print("\n" + "="*70)
    print("  ACCOUNTS-MODERNIZATION - CLEANUP MENU")
    print("="*70)
    print("\n  1. Analyze (show what will be deleted)")
    print("  2. Clean ALL (logs + results + modern)")
    print("  3. Clean LOGS only")
    print("  4. Clean RESULTS only")
    print("  5. Clean MODERN only")
    print("  6. Clean OLD files (>7 days)")
    print("  7. Exit")
    print("\n" + "="*70 + "\n")


def main():
    """Main cleanup script"""
    cleanup = CleanupManager()
    
    # Check if run with arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == 'analyze' or arg == 'status':
            cleanup.analyze()
        elif arg == 'all':
            cleanup.analyze()
            cleanup.cleanup_all(confirm=True)
        elif arg == 'logs':
            cleanup.cleanup_logs()
        elif arg == 'results':
            cleanup.cleanup_results()
        elif arg == 'modern':
            cleanup.cleanup_modern()
        elif arg == 'old':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            cleanup.cleanup_old_files(days)
        elif arg == 'force':
            # Force cleanup without confirmation
            cleanup.analyze()
            cleanup.cleanup_all(confirm=False)
        else:
            print(f"❌ Unknown argument: {arg}")
            print("\nUsage:")
            print("  python cleanup.py analyze    - Show what will be deleted")
            print("  python cleanup.py all        - Clean everything")
            print("  python cleanup.py logs       - Clean logs only")
            print("  python cleanup.py results    - Clean results only")
            print("  python cleanup.py modern     - Clean modern only")
            print("  python cleanup.py old [days] - Clean files older than N days")
            print("  python cleanup.py force      - Clean all without confirmation")
        
        return
    
    # Interactive menu
    while True:
        show_menu()
        
        try:
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                cleanup.analyze()
            elif choice == '2':
                cleanup.analyze()
                cleanup.cleanup_all(confirm=True)
            elif choice == '3':
                cleanup.cleanup_logs()
            elif choice == '4':
                cleanup.cleanup_results()
            elif choice == '5':
                cleanup.cleanup_modern()
            elif choice == '6':
                days = input("Delete files older than how many days? [7]: ").strip()
                days = int(days) if days else 7
                cleanup.cleanup_old_files(days)
            elif choice == '7':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-7.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Cleanup cancelled")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
