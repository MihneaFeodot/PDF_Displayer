import fitz  # PyMuPDF
import time
import os
import sys
import keyboard  # Detects when "C" is pressed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define how long each pair of pages is displayed (in seconds)
DISPLAY_TIME = 60  # 1-minute display per slide

# Function to get the correct path for `viewer.html`
def get_viewer_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  # Running as an .exe with PyInstaller
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Normal Python script
    return os.path.join(base_path, "pdf_viewer_more_zoomed_preview.html")

# Configure Selenium with WebDriver Manager
chrome_options = Options()
chrome_options.add_argument("--window-size=1024,768")  # Ensure correct display size
chrome_options.add_argument("--window-position=1920,0")  # Move to HDMI display (adjust if needed)
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

# Use WebDriver Manager to auto-install ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Load PDF and extract pages as images
pdf_path = "document.pdf"  # Change to your PDF file
output_folder = "pdf_pages"
os.makedirs(output_folder, exist_ok=True)

doc = fitz.open(pdf_path)
image_files = []

for i in range(len(doc)):
    page = doc[i]
    pix = page.get_pixmap()
    img_path = os.path.join(output_folder, f"page_{i + 1}.png")
    pix.save(img_path)
    image_files.append(img_path)

# Group images in pairs (Two pages per view)
pairs = [(image_files[i], image_files[i+1] if i+1 < len(image_files) else "") 
         for i in range(0, len(image_files), 2)]

# Open the existing `viewer.html`
html_path = get_viewer_path()
if not os.path.exists(html_path):
    print(f"❌ ERROR: viewer.html not found at {html_path}")
    sys.exit()

print(f"✅ Loading viewer.html from {html_path}")
driver.get(f"file:///{html_path.replace('\\', '/')}")

# Wait for the HTML page to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "pdf-image1"))
    )
    print("✅ HTML page loaded successfully!")
except Exception as e:
    print(f"❌ ERROR: HTML page did not load: {e}")
    driver.quit()
    sys.exit()

print("\n🎬 Slideshow started! Press 'C' to stop.\n")

# Display images in a loop until the user presses "C"
while not keyboard.is_pressed('c'):
    for img1, img2 in pairs:
        img1_path = os.path.abspath(img1).replace("\\", "/")
        img2_path = os.path.abspath(img2).replace("\\", "/") if img2 else ""

        # Ensure JavaScript function is ready
        try:
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return typeof updateImages === 'function'"))
        except Exception as e:
            print(f"❌ ERROR: JavaScript function not found: {e}")
            driver.quit()
            sys.exit()

        # Update images in the HTML
        print(f"🔄 Displaying: {img1_path} and {img2_path}")
        driver.execute_script(f"updateImages('file:///{img1_path}', 'file:///{img2_path}')")
        time.sleep(DISPLAY_TIME)  # Wait 60 seconds before next pair

        if keyboard.is_pressed('c'):
            print("\n🛑 Slideshow stopped by user.")
            break

# Close the browser after stopping
print("✅ Finished displaying images.")
driver.quit()
sys.exit()
