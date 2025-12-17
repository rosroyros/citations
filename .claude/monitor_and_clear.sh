#!/bin/bash
set -euo pipefail

# Monitor a tmux pane and send /clear when END_SESSION_CLEAR_REQUESTED marker is detected
#
# Usage: ./monitor_and_clear.sh <pane_number>
# Example: ./monitor_and_clear.sh 1

if [ $# -eq 0 ]; then
    echo "Usage: $0 <pane_number>"
    echo "Example: $0 1"
    exit 1
fi

PANE_NUMBER=$1
MARKER="::: END_SESSION_CLEAR_REQUESTED :::"
CHECK_INTERVAL=2  # seconds

echo "Monitoring pane ${PANE_NUMBER} for session clear marker..."
echo "Marker: ${MARKER}"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Track last seen content to avoid duplicate clears
LAST_CONTENT=""

while true; do
    # Capture the last 50 lines from the pane
    CURRENT_CONTENT=$(tmux capture-pane -t "${PANE_NUMBER}" -p -S -50 2>/dev/null || echo "")

    # Check if marker appears in new content
    if echo "$CURRENT_CONTENT" | grep -q "$MARKER"; then
        # Only trigger if this is new (not same content as last check)
        if [ "$CURRENT_CONTENT" != "$LAST_CONTENT" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Detected END_SESSION_CLEAR_REQUESTED marker!"
            echo "Sending /clear command to pane ${PANE_NUMBER}..."

            # Send /clear command
            tmux send-keys -t "${PANE_NUMBER}" "/clear" C-m

            echo "Clear command sent successfully"
            echo "Waiting 5 seconds before resuming monitoring..."
            sleep 5

            # Update last seen content
            LAST_CONTENT="$CURRENT_CONTENT"
        fi
    fi

    # Update last seen content
    LAST_CONTENT="$CURRENT_CONTENT"

    sleep "$CHECK_INTERVAL"
done
