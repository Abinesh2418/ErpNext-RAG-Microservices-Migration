#!/usr/bin/env python3
"""
Cleanup Script for Accounts-Modernization
Removes logs, results, generated Go code, and clears all caches (Redis + Qdrant)
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
        
        # Initialize cache clients
        self.redis_client = None
        self.qdrant_client = None
        self._init_cache_clients()
    
    def _init_cache_clients(self):
        """Initialize Redis and Qdrant clients"""
        # Try to initialize Redis
        try:
            import redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None
        
        # Try to initialize Qdrant
        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(host="localhost", port=6333)
        except Exception:
            self.qdrant_client = None
        
    def analyze(self):
        """Analyze what would be deleted"""
        print("\n" + "="*70)
        print("  ACCOUNTS-MODERNIZATION - CLEANUP ANALYSIS")
        print("="*70 + "\n")
        
        total_size = 0
        total_files = 0
        
        # Analyze directories
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
        
        # Analyze caches
        print("💾 CACHE STATUS")
        
        # Redis
        if self.redis_client:
            try:
                redis_keys = {
                    'conversions': len(self.redis_client.keys('conversion:*') or []),
                    'file_hashes': len(self.redis_client.keys('file_hash:*') or []),
                    'ast_cache': len(self.redis_client.keys('ast:*') or []),
                    'dependency_graph': 1 if self.redis_client.exists('dependency_graph') else 0
                }
                total_redis_keys = sum(redis_keys.values())
                
                print(f"   Redis (localhost:6379): ✅ Connected")
                print(f"   - Cached conversions: {redis_keys['conversions']}")
                print(f"   - File hashes: {redis_keys['file_hashes']}")
                print(f"   - AST cache: {redis_keys['ast_cache']}")
                print(f"   - Dependency graph: {redis_keys['dependency_graph']}")
                print(f"   - Total keys: {total_redis_keys}")
            except Exception as e:
                print(f"   Redis: ⚠️  Error - {e}")
        else:
            print(f"   Redis: ❌ Not connected")
        
        print()
        
        # Qdrant
        if self.qdrant_client:
            try:
                collections = self.qdrant_client.get_collections().collections
                collection_name = "accounts_modernization"
                collection_exists = any(c.name == collection_name for c in collections)
                
                if collection_exists:
                    info = self.qdrant_client.get_collection(collection_name)
                    point_count = info.points_count
                    print(f"   Qdrant (localhost:6333): ✅ Connected")
                    print(f"   - Collection: {collection_name}")
                    print(f"   - Indexed points: {point_count}")
                else:
                    print(f"   Qdrant (localhost:6333): ✅ Connected")
                    print(f"   - Collection: Not created yet")
            except Exception as e:
                print(f"   Qdrant: ⚠️  Error - {e}")
        else:
            print(f"   Qdrant: ❌ Not connected")
        
        print()
        print("="*70)
        print(f"  FILES: {total_files} files, {self._format_size(total_size)}")
        print("="*70 + "\n")
        
        return total_files, total_size
    
    def cleanup_all(self, confirm=True):
        """
        Clean all directories and caches
        
        Args:
            confirm: Ask for confirmation before deleting
        """
        print("\n" + "="*70)
        print("  CLEANUP ALL - DELETE EVERYTHING")
        print("="*70 + "\n")
        
        if confirm:
            response = input("⚠️  This will DELETE all logs, results, modern code, and CLEAR ALL CACHES. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cleanup cancelled")
                return False
        
        deleted_count = 0
        
        # Clean directories
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
        
        # Clear caches
        self.clear_redis_cache()
        self.clear_qdrant_cache()
        
        print("\n" + "="*70)
        print(f"  ✅ CLEANUP COMPLETE - {deleted_count} items deleted + caches cleared")
        print("="*70 + "\n")
        
        return True
    
    def clear_redis_cache(self):
        """Clear all Redis cache"""
        print(f"\n💾 Clearing Redis cache...")
        
        if not self.redis_client:
            print("   ⚠️  Redis not connected - skipping")
            return False
        
        try:
            deleted_count = 0
            
            # Clear conversion cache
            conversion_keys = self.redis_client.keys('conversion:*') or []
            if conversion_keys:
                self.redis_client.delete(*conversion_keys)
                deleted_count += len(conversion_keys)
                print(f"   ✅ Deleted {len(conversion_keys)} cached conversions")
            
            # Clear file hash cache
            hash_keys = self.redis_client.keys('file_hash:*') or []
            if hash_keys:
                self.redis_client.delete(*hash_keys)
                deleted_count += len(hash_keys)
                print(f"   ✅ Deleted {len(hash_keys)} file hashes")
            
            # Clear AST cache
            ast_keys = self.redis_client.keys('ast:*') or []
            if ast_keys:
                self.redis_client.delete(*ast_keys)
                deleted_count += len(ast_keys)
                print(f"   ✅ Deleted {len(ast_keys)} AST caches")
            
            # Clear dependency graph
            if self.redis_client.exists('dependency_graph'):
                self.redis_client.delete('dependency_graph')
                deleted_count += 1
                print(f"   ✅ Deleted dependency graph")
            
            if deleted_count == 0:
                print("   ℹ️  No Redis cache found")
            else:
                print(f"   ✅ Redis cleanup complete - {deleted_count} keys deleted")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Redis error: {e}")
            return False
    
    def clear_qdrant_cache(self):
        """Clear Qdrant vector database"""
        print(f"\n🔍 Clearing Qdrant vector database...")
        
        if not self.qdrant_client:
            print("   ⚠️  Qdrant not connected - skipping")
            return False
        
        try:
            from qdrant_client.http import models
            
            collection_name = "accounts_modernization"
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)
            
            if collection_exists:
                info = self.qdrant_client.get_collection(collection_name)
                point_count = info.points_count
                
                if point_count > 0:
                    # Delete collection
                    self.qdrant_client.delete_collection(collection_name)
                    print(f"   ✅ Deleted {point_count} indexed points")
                    
                    # Recreate empty collection
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=768,  # nomic-embed-text:v1.5 dimension
                            distance=models.Distance.COSINE
                        )
                    )
                    print("   ✅ Empty collection recreated")
                else:
                    print("   ℹ️  Collection already empty")
            else:
                print("   ℹ️  Collection doesn't exist (will be created on first use)")
            
            print("   ✅ Qdrant cleanup complete")
            return True
            
        except Exception as e:
            print(f"   ❌ Qdrant error: {e}")
            return False
    
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
    print("  2. Clean ALL (logs + results + modern + caches)")
    print("  3. Clean LOGS only")
    print("  4. Clean RESULTS only")
    print("  5. Clean MODERN only")
    print("  6. Clean REDIS cache only")
    print("  7. Clean QDRANT cache only")
    print("  8. Clean OLD files (>7 days)")
    print("  9. Exit")
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
        elif arg == 'redis':
            cleanup.clear_redis_cache()
        elif arg == 'qdrant':
            cleanup.clear_qdrant_cache()
        elif arg == 'cache':
            cleanup.clear_redis_cache()
            cleanup.clear_qdrant_cache()
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
            print("  python cleanup.py all        - Clean everything (files + caches)")
            print("  python cleanup.py logs       - Clean logs only")
            print("  python cleanup.py results    - Clean results only")
            print("  python cleanup.py modern     - Clean modern only")
            print("  python cleanup.py redis      - Clear Redis cache only")
            print("  python cleanup.py qdrant     - Clear Qdrant cache only")
            print("  python cleanup.py cache      - Clear both Redis and Qdrant")
            print("  python cleanup.py old [days] - Clean files older than N days")
            print("  python cleanup.py force      - Clean all without confirmation")
        
        return
    
    # Interactive menu
    while True:
        show_menu()
        
        try:
            choice = input("Select option (1-9): ").strip()
            
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
                cleanup.clear_redis_cache()
            elif choice == '7':
                cleanup.clear_qdrant_cache()
            elif choice == '8':
                days = input("Delete files older than how many days? [7]: ").strip()
                days = int(days) if days else 7
                cleanup.cleanup_old_files(days)
            elif choice == '9':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-9.")
            
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
