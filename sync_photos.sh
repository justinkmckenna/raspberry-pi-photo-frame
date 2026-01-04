#!/bin/bash
# Script to sync iCloud album to local folder for e-ink display

# Activate your virtual environment
source /home/justin/icloudpd-venv/bin/activate

# Run icloudpd
icloudpd \
  --username justin.k.mckenna@gmail.com \
  --album "Raspberry Pi Smart Photo Frame" \
  --directory /home/justin/photos \
  --cookie-directory /home/justin/.icloudpd \
  --no-progress-bar \
  --skip-videos \
  --skip-live-photos \
  --folder-structure none
