#!/bin/bash
set -e

# Cleanup stale PulseAudio locks/sockets
rm -rf /tmp/pulseaudio*
rm -rf ~/.config/pulse
rm -rf ~/.pulse

# Start PulseAudio in daemon mode
pulseaudio -D --exit-idle-time=-1

# Verify PulseAudio is running
if ! pactl info > /dev/null 2>&1; then
    echo "PulseAudio failed to start."
    # Try verbose start to debug if needed, but for now just fail
    # pulseaudio -v --start --exit-idle-time=-1
fi

echo "PulseAudio started successfully."

# Execute the passed command (the bot)
exec "$@"
