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
    

def images_to_pdf(base64_imgs: list[str]) -> str:  # converts more than one image in base 64 to a pdf in base64
    try:
        images = []
        for base64_img in base64_imgs:
            image_data = base64.b64decode(base64_img)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            images.append(image)

        if not images:
            raise ValueError("ERROR: No images were provided.")
        
        pdf_bytes = io.BytesIO()
        images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])
        return base64.b64encode(pdf_bytes.getvalue()).decode("utf-8")
    
    except Exception as e:
        logger.info("ERROR: An error has occurred whilde generating a pdf from one or more images")
        logger.info(str(e))
        raise HTTPException(status_code=500, detail="Failed to convert images to pdf.")

