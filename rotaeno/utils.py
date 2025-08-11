import os
import tempfile
from PIL import Image
from playwright.sync_api import sync_playwright

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, "temp")

def compress_image(image_path, max_size_mb=9.5, quality=95):
    max_size_bytes = max_size_mb * 1024 * 1024
    if os.path.getsize(image_path) > max_size_bytes:
        with Image.open(image_path) as img:
            img.thumbnail((img.width * 0.9, img.height * 0.9), Image.LANCZOS)
            img_format = img.format
            if img_format not in ["JPEG", "JPG", "PNG"]:
                return image_path
            if img.mode in ["RGBA", "P"]:
                img = img.convert("RGB")
            try:
                with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".webp", dir=TEMP_DIR) as tmp:
                    output_path = tmp.name
                    img.save(output_path, format="WEBP", quality=quality, method=6)
                    if os.path.getsize(output_path) <= max_size_bytes: return output_path
            except:
                ...
            with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".jpg", dir=TEMP_DIR) as tmp:
                output_path = tmp.name
                img.save(output_path, format="JPEG", quality=quality, optimize=True)
    else:
        return image_path
    if os.path.getsize(output_path) > max_size_bytes:
        return compress_image(output_path, max_size_mb=max_size_mb, quality=quality-20)
    else:
        return output_path

def render_html_to_jpg(window_size, html=None, html_path=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": window_size[0], "height": window_size[1]})
        page = context.new_page()

        try:
            if html is not None:
                with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".html", dir=TEMP_DIR) as tmp:
                    html_path = tmp.name
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html)

            abs_html_path = os.path.abspath(html_path)
            file_url = f"file://{abs_html_path}"

            page.goto(file_url, wait_until="load")

            total_height = page.evaluate("document.body.scrollHeight")
            page.set_viewport_size({"width": window_size[0], "height": total_height})
            page.evaluate("document.body.style.overflow = 'hidden';")

            with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".png", dir=TEMP_DIR) as tmp:
                screenshot_path = tmp.name
                page.screenshot(path=screenshot_path, timeout=180000, full_page=True)
        finally:
            browser.close()

    return compress_image(screenshot_path, 9.5)
