#!/usr/bin/env python3
"""
Analyze Nginx traffic to find top IPs and User Agents.
Usage: python3 dashboard/analyze_nginx_traffic.py [path_to_log]
"""
import sys
import os
import re
import gzip
import argparse
from collections import Counter
from datetime import datetime, timedelta

# Add parent directory to path to import parser utils if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Regex for Nginx combined log format (reused from nginx_log_parser.py)
NGINX_LOG_PATTERN = re.compile(
    r'(?P<ip>[\d\.:]+) - (?P<user>.+) \[(?P<timestamp>.+)\] "(?P<method>\w+) (?P<path>.*?) (?P<protocol>.*?)" (?P<status>\d+) (?P<size>\d+) "(?P<referer>.*?)" "(?P<ua>.*?)"'
)

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze Nginx traffic')
    parser.add_argument('log_file', nargs='?', default='/var/log/nginx/access.log', help='Path to Nginx access log')
    parser.add_argument('--lines', '-n', type=int, default=10000, help='Number of lines to parse (0 for all)')
    parser.add_argument('--days', '-d', type=int, default=7, help='Number of days to analyze')
    return parser.parse_args()

def analyze_logs(log_path, max_lines, days):
    if not os.path.exists(log_path):
        print(f"Error: Log file not found at {log_path}")
        return

    print(f"Analyzing {log_path}...")
    
    ip_counter = Counter()
    ua_counter = Counter()
    path_counter = Counter()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    open_func = gzip.open if log_path.endswith('.gz') else open
    
    line_count = 0
    match_count = 0
    
    try:
        with open_func(log_path, 'rt', encoding='utf-8', errors='ignore') as f:
            # Read from end if max_lines is set? 
            # No, standard read is fine for simple analysis, maybe we just stop after max_lines
            # or read all if max_lines is 0
            
            for line in f:
                if max_lines > 0 and line_count >= max_lines:
                    break
                    
                line_count += 1
                
                match = NGINX_LOG_PATTERN.match(line.strip())
                if not match:
                    continue
                
                data = match.groupdict()
                
                # Basic date check
                try:
                    # 07/Nov/2023:12:34:56 +0000
                    ts_str = data['timestamp'].split()[0]
                    dt = datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S")
                    if dt < cutoff_date:
                        continue
                except ValueError:
                    continue
                
                match_count += 1
                ip_counter[data['ip']] += 1
                ua_counter[data['ua']] += 1
                path_counter[data['path']] += 1
                
    except Exception as e:
        print(f"Error reading file: {e}")
        
    print(f"\nAnalyzed {match_count} requests from last {days} days ({line_count} lines read)")
    
    print("\n=== Top 20 IP Addresses ===")
    print(f"{'IP Address':<20} | {'Count':<8} | {'%':<6}")
    print("-" * 40)
    for ip, count in ip_counter.most_common(20):
        percent = (count / match_count * 100) if match_count else 0
        print(f"{ip:<20} | {count:<8} | {percent:.1f}%")
        
    print("\n=== Top 20 User Agents ===")
    for ua, count in ua_counter.most_common(20):
        print(f"{count:<8} ({count/match_count*100:.1f}%) : {ua}")

    print("\n=== Top 20 Paths ===")
    for path, count in path_counter.most_common(20):
        print(f"{count:<8} : {path}")

if __name__ == "__main__":
    args = parse_args()
    analyze_logs(args.log_file, args.lines, args.days)
