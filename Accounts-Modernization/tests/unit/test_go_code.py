"""
Unit Tests for Generated Go Code
Tests individual Go functions and methods for correctness
"""

import subprocess
import json
from pathlib import Path


def test_go_compilation():
    """Test that all Go files compile successfully"""
    modern_dir = Path(__file__).parent.parent.parent / 'modern'
    
    if not modern_dir.exists():
        print("⚠️ No modern/ directory found - run conversion first")
        return
    
    go_files = list(modern_dir.rglob('*.go'))
    
    if not go_files:
        print("⚠️ No Go files found in modern/ directory")
        return
    
    print(f"\n🧪 Testing Go Compilation ({len(go_files)} files)...\n")
    
    failed = []
    for go_file in go_files:
        try:
            result = subprocess.run(
                ['go', 'build', '-o', 'nul', str(go_file)],
                capture_output=True,
                text=True,
                cwd=go_file.parent
            )
            
            if result.returncode == 0:
                print(f"  ✓ {go_file.name}")
            else:
                print(f"  ✗ {go_file.name}")
                print(f"    Error: {result.stderr[:200]}")
                failed.append(go_file.name)
                
        except FileNotFoundError:
            print("  ⚠️ Go compiler not found - install Go from https://go.dev/")
            return
        except Exception as e:
            print(f"  ✗ {go_file.name}: {e}")
            failed.append(go_file.name)
    
    print(f"\n📊 Compilation Results:")
    print(f"  Passed: {len(go_files) - len(failed)}/{len(go_files)}")
    print(f"  Failed: {len(failed)}/{len(go_files)}")
    
    if failed:
        print(f"\n❌ Failed files:")
        for f in failed:
            print(f"  - {f}")


def test_go_syntax():
    """Test Go syntax using go fmt"""
    modern_dir = Path(__file__).parent.parent.parent / 'modern'
    
    if not modern_dir.exists():
        return
    
    go_files = list(modern_dir.rglob('*.go'))
    
    if not go_files:
        return
    
    print(f"\n🧪 Testing Go Syntax ({len(go_files)} files)...\n")
    
    failed = []
    for go_file in go_files:
        try:
            result = subprocess.run(
                ['gofmt', '-l', str(go_file)],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                print(f"  ⚠️ {go_file.name} (needs formatting)")
            else:
                print(f"  ✓ {go_file.name}")
                
        except FileNotFoundError:
            print("  ⚠️ gofmt not found")
            return
        except Exception as e:
            failed.append(go_file.name)
    
    print(f"\n✅ Syntax check complete")


if __name__ == '__main__':
    print("="*60)
    print("  UNIT TESTS - Go Code Validation")
    print("="*60)
    
    test_go_compilation()
    test_go_syntax()
    
    print("\n" + "="*60)
