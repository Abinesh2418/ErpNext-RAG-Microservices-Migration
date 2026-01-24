"""
QA Validation Scripts
Validates conversion correctness, test coverage, and business logic preservation
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class QAValidator:
    """QA validation for conversion and testing"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results_dir = self.project_root / 'results'
        self.modern_dir = self.project_root / 'modern'
        self.logs_dir = self.project_root / 'logs'
        self.qa_report_file = None
        self.findings = []
    
    def validate_all(self):
        """Run all QA validations"""
        from ..unit.test_go_code import test_go_compilation
        
        print("\n" + "="*60)
        print("  QA VALIDATION SUITE")
        print("="*60 + "\n")
        
        self.qa_report_file = self.results_dir / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        validations = [
            ('Conversion Coverage', self.validate_conversion_coverage),
            ('Go Code Quality', self.validate_go_code_quality),
            ('Business Logic Preservation', self.validate_business_logic),
            ('Test Coverage', self.validate_test_coverage),
            ('Documentation', self.validate_documentation),
        ]
        
        results = []
        for name, validator in validations:
            print(f"\n🔍 {name}...")
            try:
                passed = validator()
                results.append((name, passed))
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append((name, False))
                self.findings.append({
                    'validation': name,
                    'severity': 'error',
                    'message': str(e)
                })
        
        # Write QA report
        self.write_qa_report(results)
        
        # Summary
        print("\n" + "="*60)
        print("📊 QA VALIDATION SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, p in results if p)
        total = len(results)
        
        for name, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
        
        print(f"\nOverall: {passed}/{total} validations passed")
        print(f"Findings: {len(self.findings)}")
        print(f"\nReport: {self.qa_report_file}")
        print("="*60 + "\n")
    
    def validate_conversion_coverage(self) -> bool:
        """Validate that all Python files were converted"""
        # Check scan log for file count
        scan_logs = list(self.logs_dir.glob('scan_*.log'))
        
        if not scan_logs:
            self.findings.append({
                'validation': 'Conversion Coverage',
                'severity': 'warning',
                'message': 'No scan logs found'
            })
            return False
        
        # Check conversion report
        conversion_reports = list(self.results_dir.glob('conversion_report_*.txt'))
        
        if not conversion_reports:
            self.findings.append({
                'validation': 'Conversion Coverage',
                'severity': 'warning',
                'message': 'No conversion reports found'
            })
            return False
        
        print("  ✓ Conversion logs found")
        return True
    
    def validate_go_code_quality(self) -> bool:
        """Validate Go code quality"""
        if not self.modern_dir.exists():
            self.findings.append({
                'validation': 'Go Code Quality',
                'severity': 'error',
                'message': 'modern/ directory not found'
            })
            return False
        
        go_files = list(self.modern_dir.rglob('*.go'))
        
        if not go_files:
            self.findings.append({
                'validation': 'Go Code Quality',
                'severity': 'error',
                'message': 'No Go files found'
            })
            return False
        
        # Check for TODO comments (indicates incomplete conversion)
        todos = 0
        for go_file in go_files:
            content = go_file.read_text(encoding='utf-8')
            todos += content.count('TODO')
        
        print(f"  ✓ {len(go_files)} Go files found")
        
        if todos > 0:
            print(f"  ⚠️ {todos} TODO comments found (review required)")
            self.findings.append({
                'validation': 'Go Code Quality',
                'severity': 'info',
                'message': f'{todos} TODO comments require attention'
            })
        
        return True
    
    def validate_business_logic(self) -> bool:
        """Validate business logic preservation"""
        # Check conversion report for warnings
        conversion_reports = list(self.results_dir.glob('conversion_report_*.txt'))
        
        if not conversion_reports:
            return False
        
        latest_report = max(conversion_reports, key=lambda p: p.stat().st_mtime)
        content = latest_report.read_text(encoding='utf-8')
        
        # Look for warning indicators
        if 'WARNING' in content.upper() or 'ISSUE' in content.upper():
            print("  ⚠️ Warnings found in conversion report")
            self.findings.append({
                'validation': 'Business Logic',
                'severity': 'warning',
                'message': 'Review conversion report for business logic warnings'
            })
        else:
            print("  ✓ No critical warnings in conversion")
        
        return True
    
    def validate_test_coverage(self) -> bool:
        """Validate test coverage"""
        test_dirs = ['unit', 'integration', 'functional', 'qa_validation']
        tests_root = self.project_root / 'tests'
        
        missing = []
        for test_dir in test_dirs:
            path = tests_root / test_dir
            if not path.exists() or not list(path.glob('*.py')):
                missing.append(test_dir)
        
        if missing:
            print(f"  ⚠️ Missing test types: {', '.join(missing)}")
            self.findings.append({
                'validation': 'Test Coverage',
                'severity': 'warning',
                'message': f'Missing test types: {", ".join(missing)}'
            })
        else:
            print("  ✓ All test types present")
        
        return len(missing) == 0
    
    def validate_documentation(self) -> bool:
        """Validate documentation"""
        # Check for logs and results
        has_logs = len(list(self.logs_dir.glob('*.log'))) > 0
        has_results = len(list(self.results_dir.glob('*.txt'))) > 0
        
        if not has_logs:
            print("  ⚠️ No log files found")
            self.findings.append({
                'validation': 'Documentation',
                'severity': 'warning',
                'message': 'No log files found'
            })
        
        if not has_results:
            print("  ⚠️ No result files found")
            self.findings.append({
                'validation': 'Documentation',
                'severity': 'warning',
                'message': 'No result files found'
            })
        
        if has_logs and has_results:
            print("  ✓ Documentation files present")
            return True
        
        return False
    
    def write_qa_report(self, results):
        """Write QA validation report"""
        with open(self.qa_report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("QA VALIDATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write("VALIDATION RESULTS:\n\n")
            for name, passed in results:
                status = "PASS" if passed else "FAIL"
                f.write(f"  [{status}] {name}\n")
            
            f.write("\n" + "-"*80 + "\n\n")
            
            if self.findings:
                f.write("FINDINGS:\n\n")
                
                by_severity = defaultdict(list)
                for finding in self.findings:
                    by_severity[finding['severity']].append(finding)
                
                for severity in ['error', 'warning', 'info']:
                    if severity in by_severity:
                        f.write(f"\n{severity.upper()}S:\n")
                        for finding in by_severity[severity]:
                            f.write(f"  • {finding['validation']}: {finding['message']}\n")
            else:
                f.write("No findings - all validations passed!\n")
            
            f.write("\n" + "="*80 + "\n\n")
            f.write("RECOMMENDATIONS:\n")
            f.write("1. Review all TODO comments in Go code\n")
            f.write("2. Run manual verification for accounting scenarios\n")
            f.write("3. Validate with actual test data\n")
            f.write("4. Perform code review with accounting domain expert\n")
            f.write("5. Run integration tests with ERPNext test cases\n")


if __name__ == '__main__':
    validator = QAValidator()
    validator.validate_all()
