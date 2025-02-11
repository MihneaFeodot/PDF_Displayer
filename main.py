import fitz  # PyMuPDF for extracting pages
import time
import os
import keyboard  # Detects when "C" is pressed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

# Define how long each pair of pages is displayed (in seconds)
DISPLAY_TIME = 10  # Change this value easily

# 1. Configure Selenium with WebDriver Manager
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Open full screen
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

# Use WebDriver Manager to auto-install the correct ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 2. Load PDF and extract pages as images
pdf_path = "document.pdf"  # Change to the actual PDF file path
output_folder = "pdf_pages"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Open PDF and extract pages as images
doc = fitz.open(pdf_path)
image_files = []

for i in range(len(doc)):
    page = doc[i]
    pix = page.get_pixmap()
    img_path = os.path.join(output_folder, f"page_{i + 1}.png")
    pix.save(img_path)
    image_files.append(img_path)

# 3. Group images in pairs (Ensure two pages at a time)
pairs = [(image_files[i], image_files[i+1] if i+1 < len(image_files) else "") 
         for i in range(0, len(image_files), 2)]

# 4. Open the existing `viewer.html`
html_path = os.path.abspath("viewer.html")  # Ensure it's an absolute path
print(f"Opening HTML file: {html_path}")
driver.get(f"file://{html_path}")

# Wait until the images are present
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

# 5. Display images in a loop until the user presses "C"
while not keyboard.is_pressed('c'):
    for img1, img2 in pairs:
        img1_path = os.path.abspath(img1).replace("\\", "/")
        img2_path = os.path.abspath(img2).replace("\\", "/") if img2 else ""

        # Ensure JavaScript function is ready before updating images
        try:
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return typeof updateImages === 'function'"))
        except Exception as e:
            print(f"❌ ERROR: JavaScript function not found: {e}")
            driver.quit()
            sys.exit()

        # Update images in the HTML using JavaScript
        print(f"🔄 Displaying: {img1_path} and {img2_path}")
        driver.execute_script(f"updateImages('file://{img1_path}', 'file://{img2_path}')")
        time.sleep(DISPLAY_TIME)

        if keyboard.is_pressed('c'):
            print("\n🛑 Slideshow stopped by user.")
            break

# Close the browser after stopping
print("✅ Finished displaying images.")
driver.quit()
