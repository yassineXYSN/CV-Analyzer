import fitz  # PyMuPDF
import os
import requests
import sys
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# Configuration
OCR_API_KEY = os.getenv("OCR_API_KEY")
OCR_API_URL = "https://api.ocr.space/parse/image"
OCR_LANGUAGE = "fre"  # French for this CV

def ocr_space_image(image_bytes, filename, api_key=OCR_API_KEY):
    """Extract text from image bytes using OCR.space API"""
    headers = {'apikey': api_key}
    payload = {
        'language': OCR_LANGUAGE,
        'isOverlayRequired': False,
        'filetype': Path(filename).suffix[1:],
    }
    
    try:
        response = requests.post(
            OCR_API_URL,
            files={'file': (filename, image_bytes)},
            data=payload,
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        if result['IsErroredOnProcessing']:
            return f"OCR Error: {result['ErrorMessage'][0]}"
        
        return result['ParsedResults'][0]['ParsedText'].strip()
    
    except Exception as e:
        return f"OCR Processing Error: {str(e)}"

def process_file(file_path):
    """Process PDF or image file and extract text"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    mime_type, _ = mimetypes.guess_type(file_path)
    
    if mime_type == 'application/pdf':
        return process_pdf(file_path)
    elif mime_type and mime_type.startswith('image/'):
        return process_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

def process_pdf(file_path):
    """Extract text and images from PDF with layout preservation"""
    extracted_text = ""
    images_text = []
    
    try:
        doc = fitz.open(file_path)
        
        # Extract text with layout preservation
        for page in doc:
            # Get text blocks in natural reading order
            blocks = page.get_text("blocks", sort=True)
            
            # Group text by columns (assuming 2-column layout)
            left_col = []
            right_col = []
            col_threshold = page.rect.width * 0.4  # 40% width as separator
            
            for block in blocks:
                if block[6] == 0:  # Text block type
                    x_center = (block[0] + block[2]) / 2
                    if x_center < col_threshold:
                        left_col.append(block[4].strip())  # Block text
                    else:
                        right_col.append(block[4].strip())
            
            # Combine columns while preserving order
            page_text = "\n".join(left_col) + "\n" + "\n".join(right_col)
            extracted_text += page_text + "\n\n"
            
            # Extract and OCR images
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                filename = f"page{page.number+1}_img{img_index+1}.{ext}"
                
                try:
                    img_text = ocr_space_image(image_bytes, filename)
                    images_text.append(img_text)
                except Exception as e:
                    images_text.append(f"Error processing image: {str(e)}")
        
        doc.close()
        return extracted_text.strip(), images_text
    
    except Exception as e:
        raise RuntimeError(f"PDF Processing Error: {str(e)}")

def process_image(file_path):
    """Process single image file"""
    try:
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        text = ocr_space_image(image_bytes, os.path.basename(file_path))
        return "", [text]
    except Exception as e:
        raise RuntimeError(f"Image Processing Error: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python text_extractor.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        pdf_text, images_text = process_file(file_path)
        
        print("\n" + "="*50)
        print("Extracted text from PDF:")
        print("="*50)
        print(pdf_text)
        
        if images_text:
            print("\n" + "="*50)
            print("Extracted text from images:")
            print("="*50)
            for i, text in enumerate(images_text):
                print(f"\nImage {i+1}:\n{'-'*40}")
                print(text)
    
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()