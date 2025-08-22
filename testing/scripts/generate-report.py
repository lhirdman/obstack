#!/usr/bin/env python3
"""
Test Report Generator for ObservaStack Test Environment

Consolidates test results from various test suites into a unified report.
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def parse_junit_xml(file_path: str) -> Dict[str, Any]:
    """Parse JUnit XML test results."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Handle both 'testsuite' and 'testsuites' root elements
        if root.tag == 'testsuites':
            suites = root.findall('testsuite')
        else:
            suites = [root]
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        
        for suite in suites:
            total_tests += int(suite.get('tests', 0))
            total_failures += int(suite.get('failures', 0))
            total_errors += int(suite.get('errors', 0))
            total_skipped += int(suite.get('skipped', 0))
        
        return {
            'total_tests': total_tests,
            'failures': total_failures,
            'errors': total_errors,
            'skipped': total_skipped,
            'passed': total_tests - total_failures - total_errors - total_skipped,
            'success_rate': ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        }
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {'error': str(e)}


def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate HTML test report."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ObservaStack Test Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
            .summary { display: flex; gap: 20px; margin: 20px 0; }
            .metric { background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }
            .metric.success { background-color: #d4edda; }
            .metric.warning { background-color: #fff3cd; }
            .metric.danger { background-color: #f8d7da; }
            .test-suite { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .test-suite h3 { margin-top: 0; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ObservaStack Test Results</h1>
            <p>Generated: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="metric success">
                <h3>{total_passed}</h3>
                <p>Passed</p>
            </div>
            <div class="metric danger">
                <h3>{total_failed}</h3>
                <p>Failed</p>
            </div>
            <div class="metric warning">
                <h3>{total_skipped}</h3>
                <p>Skipped</p>
            </div>
            <div class="metric">
                <h3>{success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
        </div>
        
        {test_suites_html}
    </body>
    </html>
    """
    
    # Calculate totals
    total_passed = sum(suite.get('passed', 0) for suite in results['test_suites'].values() if 'error' not in suite)
    total_failed = sum(suite.get('failures', 0) + suite.get('errors', 0) for suite in results['test_suites'].values() if 'error' not in suite)
    total_skipped = sum(suite.get('skipped', 0) for suite in results['test_suites'].values() if 'error' not in suite)
    total_tests = total_passed + total_failed + total_skipped
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Generate test suites HTML
    test_suites_html = ""
    for suite_name, suite_data in results['test_suites'].items():
        if 'error' in suite_data:
            test_suites_html += f"""
            <div class="test-suite">
                <h3>{suite_name}</h3>
                <p style="color: red;">Error: {suite_data['error']}</p>
            </div>
            """
        else:
            test_suites_html += f"""
            <div class="test-suite">
                <h3>{suite_name}</h3>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Tests</td><td>{suite_data.get('total_tests', 0)}</td></tr>
                    <tr><td>Passed</td><td>{suite_data.get('passed', 0)}</td></tr>
                    <tr><td>Failed</td><td>{suite_data.get('failures', 0)}</td></tr>
                    <tr><td>Errors</td><td>{suite_data.get('errors', 0)}</td></tr>
                    <tr><td>Skipped</td><td>{suite_data.get('skipped', 0)}</td></tr>
                    <tr><td>Success Rate</td><td>{suite_data.get('success_rate', 0):.1f}%</td></tr>
                </table>
            </div>
            """
    
    return html_template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_passed=total_passed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        success_rate=success_rate,
        test_suites_html=test_suites_html
    )


def main():
    """Generate consolidated test report."""
    reports_dir = Path("/app/reports")
    
    # Test result files to process
    test_files = {
        "Backend Unit Tests": reports_dir / "backend-unit-results.xml",
        "Backend Integration Tests": reports_dir / "backend-integration-results.xml",
        "Frontend Unit Tests": reports_dir / "frontend-unit-results.xml",
        "E2E Tests": reports_dir / "e2e-results" / "results.xml",
        "Accessibility Tests": reports_dir / "accessibility-results" / "results.xml"
    }
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_suites": {}
    }
    
    # Process each test file
    for suite_name, file_path in test_files.items():
        if file_path.exists():
            print(f"Processing {suite_name}...")
            results["test_suites"][suite_name] = parse_junit_xml(str(file_path))
        else:
            print(f"Warning: {file_path} not found")
            results["test_suites"][suite_name] = {"error": "Results file not found"}
    
    # Generate JSON report
    json_report_path = reports_dir / "consolidated-results.json"
    with open(json_report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate HTML report
    html_report_path = reports_dir / "test-report.html"
    html_content = generate_html_report(results)
    with open(html_report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Reports generated:")
    print(f"  JSON: {json_report_path}")
    print(f"  HTML: {html_report_path}")
    
    # Print summary to console
    total_suites = len([s for s in results["test_suites"].values() if "error" not in s])
    failed_suites = len([s for s in results["test_suites"].values() if "error" in s])
    
    print(f"\nTest Summary:")
    print(f"  Test Suites Processed: {total_suites}")
    print(f"  Failed to Process: {failed_suites}")


if __name__ == "__main__":
    main()