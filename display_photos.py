#!/usr/bin/env python3
from datetime import datetime
import sys
import os
import random
import time
from PIL import Image
import pillow_heif  # HEIC support

log_file = "/home/justin/display_photos.log"
with open(log_file, "a") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting display script\n")

# Register HEIC opener for Pillow
pillow_heif.register_heif_opener()

# Waveshare library path (from your cloned repo)
sys.path.append("/home/justin/e-Paper/RaspberryPi_JetsonNano/python/lib")
from waveshare_epd import epd7in3f  # 7.3" tri-color display

# Path to your synced iCloud photos
PHOTO_DIR = "/home/justin/photos"
# Edited photos sibling folder
EDITED_DIR = os.path.join(os.path.dirname(PHOTO_DIR), os.path.basename(PHOTO_DIR) + "-edited")

# Initialize the display
epd = epd7in3f.EPD()
epd.init()
epd.Clear()

# Get all images, including HEIC
images = [
    f for f in os.listdir(PHOTO_DIR)
    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.heic'))
]

if not images:
    print("No images found in", PHOTO_DIR)
    epd.sleep()
    exit()

# Pick a random image filename
random.seed(time.time_ns())
chosen = random.choice(images)

# Prefer edited image if it exists
edited_path = os.path.join(EDITED_DIR, chosen)
orig_path = os.path.join(PHOTO_DIR, chosen)
image_path = edited_path if os.path.exists(edited_path) else orig_path
with open(log_file, "a") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Displaying: {image_path}\n")

# Open the image
img = Image.open(image_path)

# Resize to fit display
img = img.resize((epd.width, epd.height))
img = img.convert("RGB")  # Tri-color display expects RGB

# Display the image
epd.display(epd.getbuffer(img))

# Sleep the display
time.sleep(5)
epd.sleep()
