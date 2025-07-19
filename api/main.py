from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scansheet_agent.agent import ScanSheetAgent
from scansheet_agent.prompt import PromptBuilder
from dotenv import load_dotenv
from utils.encoder import merge_base64_images
import os
# import json
import logging

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scansheet_api")

# Load environment variables
load_dotenv()

# Initialize application
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allows all (not secure)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key
api_key = os.getenv("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY is missing. Check your .env file.")


# Initialize agent
agent = ScanSheetAgent(api_key=api_key, model="gpt-4.1")
prompt_builder = PromptBuilder()

@app.post("/process-image")
async def process_image(request: Request):
    try:
        data = await request.json()

        # Input fields
        image_list = data.get("image_bytes", []) # list of images in byte form
        title = data.get("title", "GenericForm")

        if not image_list or not isinstance(image_list, list):
            raise HTTPException(status_code=400, detail="'image_bytes' must be a list of base64-encoded strings.")

        # Concatenate image(s)
        try:
            image_base64 = merge_base64_images(image_list)
        except Exception:
            raise HTTPException(status_code=418, detail="Invalid image data.")

        variables = {
            "image_base64": image_base64,
            "title": title
        }

        # Build the prompt
        prompt = prompt_builder.create_prompt(
            variables=variables
        )

        # Run the agent
        response = agent.run(prompt=prompt)

        logger.info("Agent successfully responded.")
        logger.info(str(response))

        return JSONResponse(content={"table": response})

    except HTTPException as e:
        logger.info("ERROR: An exception has ocurred.")
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.info("ERROR: Agent error.")
        return JSONResponse(content={"error": str(e)}, status_code=500)

