#!/usr/bin/env python3
"""
Master Load Test Runner
Runs all load tests and generates comprehensive report
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

class LoadTestRunner:
    def __init__(self):
        self.test_dir = Path('/Users/roy/Documents/Projects/citations/load_tests')
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_environment': {
                'backend_url': 'http://localhost:8001',
                'working_directory': str(Path.cwd())
            },
            'test_results': {},
            'overall_success': False,
            'summary': {}
        }

    def check_prerequisites(self):
        """Check if backend is accessible and required files exist"""
        print('🔍 Checking prerequisites...')

        # Check backend accessibility
        try:
            import requests
            response = requests.get('http://localhost:8001/docs', timeout=5)
            if response.status_code == 200:
                print('✅ Backend is accessible')
                return True
            else:
                print(f'❌ Backend returned status {response.status_code}')
                return False
        except Exception as e:
            print(f'❌ Backend not accessible: {e}')
            return False

    def run_test_1_concurrent_submissions(self):
        """Run Test 1: High Volume Concurrent Submissions"""
        print('\n' + '='*60)
        print('🧪 TEST 1: High Volume Concurrent Submissions')
        print('='*60)

        test_script = self.test_dir / 'test_concurrent_submissions.py'

        if not test_script.exists():
            print(f'❌ Test script not found: {test_script}')
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0

            self.results['test_results']['test_1_concurrent'] = {
                'name': 'High Volume Concurrent Submissions',
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': None  # Will be parsed from output
            }

            print(f'{"✅ PASSED" if success else "❌ FAILED"}')
            if result.stdout:
                print('\nOutput:')
                print(result.stdout[-1000:])  # Show last 1000 chars

            return success

        except subprocess.TimeoutExpired:
            print('❌ Test timed out after 5 minutes')
            self.results['test_results']['test_1_concurrent'] = {
                'name': 'High Volume Concurrent Submissions',
                'success': False,
                'error': 'Timeout after 5 minutes'
            }
            return False
        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            self.results['test_results']['test_1_concurrent'] = {
                'name': 'High Volume Concurrent Submissions',
                'success': False,
                'error': str(e)
            }
            return False

    def run_test_2_parser_performance(self):
        """Run Test 2: Parser Performance Under Large Log Files"""
        print('\n' + '='*60)
        print('🧪 TEST 2: Parser Performance Under Large Log Files')
        print('='*60)

        try:
            # Step 1: Generate test log
            print('📝 Generating test log file...')
            generate_script = self.test_dir / 'generate_test_log.py'

            result = subprocess.run(
                [sys.executable, str(generate_script)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            if result.returncode != 0:
                print(f'❌ Log generation failed')
                self.results['test_results']['test_2_parser'] = {
                    'name': 'Parser Performance Under Large Log Files',
                    'success': False,
                    'error': 'Log generation failed',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                return False

            print('✅ Test log generated')

            # Step 2: Run parser performance test
            print('🔍 Running parser performance test...')
            parser_script = '/Users/roy/Documents/Projects/citations/dashboard/log_parser.py'

            if not os.path.exists(parser_script):
                print(f'❌ Parser script not found: {parser_script}')
                self.results['test_results']['test_2_parser'] = {
                    'name': 'Parser Performance Under Large Log Files',
                    'success': False,
                    'error': f'Parser script not found: {parser_script}'
                }
                return False

            start_time = time.time()
            result = subprocess.run(
                [sys.executable, parser_script],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            parser_duration = time.time() - start_time

            success = result.returncode == 0 and parser_duration < 10

            self.results['test_results']['test_2_parser'] = {
                'name': 'Parser Performance Under Large Log Files',
                'success': success,
                'parser_duration': parser_duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            print(f'Parser completed in {parser_duration:.2f}s')
            print(f'{"✅ PASSED" if success else "❌ FAILED"} (< 10s required)')

            return success

        except subprocess.TimeoutExpired:
            print('❌ Parser test timed out')
            self.results['test_results']['test_2_parser'] = {
                'name': 'Parser Performance Under Large Log Files',
                'success': False,
                'error': 'Parser test timed out'
            }
            return False
        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            self.results['test_results']['test_2_parser'] = {
                'name': 'Parser Performance Under Large Log Files',
                'success': False,
                'error': str(e)
            }
            return False

    def run_test_3_resource_monitoring(self):
        """Run Test 3: Resource Usage Monitoring During Load"""
        print('\n' + '='*60)
        print('🧪 TEST 3: Resource Usage Monitoring During Load')
        print('='*60)

        test_script = self.test_dir / 'monitor_resources.py'

        if not test_script.exists():
            print(f'❌ Test script not found: {test_script}')
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )

            success = result.returncode == 0

            self.results['test_results']['test_3_resources'] = {
                'name': 'Resource Usage Monitoring During Load',
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            print(f'{"✅ PASSED" if success else "❌ FAILED"}')

            return success

        except subprocess.TimeoutExpired:
            print('❌ Test timed out after 3 minutes')
            self.results['test_results']['test_3_resources'] = {
                'name': 'Resource Usage Monitoring During Load',
                'success': False,
                'error': 'Timeout after 3 minutes'
            }
            return False
        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            self.results['test_results']['test_3_resources'] = {
                'name': 'Resource Usage Monitoring During Load',
                'success': False,
                'error': str(e)
            }
            return False

    def run_test_4_parser_stress(self):
        """Run Test 4: Parser Stress Testing with Partial Writes"""
        print('\n' + '='*60)
        print('🧪 TEST 4: Parser Stress Testing with Partial Writes')
        print('='*60)

        test_script = self.test_dir / 'test_parser_stress.py'

        if not test_script.exists():
            print(f'❌ Test script not found: {test_script}')
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0

            self.results['test_results']['test_4_stress'] = {
                'name': 'Parser Stress Testing with Partial Writes',
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            print(f'{"✅ PASSED" if success else "❌ FAILED"}')

            return success

        except subprocess.TimeoutExpired:
            print('❌ Test timed out after 5 minutes')
            self.results['test_results']['test_4_stress'] = {
                'name': 'Parser Stress Testing with Partial Writes',
                'success': False,
                'error': 'Timeout after 5 minutes'
            }
            return False
        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            self.results['test_results']['test_4_stress'] = {
                'name': 'Parser Stress Testing with Partial Writes',
                'success': False,
                'error': str(e)
            }
            return False

    def generate_summary(self):
        """Generate test summary"""
        test_results = self.results['test_results']

        passed_tests = sum(1 for result in test_results.values() if result.get('success', False))
        total_tests = len(test_results)
        self.results['overall_success'] = passed_tests == total_tests

        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

    def print_summary(self):
        """Print test summary"""
        summary = self.results['summary']

        print('\n' + '='*60)
        print('📊 LOAD TEST SUMMARY')
        print('='*60)
        print(f'Total tests: {summary["total_tests"]}')
        print(f'Passed: {summary["passed_tests"]}')
        print(f'Failed: {summary["failed_tests"]}')
        print(f'Success rate: {summary["success_rate"]:.1f}%')

        print('\nTest Results:')
        for test_key, test_result in self.results['test_results'].items():
            status = "✅ PASS" if test_result.get('success', False) else "❌ FAIL"
            print(f'  {test_result["name"]}: {status}')

        print(f'\nOverall result: {"✅ ALL TESTS PASSED" if self.results["overall_success"] else "❌ SOME TESTS FAILED"}')

    def save_results(self):
        """Save test results to file"""
        results_file = self.test_dir / 'load_test_master_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f'\n📄 Detailed results saved to: {results_file}')
        return results_file

    def run_all_tests(self):
        """Run all load tests"""
        print('🚀 Starting Load Test Suite')
        print(f'Timestamp: {self.results["timestamp"]}')
        print(f'Test directory: {self.test_dir}')

        # Check prerequisites
        if not self.check_prerequisites():
            print('❌ Prerequisites not met, aborting tests')
            return False

        start_time = time.time()

        # Run all tests
        test_results = []
        test_results.append(self.run_test_1_concurrent_submissions())
        test_results.append(self.run_test_2_parser_performance())
        test_results.append(self.run_test_3_resource_monitoring())
        test_results.append(self.run_test_4_parser_stress())

        total_duration = time.time() - start_time
        self.results['total_duration'] = total_duration

        # Generate and print summary
        self.generate_summary()
        self.print_summary()
        self.save_results()

        print(f'\n⏱️  Total test duration: {total_duration:.2f} seconds')

        return self.results['overall_success']

def main():
    """Main test runner"""
    runner = LoadTestRunner()

    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print('\n\n🛑 Tests interrupted by user')
        sys.exit(2)
    except Exception as e:
        print(f'\n\n💥 Test suite failed with exception: {e}')
        sys.exit(3)

if __name__ == '__main__':
    main()