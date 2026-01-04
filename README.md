 # Photo Frame (e-Paper + Photo Frame Web)

This repository contains the code for running a small photo-frame web app that prepares images for an e-ink display and a few helper scripts. The current import includes:

- `photo-frame-web/` — Flask web app used to view and edit photos and generate thumbnails for the e-ink frame.
- `display_photos.py` — helper script to display images on your e-ink device (kept here as-is).
- `sync_photos.sh` — script that populates the `photos/` folder from your Apple Photos export (or another source).

Files and folders excluded from the repository (by `.gitignore`):

- `photos/` — your source photos directory (local content; not committed).
- `photos-edited/` — generated edited images saved by the app.
- `photo-frame-web/static/thumbnails/` — generated thumbnails for the gallery.

You'll need to git clone waveshare's e-Paper git repo to get waveshare drivers required for the display_photos.py program.

---

## Quick start (development)

Requirements

- Python 3.8+ (3.10 recommended)
- `pip`

Install Python dependencies (create a virtualenv first if you prefer):

```bash
cd ~/photo-frame-web
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install Flask Pillow pillow-heif
```

Run the web app (development server):

```bash
cd ~/photo-frame-web
python3 app.py
# open http://127.0.0.1:5000
```

Notes about configuration

- `PHOTO_DIR` is currently hard-coded in `photo-frame-web/app.py` to `/home/justin/photos`. Update that constant if you keep your photos somewhere else.
- `EDITED_DIR` is `/home/justin/photos-edited` and `THUMB_DIR` is `photo-frame-web/static/thumbnails` (created automatically by the app).

---

## How editing works (overview)

- When you open a photo in the web UI `GET /edit/<filename>` the app shows either the original photo or the last edited version (if one exists) so you always operate on the most recent file.
- Crop action: the UI collects crop coordinates (Cropper.js) and posts `action=crop` — the server crops the current image (edited if present, otherwise original) and writes the result to `photos-edited/<filename>` (does not overwrite the original).
- Rotate action: calling `action=rotate` performs a rotate-only operation on the current image and writes to `photos-edited/<filename>`.
- Revert: `POST /revert/<filename>` deletes `photos-edited/<filename>` so the gallery and edit page fall back to the original image.
- Thumbnails are generated from the edited image when present; otherwise from the original.

---

## Remove all generated files (Clear All)

There is a `Clear All` button in the web UI that removes all original photos (from `PHOTO_DIR`), edited photos (from `EDITED_DIR`), and PNG thumbnails (from `THUMB_DIR`). This is irreversible.

---