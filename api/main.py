from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scansheet_agent.agent import ScanSheetAgent
from scansheet_agent.prompt import PromptBuilder
from dotenv import load_dotenv
import base64
import os
# import json
# import logging

# logging.basicConfig(level=logging.info)

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
            decoded_list = [base64.b64decode(img) for img in image_list]  # decode images to bytes
            joined_bytes = b"".join(decoded_list)  # join byte images into a single one
            image_base64 = base64.b64encode(joined_bytes).decode('utf-8')  # re-encode single image as required by the library
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
        print(response)
        return JSONResponse(content={"table": response})

    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
