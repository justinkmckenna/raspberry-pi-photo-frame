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

# Pick a random image
random.seed(time.time_ns())
image_path = os.path.join(PHOTO_DIR, random.choice(images))
print("Displaying:", image_path)

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
