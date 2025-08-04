from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scansheet_agent.agent import ScanSheetAgent
from scansheet_agent.prompt import PromptBuilder
from starlette.middleware.base import BaseHTTPMiddleware ##
from dotenv import load_dotenv
# from utils.encoder import base64_image_to_pdf
from PIL import Image
import os
# import json
import logging
import base64
import io

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scansheet_api")

# Load environment variables
load_dotenv()

auth_secret = os.getenv("AUTH_TOKEN")
if not auth_secret:
    raise RuntimeError("No authorization token was found.")

gpt_api_key = os.getenv("GPT_API_KEY")
if not gpt_api_key:
    raise RuntimeError("API_KEY for chat-gpt is missing. Check your .env file.")

mistral_api_key = os.getenv("MISTRAL_API_KEY")
if not gpt_api_key:
    raise RuntimeError("API_KEY for mistral is missing. Check your .env file.")

app = FastAPI()

# Enable Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "Authorization"],
)

agent = ScanSheetAgent(
    chat_gpt_model="gpt-4.1", 
    chat_gpt_api_key=gpt_api_key,
    mistral_api_key=mistral_api_key
)
prompt_builder = PromptBuilder()

def image_to_pdf(base64_img: str) -> str:  # converts an image in base 64 to a pdf in base64 
    try:
        image_data = base64.b64decode(base64_img)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, format="PDF")
        return base64.b64encode(pdf_bytes.getvalue()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to convert image to pdf.")


class LogOriginMiddleware(BaseHTTPMiddleware):  ##
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        logger.info(f" Origem da requisição: {origin}")
        response = await call_next(request)
        return response

app.add_middleware(LogOriginMiddleware)  ##

@app.post("/process-image")
async def process_image(request: Request, authorization: str = Header(...)):
    if authorization != auth_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        
        # Input fields
        image_list = data.get("image_bytes", [])  # list of images in byte form
        title = data.get("title", "GenericForm")

        if not image_list or not isinstance(image_list, list):
            raise HTTPException(status_code=400, detail="'image_bytes' must be a list of base64-encoded strings.")

        res = ""

        for i, img_base64 in enumerate(image_list):
            try:  
                pdf_base64 = image_to_pdf(img_base64)  #  convert images to pdf (base64 encoded)
            except Exception:
                raise HTTPException(status_code=418, detail=f"Invalid image data at index {i}.")

            variables = {
                "image_base64": img_base64,
                "pdf_base64": pdf_base64,
                "title": title
            }

            # Build the prompt
            prompt = prompt_builder.create_prompt(variables=variables)

            # Run the agent
            response = agent.run(prompt=prompt)
            res += response + ", \n" 

        logger.info("Agent successfully responded for all images.")
        return JSONResponse(content={"table": res.strip()})

    except HTTPException as e:
        logger.info("ERROR: An exception has occurred.")
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.info("ERROR: Agent error.")
        return JSONResponse(content={"error": str(e)}, status_code=500)
