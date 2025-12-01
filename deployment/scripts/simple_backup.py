#!/usr/bin/env python3
import shutil
from datetime import datetime
import os

db_path = 'dashboard/data/validations.db'
backup_file = f'{db_path}.pre_deploy_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
shutil.copy2(db_path, backup_file)
print(f'Pre-deployment backup created: {backup_file}')