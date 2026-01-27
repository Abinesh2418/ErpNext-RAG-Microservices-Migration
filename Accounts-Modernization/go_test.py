import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json


class ConversionTester:
    """Tests the entire conversion pipeline"""
    
    def __init__(self):
        """Initialize tester"""
        self.project_root = Path(__file__).parent
        self.modern_dir = self.project_root / 'modern'
        self.results_dir = self.project_root / 'results'
        self.test_results = []
        
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...\n")
        
        all_ok = True
        
        # Check Python
        print(f"✅ Python: {sys.version.split()[0]}")
        
        # Check Go
        try:
            result = subprocess.run(['go', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Go: {result.stdout.strip()}")
            else:
                print("❌ Go is not installed")
                all_ok = False
        except FileNotFoundError:
            print("❌ Go is not installed - Download from: https://golang.org/dl/")
            all_ok = False
        
        # Check if conversion has been run
        if not self.modern_dir.exists():
            print("⚠️  modern/ directory not found")
            print("   Run conversion first: python cli/main.py convert <path>")
            all_ok = False
        else:
            go_files = list(self.modern_dir.rglob('*.go'))
            if not go_files:
                print("⚠️  No converted Go files found in modern/ directory")
                print("   Run conversion first: python cli/main.py convert <path>")
                all_ok = False
            else:
                print(f"✅ Found {len(go_files)} Go files in modern/ directory")
        
        return all_ok
    
    def test_groq_connection(self):
        """Test Groq API connection"""
        print("\n" + "="*70)
        print("  TESTING GROQ API CONNECTION")
        print("="*70 + "\n")
        
        try:
            import requests
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            api_key = os.getenv('GROQ_API_KEY')
            model = os.getenv('GROQ_MODEL')
            
            if not api_key:
                print("❌ GROQ_API_KEY not found in .env file")
                return False
            
            print(f"🔑 API Key: {api_key[:20]}...")
            print(f"🤖 Model: {model}")
            
            # Test API connection
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Groq API connection successful\n")
                return True
            else:
                print(f"❌ Groq API error: {response.status_code}\n")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}\n")
            return False
    
    def validate_go_syntax(self):
        """Validate Go syntax for all generated files"""
        print("\n" + "="*70)
        print("  VALIDATING GO SYNTAX")
        print("="*70 + "\n")
        
        go_files = list(self.modern_dir.rglob('*.go'))
        
        if not go_files:
            print("❌ No Go files found to validate")
            return False
        
        print(f"📝 Validating {len(go_files)} Go files...\n")
        
        all_valid = True
        for go_file in go_files:
            # Run gofmt to check syntax
            result = subprocess.run(
                ['gofmt', '-e', str(go_file)],
                capture_output=True,
                text=True
            )
            
            if result.stderr:
                print(f"❌ {go_file.name}: Syntax errors")
                print(f"   {result.stderr}")
                all_valid = False
            else:
                print(f"✅ {go_file.name}: Valid syntax")
        
        if all_valid:
            print("\n✅ All files have valid Go syntax\n")
        else:
            print("\n❌ Some files have syntax errors\n")
        
        return all_valid
    
    def test_go_compilation(self):
        """Test if Go code compiles"""
        print("\n" + "="*70)
        print("  TESTING GO COMPILATION")
        print("="*70 + "\n")
        
        # Initialize Go module if not exists
        go_mod = self.modern_dir / 'go.mod'
        if not go_mod.exists():
            print("📦 Initializing Go module...\n")
            result = subprocess.run(
                ['go', 'mod', 'init', 'accounts-modern'],
                cwd=self.modern_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Go module initialized\n")
            else:
                print(f"❌ Failed to initialize Go module: {result.stderr}\n")
                return False
        
        # Run go mod tidy
        print("📦 Tidying dependencies...\n")
        subprocess.run(['go', 'mod', 'tidy'], cwd=self.modern_dir, capture_output=True)
        
        # Try to build
        print("🔨 Building Go code...\n")
        result = subprocess.run(
            ['go', 'build', './...'],
            cwd=self.modern_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Go code compiles successfully\n")
            return True
        else:
            print("❌ Compilation errors:")
            print(result.stderr)
            print()
            return False
    
    def run_conversion_test(self, test_file):
        """Run a conversion test on a sample Python file"""
        print("\n" + "="*70)
        print("  TESTING CONVERSION PIPELINE")
        print("="*70 + "\n")
        
        if not test_file or not Path(test_file).exists():
            print("⚠️  No test file provided or file doesn't exist")
            return False
        
        print(f"📄 Testing conversion of: {test_file}\n")
        
        # Run conversion
        result = subprocess.run(
            [sys.executable, 'cli/main.py', 'convert', test_file],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Conversion completed successfully\n")
            return True
        else:
            print("❌ Conversion failed:")
            print(result.stderr)
            print()
            return False
    
    def analyze_conversion_results(self):
        """Analyze conversion results from results directory"""
        print("\n" + "="*70)
        print("  ANALYZING CONVERSION RESULTS")
        print("="*70 + "\n")
        
        if not self.results_dir.exists():
            print("⚠️  No results directory found")
            return
        
        # Find latest conversion report
        reports = sorted(self.results_dir.glob('conversion_report_*.txt'), reverse=True)
        
        if not reports:
            print("⚠️  No conversion reports found")
            return
        
        latest_report = reports[0]
        print(f"📊 Latest report: {latest_report.name}\n")
        
        with open(latest_report, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("  TEST SUMMARY")
        print("="*70 + "\n")
        
        passed = sum(1 for t in self.test_results if t['passed'])
        total = len(self.test_results)
        
        for test in self.test_results:
            status = "✅ PASSED" if test['passed'] else "❌ FAILED"
            print(f"{status}: {test['name']}")
        
        print("\n" + "="*70)
        if passed == total:
            print(f"  ✅ ALL {total} TESTS PASSED!")
        else:
            print(f"  ⚠️  {passed}/{total} tests passed ({total - passed} failed)")
        print("="*70 + "\n")


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("  ACCOUNTS-MODERNIZATION TESTING SUITE")
    print("  Python → Go Conversion Validation")
    print("="*70 + "\n")
    
    tester = ConversionTester()
    
    # Check prerequisites
    if not tester.check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing components.\n")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'api':
            # Test Groq API connection
            result = tester.test_groq_connection()
            tester.test_results.append({'name': 'Groq API Connection', 'passed': result})
            
        elif test_type == 'syntax':
            # Validate Go syntax
            result = tester.validate_go_syntax()
            tester.test_results.append({'name': 'Go Syntax Validation', 'passed': result})
            
        elif test_type == 'compile':
            # Test Go compilation
            result = tester.test_go_compilation()
            tester.test_results.append({'name': 'Go Compilation', 'passed': result})
            
        elif test_type == 'convert':
            # Test conversion with provided file
            test_file = sys.argv[2] if len(sys.argv) > 2 else None
            result = tester.run_conversion_test(test_file)
            tester.test_results.append({'name': 'Conversion Pipeline', 'passed': result})
            
        elif test_type == 'results':
            # Analyze conversion results
            tester.analyze_conversion_results()
            
        elif test_type == 'all':
            # Run all tests
            result = tester.test_groq_connection()
            tester.test_results.append({'name': 'Groq API Connection', 'passed': result})
            
            result = tester.validate_go_syntax()
            tester.test_results.append({'name': 'Go Syntax Validation', 'passed': result})
            
            result = tester.test_go_compilation()
            tester.test_results.append({'name': 'Go Compilation', 'passed': result})
            
            tester.analyze_conversion_results()
            
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("\nUsage:")
            print("  python go_test.py api              - Test Groq API connection")
            print("  python go_test.py syntax           - Validate Go syntax")
            print("  python go_test.py compile          - Test Go compilation")
            print("  python go_test.py convert <file>   - Test conversion pipeline")
            print("  python go_test.py results          - Analyze conversion results")
            print("  python go_test.py all              - Run all tests")
            sys.exit(1)
    else:
        # Run default tests
        print("Running default test suite...\n")
        
        result = tester.test_groq_connection()
        tester.test_results.append({'name': 'Groq API Connection', 'passed': result})
        
        result = tester.validate_go_syntax()
        tester.test_results.append({'name': 'Go Syntax Validation', 'passed': result})
        
        result = tester.test_go_compilation()
        tester.test_results.append({'name': 'Go Compilation', 'passed': result})
    
    # Print summary
    if tester.test_results:
        tester.print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
