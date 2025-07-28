from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scansheet_agent.agent import ScanSheetAgent
from scansheet_agent.prompt import PromptBuilder
from dotenv import load_dotenv
from utils.encoder import base64_image_to_pdf
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY is missing. Check your .env file.")

agent = ScanSheetAgent(api_key=api_key, model="gpt-4.1")
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

@app.post("/process-image")
async def process_image(request: Request):
    try:
        data = await request.json()
        
        # Input fields
        image_list = data.get("image_bytes", [])  # list of images in byte form
        title = data.get("title", "GenericForm")

        if not image_list or not isinstance(image_list, list):
            raise HTTPException(status_code=400, detail="'image_bytes' must be a list of base64-encoded strings.")

        res = ""

        for i, img in enumerate(image_list):
            try:  # Convert images to pdf (base64 encoded)
                pdf_base64 = image_to_pdf(img)  #  PDF? JPEG?
            except Exception:
                raise HTTPException(status_code=418, detail=f"Invalid image data at index {i}.")

            variables = {
                "image_base64": pdf_base64,
                "title": f"{title}_page_{i + 1}"
            }

            # Build the prompt
            prompt = prompt_builder.create_prompt(variables=variables)

            # Run the agent
            response = agent.run(prompt=prompt)
            res += response + "\n"  # join agent responses into a single one WRONG: NOT A JSON

        logger.info("Agent successfully responded for all images.")
        return JSONResponse(content={"table": res.strip()})

    except HTTPException as e:
        logger.info("ERROR: An exception has occurred.")
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.info("ERROR: Agent error.")
        return JSONResponse(content={"error": str(e)}, status_code=500)
