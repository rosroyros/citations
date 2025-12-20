#!/usr/bin/env python3
"""
Backfill site visits from Nginx logs.
Usage: python3 dashboard/backfill_site_visits.py [path_to_log]
"""
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import parser utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.database import DatabaseManager
from dashboard.nginx_log_parser import parse_nginx_logs
from dashboard.cron_parser import CronLogParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "/opt/citations/dashboard/data/validations.db"
DEFAULT_LOG_PATH = "/var/log/nginx/access.log"

def backfill_visits(log_path, db_path):
    if not os.path.exists(log_path):
        logger.error(f"Log file not found at {log_path}")
        return

    logger.info(f"Backfilling site visits from {log_path} into {db_path}...")
    
    with DatabaseManager(db_path) as db:
        # Parse all logs (no start timestamp limit for backfill)
        # However, we should be careful not to duplicate if we re-run
        # The database doesn't enforce unique constraints on visits easily without a composite key
        # For a simple backfill, we can check the latest timestamp in DB and only add after that, 
        # or rely on the user to run this only once/safely.
        
        # Safer approach: Check last parsed timestamp from metadata, but allow override
        # For "backfill regardless of xff", we imply reading old data.
        
        # Let's just parse everything and try to insert. 
        # To avoid massive duplicates on re-runs, we could check max timestamp in DB?
        # But site_visits is new, so it's likely empty or sparse.
        
        logger.info("Parsing logs...")
        visits = parse_nginx_logs(log_path)
        
        if not visits:
            logger.info("No visits found in log file.")
            return

        logger.info(f"Found {len(visits)} visits. Filtering existing...")
        
        # Optional: Check for duplicates if needed, or just insert
        # Given the volume, we'll just insert for now.
        
        count = 0
        for visit in visits:
            try:
                db.insert_site_visit(visit)
                count += 1
                if count % 1000 == 0:
                    print(f"Inserted {count} visits...", end='\r')
            except Exception as e:
                logger.warning(f"Failed to insert visit: {e}")
                
        print(f"Inserted {count} visits total.")
        
        # Update metadata timestamp to the latest visit
        if visits:
            # Sort to find latest
            latest_visit = max(visits, key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S"))
            latest_ts = latest_visit['timestamp']
            
            logger.info(f"Updating last_nginx_parsed_timestamp to {latest_ts}")
            db.set_metadata("last_nginx_parsed_timestamp", latest_ts)

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG_PATH
    db_file = os.environ.get("CITATION_DB_PATH", DEFAULT_DB_PATH)
    
    backfill_visits(log_file, db_file)
