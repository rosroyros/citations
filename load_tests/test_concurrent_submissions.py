#!/usr/bin/env python3
"""
Load Test 1: High Volume Concurrent Submissions
Test 100+ concurrent validation requests to validate system can handle production load
"""

import requests
import concurrent.futures
import time
import json
import sys

def submit_validation(citation_id):
    """Submit a validation request and measure response time"""
    try:
        citations = f'''Citation {citation_id}-1: Author Name. Book Title. Publisher, 2023.
Citation {citation_id}-2: Another Author. Article Title. Journal Name, 2022.
Citation {citation_id}-3: Third Author. Chapter Title. Book Publisher, 2021.'''

        start_time = time.time()
        response = requests.post('http://localhost:8001/api/validate/async',
                                json={'citations': citations, 'style': 'apa'},
                                timeout=30)
        end_time = time.time()

        return {
            'citation_id': citation_id,
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'job_id': response.json().get('job_id') if response.status_code == 200 else None,
            'response_text': response.text[:200] if response.status_code != 200 else None
        }
    except Exception as e:
        return {
            'citation_id': citation_id,
            'status_code': 500,
            'response_time': 30.0,
            'error': str(e)
        }

def main():
    """Run concurrent submission load test"""
    num_requests = 100

    print(f'Starting {num_requests} concurrent validation requests...')
    print('Target: http://localhost:8001/api/validate/async')

    start_time = time.time()

    # Submit all requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(submit_validation, i) for i in range(num_requests)]
        results = []

        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

            # Show progress
            if len(results) % 10 == 0:
                print(f'Completed {len(results)}/{num_requests} requests...')

    end_time = time.time()
    total_time = end_time - start_time

    # Analyze results
    successful = sum(1 for r in results if r['status_code'] == 200)
    failed = sum(1 for r in results if r['status_code'] != 200)
    avg_response_time = sum(r['response_time'] for r in results) / len(results)
    max_response_time = max(r['response_time'] for r in results)
    min_response_time = min(r['response_time'] for r in results)

    # Print results
    print(f'\n=== LOAD TEST RESULTS ===')
    print(f'Total test time: {total_time:.2f} seconds')
    print(f'Successful requests: {successful}/{num_requests} ({successful/num_requests*100:.1f}%)')
    print(f'Failed requests: {failed}/{num_requests} ({failed/num_requests*100:.1f}%)')
    print(f'Average response time: {avg_response_time:.2f}s')
    print(f'Max response time: {max_response_time:.2f}s')
    print(f'Min response time: {min_response_time:.2f}s')
    print(f'Requests per second: {num_requests/total_time:.2f}')

    # Show error details if any
    if failed > 0:
        print(f'\n=== ERROR DETAILS ===')
        error_results = [r for r in results if r['status_code'] != 200]
        for result in error_results[:5]:  # Show first 5 errors
            print(f"Request {result['citation_id']}: {result['status_code']} - {result.get('error', result.get('response_text', 'Unknown error'))}")
        if len(error_results) > 5:
            print(f'... and {len(error_results) - 5} more errors')

    # Success criteria validation
    print(f'\n=== SUCCESS CRITERIA VALIDATION ===')

    success_rate_ok = successful >= 95
    avg_time_ok = avg_response_time < 2.0
    max_time_ok = max_response_time < 5.0

    print(f'Success rate >= 95%: {"✓ PASS" if success_rate_ok else "✗ FAIL"} ({successful}/{num_requests})')
    print(f'Avg response time < 2s: {"✓ PASS" if avg_time_ok else "✗ FAIL"} ({avg_response_time:.2f}s)')
    print(f'Max response time < 5s: {"✓ PASS" if max_time_ok else "✗ FAIL"} ({max_response_time:.2f}s)')

    all_passed = success_rate_ok and avg_time_ok and max_time_ok
    print(f'\nOverall result: {"✓ LOAD TEST PASSED" if all_passed else "✗ LOAD TEST FAILED"}')

    # Save detailed results to file
    results_file = 'load_test_1_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'test_name': 'High Volume Concurrent Submissions',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'num_requests': num_requests,
                'max_workers': 10,
                'timeout': 30
            },
            'summary': {
                'total_time': total_time,
                'successful': successful,
                'failed': failed,
                'success_rate': successful/num_requests*100,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'min_response_time': min_response_time,
                'requests_per_second': num_requests/total_time
            },
            'results': results
        }, f, indent=2)

    print(f'\nDetailed results saved to: {results_file}')

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()