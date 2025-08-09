from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scansheet_agent.agent import ScanSheetAgent
from utils.pdf_generator import image_to_pdf, images_to_pdf
from utils.encryption import encrypt, decrypt
from utils.img_merger import merge_base64_images
from dotenv import load_dotenv
import logging
import os

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scansheet_api")

# Load environment variables
load_dotenv()

auth_secret = os.getenv("AUTH_TOKEN")  # requester credentials
if not auth_secret:
    raise RuntimeError("No authorization token was found.")

symm_key = os.getenv("SYMMETRIC_KEY")  # payload crytographic decodification
if not symm_key:
    raise RuntimeError("No symmetric cryptography key was found.")

gpt_api_key = os.getenv("GPT_API_KEY")  # pre-paid gpt-api key
if not gpt_api_key:
    raise RuntimeError("API_KEY for chat-gpt is missing. Check your .env file.")

mistral_api_key = os.getenv("MISTRAL_API_KEY")  # mistral-api key
if not mistral_api_key:
    raise RuntimeError("API_KEY for mistral is missing. Check your .env file.")

app = FastAPI()

# Enable Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # whitelist origin(s) if front-end is published in the web (currently iOS only)
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "Authorization"],
)

agent = ScanSheetAgent(
    chat_gpt_model="gpt-4.1", 
    chat_gpt_api_key=gpt_api_key,
    mistral_api_key=mistral_api_key
)


@app.post("/process-image")
async def process_image(request: Request, authorization: str = Header(...)):
    logger.info("Check requester credentials.")
    if authorization != auth_secret:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    
    try:
        origin = request.headers.get("origin")  # will be None if requester uses iOS native features (current)
        logger.info(f"Requisition origin: {origin}.")
    
        encrypted_data = await request.json()
        try:
            data = decrypt(encrypted_data.get("payload"), symm_key)
        except HTTPException as e:
            logger.info('decrypt func error')
            raise e
        except Exception:
            logger.info('decryption gone wrong')
            raise HTTPException(status_code=418, detail=f"Data could not be decrypted.")
        
        # Input fields
        image_list = data.get("image_bytes", [])  # list of images in byte form
        title = data.get("title", "GenericForm")

        if not image_list or not isinstance(image_list, list):
            logger.info('image_bytes error')
            raise HTTPException(status_code=400, detail="'image_bytes' must be a list of base64-encoded strings.")

        table = []
        
        logger.info("Start image processing.")

        if title == 'ficha_cadastro_individual':  # processes images as a single file (assuming they are pages of a same document)
            try:  
                pdf_base64 = images_to_pdf(image_list)  #  convert images into paged pdf (base64 encoded)
                img_base64 = merge_base64_images(image_list)  # merge images (pages) into a single one
            except HTTPException as e:
                logger.info(f'image {i} processing error')
                raise e
            except Exception:
                logger.info(f'image at {i} could not be processed')
                raise HTTPException(status_code=418, detail=f"Invalid image data at index {i}.")

            variables = {
                "image_base64": img_base64,
                "pdf_base64": pdf_base64,
                "title": title
            }

            # Run the agent
            try:
                response = agent.run(variables=variables)
            except Exception as e:
                logger.info(str(e))
            table.append(response)

            logger.info(str(response))

        else:  # processes images individually
            for i, img_base64 in enumerate(image_list):
                try:  
                    pdf_base64 = image_to_pdf(img_base64)  #  convert images to pdf (base64 encoded)
                except HTTPException as e:
                    logger.info(f'image {i} processing error')
                    raise e
                except Exception:
                    logger.info(f'image at {i} could not be processed')
                    raise HTTPException(status_code=418, detail=f"Invalid image data at index {i}.")

                variables = {
                    "image_base64": img_base64,
                    "pdf_base64": pdf_base64,
                    "title": title
                }

                # Run the agent
                try:
                    response = agent.run(variables=variables)
                except Exception as e:
                    logger.info(str(e))
                table.append(response)

                logger.info(str(response))

        logger.info(f'Number of images processed: {i + 1}')
        encrypted_table = encrypt(table, symm_key)
        logger.info("Agent successfully responded to all images.")
        logger.info(str(table))

        return JSONResponse(content={"table": encrypted_table})

    except HTTPException as e:
        logger.info("ERROR: An exception has occurred.")
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.info("ERROR: Agent error.")
        return JSONResponse(content={"error": str(e)}, status_code=500)
