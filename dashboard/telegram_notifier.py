#!/usr/bin/env python3
"""
Telegram Bot Notifier for Validation Jobs

Polled by cron every minute.
- Checks for jobs completed > last_notified_timestamp AND < NOW - 5 minutes
- Sends formatted Telegram message
- Updates last_notified_timestamp in parser_metadata
"""
import os
import sys
import sqlite3
import requests
import argparse
import datetime
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path to allow importing database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard.database import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
METADATA_KEY = "telegram_last_notified_timestamp"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "validations.db")
DASHBOARD_URL = "http://100.98.211.49:4646"

# Env vars
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_upgrade_funnel_icons(upgrade_state: Optional[str]) -> str:
    """Generate icons for upgrade funnel state."""
    if not upgrade_state:
        return ""
    
    states = upgrade_state.split(',') if isinstance(upgrade_state, str) else []
    
    # Define steps
    steps = [
        {'state': 'locked', 'icon': '🔒', 'label': 'Gated'},
        {'state': 'shown', 'icon': '🛒', 'label': 'Pricing Shown'},
        {'state': 'clicked', 'icon': '🛒', 'label': 'Pricing Shown'}, # aggregated
        {'state': 'checkout', 'icon': '💳', 'label': 'Checkout'},
        {'state': 'modal', 'icon': '💳', 'label': 'Checkout'}, # aggregated
        {'state': 'success', 'icon': '💸', 'label': 'Upgraded'}
    ]
    
    # Determined max level
    state_set = set(states)
    icons = []
    
    # Simple logic: showing all relevant icons encountered
    if 'locked' in state_set:
        icons.append(f"🔒 Gated")
    if 'shown' in state_set or 'clicked' in state_set:
        icons.append(f"🛒 Pricing Shown")
    if 'checkout' in state_set or 'modal' in state_set:
        icons.append(f"💳 Checkout")
    if 'success' in state_set:
        icons.append(f"💸 Upgraded!")
        
    if not icons:
        return ""
        
    return "\nUpgrade Funnel:\n" + "\n".join(icons)


def format_message(job: Dict[str, Any]) -> str:
    """Format job data into Telegram message."""
    
    # Icons
    status_icon = "✅" if job.get('status') == 'completed' else "❌"
    
    # Counts
    valid = job.get('valid_citations_count') or 0
    invalid = job.get('invalid_citations_count') or 0
    total = job.get('citation_count') or 0
    
    # User / Provider / User ID
    user_type = str(job.get('user_type', 'unknown')).capitalize()
    user_id = job.get('paid_user_id') or job.get('free_user_id')
    provider_map = {
        'model_c': 'Gemini',
        'model_a': 'OpenAI'
    }
    provider_raw = job.get('provider')
    provider = provider_map.get(provider_raw, provider_raw or 'Unknown')
    
    # Style
    style_map = {'apa7': 'APA 7', 'mla9': 'MLA 9', 'chicago17': 'Chicago 17'}
    style_raw = job.get('style')
    style = style_map.get(style_raw, style_raw.upper() if style_raw else 'Unknown')
    
    # Revealed
    revealed = "Yes" if job.get('results_revealed_at') else "No"
    is_gated = job.get('results_gated')
    revealed_icon = "🔓" if revealed == "Yes" else ("🔒" if is_gated else "🔓")
    
    # Corrections
    copied = job.get('corrections_copied')
    corrections_line = f"\n📋 Corrections: {copied} copied" if copied and copied > 0 else ""
    
    # Upgrade Funnel
    funnel_text = get_upgrade_funnel_icons(job.get('upgrade_state'))
    
    msg = (
        f"🔔 *New Validation*\n\n"
        f"📋 Job: `{job['job_id'][:8]}`\n"
        f"📝 Style: {style}\n"
        f"📊 {total} Citations\n"
        f"   ✅ {valid} Valid\n"
        f"   ❌ {invalid} Invalid\n\n"
        f"👤 {user_type} User"
        + (f" (ID: `{user_id[:12]}`)" if user_id else "") +
        f"\n🤖 {provider}\n"
        f"{revealed_icon} Revealed: {revealed}"
        f"{corrections_line}"
        f"\n{funnel_text}\n\n"
        f"🔗 [Dashboard]({DASHBOARD_URL})"
    )
    return msg


def send_telegram_message(message: str, dry_run: bool = False) -> bool:
    """Send message to Telegram."""
    if dry_run:
        logger.info(f"[DRY RUN] Would send:\n{message}")
        return True
        
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Telegram Notifier")
    parser.add_argument("--dry-run", action="store_true", help="Print messages without sending")
    args = parser.parse_args()

    # Initialize DB
    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found at {DB_PATH}")
        sys.exit(1)
        
    db = DatabaseManager(DB_PATH)
    
    # Logic:
    # 1. Get last notified timestamp
    last_ts = db.get_metadata(METADATA_KEY)
    
    # Use UTC time to match database format (2025-12-27T18:33:07Z)
    now = datetime.datetime.utcnow()
    cutoff_time = now - datetime.timedelta(minutes=5)
    cutoff_str = cutoff_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Initial run handling: if no timestamp, start from 5 mins ago (don't spam history)
    if not last_ts:
        logger.info("No last_notified_timestamp found. Initializing to 5 minutes ago.")
        last_ts = cutoff_str
        # Save this baseline so subsequent runs have a fixed start point
        if not args.dry_run:
            db.set_metadata(METADATA_KEY, last_ts)
        
    logger.info(f"Checking for jobs created between {last_ts} and {cutoff_str}")
    
    # 2. Query jobs
    # Using created_at as completed_at is missing from schema
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM validations 
        WHERE created_at > ? 
          AND created_at < ?
          AND (is_test_job IS NULL OR is_test_job = 0)
        ORDER BY created_at ASC
    """
    
    cursor.execute(query, (last_ts, cutoff_str))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    logger.info(f"Found {len(jobs)} jobs (filtering for completed)")
    
    # 3. Process jobs
    count = 0
    for job in jobs:
        # Check status (db has validation_status, raw dict might not have normalized 'status')
        status = job.get('validation_status') or job.get('status')
        if status != 'completed':
            continue

        # Normalize job dict for format_message
        job['status'] = status
        
        try:
            msg = format_message(job)
            success = send_telegram_message(msg, args.dry_run)
            
            if success and not args.dry_run:
                # Update metadata after EACH success to prevent duplicates if crash
                new_ts = job['created_at']
                db.set_metadata(METADATA_KEY, new_ts)
                logger.info(f"Notified for job {job['job_id']}. Updated watermark to {new_ts}")
            
            count += 1
                
        except Exception as e:
            logger.error(f"Error processing job {job.get('job_id')}: {e}")
            continue

    logger.info(f"Sent {count} notifications")

if __name__ == "__main__":
    main()
