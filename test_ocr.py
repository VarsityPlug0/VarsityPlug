import pytesseract
from PIL import Image
import cv2
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Path to your matric certificate image
img_path = r'C:\Users\money\OneDrive\Pictures\Screenshots\sample_matric.png'

# Verify file exists
if not os.path.exists(img_path):
    print(f"Error: File not found at {img_path}. Please check the path and file name.")
else:
    # Load and process image
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not load image from {img_path}. Check file integrity or path.")
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        print("Extracted Text:")
        print(text)