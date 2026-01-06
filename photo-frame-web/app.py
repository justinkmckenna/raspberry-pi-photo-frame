from flask import Flask, render_template, redirect, url_for, send_from_directory, request, jsonify
from flask import send_file
from PIL import Image, ImageOps
import os
import hashlib

import pillow_heif
pillow_heif.register_heif_opener()

PHOTO_DIR = "/home/justin/photos"
EDITED_DIR = "/home/justin/photos-edited"
THUMB_DIR = "static/thumbnails"
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(EDITED_DIR, exist_ok=True)

# E-ink resolution (CHANGE if needed)
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

app = Flask(__name__)

def hash_filename(filename: str) -> str:
    """
    Generate a stable, URL-safe hash from a filename.
    Used for thumbnails and template rendering.
    """
    name, _ = os.path.splitext(filename)
    return hashlib.md5(name.encode("utf-8")).hexdigest()


@app.template_filter("hash")
def hash_filter(s):
    return hash_filename(s)


def get_images():
    files = []
    for f in sorted(os.listdir(PHOTO_DIR)):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
            files.append(f)
    return files


def thumbnail_path(filename):
    return f"{hash_filename(filename)}.png"


def generate_thumbnail(filename, force=False):
    try:
        # Prefer edited image for thumbnail if it exists
        edited_src = os.path.join(EDITED_DIR, filename)
        src = edited_src if os.path.exists(edited_src) else os.path.join(PHOTO_DIR, filename)
        thumb = os.path.join(THUMB_DIR, hash_filename(filename) + ".png")

        if not force and os.path.exists(thumb):
            return

        img = Image.open(src)
        img = ImageOps.exif_transpose(img)  # <-- rotate according to EXIF
        img = img.convert("RGB")
        img.thumbnail((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        img.save(thumb)

    except Exception as e:
        app.logger.warning(f"Skipping {filename}: {e}")


@app.route("/")
def gallery():
    images = get_images()
    for img in images:
        generate_thumbnail(img)
    return render_template("gallery.html", images=images)


@app.route("/delete/<filename>")
def delete(filename):
    path = os.path.join(PHOTO_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for("gallery"))


@app.route("/photos/<filename>")
def photos(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/edited_photos/<filename>")
def edited_photos(filename):
    # Serve edited photo with a correct mimetype based on actual file contents.
    path = os.path.join(EDITED_DIR, filename)
    if not os.path.exists(path):
        return send_from_directory(EDITED_DIR, filename)

    try:
        img = Image.open(path)
        fmt = (img.format or '').upper()
        if fmt == 'JPEG' or fmt == 'JPG':
            mimetype = 'image/jpeg'
        elif fmt == 'PNG':
            mimetype = 'image/png'
        elif fmt == 'HEIC' or fmt == 'HEIF':
            mimetype = 'image/heif'
        else:
            mimetype = 'application/octet-stream'
    except Exception:
        mimetype = None

    if mimetype:
        return send_file(path, mimetype=mimetype)
    return send_from_directory(EDITED_DIR, filename)


@app.route("/clear_all", methods=["POST"])
def clear_all():
    """Remove all photos in PHOTO_DIR, EDITED_DIR and thumbnails in THUMB_DIR."""
    removed = {"photos": 0, "edited": 0, "thumbs": 0}

    # remove original photos
    try:
        for f in os.listdir(PHOTO_DIR):
            path = os.path.join(PHOTO_DIR, f)
            if os.path.isfile(path) and f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
                try:
                    os.remove(path)
                    removed["photos"] += 1
                except Exception as e:
                    app.logger.warning(f"Failed to remove {path}: {e}")
    except Exception as e:
        app.logger.warning(f"Failed to list PHOTO_DIR: {e}")

    # remove edited photos
    try:
        for f in os.listdir(EDITED_DIR):
            path = os.path.join(EDITED_DIR, f)
            if os.path.isfile(path) and f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
                try:
                    os.remove(path)
                    removed["edited"] += 1
                except Exception as e:
                    app.logger.warning(f"Failed to remove {path}: {e}")
    except Exception as e:
        app.logger.warning(f"Failed to list EDITED_DIR: {e}")

    # remove thumbnails
    try:
        for f in os.listdir(THUMB_DIR):
            path = os.path.join(THUMB_DIR, f)
            if os.path.isfile(path) and f.lower().endswith((".png",)):
                try:
                    os.remove(path)
                    removed["thumbs"] += 1
                except Exception as e:
                    app.logger.warning(f"Failed to remove {path}: {e}")
    except Exception as e:
        app.logger.warning(f"Failed to list THUMB_DIR: {e}")

    app.logger.info(f"Cleared files: {removed}")
    return redirect(url_for("gallery"))


@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    src = os.path.join(PHOTO_DIR, filename)
    thumb = os.path.join(THUMB_DIR, hash_filename(filename) + ".png")

    # choose which image to display on the edit page: edited version if present
    edited_path = os.path.join(EDITED_DIR, filename)
    if os.path.exists(edited_path):
        display_url = url_for('edited_photos', filename=filename)
    else:
        display_url = url_for('photos', filename=filename)

    if request.method == "POST":
        # Determine which action the user requested: 'rotate' or 'crop'
        try:
            action = request.form.get('action', 'crop')

            # Work on the edited image if it exists, otherwise the original
            edited_path = os.path.join(EDITED_DIR, filename)
            work_src = edited_path if os.path.exists(edited_path) else src

            if action == 'rotate':
                # Rotate-only operation (no cropping)
                rotate = int(request.form.get('rotate', 0))
                img = Image.open(work_src)
                img = ImageOps.exif_transpose(img)
                if rotate != 0:
                    img = img.rotate(-rotate, expand=True)

                # save rotated image into the edited folder
                img.save(edited_path)
                generate_thumbnail(filename, force=True)
                return redirect(url_for('edit', filename=filename))

            else:
                # Crop-only operation
                x = int(float(request.form['x']))
                y = int(float(request.form['y']))
                width = int(float(request.form['width']))
                height = int(float(request.form['height']))

                img = Image.open(work_src)
                img = ImageOps.exif_transpose(img)
                img = img.crop((x, y, x + width, y + height))

                # save cropped image into the edited folder (resize to display size and compress)
                try:
                    img = img.convert("RGB")
                    img = img.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT), Image.LANCZOS)
                    ext = os.path.splitext(filename)[1].lower()
                    if ext == '.png':
                        img.save(edited_path, format='PNG', optimize=True)
                    else:
                        img.save(edited_path, format='JPEG', quality=85, optimize=True)
                except Exception:
                    img.save(edited_path)

                generate_thumbnail(filename, force=True)

                return redirect(url_for('edit', filename=filename))

        except Exception as e:
            app.logger.warning(f"Failed to edit {filename}: {e}")
            return "Error processing image", 500

    # GET method: render the editor
    return render_template("edit.html", filename=filename, image_url=display_url)


@app.route("/revert/<filename>", methods=["POST"])
def revert(filename):
    """Delete the edited photo so the original is used again, then regenerate thumbnail."""
    edited_path = os.path.join(EDITED_DIR, filename)
    if os.path.exists(edited_path):
        try:
            os.remove(edited_path)
        except Exception as e:
            app.logger.warning(f"Failed to remove edited file {edited_path}: {e}")

    # regenerate thumbnail from original
    generate_thumbnail(filename, force=True)
    return redirect(url_for('edit', filename=filename))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
