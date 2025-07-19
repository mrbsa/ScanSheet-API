from io import BytesIO
from PIL import Image
import base64
import logging

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("encoder_utils")

def merge_base64_images(image_list):  # vertically stacks images into a single one
    decoded_images = []

    for img_base64 in image_list:
        try:  # decode images
            img_bytes = base64.b64decode(img_base64) 
            img = Image.open(BytesIO(img_bytes))
            decoded_images.append(img)
        except Exception as e:
            logger.info("ERROR: An error happened while decoding images.")
            logger.info(str(e))
            continue

    if not decoded_images:
        return None

    total_width = max(img.width for img in decoded_images)  # same width
    total_height = sum(img.height for img in decoded_images)  # joined height (vertical stacking)

    merged_image = Image.new('RGB', (total_width, total_height), 'white') 

    y_offset = 0
    for img in decoded_images:  # add decoded images
        merged_image.paste(img, (0, y_offset))
        y_offset += img.height

    buffer = BytesIO()
    merged_image.save(buffer, format='PNG')
    merged_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')  # re-encode merged image

    return merged_base64  # returns a single base64 encoded image