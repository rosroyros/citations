#!/bin/bash
# Play a sound to notify the user that the agent is waiting for input.
# Using & to run in background so it doesn't block (though hooks might wait, usually audio is fire-and-forget)
afplay /System/Library/Sounds/Glass.aiff &
