#!/usr/bin/env python3
"""
Background writer process for parser stress testing
Simulates concurrent log writes while parser is running
"""

import time
import random
import sys
import os
import signal
import threading

class BackgroundWriter:
    def __init__(self, log_path=None):
        self.log_path = log_path or '/Users/roy/Documents/Projects/citations/logs/citations_test.log'
        self.job_id = 1000
        self.running = False
        self.writer_thread = None
        self.stats = {
            'jobs_written': 0,
            'errors': 0,
            'start_time': None
        }

    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        log_dir = os.path.dirname(self.log_path)
        os.makedirs(log_dir, exist_ok=True)

    def _write_citation_jobs(self):
        """Writer thread function"""
        while self.running:
            try:
                with open(self.log_path, 'a') as f:
                    f.write(f'<<JOB_ID:stress-test-{self.job_id}>>\n')

                    # Write 2-4 citations per job
                    num_citations = random.randint(2, 4)
                    for i in range(num_citations):
                        citation = (f'Stress test citation {self.job_id}-{i+1}: '
                                  f'Author Name{i}. Stress Test Title {self.job_id}. '
                                  f'Stress Publisher, 2023. This is a concurrent write '
                                  f'test citation with enough text to simulate realistic data.')
                        f.write(f'{citation}\n')

                    f.write('<<<END_JOB>>>\n')
                    f.flush()  # Ensure write is flushed to disk

                self.job_id += 1
                self.stats['jobs_written'] += 1

                # Random sleep between 0.1 and 0.5 seconds
                sleep_time = random.uniform(0.1, 0.5)
                time.sleep(sleep_time)

            except Exception as e:
                self.stats['errors'] += 1
                print(f'Writer error: {e}')
                time.sleep(1)  # Wait before retry

    def start(self):
        """Start the background writer"""
        self._ensure_log_directory()
        self.running = True
        self.stats['start_time'] = time.time()
        self.writer_thread = threading.Thread(target=self._write_citation_jobs, daemon=True)
        self.writer_thread.start()
        print(f'📝 Background writer started')
        print(f'   Log file: {self.log_path}')
        print(f'   Writer PID: {os.getpid()}')
        return self

    def stop(self):
        """Stop the background writer"""
        print('🛑 Stopping background writer...')
        self.running = False

        if self.writer_thread and self.writer_thread.is_alive():
            self.writer_thread.join(timeout=3)

        duration = time.time() - self.stats['start_time']
        print(f'📊 Writer stopped')
        print(f'   Jobs written: {self.stats["jobs_written"]}')
        print(f'   Errors: {self.stats["errors"]}')
        print(f'   Duration: {duration:.2f}s')
        print(f'   Rate: {self.stats["jobs_written"]/duration:.2f} jobs/sec')

    def get_stats(self):
        """Get writer statistics"""
        if self.stats['start_time']:
            duration = time.time() - self.stats['start_time']
            self.stats['duration'] = duration
            if duration > 0:
                self.stats['jobs_per_second'] = self.stats['jobs_written'] / duration
        return self.stats

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f'\n🛑 Received signal {signum}, shutting down...')
    sys.exit(0)

def main():
    """Main writer process"""
    print('📝 Background Citation Writer Process')
    print('This process writes citation jobs to simulate concurrent log activity.')
    print('Press Ctrl+C to stop.\n')

    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Allow custom log path
    log_path = None
    if len(sys.argv) > 1:
        log_path = sys.argv[1]

    # Start writer
    writer = BackgroundWriter(log_path)
    writer.start()

    try:
        # Keep process alive
        while True:
            time.sleep(1)
            stats = writer.get_stats()
            print(f'\r📊 Jobs written: {stats["jobs_written"]} | Errors: {stats["errors"]}', end='', flush=True)

    except KeyboardInterrupt:
        print('\n')
    finally:
        writer.stop()

if __name__ == '__main__':
    main()