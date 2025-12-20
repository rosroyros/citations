import re
import gzip
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

import os

logger = logging.getLogger(__name__)

# Regex for Nginx combined log format
# 127.0.0.1 - - [07/Nov/2023:12:34:56 +0000] "GET / HTTP/1.1" 200 1234 "-" "Mozilla/5.0..."
NGINX_LOG_PATTERN = re.compile(
    r'(?P<ip>[\d\.:]+) - (?P<user>.+) \[(?P<timestamp>.+)\] "(?P<method>\w+) (?P<path>.*?) (?P<protocol>.*?)" (?P<status>\d+) (?P<size>\d+) "(?P<referer>.*?)" "(?P<ua>.*?)"'
)

# Common bot indicators in User Agent
BOT_PATTERNS = [
    r'bot\b', r'crawl', r'spider', r'slurp', r'mediapartners',
    r'headless', r'lighthouse', r'pingdom', r'uptime', r'monitor',
    r'python-requests', r'aiohttp', r'httpx', r'wget', r'curl',
    r'chatgpt', r'openai', r'anthropic', r'claude', r'bard'
]
BOT_REGEX = re.compile('|'.join(BOT_PATTERNS), re.IGNORECASE)

def parse_nginx_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse Nginx log timestamp: 07/Nov/2023:12:34:56 +0000
    Returns naive datetime in UTC (converting if necessary) or None
    """
    try:
        # Parse with timezone
        dt = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
        # Convert to UTC and make naive for consistency with app logs
        return dt.astimezone(datetime.utcnow().astimezone().tzinfo).replace(tzinfo=None)
    except ValueError:
        return None

def generate_visitor_id(ip: str, ua: str) -> str:
    """Generate a pseudo-unique visitor ID from IP and User Agent"""
    raw = f"{ip}-{ua}"
    return hashlib.md5(raw.encode()).hexdigest()

def is_static_asset(path: str) -> bool:
    """Check if path is a static asset (css, js, images, etc)"""
    # Common static extensions
    static_exts = {
        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', 
        '.svg', '.woff', '.woff2', '.ttf', '.eot', '.map', '.txt'
    }
    
    # Check extension
    if any(path.lower().endswith(ext) for ext in static_exts):
        return True
        
    # Check common asset directories
    if path.startswith(('/static/', '/assets/', '/app-assets/')):
        return True
        
    return False

def is_bot(ua: str) -> bool:
    """Check if User Agent belongs to a known bot"""
    return bool(BOT_REGEX.search(ua))

def get_ignored_ips() -> set:
    """Get set of ignored IPs from environment variable"""
    ips = os.environ.get('IGNORE_IPS', '')
    return {ip.strip() for ip in ips.split(',') if ip.strip()}

def get_ignored_uas() -> set:
    """Get set of ignored User Agent substrings from environment variable"""
    uas = os.environ.get('IGNORE_USER_AGENTS', '')
    return {ua.strip().lower() for ua in uas.split(',') if ua.strip()}

def parse_nginx_logs(log_file_path: str, start_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Parse Nginx access logs and return list of visits.
    
    Args:
        log_file_path: Path to log file (supports .gz)
        start_timestamp: Optional timestamp to start parsing from
        
    Returns:
        List of visit dictionaries
    """
    visits = []
    
    if not os.path.exists(log_file_path):
        logger.warning(f"Nginx log file not found: {log_file_path}")
        return []

    # Load filters configuration
    ignored_ips = get_ignored_ips()
    ignored_ua_snippets = get_ignored_uas()

    open_func = gzip.open if log_file_path.endswith('.gz') else open
    
    try:
        with open_func(log_file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = NGINX_LOG_PATTERN.match(line.strip())
                if not match:
                    continue
                    
                data = match.groupdict()
                
                # Check IP filter
                if data['ip'] in ignored_ips:
                    continue

                # Check User Agent filters (custom + bot)
                ua_lower = data['ua'].lower()
                if any(snippet in ua_lower for snippet in ignored_ua_snippets):
                    continue
                    
                if is_bot(data['ua']):
                    continue

                # Parse timestamp
                timestamp = parse_nginx_timestamp(data['timestamp'])
                if not timestamp:
                    continue
                    
                # Filter by timestamp if provided
                if start_timestamp and timestamp <= start_timestamp:
                    continue
                    
                # Skip static assets to focus on page visits
                if is_static_asset(data['path']):
                    continue
                    
                # Skip internal API calls or health checks if needed
                if data['path'].startswith('/api/') or data['path'] == '/health':
                    continue

                visit = {
                    "ip_address": data['ip'],
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "path": data['path'],
                    "status_code": int(data['status']),
                    "referer": data['referer'],
                    "user_agent": data['ua'],
                    "visitor_id": generate_visitor_id(data['ip'], data['ua'])
                }
                
                visits.append(visit)
                
    except Exception as e:
        logger.error(f"Error parsing Nginx logs {log_file_path}: {e}")
        
    return visits
