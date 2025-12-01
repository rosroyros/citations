#!/usr/bin/env python3
"""
Test 4: Parser Stress Testing with Partial Writes
Test parser handles concurrent writer/reader operations gracefully
"""

import subprocess
import time
import os
import sys
import json
import signal
import psutil
import requests
import concurrent.futures
from pathlib import Path

class ParserStressTest:
    def __init__(self):
        self.log_path = '/Users/roy/Documents/Projects/citations/logs/citations_test.log'
        self.parser_script = '/Users/roy/Documents/Projects/citations/dashboard/log_parser.py'
        self.writer_script = '/Users/roy/Documents/Projects/citations/load_tests/background_writer.py'
        self.writer_process = None
        self.results = {
            'parser_runs': [],
            'writer_stats': {},
            'test_duration': 0,
            'errors': []
        }

    def _ensure_dependencies(self):
        """Check if required files exist"""
        if not os.path.exists(self.parser_script):
            raise FileNotFoundError(f'Parser script not found: {self.parser_script}')

        if not os.path.exists(self.writer_script):
            raise FileNotFoundError(f'Writer script not found: {self.writer_script}')

        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        os.makedirs(log_dir, exist_ok=True)

        print('✅ Dependencies verified')

    def start_background_writer(self):
        """Start background writer process"""
        print(f'📝 Starting background writer...')
        print(f'   Script: {self.writer_script}')
        print(f'   Log file: {self.log_path}')

        try:
            # Start writer in background
            self.writer_process = subprocess.Popen(
                [sys.executable, self.writer_script, self.log_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Give it time to start
            time.sleep(2)

            if self.writer_process.poll() is None:  # Process is still running
                print(f'✅ Background writer started (PID: {self.writer_process.pid})')
                return True
            else:
                # Process already exited
                stdout, stderr = self.writer_process.communicate()
                print(f'❌ Writer failed to start')
                if stderr:
                    print(f'Error: {stderr}')
                return False

        except Exception as e:
            print(f'❌ Failed to start writer: {e}')
            return False

    def run_parser_concurrently(self, num_runs=5):
        """Run parser multiple times while writer is active"""
        print(f'🔍 Running parser {num_runs} times while writer is active...')

        for i in range(num_runs):
            print(f'\nParser run {i+1}/{num_runs}:')
            run_start = time.time()

            try:
                # Run parser script
                result = subprocess.run(
                    [sys.executable, self.parser_script],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )

                run_duration = time.time() - run_start

                run_result = {
                    'run_number': i + 1,
                    'duration': run_duration,
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }

                self.results['parser_runs'].append(run_result)

                if run_result['success']:
                    print(f'   ✅ Completed in {run_duration:.2f}s')
                else:
                    print(f'   ❌ Failed with return code {result.returncode}')
                    if result.stderr:
                        print(f'   Error: {result.stderr[:200]}...')

                    self.results['errors'].append(f'Parser run {i+1} failed: {result.stderr[:100]}')

            except subprocess.TimeoutExpired:
                run_duration = time.time() - run_start
                print(f'   ⏰ Timed out after {run_duration:.2f}s')
                self.results['parser_runs'].append({
                    'run_number': i + 1,
                    'duration': run_duration,
                    'return_code': -1,
                    'stdout': '',
                    'stderr': 'Timeout',
                    'success': False
                })
                self.results['errors'].append(f'Parser run {i+1} timed out')

            except Exception as e:
                run_duration = time.time() - run_start
                print(f'   ❌ Exception: {e}')
                self.results['parser_runs'].append({
                    'run_number': i + 1,
                    'duration': run_duration,
                    'return_code': -1,
                    'stdout': '',
                    'stderr': str(e),
                    'success': False
                })
                self.results['errors'].append(f'Parser run {i+1} exception: {e}')

            # Wait between runs
            if i < num_runs - 1:
                time.sleep(2)

    def stop_background_writer(self):
        """Stop background writer process"""
        print(f'\n🛑 Stopping background writer...')
        if self.writer_process:
            try:
                # Try graceful shutdown
                self.writer_process.terminate()
                try:
                    self.writer_process.wait(timeout=5)
                    print('✅ Writer stopped gracefully')
                except subprocess.TimeoutExpired:
                    # Force kill
                    self.writer_process.kill()
                    print('⚡ Writer force killed')

                # Get any remaining output
                stdout, stderr = self.writer_process.communicate()

            except Exception as e:
                print(f'⚠️ Error stopping writer: {e}')

    def run_concurrent_api_test(self, num_requests=20, max_workers=3):
        """Run API requests concurrently with parser/writer activity"""
        print(f'\n🌐 Running concurrent API test: {num_requests} requests')

        def submit_api_request():
            """Submit a single API request"""
            try:
                citations = 'Concurrent stress test citation: Author. Title. Publisher, 2023.'
                response = requests.post('http://localhost:8001/api/validate/async',
                                        json={'citations': citations, 'style': 'apa'},
                                        timeout=10)
                return {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_time': 0.1  # Placeholder
                }
            except Exception as e:
                return {
                    'success': False,
                    'status_code': 500,
                    'error': str(e),
                    'response_time': 10.0
                }

        start_time = time.time()
        successful = 0
        failed = 0

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(submit_api_request) for _ in range(num_requests)]

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result['success']:
                            successful += 1
                        else:
                            failed += 1
                    except Exception:
                        failed += 1

        finally:
            duration = time.time() - start_time

        print(f'   API test: {successful}/{num_requests} successful in {duration:.2f}s')
        return successful, failed

    def analyze_log_file(self):
        """Analyze the generated log file"""
        if not os.path.exists(self.log_path):
            return {'error': 'Log file not found'}

        try:
            with open(self.log_path, 'r') as f:
                content = f.read()

            # Count jobs and citations
            job_count = content.count('<<JOB_ID:')
            end_job_count = content.count('<<<END_JOB>>>')
            line_count = len(content.split('\n'))

            file_size = os.path.getsize(self.log_path)

            return {
                'file_size_bytes': file_size,
                'file_size_mb': file_size / (1024 * 1024),
                'job_count': job_count,
                'end_job_count': end_job_count,
                'line_count': line_count,
                'complete_jobs': min(job_count, end_job_count)
            }

        except Exception as e:
            return {'error': str(e)}

    def run_stress_test(self):
        """Run complete stress test"""
        print('🧪 Parser Stress Test with Concurrent Writes')
        print('=' * 50)

        test_start = time.time()

        try:
            # Step 1: Verify dependencies
            self._ensure_dependencies()

            # Step 2: Start background writer
            if not self.start_background_writer():
                return False

            # Step 3: Let writer generate some data
            print('📝 Allowing writer to generate initial data...')
            time.sleep(5)

            # Step 4: Run parser concurrently
            self.run_parser_concurrently(num_runs=5)

            # Step 5: Run concurrent API test
            self.run_concurrent_api_test(num_requests=20, max_workers=3)

            # Step 6: Let writer run a bit more
            print('📝 Allowing writer to continue...')
            time.sleep(3)

        except Exception as e:
            print(f'❌ Stress test error: {e}')
            self.results['errors'].append(f'Stress test exception: {e}')

        finally:
            # Step 7: Stop writer
            self.stop_background_writer()

            # Calculate test duration
            self.results['test_duration'] = time.time() - test_start

        # Analyze results
        return self.analyze_results()

    def analyze_results(self):
        """Analyze test results and determine success"""
        print(f'\n=== STRESS TEST RESULTS ===')
        print(f'Test duration: {self.results["test_duration"]:.2f} seconds')

        # Parser results
        parser_runs = self.results['parser_runs']
        successful_runs = sum(1 for r in parser_runs if r['success'])
        print(f'Parser runs: {successful_runs}/{len(parser_runs)} successful')

        if parser_runs:
            avg_duration = sum(r['duration'] for r in parser_runs) / len(parser_runs)
            max_duration = max(r['duration'] for r in parser_runs)
            print(f'Parser performance: avg {avg_duration:.2f}s, max {max_duration:.2f}s')

        # Log file analysis
        log_analysis = self.analyze_log_file()
        if 'error' not in log_analysis:
            print(f'Log file: {log_analysis["complete_jobs"]} complete jobs, {log_analysis["file_size_mb"]:.1f} MB')

        # Errors
        errors = self.results['errors']
        if errors:
            print(f'Errors encountered: {len(errors)}')
            for error in errors[:3]:  # Show first 3 errors
                print(f'  - {error}')

        # Success criteria
        print(f'\n=== SUCCESS CRITERIA VALIDATION ===')

        parser_success_rate = successful_runs / len(parser_runs) if parser_runs else 0
        parser_ok = parser_success_rate >= 0.8  # 80% parser success rate
        log_ok = 'error' not in log_analysis and log_analysis.get('complete_jobs', 0) > 0
        no_critical_errors = len(errors) == 0

        print(f'Parser success >= 80%: {"✓ PASS" if parser_ok else "✗ FAIL"} ({successful_runs}/{len(parser_runs)})')
        print(f'Log file generated: {"✓ PASS" if log_ok else "✗ FAIL"}')
        print(f'No critical errors: {"✓ PASS" if no_critical_errors else "✗ FAIL"} ({len(errors)} errors)')

        all_passed = parser_ok and log_ok and no_critical_errors
        print(f'\nOverall result: {"✓ STRESS TEST PASSED" if all_passed else "✗ STRESS TEST FAILED"}')

        # Save results
        results_file = 'load_test_4_stress_results.json'
        self.results['log_analysis'] = log_analysis
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f'Detailed results saved to: {results_file}')

        return all_passed

def main():
    """Main stress test"""
    stress_test = ParserStressTest()
    success = stress_test.run_stress_test()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()