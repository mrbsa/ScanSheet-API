from fastapi import HTTPException
from PIL import Image
import logging
import base64
import io

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdfgenerator_utils")

def image_to_pdf(base64_img: str) -> str:  # converts an image in base 64 to a pdf in base64 
    try:
        image_data = base64.b64decode(base64_img)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, format="PDF")
        return base64.b64encode(pdf_bytes.getvalue()).decode("utf-8")
    
    except Exception as e:
        logger.info("ERROR: An error has occurred while generating a pdf from an image.")
        logger.info(str(e))
        
        raise HTTPException(status_code=500, detail="Failed to convert image to pdf.")