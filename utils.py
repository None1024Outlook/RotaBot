import os
import time
import config
import database
from PIL import Image
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.edge.options import Options

matplotlib.use("Agg")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

songData = database.songData
songAlias = database.songAlias

def compressImage(image_path, max_size_mb=9.5, quality=95):
    max_size_bytes = max_size_mb * 1024 * 1024
    if os.path.getsize(image_path) <= max_size_bytes:
        return image_path
    with Image.open(image_path) as img:
        img.thumbnail((img.width * 0.9, img.height * 0.9), Image.LANCZOS)
        img_format = img.format
        if img_format not in ["JPEG", "JPG", "PNG"]: return image_path
        if img.mode in ["RGBA", "P"]: img = img.convert("RGB")
        output_path = image_path.rsplit(".", 1)[0] + f".{time.time()}.webp"
        try:
            img.save(output_path, format="WEBP", quality=quality, method=6)
            if os.path.getsize(output_path) <= max_size_bytes:
                return output_path
        except: ...
        output_path = image_path.rsplit(".", 1)[0] + f".{time.time()}.jpg"
        img.save(output_path, format="JPEG", quality=quality, optimize=True)
    if os.path.getsize(output_path) > max_size_bytes:
        return compressImage(output_path, max_size_mb=max_size_mb, quality=quality-20)
    else: return output_path

def renderHtmlToImage(window_size, sleep_time, html_path=None, isHTML=False, html_data=None):    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--allow-file-access-from-files")
    options.add_argument("--enable-local-file-accesses")
    options.add_argument("--no-sandbox")
    driver = webdriver.Edge(options=options)
    driver.set_window_size(window_size[0], window_size[1])
    driver.set_page_load_timeout(120)
    driver.set_script_timeout(120)
    driver.implicitly_wait(10)
    if isHTML:
        html_path = f"{config.TEMP_DIR}/{time.time()}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_data)
    abs_html_path = os.path.abspath(html_path)
    file_url = f"file://{abs_html_path}"
    driver.get(file_url)
    time.sleep(sleep_time)
    total_height = driver.execute_script("return document.body.scrollHeight") + 120
    driver.set_window_size(window_size[0], total_height)
    driver.execute_script("document.body.style.overflow = 'hidden';")
    screenshot_path = f"{config.TEMP_DIR}/{time.time()}.png"
    driver.save_screenshot(screenshot_path)
    driver.quit()
    return compressImage(screenshot_path, 9.5)

def drawBarChart(data, labels):
    plt.figure(figsize=(12, 6))
    data_range = max(data) - min(data)
    y_min = min(data) - 0.5 * data_range
    y_max = max(data) + 0.5 * data_range
    x = np.arange(len(labels))
    colors = plt.cm.Blues_r(np.linspace(0.2, 0.6, len(data)))
    plt.bar(x, data, width=0.6, color=colors, edgecolor="navy", linewidth=1, alpha=0.8, label="Rating")
    coeffs = np.polyfit(x, data, min(3, len(data)-1))
    poly = np.poly1d(coeffs)
    plt.plot(x, poly(x), "-", color="green", linewidth=2, label="Trend Line")
    equation = "y = " + " + ".join([
        f"{coeffs[i]:.3f}x^{len(coeffs)-1-i}" 
        for i in range(len(coeffs))
    ]).replace("x^0", "").replace("x^1", "x")
    plt.text(0.02, 0.95, equation, transform=plt.gca().transAxes, fontsize=9, bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"))
    for i, v in enumerate(data):
        plt.text(i, v + 0.01, f" {v:.4f}", ha="center", fontsize=9, rotation=90, bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=0.1))
    plt.xticks(x, labels, rotation=45, ha="right", fontsize=8)
    plt.yticks(np.linspace(y_min, y_max, 15))
    plt.ylim(y_min, y_max)
    plt.ylabel("Rating")
    plt.title("Best40 Rating")
    plt.grid(axis="y", linestyle=":", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    savePath = f"{config.TEMP_DIR}/{time.time()}.png"
    plt.savefig(savePath)
    plt.close()
    return savePath
