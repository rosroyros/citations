YOLO mode is enabled. All tool calls will be automatically approved.
Loaded cached credentials.
Excellent work on diagnosing the schema drift and preparing a gradual migration strategy. This level of preparation is key to a safe production deployment.

You've correctly identified the risks, and your primary question is about the safest deployment path. The custom migration script (`tools/gradual_migration_20251201.py`) is almost certainly safer for the database alteration itself, as it was designed for this specific scenario, but the standard deployment script (`deployment/scripts/deploy_with_citations.sh`) might perform other essential actions like restarting services or updating dependencies.

To give you the best recommendation, I need to understand exactly what each script does. Could you please show me the contents of these three files?

1.  `dashboard/database.py` (to verify the compatibility layer)
2.  `tools/gradual_migration_20251201.py` (to understand the migration logic)
3.  `deployment/scripts/deploy_with_citations.sh` (to see the full deployment process)

Once I review these, I can provide a concrete, step-by-step plan that minimizes risk to your production data. I'll start by reviewing the issue in the tracker.
Thank you. The issue details confirm your summary. Now, let's examine the files to determine the safest deployment strategy. I'll start with `dashboard/database.py`.
The `dashboard/database.py` file is exceptionally well-written. The compatibility layer that handles both `status` and `validation_status` in all query methods (`insert`, `get`, `get_count`, `get_stats`) is robust and significantly de-risks the deployment.

However, the automatic migration within `_create_schema` is incomplete. It only adds the `citations_text` column. It does *not* add the other new columns (`completed_at`, `duration_seconds`, `token_usage_*`, and importantly, `status` itself) to an existing table. The `CREATE TABLE` statement is only for new databases.

This confirms that the manual migration script is absolutely necessary to update the production database schema without data loss.

Now, let's examine the migration script itself.
This migration script is excellent. It's safe, idempotent, and clear.

Key safety features I've noted:
-   **Atomic Transactions:** It wraps the entire migration in a `BEGIN TRANSACTION...COMMIT/ROLLBACK` block, ensuring that if any step fails, the database is left untouched.
-   **Idempotency:** It checks for existing columns before attempting to add them, meaning it can be run multiple times without causing errors.
-   **User Confirmation:** It requires manual confirmation before running, preventing accidental execution.

This script is the correct tool for altering the production database schema.

Now for the final piece. Let's look at the standard deployment script to see how this manual migration step will fit into the overall process.
I have now reviewed all three files. The `deploy_with_citations.sh` script is a thorough process, but it critically misunderstands how the database migration needs to happen.

**Analysis of `deploy_with_citations.sh`:**
*   It relies on `database.py` to automatically handle the schema migration when the services restart.
*   As we discovered, `database.py` only adds the `citations_text` column and does **not** add the other required columns (`status`, `completed_at`, `duration_seconds`, etc.) to an existing database.
*   **Conclusion:** Running the standard deployment script by itself will fail. The backend service will restart with code that expects columns that don't exist, likely causing it to crash or throw errors.

### Recommended Deployment Strategy

The safest approach is a hybrid one: perform a manual migration while services are stopped, and then run the standard deployment script to complete the process. This leverages the safety of your custom migration script and the completeness of your standard deployment process.

Here is the step-by-step plan I recommend:

**1. Local Preparation**
- Ensure the latest versions of `dashboard/database.py` and `tools/gradual_migration_20251201.py` are committed to your `main` branch and pushed.

**2. Production Deployment Execution**

Execute these commands on the production server (`178.156.161.140`):

```bash
# Step 1: Navigate to the application directory
cd /opt/citations

# Step 2: Pull the latest code changes
# This brings the new database.py and the migration script to the server.
echo "Pulling latest code..."
git pull origin main

# Step 3: Create a manual backup before making changes
echo "Creating a manual safety backup..."
./deployment/scripts/backup_database.sh manual_migration_backup

# Step 4: Stop running services to unlock the database
echo "Stopping backend services..."
sudo systemctl stop citations-backend
sudo systemctl stop citations-dashboard

# Step 5: Activate virtual environment and run the gradual migration script
echo "Running gradual database migration..."
source venv/bin/activate
python3 tools/gradual_migration_20251201.py
# (You will be prompted to confirm with 'y')

# Step 6: Run the standard deployment script
# This script will now run against a corrected schema. It will handle
# dependency updates, frontend builds, and service restarts correctly.
echo "Running standard deployment script..."
./deployment/scripts/deploy_with_citations.sh

# Step 7: Monitor the application logs for any errors
echo "Deployment complete. Monitoring logs..."
sudo journalctl -u citations-backend -f
```

### Why This Approach Is Safest:

*   **Minimizes Downtime:** The services are only stopped for the brief period of the schema migration.
*   **Atomic Migration:** The manual script is transactional, preventing a partially migrated state.
*   **Uses Standard Processes:** It finishes with your established deployment script, ensuring all other parts of the system (dependencies, frontend, nginx) are updated correctly.
*   **Verification:** The `deploy_with_citations.sh` script's own verification steps will now serve as a final check that your manual migration was successful.

This plan directly addresses the schema mismatch while respecting your existing deployment and rollback procedures.
